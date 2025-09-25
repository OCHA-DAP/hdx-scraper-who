from hdx.database.no_timezone import Base as NoTZBase
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db_indicators import DBIndicators  # noqa: F401


class DBCategories(NoTZBase):
    __tablename__ = "categories"
    title: Mapped[str] = mapped_column(primary_key=True)
    indicator_code: Mapped[int] = mapped_column(
        ForeignKey("indicators.code"), primary_key=True
    )

    indicators = relationship("DBIndicators")
