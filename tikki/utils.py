"""
Common utilities that are used throughout the application. Move anything that is used
more than once that isn't specific to any certain functionality here.
"""

import datetime
import json
import logging
import os
import traceback
import urllib.request
from typing import Any, Dict, List, Optional, Tuple, Type, Union
from uuid import UUID, uuid4

import dateutil.parser
import flask
import jwt
from flask import has_request_context, request
from flask_jwt_simple import get_jwt_identity
from jwt.algorithms import RSAAlgorithm  # type: ignore
from werkzeug.datastructures import MultiDict

from tikki.db import tables
from tikki.exceptions import (AppException, DbApiException, Flask400Exception,
                              Flask500Exception, FlaskRequestException,
                              NoRecordsException)

APP_NAME = 'tikki'


def _add_config_from_env(app: Any, config_key: str, env_variable: str,
                         missing_list: Optional[List[str]] = None,
                         default_value: Any = None) -> bool:
    """
    Function for adding configuration variables to a Flask app from environment
    variables.

    :param app: Flask app object
    :param config_key: the name of the config key in the app: app.config[config_key]
    :param env_variable: the name of the environment variable in which the value is stored
    :param missing_list: a list of strings to which missing environment variables
    are added. Can be omitted.
    :param default_value: if value is missing, set config value to this.
    :return: True if successful, False if environment variable was undefined
    """
    val = os.environ.get(env_variable, None)
    if val is not None:
        app.config[config_key] = val
        return True
    elif default_value:
        app.config[config_key] = default_value
        return True

    if missing_list is not None:
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


def get_auth0_payload(app: Any, request):
    public_key = app.config['AUTH0_PUBLIC_KEY']
    audience = app.config['AUTH0_AUDIENCE']
    token = get_args(request.json, required={'token': str})['token'].encode()
    payload = jwt.decode(token, public_key, algorithms=['RS256'], audience=audience)
    return payload


def init_app(app: Any):
    """
    Initializes the Flask app with all necessary config parameters.
    """

    class RequestFormatter(logging.Formatter):
        def format(self, record):
            if has_request_context():
                record.url = request.url
                record.remote_addr = request.remote_addr
                jwt_identity = get_jwt_identity()
                record.jwt_identity = '' if jwt_identity is None else jwt_identity
            else:
                record.url, record.remote_addr, record.jwt_identity = '', '', ''
            return super().format(record)

    # Setup logging
    logger = logging.getLogger(APP_NAME)
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    log_formatter = RequestFormatter('[%(asctime)s] - %(name)s - %(levelname)s - %(remote_addr)s - %(url)s - %(jwt_identity)s - %(message)s')  # noqa
    ch.setFormatter(log_formatter)
    logger.addHandler(ch)

    # Disable deprecation warning for flask-sqlalchemy
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    missing_vars: List[str] = []
    _add_config_from_env(app, 'JWT_SECRET_KEY', 'TIKKI_JWT_SECRET', missing_vars)
    _add_config_from_env(app, 'SQLALCHEMY_DATABASE_URI', 'TIKKI_SQLA_DB_URI', missing_vars)  # noqa
    _add_config_from_env(app, 'AUTH0_AUDIENCE', 'TIKKI_AUTH0_AUDIENCE', missing_vars)

    url = 'https://tikkifi.eu.auth0.com/.well-known/jwks.json'
    contents = urllib.request.urlopen(url).read()
    jwks = json.loads(contents)
    app.config['AUTH0_JWKS'] = jwks
    key = json.dumps(json.loads(contents)['keys'][0])
    app.config['AUTH0_PUBLIC_KEY'] = RSAAlgorithm.from_jwk(key)

    if missing_vars:
        raise RuntimeError('Following environment variables undefined: '
                           + ', '.join(missing_vars))


def create_jwt_identity(user: tables.Base) -> Dict[str, Any]:
    identity: Dict[str, Any] = {'sub': str(user.id), 'rol': user.type_id}
    now = datetime.datetime.utcnow()
    identity["iat"] = int(now.timestamp())
    identity["exp"] = int((now + datetime.timedelta(days=1)).timestamp())
    return identity


def parse_value(value: Any, default_type: Type[Any]) -> Any:
    # datetimes will be sent in string format, therefore need
    # to be parsed first
    if default_type is datetime.datetime and isinstance(value, str):
        return dateutil.parser.parse(value, ignoretz=True)
    return value if isinstance(value, default_type) else None


def get_anydict_value(source_dict: Dict[str, Any], key: str, default_value: Any,
                      default_type: Type[Any]):
    if isinstance(source_dict, MultiDict):
        value = source_dict.get(key, default_value, default_type)
        return parse_value(value, default_type)
    elif isinstance(source_dict, dict):
        value = source_dict.get(key, default_value)
        return parse_value(value, default_type)

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


def flask_validate_request_is_json(req) -> None:
    """
    Make sure that request contains json object; if not, raise exception
    :param req: Flask http request
    :return:
    """
    if not req.is_json:
        raise Flask400Exception('Request body is not JSON.')


def flask_return_exception(e, return_type: int = 500) -> Tuple[Dict[str, Any], int]:
    return flask.jsonify({'http_status_code': return_type, 'error': str(e)}), return_type


def flask_return_success(result, return_type: int = 200):
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
    logger = logging.getLogger(APP_NAME)
    logger.error(traceback.format_exc())
    return flask_return_exception(traceback.format_exc(), 500)


def generate_uuid(count: int = 1) -> Optional[Union[UUID, List[UUID]]]:
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
