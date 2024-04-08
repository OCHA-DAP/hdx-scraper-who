from hdx.database import NoTZBase
from sqlalchemy.orm import Mapped, mapped_column


class DBCategories(NoTZBase):
    __tablename__ = "categories"
    title: Mapped[str] = mapped_column(primary_key=True)
