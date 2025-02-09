from typing import Union, Optional, Any, Coroutine, Callable

from sqlalchemy.engine.url import URL
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
    AsyncConnection,
    AsyncSession,
    AsyncEngine
)

from .tables import base_table_class
from .orm import WikiDBOrm

from ..loggers import wiki_logger


__all__ = (
    "WikiDB",
)


class WikiDB:
    """
    Engine for work with database. Need for connect, create, drop database and create ORM session.

    Note:
        You can indicate :code:`db_url` or :code:`wiki_db` for connect to database.

    Args:
        url: SQLAlchemy URL for connect to database.
        engine: Your :code:`AsyncEngine` for connect to database.
        drop: Before creating all tables (if exists) drop database.
        echo: Logging of SQLAlchemy database engine.
        kwargs: Advanced params for :code:`AsyncEngine`.

    Raises:
        ValueError: if url and engine not be indicated.
    """

    # Magic methods
    def __init__(
            self,
            *,
            url: Optional[Union[str, URL]] = None,
            engine: Optional[AsyncEngine] = None,
            drop: bool = False,
            echo: bool = False,
            **kwargs: Any
    ) -> None:

        if url is None and engine is None:
            raise ValueError("At least one of the parameters should be indicated: url or engine")

        self.__url = url
        self.__engine = create_async_engine(self.__url, echo=echo, **kwargs) if engine is None else engine
        self.__session_maker = async_sessionmaker(
            bind=self.__engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        # WikiDB params
        self.__db_configured = False
        self.__db_drop_param = drop

    # Getters
    @property
    def url(self) -> Union[str, URL]:
        return self.__url

    @property
    def engine(self) -> AsyncEngine:
        return self.__engine

    @property
    def session_maker(self) -> async_sessionmaker:
        return self.__session_maker

    @property
    def session(self) -> AsyncSession:
        """
        Returns:
            Class of async ORM session for connect database. Is not open ORM session.
        """

        return self.__session_maker()

    # Main methods
    def orm_decorator(self):
        """
        Decorator for connect to database.
        Forward in function open :code:`WikiDBOrm` session for work with ORM.

        e.g.::

            from asyncwiki.database import WikiDB

            wiki_db = WikiDB(url="sqlalchemy_url")

            @wiki_db.orm_decorator()  # must be called without args
            async def search_page(arg_1, arg_2, orm: WikiDBOrm):
                # orm arg must be kwargs

                page = await orm.select_page_by_query("Some query", lang="en")

        Returns:
            Decorator function
        """

        def decor(func) -> Callable[[tuple[Any, ...], dict[str, Any]], Coroutine[Any, Any, Any]]:
            async def wrapper(*args, **kwargs) -> Coroutine[Any, Any, Any]:
                if self.__db_configured is False:
                    await self.setup_db()

                async with WikiDBOrm(self.session) as orm:
                    kwargs["orm"] = orm
                    return await func(*args, **kwargs)

            return wrapper
        return decor

    async def setup_db(self) -> None:
        """
        Make first database setup: if you need drop database and create all tables if exists.

        Note:
            This function call automatically then open first connection to the database.
            But if you need you can call it yourself.

        Returns:
            None
        """

        if self.__db_configured:
            wiki_logger.db.warning("Database already configured")
            return

        drop_param = self.__db_drop_param

        if drop_param:
            await self.drop_db()

        await self.create_db()
        self.__db_configured = True

        wiki_logger.db.info("Database successful configured")

    async def create_db(self) -> None:
        """Create all tables in database"""

        async with self.__engine.begin() as conn:  # type: AsyncConnection
            await conn.run_sync(base_table_class.metadata.create_all)
            wiki_logger.db.info("All tables created")

    async def drop_db(self) -> None:
        """Drop all database content"""

        async with self.__engine.begin() as conn:  # type: AsyncConnection
            await conn.run_sync(base_table_class.metadata.drop_all)
            wiki_logger.db.info("Database dropped success")
