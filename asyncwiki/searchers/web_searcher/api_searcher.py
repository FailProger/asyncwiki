from typing import Optional, Any

import asyncio as _asyncio
from aiohttp import ClientSession, ClientResponse

from ...parsers import WikipediaParser
from ...utils import get_response

from ...types import WikiSimpleResult, WikiResult, WikiQuery
from ...tuples import APISearchResult
from ...params import WPSearchPriority

from ...exc import WikiNoneSearchResults

from ...config import wiki_search_url, wiki_page_url
from ...loggers import wiki_logger, LogTimer


__all__ = (
    "WikiApiWebSearcher",
)


class WikiApiWebSearcher:
    """
    Wikipedia Api scraper. Use Api to search. Is more accurate than Fast scraper but is slower

    Note:
        This class is designed for internal use.

    Args:
        token: Wikimedia API token. If not, then in one hour the maximum number
               of search queries is 500. More about - https://api.wikimedia.org/wiki/Rate_limits
    """

    # Magic methods
    def __init__(self, token: Optional[str] = None) -> None:
        self.token = token if token else ""

    # Getters and setters
    @property
    def token(self) -> str:
        return self.__token if self.__token != "" else None

    @token.setter
    def token(self, token: str) -> None:
        self.__token = token
        self.__api_headers = {"Authorization": self.__token}

    # Main methods
    async def api_search(
            self,
            session: ClientSession,
            wiki_query: WikiQuery
    ) -> WikiResult:
        """
        Performs a full search. Gets the article page and the additional results.

        Args:
            session: Session of :code:`ClientSession` for getting response.
            wiki_query: :code:`WikiQuery` object for search.

        Returns:
            Generated search result - :code:`WikiResult`.

        Raises:
            WikiNoneSearchResults: If nothing was found.
        """

        wiki_logger.api_scraper.info("API scraper started")

        loop = _asyncio.get_running_loop()
        lang = wiki_query.lang

        search_results = await self.__api_search_page(session, wiki_query)
        key = search_results.keys[0]
        title = search_results.titles[0]

        task1 = _asyncio.create_task(self.__api_get_page(session, key, lang))
        task2 = loop.run_in_executor(None, self.__get_links, search_results, lang)

        page, simple_results = await _asyncio.gather(task1, task2)  # type: str, list[WikiSimpleResult]
        summary = WikipediaParser.parse(page, summary_only=True)

        return WikiResult(key, title, lang, summary, simple_results)

    async def __api_search_page(
            self,
            session: ClientSession,
            wiki_query: WikiQuery
    ) -> APISearchResult:
        """
        Searches for potential pages by search query.

        Args:
            session: Session of :code:`ClientSession` for getting response.
            wiki_query: :code:`WikiQuery` object for search.

        Returns:
            NamedTuple of WikiApi pre result - titles and keys of Wikipedia pages.

        Raises:
            WikiNoneSearchResults: If nothing was found.
        """

        timer = LogTimer()

        search_params = wiki_query.search_params
        number_of_results = search_params.number_of_results
        number_of_results += number_of_results * 5

        title_search_url = wiki_search_url.format(wiki_query.lang, "title")
        page_search_url = wiki_search_url.format(wiki_query.lang, "page")
        kwargs = {
            "headers": self.__api_headers,
            "params": {
                "q": wiki_query.query,
                "limit": number_of_results
            }
        }

        task1 = _asyncio.create_task(get_response(session, wiki_logger.api_scraper, title_search_url, **kwargs))
        task2 = _asyncio.create_task(get_response(session, wiki_logger.api_scraper, page_search_url, **kwargs))

        results_by_title, results_by_content = await _asyncio.gather(task1, task2)  # type: ClientResponse, ClientResponse

        task1 = _asyncio.create_task(results_by_title.json())
        task2 = _asyncio.create_task(results_by_content.json())

        title_json, content_json = await _asyncio.gather(task1, task2)  # type: dict[str, Any], dict[str, Any]

        title_pages: list[dict[str, str]] = title_json["pages"]
        content_pages: list[dict[str, str]] = content_json["pages"]

        if search_params.priority == WPSearchPriority.content:
            if content_pages:
                pages = content_pages

            else:
                pages = title_pages
                wiki_logger.api_scraper.warning("Search priority changed to title")

        else:
            if title_pages:
                pages = title_pages

            else:
                pages = content_pages
                wiki_logger.api_scraper.warning("Search priority changed to content")

        pages_len = len(pages)
        if pages_len == 0:
            wiki_logger.api_scraper.error("Not received any results")
            raise WikiNoneSearchResults

        title_list = []
        key_list = []

        for i in range(0, pages_len):
            page = pages[i]

            title_list.append(page["title"])
            key_list.append(page["key"])

            if i + 1 == number_of_results:
                break

        result = APISearchResult(title_list, key_list)

        wiki_logger.api_scraper.info(f"Search results received in {timer.stop()} sec")
        return result

    # Class methods
    @classmethod
    async def __api_get_page(
            cls,
            session: ClientSession,
            key: str,
            lang: str
    ) -> str:
        """
        Gets the HTML code of the page by its key.

        Args:
            session: Session of :code:`ClientSession` for getting response.
            key: Key of Wikipedia article.
            lang: Language code of search query.

        Returns:
            HTML code of Wikipedia article - :code:`str`
        """

        timer = LogTimer()

        page_url = wiki_page_url.format(lang, key)

        response = await get_response(session, wiki_logger.api_scraper, page_url)
        page = await response.text()

        wiki_logger.api_scraper.info(f"Page received in {timer.stop()} sec")
        return page

    @classmethod
    def __get_links(cls, search_result: APISearchResult, lang: str) -> list[WikiSimpleResult]:
        """
        Compile advanced results link for :code:`WikiResult`.

        Args:
            search_result: Raw API search results.
            lang: Language code of search query.

        Returns:
            List of :code:`WikiSimpleResult`.
        """

        title_list = search_result.titles[0:]
        key_list = search_result.keys[0:]

        url_list = []

        for i in range(0, len(title_list)):
            url_list.append(
                WikiSimpleResult(
                    title=title_list[i],
                    raw_link=key_list[i],
                    lang=lang,
                )
            )

        return url_list
