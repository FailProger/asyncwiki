from time import perf_counter as _perf_counter
from logging import Logger, getLogger, DEBUG, INFO, WARNING, ERROR, CRITICAL


__all__ = (
    "FULL",
    "MAIN",
    "CHILDREN",
    "SCRAPER",
    "FAST_SCRAPER",
    "API_SCRAPER",
    "DB",
    "wiki_logger",
    "LogTimer",
    "WikiLogger"
)


# WikiLogger parameters
FULL = 100
MAIN = 110
CHILDREN = 120
SCRAPER = 130
FAST_SCRAPER = 140
API_SCRAPER = 150
DB = 160


class LogTimer:
    """Class for measure time of functions work"""

    # Sign start with time will be round.
    _ndigits: int = 3

    def __init__(self) -> None:
        self.__start_time = round(_perf_counter(), self._ndigits)
        self.__result = None

    @property
    def start_time(self) -> float:
        return self.__start_time

    @property
    def result(self) -> float:
        if self.__result:
            return self.__result

        else:
            raise RuntimeError("Timer not stopped")

    def stop(self) -> float:
        """
        Stop timer amd return result.

        Returns:
            Time after creating object.
        """

        self.__result = round(_perf_counter() - self.__start_time, self._ndigits)
        return self.__result


class WikiLogger:
    """Class for WikiSearcher logging"""

    # Loggers names
    __wiki_name = "wiki"
    __db_name = "db"
    __scraper_name = "scraper"
    __fast_scraper_name = "fast"
    __api_scraper_name = "api"

    __is_one = None

    def __new__(cls, *args, **kwargs):
        """Blocking to create new items"""

        if cls.__is_one is None:
            cls.__is_one = super().__new__(cls)

        return cls.__is_one

    def __init__(self) -> None:
        # Main logger
        self.__wiki = getLogger(self.__wiki_name)

        # Children loggers
        self.__db = self.wiki.getChild(self.__db_name)  # DB logger

        self.__scraper = self.wiki.getChild(self.__scraper_name)  # Scraper logger
        self.__fast_scraper = self.scraper.getChild(self.__fast_scraper_name)
        self.__api_scraper = self.scraper.getChild(self.__api_scraper_name)

        self.setup(CRITICAL)  # Disable all loggers

    @property
    def wiki(self) -> Logger:
        return self.__wiki

    @property
    def scraper(self) -> Logger:
        return self.__scraper

    @property
    def fast_scraper(self) -> Logger:
        return self.__fast_scraper

    @property
    def api_scraper(self) -> Logger:
        return self.__api_scraper

    @property
    def db(self) -> Logger:
        return self.__db

    # Function of setup loggers
    def setup(self, *params: int) -> None:
        """
        Enable loggers of WikiSearcher

        Note:
            :code:`FULL` - Enable all loggers\n
            :code:`MIAN` - Enable only main logger\n
            :code:`CHILDREN` - Enable main logger and some his children\n
            :code:`SCRAPER` - Enable main and scraper loggers\n
            :code:`FAST_SCRAPER` - Enable main, scraper and async scraper loggers\n
            :code:`API_SCRAPER` - Enable main. scraper and API searcher loggers\n
            :code:`DB` - Enable main and database searcher loggers\n
            :code:`DEBUG`, :code:`INFO`, :code:`WARNING`, :code:`ERROR`, :code:`CRITICAL` - Change logging level.

        Args:
            params: Can pass multiple parameters.
        """

        for param in params:
            if param == FULL:
                self.wiki.setLevel(INFO)
                self.db.setLevel(INFO)
                self.scraper.setLevel(INFO)
                self.fast_scraper.setLevel(INFO)
                self.api_scraper.setLevel(INFO)

            elif param == MAIN:
                self.wiki.setLevel(INFO)

            elif param == CHILDREN:
                self.wiki.setLevel(INFO)
                self.db.setLevel(INFO)
                self.scraper.setLevel(INFO)

            elif param == SCRAPER:
                self.wiki.setLevel(INFO)
                self.scraper.setLevel(INFO)
                self.fast_scraper.setLevel(CRITICAL)
                self.api_scraper.setLevel(CRITICAL)

            elif param == FAST_SCRAPER:
                self.wiki.setLevel(INFO)
                self.scraper.setLevel(INFO)
                self.fast_scraper.setLevel(INFO)

            elif param == API_SCRAPER:
                self.wiki.setLevel(INFO)
                self.scraper.setLevel(INFO)
                self.api_scraper.setLevel(INFO)

            elif param == DB:
                self.wiki.setLevel(INFO)
                self.db.setLevel(INFO)

            elif param == DEBUG or param == INFO or param == WARNING or param == ERROR or param == CRITICAL:
                self.wiki.setLevel(param)
                self.db.setLevel(param)
                self.scraper.setLevel(param)
                self.fast_scraper.setLevel(param)
                self.api_scraper.setLevel(param)

    @classmethod
    def change_ndigits(cls, ndigits: int) -> None:
        """
        Changes the number of decimal places in the logs time.

        Args:
            ndigits: Sign start with time will be round.

        Returns:
            None
        """

        LogTimer._ndigits = ndigits


# Main WikiSearcher logger
wiki_logger = WikiLogger()
