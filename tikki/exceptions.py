"""
Collection of exceptions used by the application.
"""


class AppException(Exception):
    """
    Base class for exceptions related to the App.
    """
    pass


class FlaskRequestException(Exception):
    """
    Base class for exceptions related to Flask requests.
    """
    pass


class Flask400Exception(FlaskRequestException):
    """
    Bad Request Error. Indicates that the server was unable to understand the
    intent or contents of the request.
    """
    pass


class Flask500Exception(FlaskRequestException):
    """
    Internal Server Error. Indicates that the server encountered an unexpected internal
    condition that prevented it from fulfilling the request.
    """
    pass


class DbApiException(Exception):
    """
    Base class for exceptions related to Db Api calls.
    """


class NoRecordsException(DbApiException):
    """
    Exception to indicate that no rows were found. Should only be used if rows
    are expected.
    """
    pass


class TooManyRecordsException(DbApiException):
    """
    Exception to indicate that too many rows were found. Usually used to ensure that
    an update query only updates a single row.
    """
    pass
