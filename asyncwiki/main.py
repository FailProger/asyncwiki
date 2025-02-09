from typing import Union, Optional, Any

from sqlalchemy.engine.url import URL
from .database import WikiDB

from .searchers import WikiDBSearcher, WikiWebSearcher

from .types import WikiResult, WikiQuery
from .params import (
    WikiSearchParams,
    WPQueryTreatments,
    WPDBSearch
)

from .exc import WikiDBExc

from .loggers import wiki_logger, LogTimer


__all__ = (
    "WikiSearcher",
)


class WikiSearcher:
    """
    Wikipedia searcher. Search page by title or content in Wikipedia. Also use for it Wikimedia API
    and save founded pages in database.\n

    Notes:
        Include :code:`WikiWebSearcher` and :code:`WikiDBSearcher`.

        If not :code:`db_url` and :code:`wiki_db`, database don`t use.

    Args:
        token: Wikimedia API token. If not, then in one hour the maximum number of search queries is 500.
                  More about - https://api.wikimedia.org/wiki/Rate_limits
        db_url: SQLAlchemy URL for connect to database. If not it and wiki_db, database don`t use.
        wiki_db: Your :code:`WikiDB` object for connect to database. If not it and db_url, database don`t use.
        kwargs: Advanced params for :code:`WikiDB`.
    """

    # Magic methods
    def __init__(
            self,
            token: Optional[str] = None,
            *,
            db_url: Optional[Union[str, URL]] = None,
            wiki_db: Optional[WikiDB] = None,
            **kwargs: Any
    ) -> None:

        self.__web_searcher = WikiWebSearcher(token)
        self.__db_searcher = WikiDBSearcher(db_url=db_url, wiki_db=wiki_db, **kwargs) if db_url or wiki_db else None

    # Getters and setters
    @property
    def web_searcher(self) -> WikiWebSearcher:
        return self.__web_searcher

    @property
    def token(self) -> str:
        return self.__web_searcher.token

    @token.setter
    def token(self, token: str) -> None:
        self.__web_searcher.token = token

    @property
    def db_searcher(self) -> WikiDBSearcher:
        return self.__db_searcher

    @property
    def db_url(self) -> Union[str, URL]:
        return self.__db_searcher.db_url if self.__db_searcher else None

    # Main methods
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
            wiki_logger.wiki.error("Database is not yet connected")

    async def search(
            self,
            query: str,
            lang: str = "en",
            search_params: WikiSearchParams = WikiSearchParams(),
    ) -> Union[WikiResult, None]:
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
            assert self.__db_searcher and search_params.db_search == WPDBSearch.yes, "Don`t search in database"
            result = await self.__db_searcher.search(wiki_query)
            assert result

        except (WikiDBExc, AssertionError) as error:
            if type(error) is AssertionError and str(error) != "":
                wiki_logger.wiki.warning(error)

            result = await self.__web_searcher.search(wiki_query)

            if result is None:
                wiki_logger.wiki.warning("Searchers not found anything")
                return result

            else:
                if (
                        self.__db_searcher is None or wiki_query.is_link or
                        search_params.query_treatment == WPQueryTreatments.without
                ):
                    wiki_logger.wiki.warning("Don`t save result in database")

                else:
                    await self.__db_searcher.save_result(wiki_query.query, result)

        wiki_logger.wiki.info(f"Result got in {timer.stop()} sec")
        return result
