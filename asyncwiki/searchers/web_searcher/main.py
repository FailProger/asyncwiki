from typing import Union, Optional

import asyncio as _asyncio
from aiohttp import ClientSession

from .api_searcher import WikiApiWebSearcher
from .fast_searcher import WikiFastWebSearcher

from ...types import WikiResult, WikiQuery
from ...params import WPSearchModes, WikiSearchParams

from ...exc import WikiScraperExc

from ...loggers import wiki_logger, LogTimer


__all__ = (
    "WikiWebSearcher"
)


class WikiWebSearcher:
    """
    Wikipedia scraper. Use two scraper to search:\n
    Fast scraper - is not accurate because don`t use Wikimedia API but is fast.\n
    API scraper - use Wikimedia API and is more accurate but is slower.

    Args:
        token: Wikimedia API token. Need for API scraper. If not, then in one hour the maximum number
               of search queries is 500. More about - https://api.wikimedia.org/wiki/Rate_limits
    """

    # Magic methods
    def __init__(self, token: Optional[str] = None) -> None:
        self.__wiki_api_searcher = WikiApiWebSearcher(token)

    # Getters and setters
    @property
    def token(self) -> str:
        return self.__wiki_api_searcher.token

    @token.setter
    def token(self, token: str):
        self.__wiki_api_searcher.token = token

    # Main methods
    async def search(
            self,
            query: Union[str, WikiQuery],
            lang: str = "en",
            search_params: WikiSearchParams = WikiSearchParams()
    ) -> Union[WikiResult, None]:
        """
        Scrape pages from Wikipedia.

        Args:
            query: Query for searching in Wikipedia.
            lang: Language code of search query. Default - :code:`en`.
            search_params: Search parameters. Object of :code:`WikiSearchParams`.

        Returns:
            Page title, link, summary (first :code:`n` paragraphs) and list of additional
            results (pages title and link).
        """

        wiki_logger.scraper.info("Scraping started")
        timer = LogTimer()

        loop = _asyncio.get_running_loop()

        wiki_query: WikiQuery = WikiQuery(query, lang, search_params) if type(query) is str else query
        search_params = wiki_query.search_params

        result = None

        async with ClientSession(loop=loop) as session:
            try:
                assert search_params.mode == WPSearchModes.fast or wiki_query.is_link, "Use API scraper"
                wiki_logger.scraper.info("Use Fast scraper")
                result = await WikiFastWebSearcher.fast_search(session, wiki_query)

            except (WikiScraperExc, AssertionError) as error:
                if type(error) is AssertionError:
                    wiki_logger.scraper.info(error)

                else:
                    wiki_logger.fast_scraper.warning("Fast scraper not found anything")
                    wiki_logger.scraper.warning("Scraper changed on API")

                try:
                    result = await self.__wiki_api_searcher.api_search(session, wiki_query)

                except WikiScraperExc:
                    wiki_logger.api_scraper.warning("API scraper not found anything")

        if result is None:
            wiki_logger.scraper.warning("Scrapers not found anything")

        else:
            wiki_logger.scraper.info(f"Scraping finished in {timer.stop()} sec")

        return result
