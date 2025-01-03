

class WikiExc(RuntimeError):
    """Main exception to WikiSearcher"""
    pass


########################################################################################################################


class WikiWebExc(WikiExc):
    """Main exception to WikiWebSearcher"""
    pass


class WikiScraperExc(WikiWebExc):
    """Class of scraper exceptions"""
    pass


########################################################################################################################


class _WikiUseAPIScrapperExc(WikiScraperExc):
    """Raise when need use API scraper"""
    pass


########################################################################################################################


class WikiRequestExc(WikiScraperExc):
    """Class of HTTP request exceptions"""
    pass


class WikiNoneSearchResults(WikiRequestExc):
    """Raise if API searcher not received any results"""
    pass


class WikiResNotReceived(WikiRequestExc):
    """Raise if one of response is not received"""
    pass


########################################################################################################################


class WikiParsingExc(WikiScraperExc):
    """Class of parsing exceptions"""
    pass


class WikiContentNotFound(WikiParsingExc):
    """Raise if content not found on page"""
    pass


class WikiParagraphNotFound(WikiParsingExc):
    """Raise if paragraph not found on page"""
    pass


class WikiSummaryNotFound(WikiParsingExc):
    """Raise if summary not found on page"""
    pass


class WikiShortSummary(WikiParsingExc):
    """Raise if summary len short then 10 signs"""
    pass


########################################################################################################################


class WikiDBExc(WikiExc):
    """Main exception to WikiDBSearcher"""
    pass


class _WikiNotUseDBSearch(WikiDBExc):
    """Raise if search in database not use"""
    pass


class WikiDBPageNotFound(WikiDBExc):
    """Raise if page not found in database"""
    pass
