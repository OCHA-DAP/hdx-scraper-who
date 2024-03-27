from hdx.database import NoTZBase
from sqlalchemy.orm import Mapped, mapped_column


class DBIndicatorData(NoTZBase):
    __tablename__ = "indicator_data"
    id: Mapped[int] = mapped_column(primary_key=True)
    indicator_code: Mapped[str] = mapped_column(index=True)
    indicator_name: Mapped[str] = mapped_column()
    indicator_url: Mapped[str] = mapped_column(nullable=True)
    year: Mapped[int] = mapped_column()
    start_year: Mapped[int] = mapped_column()
    end_year: Mapped[int] = mapped_column()
    region_code: Mapped[str] = mapped_column(nullable=True)
    region_display: Mapped[str] = mapped_column(nullable=True)
    country_code: Mapped[str] = mapped_column()
    country_display: Mapped[str] = mapped_column(nullable=True)
    dimension_type: Mapped[str] = mapped_column(nullable=True)
    dimension_code: Mapped[str] = mapped_column(nullable=True)
    dimension_name: Mapped[str] = mapped_column(nullable=True)
    numeric: Mapped[float] = mapped_column(nullable=True)
    value: Mapped[str] = mapped_column(nullable=True)
    low: Mapped[str] = mapped_column(nullable=True)
    high: Mapped[str] = mapped_column(nullable=True)
