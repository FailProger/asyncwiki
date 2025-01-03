
__all__ = (
    "WPSearchModes",
    "WPSearchPriority",
    "WPQueryTreatments",
    "WPDBSearch",
    "WPDBSearchByURL",
    "WikiSearchParams"
)


class WPSearchModes:
    """
    Change how fast WikiSearcher will search articles. The slower, the more and correct information will be.

    Note:
        WP - Wiki Params
    """

    default = 1
    fast = 2


class WPSearchPriority:
    """
    WikiSearcher will be pay more attention on selected item.

    Note:
        WP - Wiki Params
    """

    title = 1
    content = 2


class WPQueryTreatments:
    """
    Change how WikiSearcher will clear and adjust search query.

    Note:
        WP - Wiki Params
    """

    default = 1
    without = 2


class WPDBSearch:
    """
    Use search in database (if it connected) or no.

    Note:
        WP - Wiki Params
    """

    no = 1
    yes = 2


class WPDBSearchByURL:
    """
    Search page in database by url or no.

    Note:
        WP - Wiki Params
    """

    no = 1
    yes = 2


class WikiSearchParams:
    """
    Search params. Apply to a one search query and not to the WikiSearcher in general.

    Note:
        WP - Wiki Params

    Args:
        mode: Change how fast WikiSearcher will search articles. The slower,
                 the more and correct information will be.
        priority: Searcher will be pay more attention on selected item.
        query_treatment: Change how WikiSearcher will clear and adjust search query.
        db_search: Use search in database (if it connected) or no.
        db_search_by_url: Search page in database by url or no.
        number_of_results: Defines quantity of results (if using :code:`default mode`
                              also will be added 5 advanced results).
    """

    def __init__(
        self,
        mode: int = WPSearchModes.default,
        priority: int = WPSearchPriority.content,
        query_treatment: int = WPQueryTreatments.without,
        db_search: int = WPDBSearch.yes,
        db_search_by_url: int = WPDBSearchByURL.no,
        number_of_results: int = 1
    ) -> None:

        self.mode = mode
        self.priority = priority
        self.query_treatment = query_treatment
        self.db_search = db_search
        self.db_search_by_url = db_search_by_url
        self.number_of_results = number_of_results
