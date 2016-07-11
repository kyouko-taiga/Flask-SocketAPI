class SocketAPIError(Exception):
    pass


class InvalidRouteError(SocketAPIError):
    pass


class InvalidRequestError(SocketAPIError):
    pass


class NotFoundError(InvalidRequestError):
    pass
