from hdx.database import NoTZBase
from sqlalchemy.orm import Mapped, mapped_column


class DBDimensions(NoTZBase):
    __tablename__ = "dimensions"
    code: Mapped[str] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(primary_key=True)
