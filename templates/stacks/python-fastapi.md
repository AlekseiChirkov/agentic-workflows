# Stack: Python / FastAPI / GCP
# Append to AGENTS.md → ## Standards when using this stack.
# setup-new-project.sh handles this automatically when stack=python-fastapi is selected.

---

## Architecture: Clean Layered Structure

Layer boundaries are strict. Dependencies flow INWARD only — never outward.

```
api/              → HTTP contract only: routing, request parsing, response mapping
application/      → use cases and orchestration — no business logic, no I/O
domain/           → entities, business rules, pure functions — NO I/O, NO framework imports
infrastructure/   → DB, external APIs, cloud services, messaging
```

**Hard rules:**
- Domain MUST NOT import from infrastructure or application
- Use cases MUST NOT import from api layer
- Routers MUST NOT contain business logic — delegate entirely to use cases
- ORM models MUST NOT cross into domain — use `to_domain()` / `from_domain()`

**Violation signal:** needing to import an infrastructure class into domain means the design
is wrong. Introduce a Protocol in domain, implement it in infrastructure.

**Project structure:**
```
src/
├── domain/
│   ├── entities/         # Pure Python dataclasses or frozen Pydantic models
│   ├── repositories/     # Protocol interfaces only — no implementations
│   ├── services/         # Pure business logic, no I/O
│   └── exceptions.py     # Domain exception hierarchy
├── application/
│   └── use_cases/        # One file per use case
├── infrastructure/
│   ├── database/
│   │   ├── models/       # SQLAlchemy ORM models
│   │   └── repositories/ # Concrete repository implementations
│   ├── external/         # Third-party API clients
│   └── gcp/              # Cloud-specific adapters
├── api/
│   ├── routers/          # FastAPI routers, one per domain entity
│   ├── schemas/          # Pydantic request/response schemas
│   └── dependencies.py   # FastAPI Depends() factories
├── config.py             # Pydantic Settings
└── main.py               # FastAPI app factory
```

---

## SOLID — Practical Rules

**Single Responsibility** — one reason to change per module.
- Signal of violation: "and" in the function name (`validate_and_save_user`).
- Fix: split into `validate_user` + `save_user`, compose in use case.

**Open/Closed** — extend via new code, not by modifying existing.
- Prefer Strategy pattern over growing if/elif chains.
- Signal: adding a new `if type == "X"` branch to existing logic.

**Liskov Substitution** — subtypes must be substitutable for base type without surprises.
- If overriding a method changes its contract — use composition, not inheritance.
- Protocol/ABC implementations must honor the full contract.

**Interface Segregation** — small, focused interfaces.
- Use `Protocol` with minimal method sets.
- Never force implementors to define unused methods.

**Dependency Inversion** — depend on abstractions, not concretions.
- Use cases receive repositories and services via constructor injection.
- Never instantiate infrastructure classes inside domain or application layers.

---

## Repository Pattern — Required for All Data Access

Every data source (DB, external API, cache) is accessed through a Repository Protocol.

```python
# domain/repositories/order_repository.py
from typing import Protocol
from uuid import UUID
from domain.entities.order import Order

class OrderRepository(Protocol):
    async def get_by_id(self, order_id: UUID) -> Order | None: ...
    async def save(self, order: Order) -> Order: ...
    async def delete(self, order_id: UUID) -> None: ...
```

- Protocol lives in `domain/` — domain owns the interface
- Implementation lives in `infrastructure/database/repositories/`
- Tests use `InMemory*` implementations — never mock repositories directly

---

## Dependency Injection

Use cases receive all dependencies via constructor. No service locators. No global state.

```python
class CreateOrderUseCase:
    def __init__(
        self,
        order_repo: OrderRepository,
        event_publisher: EventPublisher,
        payment_service: PaymentService,
    ) -> None:
        self._order_repo = order_repo
        self._event_publisher = event_publisher
        self._payment_service = payment_service

    async def execute(self, command: CreateOrderCommand) -> Order:
        ...
```

---

## Naming: Explicit Over Clever

| Bad | Good | Why |
|-----|------|-----|
| `process(data, mode)` | `process_payment(payload: PaymentDTO, mode: ProcessingMode)` | Intent clear |
| `user_service.py` | `user_registration_service.py` | Specific responsibility |
| `handle()` | `handle_order_cancellation()` | No ambiguity |
| `flag` | `is_email_verified` | Boolean reads as predicate |

**Rules:**
- Functions: verb + noun (`create_order`, `validate_email`, `publish_event`)
- Classes: noun describing the concept (`OrderRepository`, `PaymentProcessor`)
- Booleans: `is_`, `has_`, `can_`, `should_` prefix
- No abbreviations except: `id`, `url`, `dto`, `api`, `db`

---

## Functions and Classes

**Functions:**
- Maximum 30 lines — if longer, extract
- Maximum 3 parameters — if more, introduce a DTO/dataclass
- Single level of abstraction per function
- No side effects in query functions (`get_`, `find_`, `calculate_`)

**Classes:**
- Constructor only sets state — no I/O, no computation
- Prefer composition over inheritance. Max 1 level of inheritance for domain entities
- Dataclasses / Pydantic models for data containers. Classes with methods for behavior

---

## Error Handling

```python
# Wrong
try:
    result = db.execute(query)
except Exception:
    return None

# Correct
try:
    result = await self._session.execute(query)
except SQLAlchemyError as e:
    raise RepositoryError(f"Failed to fetch order {order_id}") from e
```

- Never use bare `except:` or `except Exception:` without re-raise or explicit logging
- Define domain exceptions in `domain/exceptions.py`
- Raise early, catch late — validate at boundaries, let domain raise domain exceptions
- Always include context: `OrderNotFoundError(f"Order {order_id} not found")`
- Infrastructure exceptions must be wrapped before crossing layer boundaries

---

## Python Standards

**Type hints — mandatory:**
```python
# Wrong
def get_user(user_id):
    ...

# Correct
async def get_user(user_id: UUID) -> User | None:
    ...
```

- `X | None` not `Optional[X]`
- `X | Y` not `Union[X, Y]`
- Built-in generics: `list[str]`, `dict[str, int]`
- No `Any` without explanation comment

**Pydantic v2 — for all external data:**
```python
class CreateOrderRequest(BaseModel):
    customer_id: UUID
    items: list[OrderItemDTO] = Field(min_length=1)
    delivery_address: str = Field(min_length=10, max_length=500)
```
- Request/Response schemas live in `api/schemas/`
- Domain entities use `dataclass` or frozen Pydantic — never plain Pydantic as domain entity

**Async rules:**

| Situation | Use |
|-----------|-----|
| DB queries, external HTTP, file I/O | `async def` |
| CPU-bound computation | `def` (sync) |
| Pure business logic | `def` (sync) |

- Never `await` inside list comprehensions — use `asyncio.gather()`
- Never `time.sleep()` in async code — use `asyncio.sleep()`

**FastAPI routers:**
```python
@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    request: CreateOrderRequest,
    use_case: CreateOrderUseCase = Depends(get_create_order_use_case),
) -> OrderResponse:
    try:
        order = await use_case.execute(CreateOrderCommand(**request.model_dump()))
        return OrderResponse.model_validate(order)
    except OrderValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
```
- Routers only: parse HTTP → call use case → map response → handle exceptions
- Always `response_model` and `status_code`
- Domain exceptions map to HTTP in router — never in use case

**SQLAlchemy (2.0 style):**
```python
class OrderModel(Base):
    __tablename__ = "orders"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    status: Mapped[OrderStatus] = mapped_column(SAEnum(OrderStatus))

    def to_domain(self) -> Order: ...
    @classmethod
    def from_domain(cls, order: Order) -> "OrderModel": ...
```
- Always `Mapped[]` annotations
- Always `to_domain()` and `from_domain()` — never leak ORM models to domain
- Async sessions only: `AsyncSession`

**Logging — structured only:**
```python
import structlog
logger = structlog.get_logger(__name__)

logger.info("order_created", order_id=str(order.id), customer_id=str(order.customer_id))
# Never: print() or logger.info(f"Order {order.id} created")
```

---

## Testing Standards

**Philosophy: test behavior, not implementation.**

```python
# Wrong — tests internals
def test_order_calls_save():
    repo = Mock()
    use_case.execute(command)
    repo.save.assert_called_once()

# Correct — tests observable outcome
async def test_created_order_is_retrievable():
    repo = InMemoryOrderRepository()
    order = await CreateOrderUseCase(repo).execute(command)
    assert await repo.get_by_id(order.id) is not None
```

**TDD sequence — no exceptions:**
```
1. SPEC       → Acceptance Criteria in .ai/specs/
2. TESTS      → generate tests from Acceptance Criteria
3. REVIEW     → human reviews tests (critical gate)
4. IMPLEMENT  → write code to pass tests
5. VERIFY     → all green, lint passes
```

**Test structure — AAA always:**
```python
async def test_order_cannot_exceed_maximum_items():
    # Arrange
    repo = InMemoryOrderRepository()
    use_case = CreateOrderUseCase(repo, event_bus=FakeEventBus())
    command = CreateOrderCommand(items=[...] * 51)  # over limit

    # Act & Assert
    with pytest.raises(OrderValidationError, match="maximum 50 items"):
        await use_case.execute(command)
```

**InMemory repositories — required, never Mock():**
```python
class InMemoryOrderRepository:
    def __init__(self) -> None:
        self._store: dict[UUID, Order] = {}

    async def get_by_id(self, order_id: UUID) -> Order | None:
        return self._store.get(order_id)

    async def save(self, order: Order) -> Order:
        self._store[order.id] = order
        return order
```

**What to test per layer:**

| Layer | Type | Coverage target |
|-------|------|----------------|
| Domain entities | Unit | 90%+ |
| Use cases | Unit (InMemory repos) | 90%+ |
| Repositories | Integration (real DB) | 70%+ |
| Routers | Integration (HTTP) | 80%+ |
| E2E | E2E | Top 3-5 paths only |

**Test naming:** `test_<subject>_<condition>_<expected_outcome>`
```python
# Wrong: test_create_order, test_error
# Correct:
async def test_cancelled_order_cannot_be_shipped():
async def test_order_with_zero_quantity_raises_validation_error():
```

**Edge cases — generate tests for every use case:**
- Happy path
- Empty / null inputs
- Boundary values (min/max)
- Duplicate operations (create twice, delete twice)
- Invalid state transitions
- Missing dependencies (entity not found)
- Permission boundaries

---

## Infrastructure Standards

**General:**
- IaC is code — same quality standards apply
- No manual changes to IaC-managed resources
- Least privilege IAM — explicit minimal permissions per service account
- No secrets in code — Secret Manager (GCP) / Secrets Manager (AWS)
- Encryption at rest and in transit by default

**Terraform structure:**
```
infrastructure/
├── modules/<module>/     # main.tf, variables.tf, outputs.tf
└── environments/
    ├── staging/          # calls modules with staging values
    └── production/       # calls modules with production values
```
- Every variable has `description` and `type`
- No hardcoded project IDs or regions in modules
- `terraform fmt` + `terraform validate` before every commit

**Forbidden IAM:**
- `roles/editor` or `roles/owner` on service accounts
- `allUsers` on non-public resources
- Shared service accounts between services
- Long-lived service account keys — use Workload Identity

**Docker:**
```dockerfile
FROM python:3.12.3-slim-bookworm   # pin exact version, never :latest
RUN useradd --uid 1001 appuser     # non-root user required
COPY pyproject.toml uv.lock ./     # dependencies before source
COPY src/ ./src/
USER appuser
```

**Observability — required from day one:**
- Structured logging: `{"event": "...", "order_id": "...", "duration_ms": 45}`
- Health endpoints: `/health/live` (process alive) + `/health/ready` (dependencies up)
- Metrics: `/metrics` in Prometheus format

**Config:**
```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    database_url: str
    environment: Literal["local", "staging", "production"]
    secret_key: str  # injected from Secret Manager in production
```
- All config from environment variables
- `.env.example` committed, `.env` in `.gitignore`
- Secrets never in `.env` files committed to git

---

## Forbidden — Absolute Rules

**Code:**
- Business logic in routers or infrastructure layer
- Direct DB access bypassing repository interface
- `print()` in non-script code — use structlog
- Bare `except:` or `except Exception:` without re-raise
- `from module import *`
- Mutable default arguments: `def fn(items=[])` → use `None`
- `Any` without explanation comment
- `global` keyword
- Circular imports

**Infrastructure:**
- Hardcoded secrets, credentials, project IDs, or environment-specific values in modules
- `roles/editor` or `roles/owner` on service accounts
- `:latest` Docker image tags
- Running containers as root
- Manual changes to IaC-managed resources

**Tests:**
- `Mock()` for repository interfaces — use InMemory implementations
- `time.sleep()` — use time mocking
- Tests that depend on execution order
- Hardcoded UUIDs or dates — use `uuid4()` and `datetime.utcnow()`
