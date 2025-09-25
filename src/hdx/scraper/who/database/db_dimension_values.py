from hdx.database.no_timezone import Base as NoTZBase
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db_dimensions import DBDimensions  # noqa: F401


class DBDimensionValues(NoTZBase):
    __tablename__ = "dimension_values"
    code: Mapped[str] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(primary_key=True)
    dimension_code: Mapped[int] = mapped_column(ForeignKey("dimensions.code"))

    dimensions = relationship("DBDimensions")
