from typing import Any

import asyncio as _asyncio
from aiohttp import ClientSession, ClientResponse

from bs4 import BeautifulSoup
from bs4.element import ResultSet, PageElement

from ..types import WikiSimpleResult, WikiResult, WikiQuery
from ..tuples import APISearchResult
from ..params import WPSearchModes, WikiSearchParams, WPSearchPriority

from ..exc import (
    WikiScraperExc,
    _WikiUseAPIScrapperExc,
    WikiNoneSearchResults,
    WikiResNotReceived,
    WikiContentNotFound,
    WikiParagraphNotFound,
    WikiSummaryNotFound,
    WikiShortSummary
)

from ..utils.wikiSyncDef import wiki_text_cuter, wiki_text_compiler

from ..config import wiki_search_url, wiki_page_url
from ..logger import wiki_logger, LogTimer


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

    def __init__(self, token: str = None) -> None:
        self.token = token if token else ""

    @property
    def token(self) -> str:
        return self.__token if self.__token != "" else None

    @token.setter
    def token(self, token: str):
        self.__token = token
        self.__api_headers = {"Authorization": token}

    async def search(
            self,
            query: str | WikiQuery,
            lang: str = "en",
            search_params: WikiSearchParams = WikiSearchParams()
    ) -> WikiResult:
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

        async with ClientSession(loop=loop) as session:
            try:
                if search_params.mode == WPSearchModes.default and wiki_query.is_link is False:
                    raise _WikiUseAPIScrapperExc

                result = await self.__fast_search(session, wiki_query)

            except WikiScraperExc as error:
                if type(error) is not _WikiUseAPIScrapperExc:
                    wiki_logger.scraper.warning("Scraper changed on API")

                result = await self.__api_search(session, wiki_query)

        wiki_logger.scraper.info(f"Scraping finished in {timer.stop()} sec")
        return result

    async def __fast_search(
            self,
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

        page_url = wiki_query.query if wiki_query.is_link else wiki_page_url.format(lang, query)

        response = await self.__get_response(session, page_url)
        page = await response.text()

        wiki_logger.fast_scraper.info(f"Page received in {timer.stop()} sec")

        key, title, summary = self.__parse(page)
        return WikiResult(key, title, lang, summary)

    async def __api_search(
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
        """

        wiki_logger.api_scraper.info("API scraper started")

        lang = wiki_query.lang
        loop = _asyncio.get_running_loop()

        search_result = await self.__api_search_page(session, wiki_query)
        key = search_result.keys[0]
        title = search_result.titles[0]

        task1 = _asyncio.create_task(self.__api_get_page(session, key, lang))
        task2 = loop.run_in_executor(None, self.__get_links, search_result, lang)

        page, simple_results = await _asyncio.gather(task1, task2)  # type: str, list[WikiSimpleResult]
        summary = self.__parse(page, summary_only=True)

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
        """

        timer = LogTimer()

        search_params = wiki_query.search_params
        number_of_results = search_params.number_of_results
        number_of_results += number_of_results * 5

        title_search_url = wiki_search_url.format(wiki_query.lang, "title")
        page_search_url = wiki_search_url.format(wiki_query.lang, "page")
        params = {
            "q": wiki_query.query,
            "limit": number_of_results
        }

        task1 = _asyncio.create_task(self.__get_response(session, title_search_url, self.__api_headers, params))
        task2 = _asyncio.create_task(self.__get_response(session, page_search_url, self.__api_headers, params))

        title_res, page_res = await _asyncio.gather(task1, task2)  # type: ClientResponse, ClientResponse

        task1 = _asyncio.create_task(title_res.json())
        task2 = _asyncio.create_task(page_res.json())

        title_json, page_json = await _asyncio.gather(task1, task2)  # type: dict[str, Any], dict[str, Any]

        title_pages: list[dict[str, str]] = title_json["pages"]
        page_pages: list[dict[str, str]] = page_json["pages"]

        if search_params.priority == WPSearchPriority.content:
            pages = page_pages if page_pages else title_pages

        else:
            pages = title_pages if title_pages else page_pages

        if len(pages) == 0:
            wiki_logger.api_scraper.error("Not received any results")
            raise WikiNoneSearchResults

        title_list = []
        key_list = []

        for i in range(0, number_of_results):
            try:
                page = pages[i]

                title_list.append(page["title"])
                key_list.append(page["key"])

            except IndexError:
                break

        result = APISearchResult(title_list, key_list)

        wiki_logger.api_scraper.info(f"Search results received in {timer.stop()} sec")
        return result

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

        response = await cls.__get_response(session, page_url)
        page = await response.text()

        wiki_logger.api_scraper.info(f"Page received in {timer.stop()} sec")
        return page

    @classmethod
    def __parse(cls, page: str, summary_only: bool = False) -> tuple[str, str, str] | str:
        """
        Gets the summary and title of the page.

        Args:
            page: HTML code of Wikipedia article.
            summary_only: If true return only summary.

        Returns:
            Page key, title, and summary - :code:`tuple[str,str,str]`.
        """

        soup = BeautifulSoup(page, "lxml")

        p_list, bold = cls.__get_p_list_and_bold(soup)
        summary = wiki_text_cuter(
            wiki_text_compiler(p_list, bold)
        )

        if len(summary) < 10:
            wiki_logger.scraper.warning("Summary is very short")
            raise WikiShortSummary

        if summary_only:
            return summary

        title = soup.find("h1", id="firstHeading").text
        key = (soup.find("link", rel="canonical", href=True)["href"]).split("/")[-1]

        wiki_logger.scraper.info("Summary and title parsed")
        return key, title, summary

    @classmethod
    def __get_p_list_and_bold(cls, soup: BeautifulSoup) -> tuple[ResultSet[PageElement], PageElement]:
        """
        Find first :code:`n` paragraphs in summary.

        Args:
            soup: Article page - :code:`BeautifulSoup`.

        Returns:
            :code:`ResultSet` with all found paragraphs.
        """

        p_limit = 5 - 1
        content = soup.find(class_="mw-content-ltr mw-parser-output")

        if content is None:
            wiki_logger.scraper.error("Content not found on page")
            raise WikiContentNotFound

        table = content.find("table", class_="infobox")
        if table:
            table.replace_with()

        first_p = content.find("p")

        if first_p is None:
            wiki_logger.scraper.error("First paragraph not found on page")
            raise WikiParagraphNotFound

        while first_p.findChild("b") is None:
            first_p = first_p.find_next("p")

        p_list = first_p.find_next_siblings("p", limit=p_limit)  # type: ResultSet[PageElement | BeautifulSoup]
        p_list.insert(0, first_p)

        bold = p_list[0].findChild("b")  # Находит жирно выделенное слово в первом абзаце, чтобы удалить его потом

        if len(p_list) == 0:
            wiki_logger.scraper.error("Summary not found")
            raise WikiSummaryNotFound

        return p_list, bold

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

    @classmethod
    async def __get_response(
            cls,
            session: ClientSession,
            url: str,
            headers: dict[str, str] = None,
            params: dict[str, Any] = None
    ) -> ClientResponse:
        """
        Receive response by URL.

        Args:
            session: Session of :code:`ClientSession` for getting response.
            url: URL for getting response.
            headers: Headers for HTTP request.
            params: Advanced params for HTTP request.

        Returns:
            :code:`ClientResponse`
        """

        res = await session.get(url=url, headers=headers, params=params)

        if res.status != 200:
            wiki_logger.scraper.error("Failed get response")
            raise WikiResNotReceived

        return res
