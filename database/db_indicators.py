from hdx.database import NoTZBase
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db_categories import DBCategories  # noqa: F401


class DBIndicators(NoTZBase):
    __tablename__ = "indicators"
    code: Mapped[str] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column()
    url: Mapped[str] = mapped_column(nullable=True)
    category_title: Mapped[int] = mapped_column(
        ForeignKey("categories.title"), nullable=True, index=True
    )

    dimensions = relationship("DBCategories")
