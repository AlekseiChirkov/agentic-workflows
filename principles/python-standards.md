---
trigger: always_on
---
# Python Standards

Applies to all Python code. Version: 3.11+ unless project CLAUDE.md specifies otherwise.

---

## Type Hints — Mandatory

Every function, method, and class attribute must have type hints.
No `Any` without explicit comment explaining why.

```python
# Wrong
def get_user(user_id):
    ...

# Correct
async def get_user(user_id: UUID) -> User | None:
    ...
```

**Rules:**
- Use `X | None` instead of `Optional[X]` (Python 3.10+)
- Use `X | Y` instead of `Union[X, Y]`
- Use built-in generics: `list[str]`, `dict[str, int]`, `tuple[int, ...]`
- Use `TypeAlias` for complex reusable types
- Use `TypeVar` for generic functions, not `Any`

---

## Pydantic — Data Validation at Boundaries

All external data (API requests, API responses, config, events) uses Pydantic v2.

```python
from pydantic import BaseModel, Field, field_validator
from uuid import UUID

class CreateOrderRequest(BaseModel):
    customer_id: UUID
    items: list[OrderItemDTO] = Field(min_length=1)
    delivery_address: str = Field(min_length=10, max_length=500)

    @field_validator("delivery_address")
    @classmethod
    def address_must_not_be_po_box(cls, v: str) -> str:
        if v.lower().startswith("p.o. box"):
            raise ValueError("PO Box addresses are not accepted")
        return v.strip()
```

- Request/Response schemas live in `api/schemas/`
- Domain entities use `dataclass` or Pydantic with `model_config = ConfigDict(frozen=True)`
- Never use Pydantic models as domain entities — they are DTOs

---

## Async: When to Use

| Situation | Use |
|-----------|-----|
| Database queries (SQLAlchemy async) | `async def` |
| External HTTP calls | `async def` |
| File I/O (aiofiles) | `async def` |
| CPU-bound computation | `def` (sync) + run in executor if needed |
| Pure business logic | `def` (sync) |
| Simple data transformation | `def` (sync) |

**Rules:**
- Do not `await` inside list comprehensions — use `asyncio.gather()` for parallel calls
- Never call `asyncio.run()` inside async context
- Never use `time.sleep()` in async code — use `asyncio.sleep()`
- Mark I/O-bound use cases as `async def execute()` — they call async repositories

---

## FastAPI Patterns

```python
# api/routers/orders.py
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

router = APIRouter(prefix="/orders", tags=["orders"])

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
    except CustomerNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
```

**Rules:**
- Routers only: validate HTTP → call use case → map to response schema → handle exceptions
- One router file per domain entity
- Use `status.HTTP_*` constants, never raw numbers
- Always specify `response_model` and `status_code`
- Domain exceptions map to HTTP exceptions in the router — never in the use case

---

## SQLAlchemy Async Patterns

```python
# infrastructure/database/models/order_model.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Enum as SAEnum
from uuid import UUID
import uuid

class Base(DeclarativeBase):
    pass

class OrderModel(Base):
    __tablename__ = "orders"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    status: Mapped[OrderStatus] = mapped_column(SAEnum(OrderStatus))
    customer_id: Mapped[UUID] = mapped_column(index=True)

    def to_domain(self) -> Order:
        return Order(id=self.id, status=self.status, customer_id=self.customer_id)

    @classmethod
    def from_domain(cls, order: Order) -> "OrderModel":
        return cls(id=order.id, status=order.status, customer_id=order.customer_id)
```

- ORM models live in `infrastructure/database/models/`
- Always define `to_domain()` and `from_domain()` — never leak ORM models to domain
- Use `Mapped[]` type annotations (SQLAlchemy 2.0 style)
- Async sessions only: `AsyncSession` from `sqlalchemy.ext.asyncio`

---

## Logging

```python
import structlog

logger = structlog.get_logger(__name__)

# Correct — structured, with context
logger.info("order_created", order_id=str(order.id), customer_id=str(order.customer_id))
logger.error("payment_failed", order_id=str(order.id), error=str(e), exc_info=True)

# Wrong — unstructured
logger.info(f"Order {order.id} created")
print(f"DEBUG: {order}")
```

- Use `structlog` for structured logging
- Always include relevant IDs as key-value pairs
- Never log sensitive data (passwords, tokens, PII)
- Log at boundaries: incoming requests, outgoing calls, domain events published

---

## Project Structure

```
src/
├── domain/
│   ├── entities/           # Pure Python dataclasses or frozen Pydantic models
│   ├── repositories/       # Protocol interfaces only — no implementations
│   ├── services/           # Pure business logic, no I/O
│   └── exceptions.py       # Domain exception hierarchy
├── application/
│   └── use_cases/          # One file per use case
├── infrastructure/
│   ├── database/
│   │   ├── models/         # SQLAlchemy ORM models
│   │   └── repositories/   # Concrete repository implementations
│   ├── external/           # Third-party API clients
│   └── gcp/ (or aws/)      # Cloud-specific adapters
├── api/
│   ├── routers/            # FastAPI routers, one per domain entity
│   ├── schemas/            # Pydantic request/response schemas
│   └── dependencies.py     # FastAPI Depends() factories
├── config.py               # Pydantic Settings
└── main.py                 # FastAPI app factory
```

---

## Forbidden in Python Code

- `from module import *`
- Mutable default arguments: `def fn(items=[])` → use `None` with guard
- Bare `except:` or `except Exception:` without re-raise
- `type: ignore` without explanation comment
- `Any` without explanation comment
- `global` keyword
- `print()` in non-script code
