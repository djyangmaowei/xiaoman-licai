from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DailyValuation(Base):
    __tablename__ = "daily_valuations"

    id: Mapped[int] = mapped_column(primary_key=True)
    valuation_date: Mapped[date] = mapped_column(Date, unique=True, index=True)
    cash: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    total_assets: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    total_shares: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    unit_nav: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
