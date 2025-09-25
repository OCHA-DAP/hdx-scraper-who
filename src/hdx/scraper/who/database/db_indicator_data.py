from hdx.database.no_timezone import Base as NoTZBase
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db_indicators import DBIndicators  # noqa: F401


class DBIndicatorData(NoTZBase):
    __tablename__ = "indicator_data"
    id: Mapped[int] = mapped_column(primary_key=True)
    indicator_code: Mapped[int] = mapped_column(ForeignKey("indicators.code"))
    indicator_name: Mapped[str] = mapped_column()
    indicator_url: Mapped[str] = mapped_column(nullable=True)
    year: Mapped[int] = mapped_column()
    start_year: Mapped[int] = mapped_column()
    end_year: Mapped[int] = mapped_column()
    region_code: Mapped[str] = mapped_column(nullable=True)
    region_display: Mapped[str] = mapped_column(nullable=True)
    country_code: Mapped[str] = mapped_column(index=True)
    country_display: Mapped[str] = mapped_column(nullable=True)
    dimension_type: Mapped[str] = mapped_column(nullable=True)
    dimension_code: Mapped[str] = mapped_column(nullable=True)
    dimension_name: Mapped[str] = mapped_column(nullable=True)
    numeric: Mapped[float] = mapped_column(nullable=True)
    value: Mapped[str] = mapped_column(nullable=True)
    low: Mapped[str] = mapped_column(nullable=True)
    high: Mapped[str] = mapped_column(nullable=True)

    indicators = relationship("DBIndicators")
