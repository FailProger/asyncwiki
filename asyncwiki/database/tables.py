import datetime as _datetime

from sqlalchemy import func, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


__all__ = (
    "base_table_class",
    "WikiDBPages",
    "WikiDBQueries"
)


_now = func.now() + _datetime.timedelta(hours=3)


class Base(DeclarativeBase):
    """Main class of database tables"""

    created: Mapped[DateTime] = mapped_column(DateTime, default=_now)
    updated: Mapped[DateTime] = mapped_column(DateTime, default=_now, onupdate=_now)


# Var of main tables class
base_table_class = Base


class WikiDBPages(base_table_class):
    """Class of Wikipedia pages"""

    __tablename__ = "wiki_page"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    key: Mapped[str] = mapped_column(String(150), nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    lang: Mapped[str] = mapped_column(String(5), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)

    # Advanced search results
    simple_result1: Mapped[str] = mapped_column(String(500), nullable=True)
    simple_result2: Mapped[str] = mapped_column(String(500), nullable=True)
    simple_result3: Mapped[str] = mapped_column(String(500), nullable=True)
    simple_result4: Mapped[str] = mapped_column(String(500), nullable=True)
    simple_result5: Mapped[str] = mapped_column(String(500), nullable=True)


class WikiDBQueries(base_table_class):
    """Class of search query, need for find Wikipedia pages"""

    __tablename__ = "wiki_query"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    query: Mapped[str] = mapped_column(String(250), nullable=False)
    lang: Mapped[str] = mapped_column(String(5), nullable=False)
    page_id: Mapped[int] = mapped_column(ForeignKey(WikiDBPages.id, ondelete="CASCADE"))
