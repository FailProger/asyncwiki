from bs4 import BeautifulSoup
from bs4.element import PageElement, ResultSet

from ..types import WikiSimpleResult
from ..tuples import ContentSups
from ..config import wiki_summary_limit


__all__ = (
    "get_all_sup_in_p",
    "wiki_text_compiler",
    "wiki_text_cuter",
    "results_preparer"
)


def get_all_sup_in_p(p: PageElement | BeautifulSoup, index: int) -> ContentSups:
    """
    Searches for extra characters in a paragraph.

    Args:
        p: Summary paragraph :code:`BeautifulSoup` object.
        index: Index of a paragraph in a list of paragraphs.

    Returns:
        :code:`WikiContentSups` to remove unnecessary elements.
    """

    raw_sups = p.find_all("sup")
    sups = [sup.text for sup in raw_sups]
    return ContentSups(index, sups)


def wiki_text_compiler(p_list: ResultSet[PageElement], bold: PageElement) -> str:
    """
    Constructs the main text for the WikiWebSearcher.

    Args:
        p_list: List of body paragraph :code:`BeautifulSoup` objects.
        bold: Bold word in first paragraph.

    Returns:
        A cleaned summary for the search result.
    """

    all_p_sups_list = [get_all_sup_in_p(p, p_list.index(p)) for p in p_list]

    summary_list: list[str] = []

    for sups in all_p_sups_list:
        p_index = sups.paragraph_index  # type: int
        clear_p = p_list[p_index].text  # type: str
        sups_list = sups.sups_text  # type: list[str]

        for sup in sups_list:
            clear_p = clear_p.replace(f"{sup}", "")

        summary_list.append(clear_p)

    summary_list[0] = summary_list[0].replace(f"{bold.text}", f"<b>{bold.text}</b>", 1)

    text = "".join(summary_list)

    return text


def wiki_text_cuter(text: str) -> str:
    """
    Trims a summary obtained from Wikipedia to the end of the paragraph, starting at a specific character.

    Args:
        text: Ready summary text.

    Returns:
        Trimmed summary.
    """

    while len(text) != 0 and text[0] == "\n" or len(text) != 0 and text[0] == " ":
        text = text[1:]

    if len(text) == 0:
        return text

    sign = text.find("\n", wiki_summary_limit)

    if sign == -1:
        sign = text.find("\n")

    cut_text = text[:sign]

    if cut_text[-1] == ":":
        pass
    elif cut_text[-1] != ".":
        cut_text += "."

    return cut_text


def results_preparer(simple_results: list[WikiSimpleResult]):
    """Prepares results for entering into the database."""

    preparing_results = []

    for i in range(0, 5):
        try:
            res = f"{simple_results[i].title}|{simple_results[i].raw_link}"
            preparing_results.append(res)

        except IndexError:
            preparing_results.append(None)

    return preparing_results
