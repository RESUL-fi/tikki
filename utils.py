from werkzeug.datastructures import MultiDict
import datetime
from exceptions import (
    AppException,
    DbApiException,
    FlaskRequestException,
    Flask400Exception,
    Flask500Exception,
    NoRecordsException,
)
import flask
from typing import Dict, List, Union, Optional, Any, Type, Tuple
import traceback
from uuid import UUID, uuid4
import dateutil.parser
import os
from db import tables


def _add_config_from_env(app: Any, config_key: str, env_variable: str,
                         missing_list: List[str]) -> bool:
    """
    Function for adding configuration variables to a Flask app from environment
    variables.

    :param app: Flask app object
    :param config_key: the name of the config key in the app: app.config[config_key]
    :param env_variable: the name of the environment variable in which the value is stored
    :param missing_list: a list of strings to which missing environment variables
    are added
    :return: True if successful, False if environment variable was undefined
    """
    val = os.environ.get(env_variable, None)
    if val is not None:
        app.config[config_key] = val
        return True
    else:
        missing_list.append(env_variable)
        return False

def get_sqla_uri() -> str:
    """
    Retrieve SQL Alchemy URI from environment variables
    :return: SQL Alchemy URI
    """
    uri = os.environ.get('TIKKI_SQLA_DB_URI', None)
    if uri is not None:
        return uri
    raise RuntimeError('SQLA_DB_URI environment variable undefined')


def init_app_config(app: Any):
    """
    Initializes the Flask app with all necessary config parameters.
    """
    missing_env_vars = []  # type: List[str]
    _add_config_from_env(app, 'JWT_SECRET_KEY', 'TIKKI_JWT_SECRET', missing_env_vars)
    _add_config_from_env(app, 'SQLA_DB_URI', 'TIKKI_SQLA_DB_URI', missing_env_vars)

    if len(missing_env_vars) > 0:
        raise RuntimeError('Following environment variables undefined: ' +
                           ', '.join(missing_env_vars))


def create_jwt_identity(user: tables.Base) -> Dict[str, Any]:
    return {'sub': str(user.id), 'rol': user.type_id}


def parse_value(value: str, default_type: Type[Any]):
    if default_type is datetime.datetime:
        return dateutil.parser.parse(value)
    return value if isinstance(value, default_type) else None


def get_anydict_value(source_dict: Dict[str, Any], key: str, default_value: Any,
                      default_type: Type[Any]):
    if isinstance(source_dict, MultiDict):
        value = source_dict.get(key, default_value, default_type)
        return parse_value(value, default_type)
    elif isinstance(source_dict, dict):
        value = source_dict.get(key, default_value)
        return parse_value(value, default_type)
    else:
        raise AppException('Unsupported source_dict type: ' + type(source_dict).__name__)


def get_args(received: Dict[str, Any], required: Optional[Dict[str, Type[Any]]] = None,
             defaultable: Optional[Dict[str, Any]] = None,
             optional: Optional[Dict[str, Type[Any]]] = None,
             constant: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Retrieve parameters from a dict or MultiDict

    :param received: The dict or MultiDict that contains the source data
    :param required: The name and type of required key/value
    :param defaultable: The name and value of keys that will default to value if missing
    from received
    :param optional: The name and type of values that will be extracted from received
    if present
    :param constant: The name and value that will added to return dict. If key is present
    in received, the value will be overwritten by the value in constant
    :return:
    """
    # Initialize local variables

    if required is None and defaultable is None and optional is None and constant is None:
        raise AppException('One of the following is required: '
                           'required, defaultable, optional or constant.')

    required = required if required else {}
    defaultable = defaultable if defaultable else {}
    optional = optional if optional else {}
    constant = constant if constant else {}
    missing: List[str] = []
    ret_dict: Dict[str, Any] = {}

    # First loop through required args and add missing keys to error list

    for key, default_type in required.items():
        val = get_anydict_value(received, key, None, default_type)
        if val is None:
            missing.append(key)
        ret_dict[key] = val

    # Next loop through defaultable args, falling back to default values

    for key, default_value in defaultable.items():
        default_type = type(default_value)
        val = get_anydict_value(received, key, default_value, default_type)
        ret_dict[key] = val

    # Next loop through optional args, omitting them if missing

    for key, default_type in optional.items():
        val = get_anydict_value(received, key, None, default_type)
        if val is not None:
            ret_dict[key] = val

    # Finally copy constants

    ret_dict.update(constant)

    # Raise error if

    if len(missing) > 0:
        msg = "Missing following arguments:"
        for arg in missing:
            msg += ' ' + arg
        raise AppException(msg)

    return ret_dict


def flask_validate_request_is_json(request) -> None:
    """
    Make sure that request contains json object; if not, raise exception
    :param request: Flask http request
    :return:
    """
    if not request.is_json:
        raise Flask400Exception('Request body is not JSON.')


def flask_return_exception(e, return_type: int=500) -> Tuple[Dict[str, Any], int]:
    return flask.jsonify({'http_status_code': return_type, 'error': str(e)}), return_type


def flask_return_success(result, return_type: int=200):
    return flask.jsonify({'result': result}), return_type


def flask_handle_exception(exception: Union[FlaskRequestException, DbApiException]) \
        -> Tuple[Dict[str, Any], int]:
    """
    Convert exception into tuple that can be returned to the user by Flask

    :param exception:
    :return: A tuple with jsonified error message and a http response type
    """
    if isinstance(exception, Flask400Exception):
        return flask_return_exception(exception, 400)
    elif isinstance(exception, Flask500Exception):
        return flask_return_exception(exception, 500)
    elif isinstance(exception, NoRecordsException):
        return flask_return_exception(exception, 400)
    else:
        return flask_return_exception(traceback.format_exc(), 500)


def generate_uuid(count: int=1) -> Optional[Union[UUID, List[UUID]]]:
    """
    Function for generating UUIDs

    :param count: How many UUIDs to generate
    :return: If count == 1, returns just one UUID. For more than one, returns a list
    of UUIDs. For other values of one returns None
    """
    if count == 1:
        return uuid4()
    elif count > 1:
        return [uuid4() for _ in range(count)]
    return None
