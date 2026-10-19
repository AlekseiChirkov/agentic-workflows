---
trigger: always_on
---
# Testing Standards

---

## Philosophy: Test Behavior, Not Implementation

Tests document what the system does, not how it does it.
A test that breaks on refactoring without behavior change is a bad test.

```python
# Wrong — tests implementation detail
def test_order_calls_repository_save():
    repo = Mock()
    use_case = CreateOrderUseCase(repo)
    use_case.execute(command)
    repo.save.assert_called_once()  # testing internals

# Correct — tests observable behavior
async def test_created_order_is_retrievable():
    repo = InMemoryOrderRepository()
    use_case = CreateOrderUseCase(repo)
    
    order = await use_case.execute(CreateOrderCommand(customer_id=uuid4(), items=[...]))
    
    saved = await repo.get_by_id(order.id)
    assert saved is not None
    assert saved.status == OrderStatus.PENDING
```

---

## TDD Workflow with AI

Every feature follows this sequence — no exceptions:

```
1. SPEC       → write spec in .ai/specs/ with Acceptance Criteria
2. TESTS      → AI generates tests from Acceptance Criteria
3. REVIEW     → YOU review tests (this is the critical gate)
4. IMPLEMENT  → AI writes implementation to pass tests
5. VERIFY     → all tests green, lint passes
6. REVIEW     → you review architecture decisions only
```

**Why reviewing tests is more important than reviewing code:**
Correct tests + wrong code = tests catch the bug.
Wrong tests + correct code = you've built the wrong thing and don't know it.

### Where this sequence is executed

This sequence is not advisory — it is enforced by the pipeline:

| Step above | Executed by |
|---|---|
| 1. SPEC | `/phase-discovery` → `.ai/specs/` + `T-XX/description.md → ## Acceptance Criteria` |
| — plan | `/pd-decompose` → `T-XX/description.md → ## Test Plan` (level + scenario per criterion) |
| 2. TESTS | **`/pae-tests`** — writes the tests and observes them fail (RED) |
| 3. REVIEW | `/pae-tests` review gate — AC→test mapping presented before implementation |
| 4. IMPLEMENT | `/pae-implement` — implements until the RED set passes (GREEN), set frozen |
| 5. VERIFY | `/pae-implement → Final Verification` — GREEN check + regression run + lint |
| 6. REVIEW | `/pav-check` (test-set audit) → `/pv-review` (architecture) |

The process contract — the test-level gate, what counts as RED, and what implementation may
not do to a test — lives in the **`tdd`** rule. This file governs test *style*; that rule
governs test *process*. Where a project's `flow: quick` tier applies, the same sequence runs
inline against `## Contract (quick)` — see `quick-flow`.

---

## Test Structure: AAA

Every test follows Arrange → Act → Assert. No exceptions.

```python
async def test_order_cannot_exceed_maximum_items():
    # Arrange
    repo = InMemoryOrderRepository()
    use_case = CreateOrderUseCase(repo, event_bus=FakeEventBus())
    command = CreateOrderCommand(
        customer_id=uuid4(),
        items=[OrderItemDTO(product_id=uuid4(), quantity=1)] * 51,  # over limit
    )

    # Act & Assert
    with pytest.raises(OrderValidationError, match="maximum 50 items"):
        await use_case.execute(command)
```

---

## What to Test

| Layer | Test type | What to cover |
|-------|-----------|---------------|
| Domain entities | Unit | Business rules, state transitions, validation |
| Use cases | Unit (with InMemory repos) | Happy path, all error paths, edge cases |
| Repositories | Integration | Real DB queries, transactions, constraints |
| Routers | Integration | HTTP contract: status codes, response schema, auth |
| End-to-end | E2E (few) | Critical user journeys only |

**Coverage targets:**
- Domain + Use cases: 90%+
- Infrastructure: 70%+ (integration tests are expensive)
- API layer: 80%+ (contract tests)
- E2E: cover top 3-5 critical paths only

---

## InMemory Repositories — Required Pattern

Never mock repositories directly. Always use InMemory implementations.

```python
# tests/fakes/repositories.py
class InMemoryOrderRepository:
    def __init__(self) -> None:
        self._store: dict[UUID, Order] = {}

    async def get_by_id(self, order_id: UUID) -> Order | None:
        return self._store.get(order_id)

    async def save(self, order: Order) -> Order:
        self._store[order.id] = order
        return order

    async def delete(self, order_id: UUID) -> None:
        self._store.pop(order_id, None)

    # Test helpers — not part of the Protocol
    def all(self) -> list[Order]:
        return list(self._store.values())

    def count(self) -> int:
        return len(self._store)
```

**Why:** InMemory implementations test the full use case logic including repository interaction patterns. Mocks test nothing but call signatures.

---

## Test Naming

Test name = what behavior is being verified.

```python
# Wrong
def test_create_order():
def test_order_error():
def test_1():

# Correct
async def test_order_creation_publishes_order_created_event():
async def test_cancelled_order_cannot_be_shipped():
async def test_order_with_zero_quantity_item_raises_validation_error():
```

Pattern: `test_<subject>_<condition>_<expected_outcome>`

---

## Fixtures

```python
# conftest.py
import pytest
from tests.fakes.repositories import InMemoryOrderRepository
from tests.fakes.event_bus import FakeEventBus

@pytest.fixture
def order_repo() -> InMemoryOrderRepository:
    return InMemoryOrderRepository()

@pytest.fixture
def event_bus() -> FakeEventBus:
    return FakeEventBus()

@pytest.fixture
def create_order_use_case(order_repo, event_bus) -> CreateOrderUseCase:
    return CreateOrderUseCase(order_repo=order_repo, event_publisher=event_bus)

# Reusable domain object builders
@pytest.fixture
def valid_order_command() -> CreateOrderCommand:
    return CreateOrderCommand(
        customer_id=uuid4(),
        items=[OrderItemDTO(product_id=uuid4(), quantity=2)],
        delivery_address="123 Main St, City, Country",
    )
```

---

## Edge Cases Checklist

AI must generate tests for these categories for every use case:

- [ ] Happy path — correct inputs, expected output
- [ ] Empty / null inputs — `None`, empty list, empty string
- [ ] Boundary values — min/max quantities, lengths, amounts
- [ ] Duplicate operations — create twice, delete twice
- [ ] Invalid state transitions — cancel shipped order, ship cancelled order
- [ ] Missing dependencies — entity not found (returns `None` from repo)
- [ ] Concurrent operations — if applicable (optimistic locking)
- [ ] Permission boundaries — unauthorized access

---

## Integration Test Pattern

```python
# tests/integration/test_order_repository.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@pytest.fixture(scope="session")
async def db_engine():
    engine = create_async_engine("postgresql+asyncpg://test:test@localhost/test_db")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def session(db_engine):
    async with AsyncSession(db_engine) as session:
        yield session
        await session.rollback()  # always rollback after test

async def test_order_repository_saves_and_retrieves(session):
    repo = PostgresOrderRepository(session)
    order = Order(id=uuid4(), status=OrderStatus.PENDING, customer_id=uuid4())
    
    await repo.save(order)
    retrieved = await repo.get_by_id(order.id)
    
    assert retrieved is not None
    assert retrieved.id == order.id
    assert retrieved.status == order.status
```

---

## Forbidden in Tests

- `Mock()` for repository interfaces — use InMemory implementations
- `time.sleep()` in tests — use time mocking or async fixtures
- Tests that depend on execution order
- Hardcoded IDs or dates — use `uuid4()` and `datetime.utcnow()`
- Assertions on internal state of objects not exposed via public interface
- `assert True` or `assert result is not None` as the only assertion
