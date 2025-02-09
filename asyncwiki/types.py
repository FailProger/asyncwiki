from typing import Union, Optional

from spellchecker import SpellChecker as _SpellChecker

from bs4 import BeautifulSoup

from .params import (
    WikiSearchParams,
    WPQueryTreatments,
    WPDBSearch,
    WPDBSearchByURL
)

from .config import (
    title_tag,
    summary_tag,
    page_url_tag,
    srtitle_tag_name,
    simple_results_tag,
    default_answer_template,
    query_clean_list,
    wiki_page_url
)
from .loggers import wiki_logger


__all__ = (
    "WikiQuery",
    "WikiResult",
    "WikiSimpleResult"
)


class WikiQuery:
    """
    Clean the search query of unnecessary words and
    check is one a link to a Wikipedia page or not.

    Args:
        query: Raw search query for correction.
        lang: Language of query.
        search_params: Parameters of searchin, need for correct cleaning.
    """

    # Magic methods
    def __init__(self, query: str, lang: str, search_params: WikiSearchParams) -> None:

        self.__raw_query = query
        self.__lang = lang
        self.__search_params = search_params

        self.__is_link = self.__link_checker()
        self.__query = self.__clean()

    # Getters
    @property
    def raw_query(self) -> str:
        return self.__raw_query

    @property
    def lang(self) -> str:
        return self.__lang

    @property
    def search_params(self) -> WikiSearchParams:
        return self.__search_params

    @property
    def is_link(self) -> bool:
        return self.__is_link

    @property
    def query(self) -> str:
        return self.__query

    # Main methods
    def __link_checker(self) -> bool:
        """
        Checks the search query is a link to a Wikipedia page or not.

        Returns:
            True if yes, false if not.
        """

        split = self.__raw_query.split("//")

        if split[0] == "https:":
            split_query = split[1].split("/")[0].split(".")
            split_len = len(split_query)

            if (split_query[0] if split_len == 2 else split_query[1]) == "wikipedia":
                if split_len == 3:
                    self.__lang = split_query[0]

                if self.__search_params.db_search_by_url == WPDBSearchByURL.no:
                    self.search_params.db_search = WPDBSearch.no

                return True

        else:
            return False

    def __clean(self) -> str:
        """
        Clean the search query of unnecessary words and corrects spelling.

        Returns:
            Clean search query.
        """

        raw_query = self.__raw_query
        lang = self.__lang
        search_params = self.__search_params

        # Does not process the query if so set in the parameters
        if self.is_link:
            return raw_query

        elif search_params.query_treatment == WPQueryTreatments.without:
            return raw_query.replace(" ", "_")

        spell = _SpellChecker(language=lang)
        spell_split = spell.split_words(raw_query)  # Separates words by removing spaces and characters

        # Filtering unnecessary words
        words_list = [word if word.lower() not in query_clean_list else ... for word in spell_split]
        result = "_".join(words_list)

        # Add here machine learning for correctly work!!!

        if result is None or result == "":
            wiki_logger.wiki.warning("Failed to clean search query")
            result = raw_query.replace(" ", "_")

        return result


class WikiSimpleResult:
    """
    Class of advanced search results. Need for WikiResult compile.

    Args:
        title: Title of simple article.
        raw_link: Raw link to simple article.
        lang: Language code of search query.
    """

    __wiki_folder = "/wiki/"

    # Magic methods
    def __init__(self, title: str, raw_link: str, lang: str) -> None:
        self.title = title
        self.__lang = lang
        self.raw_link = raw_link

    # Getters and setters
    @property
    def lang(self) -> str:
        return self.__lang

    @property
    def raw_link(self) -> str:
        return self.__raw_link

    @raw_link.setter
    def raw_link(self, raw_link: str) -> None:
        """Clean and compile link."""

        wiki = raw_link.find(self.__wiki_folder)
        if wiki != -1:
            raw_link = raw_link[wiki + len(self.__wiki_folder):]

        link = wiki_page_url.format(self.lang, raw_link)

        self.__raw_link = raw_link
        self.__link = link

    @property
    def link(self) -> str:
        return self.__link

    # Main methods
    def html_text(self) -> str:
        """Return html text with clean link to article."""

        return f"<i><a href='{self.link}'>{self.title}</a></i>"


class WikiResult:
    """
    Class of WikiSearcher result.

    Args:
        title: Wikipedia page title.
        key: Key of Wikipedia page.
        lang: Wikipedia page language code.
        summary: Wikipedia page summary.
        simple_results: Advanced search results.
    """

    # Magic methods
    def __init__(
            self,
            key: str,
            title: str,
            lang: str,
            summary: str,
            simple_results: Optional[list[WikiSimpleResult]] = None
    ) -> None:

        self.__key = key
        self.title = title
        self.__lang = lang
        self.__url = wiki_page_url.format(lang, key)
        self.summary = summary
        self.simple_results = simple_results

    def __str__(self) -> str:
        return self.compile()

    # Getters and setters
    @property
    def key(self) -> str:
        return self.__key

    @property
    def lang(self) -> str:
        return self.__lang

    @property
    def url(self) -> str:
        return self.__url

    @property
    def simple_results(self) -> Union[list[WikiSimpleResult], None]:
        return self.__simple_results

    @simple_results.setter
    def simple_results(self, simple_results: list[WikiSimpleResult]) -> None:
        if type(simple_results) is list:
            for result in simple_results:
                if result.title.lower() == self.title.lower():
                    simple_results.remove(result)

        self.__simple_results = simple_results[:5] if simple_results else None

    # Main methods
    def compile(self, template: str = default_answer_template) -> str:
        """
        Apply a template to :code:`WikiResult`.

        Args:
            template: Your template.

        Returns:
            Beautiful compiled text
        """

        simple_results = self.simple_results

        soup = BeautifulSoup(template, "lxml")
        srtitle = str(soup.find(srtitle_tag_name))

        if type(simple_results) is list:
            if srtitle:
                clear_srtitle = (
                    srtitle.
                    replace(f"<{srtitle_tag_name}>", "").
                    replace(f"</{srtitle_tag_name}>", "")
                )
                template = template.replace(srtitle, clear_srtitle)

            if len(simple_results) != 0:
                template = template.replace(
                    simple_results_tag, "\n".join([result.html_text() for result in simple_results])
                )

            else:
                ops_text = (
                    "Увы, но ничего не нашлось" if self.lang == "ru" else "Sorry, but anything not be found"
                )
                template = template.replace(simple_results_tag, ops_text)

        else:
            if srtitle:
                template = template.replace(srtitle, "")

            template = template.replace(simple_results_tag, "")

        template = (
            template.
            replace(title_tag, self.title).
            replace(summary_tag, self.summary.replace(" < ", " ").replace(" > ", " ")).
            replace(page_url_tag, self.url)
        )

        return template
