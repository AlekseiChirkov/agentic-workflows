---
trigger: always_on
---
# Code Quality Principles

These principles apply to ALL code produced in any workflow phase.
They are not optional — deviations require explicit justification in `notes:`.

---

## Architecture: Clean Layered Structure

Every project must respect layer boundaries. Dependencies flow INWARD only.

```
API / CLI Layer         → routers, handlers, CLI commands
Application Layer       → use cases, orchestration, no business logic
Domain Layer            → entities, business rules, pure functions, NO I/O
Infrastructure Layer    → DB, external APIs, cloud services, messaging
```

**Hard rules:**
- Domain layer MUST NOT import from infrastructure or application layers
- Use cases MUST NOT import from API layer
- Routers MUST NOT contain business logic — delegate to use cases
- Infrastructure MUST NOT leak into domain (no SQLAlchemy models in domain entities)

**Violation signal:** if you need to import an infrastructure class into domain — the design is wrong. Introduce an abstraction (Protocol / ABC) in domain, implement it in infrastructure.

---

## SOLID — Practical Application

**Single Responsibility** — one reason to change per module.
- A class/function does one thing. Name it after that thing.
- Signal of violation: "and" in the function name (`validate_and_save_user`).
- Fix: split into `validate_user` + `save_user`, compose in use case.

**Open/Closed** — extend via new code, not by modifying existing.
- Prefer Strategy pattern and dependency injection over conditionals that grow.
- Signal of violation: adding a new `if type == "X"` branch to existing logic.

**Liskov Substitution** — subtypes must be substitutable for their base type.
- If overriding a method changes its contract — use composition, not inheritance.
- In Python: if using ABC or Protocol, implementations must honor the full contract.

**Interface Segregation** — small, focused interfaces.
- Use `Protocol` with minimal method sets. Never force implementors to define unused methods.
- Prefer multiple small Protocols over one large ABC.

**Dependency Inversion** — depend on abstractions, not concretions.
- Use cases receive repositories and services via constructor injection.
- Never instantiate infrastructure classes inside domain or application layers.
- This is the most critical principle for testability.

---

## Naming: Explicit Over Clever

Names must communicate intent without requiring context.

| Bad | Good | Why |
|-----|------|-----|
| `process(data, mode)` | `process_payment(payload: PaymentDTO, mode: ProcessingMode)` | Intent clear from signature |
| `user_service.py` | `user_registration_service.py` | Specific responsibility |
| `handle()` | `handle_order_cancellation()` | No ambiguity |
| `data` | `raw_event_payload` | Type + role |
| `flag` | `is_email_verified` | Boolean reads as predicate |

**Rules:**
- Functions: verb + noun (`create_order`, `validate_email`, `publish_event`)
- Classes: noun describing the concept (`OrderRepository`, `PaymentProcessor`)
- Booleans: `is_`, `has_`, `can_`, `should_` prefix
- No abbreviations except universally accepted (`id`, `url`, `dto`, `api`)

---

## Functions and Classes

**Function rules:**
- Maximum 30 lines. If longer — extract.
- Maximum 3 parameters. If more — introduce a DTO/dataclass.
- Single level of abstraction per function (no mixing high-level orchestration with low-level details).
- No side effects in functions named as queries (`get_`, `find_`, `calculate_`).

**Class rules:**
- Constructor only sets state — no I/O, no computation.
- Prefer composition over inheritance. Max 1 level of inheritance for domain entities.
- Dataclasses / Pydantic models for data containers. Classes with methods for behavior.

---

## Error Handling

- Never use bare `except:` or `except Exception:` without re-raise or explicit logging.
- Define domain-specific exceptions in `domain/exceptions.py`.
- Raise early, catch late — validate inputs at the boundary (API layer), let domain raise domain exceptions.
- Always include context in exception messages: `OrderNotFoundError(f"Order {order_id} not found")`.
- Infrastructure exceptions must be wrapped before crossing layer boundaries.

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

---

## Repository Pattern — Required for All Data Access

Every data source (DB, external API, cache) is accessed through a Repository interface.

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
- Implementation lives in `infrastructure/` — infra fulfills the contract
- Tests use `InMemory*` implementations — never mock the repository directly

---

## Dependency Injection

Use cases receive all dependencies via constructor. No service locators. No global state.

```python
# application/use_cases/create_order.py
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

## What Is Forbidden

- Business logic in routers or infrastructure layer
- Direct database access from use cases (always go through repository)
- Hardcoded configuration values (use settings / environment variables)
- Credentials or secrets in code
- `print()` for debugging in production code (use structured logging)
- Global mutable state
- Circular imports (signal of wrong layer boundaries)
- References to AI-pipeline artifacts in code, comments, docstrings, or test names —
  subtask ids (`T-04`), spec or task names, `ADR-0007`, `architecture.md`, `state.md`, or any
  path under `.ai/`. Knowledge-base tracking follows repository policy; product code must
  remain understandable independently of planning records. State the decision itself in the
  code instead of citing where it was recorded. Workflow definitions and knowledge-base
  records may use the identifiers and paths needed to describe the process.
