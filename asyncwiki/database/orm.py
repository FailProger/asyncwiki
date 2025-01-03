from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .tables import WikiDBPages, WikiDBQueries

from ..types import WikiResult
from ..utils.wikiSyncDef import results_preparer


__all__ = (
    "WikiDBOrm"
)


class WikiDBOrm:
    """
    Object for comfortable work with SQLAlchemy ORM.

    e.g.::

        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
        from asyncwiki.database import WikiDB, WikiDBOrm

        # use SQLAlchemy
        engine = create_async_engine("sqlalchemy_url")
        session_maker = async_sessionmaker(bind=engine, class_=AsyncSession)
        session = session_maker()

        # use WikiDB
        wiki_db = WikiDB("sqlalchemy_url)
        session = wiki_db.session  # equal session = wiki_db.session_maker()

        async def search_page():
            async with WikiDBOrm(session) as orm:
                page = await orm.select_page_by_query("Some query", lang="en")

    Args:
        session: Object of SQLAlchemy :code:`AsyncSession`, not open ORM session. It will be opened later.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.__session = session

    async def __aenter__(self):
        """Using async context manager for connect to database with ORM"""

        self.__session = await self.__session.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Closing async context manager with closing ORM session"""

        await self.__session.__aexit__(exc_type, exc_val, exc_tb)

    @property
    def session(self) -> AsyncSession:
        return self.__session

    async def add_page(self, page: WikiResult) -> WikiDBPages:
        """
        Add new Wikipedia page in database. Before preparing advanced search results.

        Args:
            page: Result of Wikipedia scraping.

        Returns:
            Added pages - :code:`WikiPages`.
        """

        preparing_results = results_preparer(page.simple_results)

        query = WikiDBPages(
            key=page.key,
            title=page.title,
            lang=page.lang,
            summary=page.summary,
            simple_result1=preparing_results[0],
            simple_result2=preparing_results[1],
            simple_result3=preparing_results[2],
            simple_result4=preparing_results[3],
            simple_result5=preparing_results[4]
        )

        self.__session.add(query)
        await self.__session.commit()

        return query

    async def select_page_by_key(self, key: str, lang: str) -> WikiDBPages:
        """
        Select one Wikipedia page by key and language code.

        Args:
            key: Wikipedia page key.
            lang: Language code of Wikipedia page.

        Returns:
            Wikipedia page - :code:`WikiPages`
        """

        query = select(WikiDBPages).where(
            WikiDBPages.key == key,
            WikiDBPages.lang == lang
        )

        result = await self.__session.execute(query)

        return result.scalar()

    async def select_page_id_by_key(self, key: str, lang: str) -> int:
        """
        Select one Wikipedia id page by key and language code.

        Args:
            key: Wikipedia page key.
            lang: Language code of Wikipedia page.

        Returns:
            Database page id
        """

        query = select(WikiDBPages.id).where(
            WikiDBPages.key == key,
            WikiDBPages.lang == lang
        )

        result = await self.__session.execute(query)

        return result.scalar()

    async def select_page_by_query(self, query: str, lang: str) -> WikiDBPages:
        """
        Select page by search query.

        Args:
            query: Search query.
            lang: Language code of search query.

        Returns:
            Wikipedia page - :code:`WikiPages`
        """

        db_query = select(WikiDBPages).where(
            WikiDBQueries.query == query.lower(),
            WikiDBQueries.lang == lang
        ).join_from(
            WikiDBQueries,
            WikiDBPages
        )

        result = await self.__session.execute(db_query)

        return result.scalar()

    async def add_query(self, query: str, lang: str, page_id: int) -> WikiDBQueries:
        """
        Add new search query to database and return it.

        Args:
            query: Search query.
            lang: Language code of search query.
            page_id: Wikipedia page id to which query will be referred.

        Returns:
            Added search query - :code:`WikiQueries`
        """

        db_query = WikiDBQueries(
            query=query,
            lang=lang,
            page_id=page_id
        )

        self.__session.add(db_query)
        await self.__session.commit()

        return db_query

    async def select_query_id(self, query: str, lang: str, page_id: int) -> int:
        """
        Select search query id by query, language code and page id.

        Args:
            query: Search query.
            lang: Language code of search query.
            page_id: Wikipedia page id to which query referred.

        Returns:
            Search query id
        """

        db_query = select(WikiDBQueries.id).where(
            WikiDBQueries.query == query,
            WikiDBQueries.lang == lang,
            WikiDBQueries.page_id == page_id
        )

        result = await self.__session.execute(db_query)
        return result.scalar()
