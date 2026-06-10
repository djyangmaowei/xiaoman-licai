# Xiaoman Family Fund MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first deployable “小满理财” Web MVP for family-fund ledger, NAV calculation, T+1 price updates, holdings display, basic alerts, and role-based read/write access.

**Architecture:** Use a FastAPI backend with server-rendered Jinja pages for the lightweight UI. Keep financial calculations in pure domain services with tests, persist records through SQLAlchemy models, and run scheduled price updates through a small job module that can also be triggered manually.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL in production, SQLite for local tests, Jinja2, pytest, Ruff.

---

## File Structure

- `pyproject.toml`: Python package metadata, dependencies, test and lint config.
- `README.md`: local development, test, and deployment overview.
- `.env.example`: required runtime environment variables.
- `app/main.py`: FastAPI app factory and router registration.
- `app/core/config.py`: environment-based settings.
- `app/core/security.py`: password hashing and session helpers.
- `app/db/session.py`: SQLAlchemy engine, session factory, and dependency.
- `app/db/base.py`: declarative base import surface.
- `app/models/*.py`: SQLAlchemy tables for users, products, fund flows, trades, prices, valuations, alerts, and update logs.
- `app/schemas/*.py`: Pydantic request and response schemas.
- `app/domain/ledger.py`: pure cash, share, and holding calculations.
- `app/domain/valuation.py`: pure daily valuation calculations.
- `app/domain/alerts.py`: pure alert evaluation rules.
- `app/services/*.py`: database-backed orchestration for ledger entries, products, prices, valuation, alerts, and users.
- `app/jobs/update_prices.py`: scheduled and manual T+1 update entrypoint.
- `app/templates/*.html`: server-rendered pages with “小满理财” branding.
- `app/static/styles.css`: restrained dashboard styling and logo treatment.
- `tests/domain/*.py`: calculation-focused tests.
- `tests/api/*.py`: FastAPI endpoint tests.
- `alembic/`: schema migration files.
- `docs/deployment/tencent-cloud.md`: Tencent Cloud deployment and backup runbook.

## Task 1: Project Scaffold And Test Harness

**Files:**
- Create: `pyproject.toml`
- Create: `app/__init__.py`
- Create: `app/main.py`
- Create: `tests/test_health.py`
- Create: `README.md`
- Create: `.env.example`

- [ ] **Step 1: Write the first failing health test**

Create `tests/test_health.py`:

```python
from fastapi.testclient import TestClient

from app.main import create_app


def test_health_check_returns_ok():
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "xiaoman-finance"}
```

- [ ] **Step 2: Run the failing test**

Run:

```bash
pytest tests/test_health.py -v
```

Expected: FAIL because `app.main` does not exist.

- [ ] **Step 3: Add project metadata and minimal app**

Create `pyproject.toml`:

```toml
[project]
name = "xiaoman-finance"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "alembic>=1.13",
  "fastapi>=0.115",
  "jinja2>=3.1",
  "passlib[bcrypt]>=1.7",
  "psycopg[binary]>=3.2",
  "pydantic-settings>=2.5",
  "python-multipart>=0.0.9",
  "sqlalchemy>=2.0",
  "uvicorn[standard]>=0.30",
]

[dependency-groups]
dev = [
  "httpx>=0.27",
  "pytest>=8.3",
  "ruff>=0.6",
]

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
line-length = 100
```

Create `app/main.py`:

```python
from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="小满理财")

    @app.get("/health")
    def health_check() -> dict[str, str]:
        return {"status": "ok", "service": "xiaoman-finance"}

    return app


app = create_app()
```

Create empty `app/__init__.py`.

Create `.env.example`:

```bash
DATABASE_URL=postgresql+psycopg://xiaoman:change-me@localhost:5432/xiaoman
APP_SECRET_KEY=change-me-before-deploy
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=change-me-before-deploy
```

Create `README.md`:

```markdown
# 小满理财

家庭基金量化系统 MVP。第一版用于手动录入资金和交易流水、计算家庭基金份额和净值、更新 T+1 产品价格、展示持仓和基础预警。

## Local checks

Run `pytest -v` and `ruff check .` before handing off changes.
```

- [ ] **Step 4: Verify scaffold**

Run:

```bash
pytest tests/test_health.py -v
ruff check .
```

Expected: both PASS.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml app tests README.md .env.example
git commit -m "chore: scaffold xiaoman finance app"
```

## Task 2: Domain Ledger Calculations

**Files:**
- Create: `app/domain/ledger.py`
- Create: `tests/domain/test_ledger.py`

- [ ] **Step 1: Write failing ledger tests**

Create `tests/domain/test_ledger.py`:

```python
from decimal import Decimal

from app.domain.ledger import (
    apply_buy_trade,
    apply_subscription,
    calculate_unit_nav,
)


def test_first_subscription_uses_initial_nav_one():
    result = apply_subscription(
        cash=Decimal("0"),
        total_shares=Decimal("0"),
        unit_nav=Decimal("1.0000"),
        amount=Decimal("10000"),
    )

    assert result.cash == Decimal("10000")
    assert result.total_shares == Decimal("10000.0000")


def test_later_subscription_uses_current_nav():
    result = apply_subscription(
        cash=Decimal("2000"),
        total_shares=Decimal("10000"),
        unit_nav=Decimal("1.2500"),
        amount=Decimal("2500"),
    )

    assert result.cash == Decimal("4500")
    assert result.total_shares == Decimal("12000.0000")


def test_buy_trade_reduces_cash_without_changing_total_shares():
    result = apply_buy_trade(
        cash=Decimal("10000"),
        total_shares=Decimal("10000"),
        gross_amount=Decimal("6000"),
        fee=Decimal("3"),
    )

    assert result.cash == Decimal("3997")
    assert result.total_shares == Decimal("10000")


def test_unit_nav_is_total_assets_divided_by_total_shares():
    nav = calculate_unit_nav(total_assets=Decimal("12345.67"), total_shares=Decimal("10000"))

    assert nav == Decimal("1.2346")
```

- [ ] **Step 2: Run failing tests**

Run:

```bash
pytest tests/domain/test_ledger.py -v
```

Expected: FAIL because `app.domain.ledger` does not exist.

- [ ] **Step 3: Implement minimal pure ledger functions**

Create `app/domain/ledger.py`:

```python
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


MONEY_QUANT = Decimal("0.01")
SHARE_QUANT = Decimal("0.0001")
NAV_QUANT = Decimal("0.0001")


@dataclass(frozen=True)
class LedgerState:
    cash: Decimal
    total_shares: Decimal


def quantize_money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def quantize_shares(value: Decimal) -> Decimal:
    return value.quantize(SHARE_QUANT, rounding=ROUND_HALF_UP)


def quantize_nav(value: Decimal) -> Decimal:
    return value.quantize(NAV_QUANT, rounding=ROUND_HALF_UP)


def apply_subscription(
    cash: Decimal,
    total_shares: Decimal,
    unit_nav: Decimal,
    amount: Decimal,
) -> LedgerState:
    if amount <= 0:
        raise ValueError("subscription amount must be positive")
    if unit_nav <= 0:
        raise ValueError("unit nav must be positive")

    new_shares = quantize_shares(amount / unit_nav)
    return LedgerState(
        cash=quantize_money(cash + amount),
        total_shares=quantize_shares(total_shares + new_shares),
    )


def apply_buy_trade(
    cash: Decimal,
    total_shares: Decimal,
    gross_amount: Decimal,
    fee: Decimal,
) -> LedgerState:
    if gross_amount <= 0:
        raise ValueError("buy amount must be positive")
    if fee < 0:
        raise ValueError("fee cannot be negative")

    cash_after = cash - gross_amount - fee
    if cash_after < 0:
        raise ValueError("cash cannot be negative after buy")
    return LedgerState(cash=quantize_money(cash_after), total_shares=total_shares)


def calculate_unit_nav(total_assets: Decimal, total_shares: Decimal) -> Decimal:
    if total_shares == 0:
        return Decimal("1.0000")
    if total_shares < 0:
        raise ValueError("total shares cannot be negative")
    return quantize_nav(total_assets / total_shares)
```

- [ ] **Step 4: Verify ledger tests**

Run:

```bash
pytest tests/domain/test_ledger.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/domain/ledger.py tests/domain/test_ledger.py
git commit -m "feat: add family fund ledger calculations"
```

## Task 3: Valuation And Alert Domain Rules

**Files:**
- Create: `app/domain/valuation.py`
- Create: `app/domain/alerts.py`
- Create: `tests/domain/test_valuation.py`
- Create: `tests/domain/test_alerts.py`

- [ ] **Step 1: Write failing valuation and alert tests**

Create `tests/domain/test_valuation.py`:

```python
from decimal import Decimal

from app.domain.valuation import HoldingValue, calculate_daily_valuation


def test_daily_valuation_sums_cash_and_holdings():
    valuation = calculate_daily_valuation(
        cash=Decimal("4000"),
        total_shares=Decimal("10000"),
        holdings=[
            HoldingValue(code="515450", market_value=Decimal("3000")),
            HoldingValue(code="518880", market_value=Decimal("5000")),
        ],
    )

    assert valuation.total_assets == Decimal("12000.00")
    assert valuation.unit_nav == Decimal("1.2000")
```

Create `tests/domain/test_alerts.py`:

```python
from decimal import Decimal

from app.domain.alerts import evaluate_weight_alert


def test_weight_alert_triggers_when_deviation_exceeds_threshold():
    alert = evaluate_weight_alert(
        product_code="563360",
        current_weight=Decimal("0.38"),
        target_weight=Decimal("0.30"),
        threshold=Decimal("0.05"),
    )

    assert alert is not None
    assert alert.product_code == "563360"
    assert alert.severity == "warning"


def test_weight_alert_ignores_small_deviation():
    alert = evaluate_weight_alert(
        product_code="563360",
        current_weight=Decimal("0.32"),
        target_weight=Decimal("0.30"),
        threshold=Decimal("0.05"),
    )

    assert alert is None
```

- [ ] **Step 2: Run failing tests**

Run:

```bash
pytest tests/domain/test_valuation.py tests/domain/test_alerts.py -v
```

Expected: FAIL because modules do not exist.

- [ ] **Step 3: Implement valuation and alert rules**

Create `app/domain/valuation.py`:

```python
from dataclasses import dataclass
from decimal import Decimal

from app.domain.ledger import quantize_money, quantize_nav


@dataclass(frozen=True)
class HoldingValue:
    code: str
    market_value: Decimal


@dataclass(frozen=True)
class DailyValuation:
    total_assets: Decimal
    unit_nav: Decimal


def calculate_daily_valuation(
    cash: Decimal,
    total_shares: Decimal,
    holdings: list[HoldingValue],
) -> DailyValuation:
    total_holdings = sum((holding.market_value for holding in holdings), Decimal("0"))
    total_assets = quantize_money(cash + total_holdings)
    unit_nav = Decimal("1.0000") if total_shares == 0 else quantize_nav(total_assets / total_shares)
    return DailyValuation(total_assets=total_assets, unit_nav=unit_nav)
```

Create `app/domain/alerts.py`:

```python
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class AlertDecision:
    product_code: str
    severity: str
    message: str


def evaluate_weight_alert(
    product_code: str,
    current_weight: Decimal,
    target_weight: Decimal,
    threshold: Decimal,
) -> AlertDecision | None:
    deviation = abs(current_weight - target_weight)
    if deviation <= threshold:
        return None
    return AlertDecision(
        product_code=product_code,
        severity="warning",
        message=f"{product_code} 仓位偏离目标 {deviation:.2%}",
    )
```

- [ ] **Step 4: Verify**

Run:

```bash
pytest tests/domain -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/domain tests/domain
git commit -m "feat: add valuation and alert rules"
```

## Task 4: Database Models And Migrations

**Files:**
- Create: `app/db/base.py`
- Create: `app/db/session.py`
- Create: `app/models/user.py`
- Create: `app/models/product.py`
- Create: `app/models/ledger.py`
- Create: `app/models/market_data.py`
- Create: `app/models/valuation.py`
- Create: `app/models/alert.py`
- Create: `alembic.ini`
- Create: `alembic/env.py`
- Create: `alembic/versions/0001_initial_schema.py`
- Create: `tests/api/conftest.py`

- [ ] **Step 1: Add model import smoke test**

Create `tests/api/conftest.py` with a test database fixture shell:

```python
import pytest


@pytest.fixture
def sample_database_url(tmp_path):
    return f"sqlite:///{tmp_path / 'test.db'}"
```

Create `tests/api/test_models_import.py`:

```python
from app.db.base import Base
from app.models import alert, ledger, market_data, product, user, valuation


def test_models_register_tables():
    assert "users" in Base.metadata.tables
    assert "products" in Base.metadata.tables
    assert "fund_flows" in Base.metadata.tables
    assert "trades" in Base.metadata.tables
    assert "price_points" in Base.metadata.tables
    assert "daily_valuations" in Base.metadata.tables
    assert "alerts" in Base.metadata.tables
```

- [ ] **Step 2: Run failing import test**

Run:

```bash
pytest tests/api/test_models_import.py -v
```

Expected: FAIL because database modules do not exist.

- [ ] **Step 3: Create SQLAlchemy model skeleton**

Implement tables with these required columns:

```python
# app/db/base.py
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

Each model file must define one focused group:

- `users`: `id`, `email`, `password_hash`, `role`, `created_at`.
- `products`: `id`, `asset_class`, `name`, `code`, `channel`, `target_weight`, `is_active`.
- `fund_flows`: `id`, `flow_type`, `trade_date`, `amount`, `unit_nav`, `shares_delta`, `note`, `created_at`.
- `trades`: `id`, `trade_type`, `trade_date`, `product_id`, `amount`, `quantity`, `price`, `fee`, `note`, `created_at`.
- `price_points`: `id`, `product_id`, `price_date`, `price`, `source`, `fetched_at`, `status`, `error_message`.
- `daily_valuations`: `id`, `valuation_date`, `cash`, `total_assets`, `total_shares`, `unit_nav`, `created_at`.
- `alerts`: `id`, `alert_date`, `alert_type`, `severity`, `product_id`, `message`, `is_active`, `created_at`.

- [ ] **Step 4: Verify model registration**

Run:

```bash
pytest tests/api/test_models_import.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/db app/models alembic.ini alembic tests/api
git commit -m "feat: add initial database schema"
```

## Task 5: Services For Confirmed Manual Ledger Entry

**Files:**
- Create: `app/services/ledger_service.py`
- Create: `app/schemas/ledger.py`
- Create: `tests/api/test_ledger_service.py`

- [ ] **Step 1: Write service tests for the key user workflow**

Create `tests/api/test_ledger_service.py`:

```python
from decimal import Decimal

from app.schemas.ledger import CombinedBuyInstruction
from app.services.ledger_service import prepare_combined_buy_entries


def test_combined_buy_instruction_creates_subscription_and_buy_draft():
    draft = prepare_combined_buy_entries(
        CombinedBuyInstruction(
            trade_date="2026-06-10",
            amount=Decimal("10000"),
            product_name="华安黄金ETF",
            product_code="518880",
            unit_nav=Decimal("1.0000"),
            price=Decimal("5.000"),
            fee=Decimal("1.00"),
            use_existing_cash=False,
        )
    )

    assert len(draft.entries) == 2
    assert draft.entries[0].entry_type == "SUBSCRIBE"
    assert draft.entries[0].shares_delta == Decimal("10000.0000")
    assert draft.entries[1].entry_type == "BUY"
    assert draft.entries[1].quantity == Decimal("1999.8000")


def test_existing_cash_buy_creates_only_buy_draft():
    draft = prepare_combined_buy_entries(
        CombinedBuyInstruction(
            trade_date="2026-06-10",
            amount=Decimal("10000"),
            product_name="华安黄金ETF",
            product_code="518880",
            unit_nav=Decimal("1.0000"),
            price=Decimal("5.000"),
            fee=Decimal("0.00"),
            use_existing_cash=True,
        )
    )

    assert [entry.entry_type for entry in draft.entries] == ["BUY"]
```

- [ ] **Step 2: Run failing service tests**

Run:

```bash
pytest tests/api/test_ledger_service.py -v
```

Expected: FAIL because schemas and service do not exist.

- [ ] **Step 3: Implement draft preparation without mutating database**

Create `app/schemas/ledger.py` and `app/services/ledger_service.py` so `prepare_combined_buy_entries()` returns a draft summary only. It must not write to the database. Quantity calculation:

```text
quantity = (amount - fee) / price
```

Quantize quantity to `0.0001`.

- [ ] **Step 4: Verify**

Run:

```bash
pytest tests/api/test_ledger_service.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/schemas/ledger.py app/services/ledger_service.py tests/api/test_ledger_service.py
git commit -m "feat: prepare confirmed ledger entry drafts"
```

## Task 6: API Routes For Products, Ledger, Valuation, And Alerts

**Files:**
- Create: `app/api/routes.py`
- Create: `app/api/products.py`
- Create: `app/api/ledger.py`
- Create: `app/api/valuation.py`
- Create: `app/api/alerts.py`
- Modify: `app/main.py`
- Create: `tests/api/test_routes.py`

- [ ] **Step 1: Write route tests**

Create `tests/api/test_routes.py`:

```python
from fastapi.testclient import TestClient

from app.main import create_app


def test_home_page_contains_brand_name():
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert "小满理财" in response.text


def test_api_product_config_lists_seed_assets():
    client = TestClient(create_app())

    response = client.get("/api/products/seed")

    assert response.status_code == 200
    assert response.json()[0]["asset_class"] == "债券"
```

- [ ] **Step 2: Run failing route tests**

Run:

```bash
pytest tests/api/test_routes.py -v
```

Expected: FAIL because routes do not exist.

- [ ] **Step 3: Implement minimal routes**

Add routers and register them in `create_app()`. The seed product endpoint returns the six spec products from `2026.6.9.docx`. The home route returns server-rendered HTML or a plain HTML response containing “小满理财”.

- [ ] **Step 4: Verify**

Run:

```bash
pytest tests/api/test_routes.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/api app/main.py tests/api/test_routes.py
git commit -m "feat: add MVP web and API routes"
```

## Task 7: T+1 Price Update Service

**Files:**
- Create: `app/services/price_service.py`
- Create: `app/jobs/update_prices.py`
- Create: `tests/api/test_price_service.py`

- [ ] **Step 1: Write price service tests**

Create `tests/api/test_price_service.py`:

```python
from decimal import Decimal

from app.services.price_service import PriceFetchResult, select_latest_successful_price


def test_latest_successful_price_ignores_failed_result():
    result = select_latest_successful_price(
        [
            PriceFetchResult("518880", "2026-06-09", Decimal("5.10"), "eastmoney", "success", None),
            PriceFetchResult("518880", "2026-06-10", None, "eastmoney", "failed", "not disclosed"),
        ]
    )

    assert result.price == Decimal("5.10")
    assert result.price_date == "2026-06-09"
```

- [ ] **Step 2: Run failing test**

Run:

```bash
pytest tests/api/test_price_service.py -v
```

Expected: FAIL because price service does not exist.

- [ ] **Step 3: Implement price result selection and update job shell**

Implement `PriceFetchResult` and `select_latest_successful_price()`. Add `app/jobs/update_prices.py` with a callable `run_price_update(target_date: str | None = None) -> int` that returns the number of products attempted. The first implementation can use an injected fetcher in tests and must not perform network calls by default.

- [ ] **Step 4: Verify**

Run:

```bash
pytest tests/api/test_price_service.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/services/price_service.py app/jobs/update_prices.py tests/api/test_price_service.py
git commit -m "feat: add T+1 price update service shell"
```

## Task 8: Server-Rendered UI With 小满理财 Branding

**Files:**
- Create: `app/templates/base.html`
- Create: `app/templates/dashboard.html`
- Create: `app/templates/holdings.html`
- Create: `app/templates/ledger.html`
- Create: `app/templates/updates.html`
- Create: `app/templates/alerts.html`
- Create: `app/static/styles.css`
- Modify: `app/main.py`
- Create: `tests/api/test_pages.py`

- [ ] **Step 1: Write page tests**

Create `tests/api/test_pages.py`:

```python
from fastapi.testclient import TestClient

from app.main import create_app


def test_dashboard_contains_core_nav_items():
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert "小满理财" in response.text
    assert "总览" in response.text
    assert "持仓" in response.text
    assert "流水" in response.text
    assert "预警" in response.text
```

- [ ] **Step 2: Run failing page test**

Run:

```bash
pytest tests/api/test_pages.py -v
```

Expected: FAIL until templates and route rendering exist.

- [ ] **Step 3: Implement templates and CSS**

Use a compact dashboard style:

- Text logo: `小满理财`
- Logo mark: a small rounded square containing `小`
- Main colors: low-saturation green, white, neutral gray
- No marketing hero section
- No decorative gradients or oversized cards

- [ ] **Step 4: Verify**

Run:

```bash
pytest tests/api/test_pages.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/templates app/static app/main.py tests/api/test_pages.py
git commit -m "feat: add xiaoman branded web pages"
```

## Task 9: Simple Role-Based Access

**Files:**
- Create: `app/core/security.py`
- Create: `app/services/user_service.py`
- Create: `tests/api/test_security.py`

- [ ] **Step 1: Write security tests**

Create `tests/api/test_security.py`:

```python
from app.core.security import can_write


def test_admin_can_write():
    assert can_write("admin") is True


def test_viewer_cannot_write():
    assert can_write("viewer") is False
```

- [ ] **Step 2: Run failing security tests**

Run:

```bash
pytest tests/api/test_security.py -v
```

Expected: FAIL because security helper does not exist.

- [ ] **Step 3: Implement minimal role helper**

Create `app/core/security.py`:

```python
def can_write(role: str) -> bool:
    return role == "admin"
```

Add route-level write checks in ledger, product, update, and config mutations.

- [ ] **Step 4: Verify**

Run:

```bash
pytest tests/api/test_security.py tests/api -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/core/security.py app/services/user_service.py app/api tests/api/test_security.py
git commit -m "feat: add simple family role access"
```

## Task 10: Deployment And Operations Runbook

**Files:**
- Create: `docs/deployment/tencent-cloud.md`
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Modify: `README.md`

- [ ] **Step 1: Write deployment doc with exact commands**

Create `docs/deployment/tencent-cloud.md` covering:

```markdown
# 腾讯云部署 Runbook

## Services

- FastAPI app: `xiaoman-web`
- PostgreSQL: `xiaoman-db`

## First deploy

- `docker compose up -d --build`
- `docker compose exec web alembic upgrade head`
- `docker compose exec web pytest -v`

## Daily backup

- `docker compose exec db pg_dump -U xiaoman xiaoman > backups/xiaoman-$(date +%F).sql`

## Manual T+1 update

- `docker compose exec web python -m app.jobs.update_prices`
```

- [ ] **Step 2: Add container files**

Create a Dockerfile that runs:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Create `docker-compose.yml` with `web` and `db` services, using PostgreSQL 16.

- [ ] **Step 3: Verify docs and config exist**

Run:

```bash
test -f docs/deployment/tencent-cloud.md
test -f Dockerfile
test -f docker-compose.yml
```

Expected: all commands exit with code 0.

- [ ] **Step 4: Commit**

```bash
git add docs/deployment Dockerfile docker-compose.yml README.md
git commit -m "docs: add tencent cloud deployment runbook"
```

## Task 11: Final MVP Verification

**Files:**
- Modify only files required by failing checks.

- [ ] **Step 1: Run full test suite**

Run:

```bash
pytest -v
```

Expected: PASS.

- [ ] **Step 2: Run lint**

Run:

```bash
ruff check .
```

Expected: PASS.

- [ ] **Step 3: Start local server**

Run:

```bash
uvicorn app.main:app --reload --port 8000
```

Expected: server starts at `http://127.0.0.1:8000`.

- [ ] **Step 4: Browser check**

Open `http://127.0.0.1:8000` and verify:

1. Brand name “小满理财” is visible.
2. Navigation shows 总览、持仓、流水、数据更新、预警.
3. The page is readable on desktop and mobile widths.
4. No write action is available to viewer role.

- [ ] **Step 5: Commit final fixes**

```bash
git add .
git commit -m "chore: verify xiaoman MVP"
```

## Self-Review

Spec coverage:

1. “小满理财” brand and Logo direction: Task 8.
2. Manual external and internal ledger entry: Task 2 and Task 5.
3. NAV and share calculation: Task 2 and Task 3.
4. Product configuration from the Word document: Task 6.
5. T+1 data update shell and failure handling: Task 7.
6. Dashboard, holdings, ledger, update, and alert pages: Task 6 and Task 8.
7. Admin write and family read-only role: Task 9.
8. Tencent Cloud deployment and PostgreSQL production target: Task 10.

Placeholder scan: plan uses concrete file paths, commands, and expected outcomes. Implementation details that depend on code written in earlier tasks are constrained by tests before the code step.

Type consistency: ledger domain uses `Decimal`, quantized money to `0.01`, shares and quantities to `0.0001`, and NAV to `0.0001` throughout the plan.
