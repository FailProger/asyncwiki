from typing import Union

from bs4 import BeautifulSoup
from bs4.element import ResultSet, PageElement

from ..exc import (
    WikiContentNotFound,
    WikiParagraphNotFound,
    WikiSummaryNotFound,
    WikiShortSummary
)

from ..utils import wiki_text_cuter, wiki_text_compiler

from ..config import wiki_summary_len_threshold
from ..loggers import wiki_logger


__all__ = (
    "WikipediaParser",
)


class WikipediaParser:
    """Parser for Wikipedia pages"""

    # Class methods
    @classmethod
    def parse(cls, page: str, summary_only: bool = False) -> Union[tuple[str, str, str], str]:
        """
        Gets the summary and title of the page.

        Args:
            page: HTML code of Wikipedia article.
            summary_only: If true return only summary.

        Returns:
            Page key, title, and summary - :code:`tuple[str,str,str]`.

        Raises:
            WikiShortSummary: If summary len less than :code:`wiki_summary_len_threshold`.
        """

        soup = BeautifulSoup(page, "lxml")

        p_list, bold = cls.__get_p_list_and_bold(soup)
        summary = wiki_text_cuter(
            wiki_text_compiler(p_list, bold)
        )

        if len(summary) < wiki_summary_len_threshold:
            wiki_logger.scraper.error("Summary is very short")
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

        Raises:
            WikiContentNotFound: If content on page not found.
            WikiParagraphNotFound: If first paragraph not found.
            WikiSummaryNotFound: If summary text not found.
        """

        p_limit = 5 - 1
        content = soup.find(class_="mw-content-ltr mw-parser-output")

        if content is None:
            wiki_logger.scraper.error("Content not found on page")
            raise WikiContentNotFound

        table = content.find("table", class_="infobox")
        if table:
            table.replace_with("")

        first_p = content.find("p")

        if first_p is None:
            wiki_logger.scraper.error("First paragraph not found on page")
            raise WikiParagraphNotFound

        while first_p.findChild("b") is None:
            first_p = first_p.find_next("p")

        p_list = first_p.find_next_siblings("p", limit=p_limit)  # type: ResultSet[Union[PageElement, BeautifulSoup]]
        p_list.insert(0, first_p)

        bold = p_list[0].findChild("b")  # Находит жирно выделенное слово в первом абзаце, чтобы удалить его потом

        if len(p_list) == 0:
            wiki_logger.scraper.error("Summary not found")
            raise WikiSummaryNotFound

        return p_list, bold
