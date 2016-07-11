class SocketAPIError(Exception):
    pass


class InvalidRequestError(SocketAPIError):
    pass


class InvalidURIError(InvalidRequestError):
    pass


class NotFoundError(InvalidRequestError):
    pass
