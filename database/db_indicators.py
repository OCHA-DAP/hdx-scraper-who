from hdx.database import NoTZBase
from sqlalchemy.orm import Mapped, mapped_column


class DBIndicators(NoTZBase):
    __tablename__ = "indicators"
    code: Mapped[str] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column()
    url: Mapped[str] = mapped_column(nullable=True)
