from sqlalchemy.engine.url import URL
from .database import WikiDB

from .searchers import WikiDBSearcher, WikiWebSearcher

from .types import WikiResult, WikiQuery
from .params import (
    WikiSearchParams,
    WPSearchModes,
    WPQueryTreatments,
    WPDBSearch,
)

from .exc import (
    WikiDBExc,
    _WikiNotUseDBSearch
)

from .logger import wiki_logger, LogTimer


__all__ = (
    "WikiSearcher"
)


class WikiSearcher:
    """
    Wikipedia searcher. Search page by title or content in Wikipedia. Also use for it Wikimedia API
    and save founded pages in database.\n

    Note:
        Include :code:`WikiWebSearcher` and :code:`WikiDBSearcher`.

    Args:
        token: Wikimedia API token. If not, then in one hour the maximum number of search queries is 500.
                  More about - https://api.wikimedia.org/wiki/Rate_limits
        db_url: SQLAlchemy URL for connect to database or your :code:`WikiDB` object.
                   If not, database don`t use.
        kwargs: Advanced params for :code:`WikiDB`.
    """

    __modes = WPSearchModes
    __treatments = WPQueryTreatments

    def __init__(
            self,
            token: str = None,
            db_url: str | URL | WikiDB = None,
            **kwargs
    ) -> None:

        self.__web_searcher = WikiWebSearcher(token)
        self.__db_searcher = WikiDBSearcher(db_url, **kwargs) if db_url else None

    @property
    def web_searcher(self) -> WikiWebSearcher:
        return self.__web_searcher

    @property
    def token(self) -> str:
        return self.__web_searcher.token

    @property
    def db_searcher(self) -> WikiDBSearcher:
        return self.__db_searcher

    @property
    def db_engine(self) -> WikiDB:
        return self.__db_searcher.db_engine if self.__db_searcher else None

    @property
    def db_url(self) -> str | URL:
        return self.__db_searcher.db_url if self.__db_searcher else None

    async def setup_db(self) -> None:
        """
        Make first database setup: if you need drop database and create all tables if exists.\n
        This function call automatically then open first connection to the database.
        But if you need you can call it yourself.

        Return:
            None
        """

        if self.__db_searcher:
            await self.__db_searcher.setup_db()

        else:
            wiki_logger.wiki.warning("Database is not yet connected")

    async def search(
            self,
            query: str,
            lang: str = "en",
            search_params: WikiSearchParams = WikiSearchParams(),
    ) -> WikiResult | None:
        """
        Search pages in Wikipedia, first in database, second scrape site.

        Args:
            query: Query for searching in Wikipedia.
            lang: Language code of search query. Default - :code:`en`.
            search_params: Search parameters. Object of :code:`WikiSearchParams`.

        Returns:
            Page title, link, summary (first :code:`n` paragraphs) and list of additional
            results (pages title and link).
        """

        wiki_logger.wiki.info("Searching started")
        timer = LogTimer()

        wiki_query = WikiQuery(query, lang, search_params)
        wiki_logger.wiki.info(f"Search query '{wiki_query.query}' accepted")

        try:
            if self.__db_searcher is None or search_params.db_search == WPDBSearch.no:
                wiki_logger.wiki.warning("Don`t search in database")
                raise _WikiNotUseDBSearch

            result = await self.__db_searcher.search(wiki_query)

        except WikiDBExc:
            result = await self.__web_searcher.search(wiki_query)

            if result is None:
                wiki_logger.wiki.error("Searchers not found anything")
                return result

            else:
                if (
                    self.__db_searcher is None or
                    wiki_query.is_link or
                    search_params.query_treatment == self.__treatments.without
                ):
                    wiki_logger.wiki.warning("Don`t save result in database")

                else:
                    await self.__db_searcher.save_result(wiki_query.query, result)

        wiki_logger.wiki.info(f"Result got in {timer.stop()} sec")
        return result
