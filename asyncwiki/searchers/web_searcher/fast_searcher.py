from aiohttp import ClientSession

from ...parsers import WikipediaParser
from ...utils import get_response

from ...types import WikiResult, WikiQuery

from ...config import wiki_page_url
from ...loggers import wiki_logger, LogTimer


__all__ = (
    "WikiFastWebSearcher",
)


class WikiFastWebSearcher:
    """
    Wikipedia Fast scraper. Is not accurate because don`t use Wikimedia API but is fast.\n

    Note:
        This class is designed for internal use.
    """

    # Class methods
    @classmethod
    async def fast_search(
            cls,
            session: ClientSession,
            wiki_query: WikiQuery,
    ) -> WikiResult:
        """
        Performs a quick search. Does not receive pages of additional results, which speeds up the process.

        Args:
            session: Session of :code:`ClientSession` for getting response.
            wiki_query: :code:`WikiQuery` object for search.

        Returns:
            Generated search result - :code:`WikiResult`.
        """

        wiki_logger.fast_scraper.info("Fast scraper started")
        timer = LogTimer()

        query = wiki_query.query
        lang = wiki_query.lang

        page_url = wiki_page_url.format(lang, query) if not wiki_query.is_link else wiki_query.query

        response = await get_response(session, wiki_logger.fast_scraper, page_url)
        page = await response.text()

        wiki_logger.fast_scraper.info(f"Page received in {timer.stop()} sec")

        key, title, summary = WikipediaParser.parse(page)
        return WikiResult(key, title, lang, summary)
