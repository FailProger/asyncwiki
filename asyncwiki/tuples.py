from typing import NamedTuple


__all__ = (
    "ContentSups",
    "APISearchResult"
)


class ContentSups(NamedTuple):
    """NamedTuple of extra elements in paragraph."""

    paragraph_index: int
    sups_text: list[str]


class APISearchResult(NamedTuple):
    """NamedTuple of WikiApi pre result - titles and keys of Wikipedia pages"""

    titles: list[str]
    keys: list[str]
