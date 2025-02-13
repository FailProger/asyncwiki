from typing import Union, Optional, Any

from sqlalchemy.engine.url import URL
from sqlalchemy.exc import DBAPIError

from ..database import WikiDBOrm, WikiDB
from ..database.tables import WikiDBPages

from ..types import WikiResult, WikiSimpleResult, WikiQuery
from ..params import WPSearchModes, WikiSearchParams

from ..loggers import wiki_logger, LogTimer


__all__ = (
    "WikiDBSearcher",
)


class WikiDBSearcher:
    """
    Search page by title in database and save founded by scraper pages in it.\n

    Note:
        You can indicate :code:`db_url` or :code:`wiki_db` for connect to database.

    Args:
        db_url: SQLAlchemy URL for connect to database or your :code:`WikiDB` object.
        wiki_db: Your :code:`WikiDB` object for connect to database.
        drop_db: Before creating all tables (if exists) drop database.
        db_echo: Logging of SQLAlchemy database engine.
        kwargs: Advanced params for :code:`WikiDB`.

    Raises:
        ValueError: if db_url and wiki_db not be indicated.
    """

    # Magic methods
    def __init__(
            self,
            *,
            db_url: Optional[Union[str, URL]] = None,
            wiki_db: Optional[WikiDB] = None,
            drop_db: bool = False,
            db_echo: bool = False,
            **kwargs: Any
    ) -> None:

        if db_url is None and wiki_db is None:
            raise ValueError("At least one of the parameters should be indicated: db_url or wiki_db")

        self.__db_engine: WikiDB = wiki_db if wiki_db else WikiDB(
            url=db_url,
            drop=drop_db,
            echo=db_echo,
            **kwargs
        )

        # Create functions with WikiDB decorator for receiving ORM connection.
        self.__search_func = self.__db_engine.orm_decorator()(self.__search)
        self.__save_func = self.__db_engine.orm_decorator()(self.__save_result)

    # Getters
    @property
    def db_engine(self) -> WikiDB:
        return self.__db_engine

    @property
    def db_url(self) -> Union[str, URL]:
        return self.__db_engine.url

    # Main methods
    async def setup_db(self) -> None:
        """
        Make first database setup: if you need drop database and create all tables if exists.

        Note:
            This function call automatically then open first connection to the database.
            But if you need you can call it yourself.

        Returns:
            None
        """

        await self.__db_engine.setup_db()

    async def search(
            self,
            query: Union[str, WikiQuery],
            lang: str = "en",
            search_params: WikiSearchParams = WikiSearchParams()
    ) -> Union[WikiResult, None]:
        """
        Try to find page in database.
        Saves result of searching to the database if most of the information has been find.

        Args:
            query: Query for searching in Wikipedia
            lang: Language code of search query. Default - :code:`en`.
            search_params: Search parameters. Object of :code:`WikiSearchParams`.

        Returns:
            Page title, link, summary (first :code:`n` paragraphs) and list of additional
            results (pages title and link).

        Raises:
            WikiDBPageNotFound: If searcher not found page in database.
        """

        return await self.__search_func(query, lang, search_params)

    async def save_result(
            self,
            query: str,
            result: WikiResult
    ) -> None:
        """
        Saves result of searching to the database if most of the information has been find.

        Args:
            query: The search query for which the result was found.
            result: Result of searching - :code:`WikiResult`.

        Returns:
            None
        """

        return await self.__save_func(query, result)

    # Class methods
    @classmethod
    async def __search(
            cls,
            query: Union[str, WikiQuery],
            lang: str = "en",
            search_params: WikiSearchParams = WikiSearchParams(),
            *,
            orm: WikiDBOrm,
    ) -> Union[WikiResult, None]:
        """
        Main search function. Saves result of searching to the database if most of the information has been find.
        Used with WikiDB ORM decorator for connect to database.

        Args:
            query: Query for searching in Wikipedia
            lang: Language code of search query. Default - :code:`en`.
            search_params: Search parameters. Object of :code:`WikiSearchParams`.
            orm: Wiki ORM session - :code:`WikiDBOrm`. This param forwarded by ORM decorator.

        Returns:
            Page title, link, summary (first :code:`n` paragraphs) and list of additional
            results (pages title and link).

        Raises:
            WikiDBPageNotFound: If searcher not found page in database.
        """

        wiki_logger.db.info("Searching in database started")
        timer = LogTimer()

        wiki_query: WikiQuery = WikiQuery(query, lang, search_params) if type(query) is str else query
        lang = wiki_query.lang
        search_params = wiki_query.search_params

        if wiki_query.is_link:
            key = wiki_query.query.split("/")[-1]
            page = await orm.select_page_by_key(key, lang)

        else:
            page = await orm.select_page_by_query(wiki_query.query, lang)

        if page is None:
            wiki_logger.db.warning("Page not found in database")
            return

        simple_results = cls.__simple_results_converter(page, search_params.mode)

        wiki_logger.db.info(f"Page found in database in {timer.stop()}")
        return WikiResult(page.key, page.title, page.lang, page.summary, simple_results)

    @classmethod
    async def __save_result(
            cls,
            query: str,
            result: WikiResult,
            *,
            orm: WikiDBOrm,
    ) -> None:
        """
        Main save function. Saves result of searching to the database if most of the information has been find.
        Used with WikiDB ORM decorator for connect to database.

        Args:
            query: The search query for which the result was found. Not :code:`WikiQuery`.
            result: Result of searching - :code:`WikiResult`.
            orm: Wiki ORM session - :code:`WikiDBOrm`. This param forwarded by ORM decorator.

        Returns:
            None

        Raises:
            DBAPIError: If failed to save result in database.
        """

        if result.simple_results:
            wiki_logger.db.info("Save result")
            timer = LogTimer()

            query = query.lower()

            page_id = await orm.select_page_id_by_key(result.key, result.lang)
            if page_id is None:
                try:
                    page_id = (await orm.add_page(result)).id
                    wiki_logger.db.info("Page saved in database")

                except DBAPIError as er:
                    wiki_logger.db.critical(f"Failed to save page to database:\n{er}")
                    raise

            else:
                wiki_logger.db.warning("This page already exist")

            query_id = await orm.select_query_id(query, result.lang, page_id)
            if query_id is None:
                try:
                    await orm.add_query(query, result.lang, page_id)
                    wiki_logger.db.info("Search query saved in database")

                except DBAPIError as er:
                    wiki_logger.db.critical(f"Failed to save search query to database:\n{er}")
                    raise

            else:
                wiki_logger.db.warning("Search query already exist")

            wiki_logger.db.info(f"Result saved in {timer.stop()} sec")

    @classmethod
    def __simple_results_converter(
            cls,
            page: WikiDBPages,
            search_mode: int
    ) -> Union[list[WikiSimpleResult], None]:
        """
        Converts advanced search results to the :code:`WikiSimpleSearchResult` class

        Args:
            page: Object of SQLAlchemy table class - :code:`WikiPages`.
            search_mode: One of :code:`WPSearchModes`.

        Returns:
            List of :code:`WikiSimpleResult` or :code:`None` when using fast mode.
        """

        if search_mode == WPSearchModes.default:
            raw_simple_results = [
                page.simple_result1,
                page.simple_result2,
                page.simple_result3,
                page.simple_result4,
                page.simple_result5
            ]  # type: list[str]

            simple_results = [
                WikiSimpleResult(
                    res.split("|")[0], res.split("|")[-1], page.lang
                ) for res in raw_simple_results if res
            ]
            return simple_results
