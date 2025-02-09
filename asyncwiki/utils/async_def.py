from typing import Any

from aiohttp import ClientSession, ClientResponse

from ..exc import WikiResNotReceived

from logging import Logger


__all__ = (
    "get_response",
)


async def get_response(
        session: ClientSession,
        logger: Logger,
        url: str,
        **kwargs: Any
) -> ClientResponse:
    """
    Receive response by URL.

    Args:
        session: Session of :code:`ClientSession` for getting response.
        logger: Logger for raise error.
        url: URL for getting response.
        kwargs: kwargs for :code:`ClientSession.get()`

    Returns:
        :code:`ClientResponse`

    Raises:
        WikiResNotReceived: If response was not received.
    """

    response = await session.get(url, **kwargs)

    if response.status != 200:
        logger.error("Failed get response")
        raise WikiResNotReceived

    return response