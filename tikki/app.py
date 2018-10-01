# -*- coding: utf-8 -*-
"""Tikki backend

This module serves the RESTful interface required by the Tikki application.
"""
import argparse
import datetime
from tikki.db.tables import User, Record, RecordType, Event, UserEventLink
from tikki import db as db_api
from enum import IntEnum
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_simple import (
    create_jwt,
    get_jwt_identity,
    jwt_optional,
    jwt_required,
    JWTManager,
)
import utils
from werkzeug.security import generate_password_hash, check_password_hash


class RecordCategoryTypeEnum(IntEnum):
    UNKNOWN = 0
    TEST = 1
    QUESTIONNAIRE = 2
    ACTIVITY = 3


class RecordTypeEnum(IntEnum):
    COOPERS_TEST = 1
    PUSH_UP_60_TEST = 2
    SIT_UPS = 3
    STANDING_JUMP = 4
    PULL_UPS = 5
    ACTIVITY_STATUS = 6
    EDUCATION_DURATION = 7
    CURRENT_FITNESS = 8
    WORKING_ABILITY = 9
    HIGH_BLOOD_PRESSURE = 10
    DIABETES = 11
    ALCOHOL = 12
    SMOKING = 13
    FAMILY_STATUS = 14
    DEPRESSION = 15
    SICK_LEAVE = 16


app = Flask(__name__)
utils.init_app_config(app)
db_api.init(app)
jwt = JWTManager(app)
CORS(app)


def get_obj_type(path):
    if path == '/user':
        return User
    elif path == '/record':
        return Record
    elif path == '/event':
        return Event
    elif path == 'user-event-link':
        return UserEventLink


@jwt.jwt_data_loader
def add_claims_to_access_token(identity):
    now = datetime.datetime.utcnow()
    sub, rol = identity['sub'], identity['rol']
    return {
        'exp': now + app.config['JWT_EXPIRES'],
        'iat': now,
        'nbf': now,
        'sub': sub,
        'rol': rol
    }


@app.route('/login', methods=['POST'])
def login():
    try:
        utils.flask_validate_request_is_json(request)
        username_filter = utils.get_args(request.json, required={'username': str})
        password_filter = utils.get_args(request.json, required={'password': str})
        user = db_api.get_row(User, username_filter)
        if user is not None and check_password_hash(user.password,
                                                    password_filter['password']):
            identity = utils.create_jwt_identity(user)
            return utils.flask_return_success({'jwt': create_jwt(identity),
                                              'user': user.jsondict})
        else:
            return utils.flask_return_exception('Incorrect username or password', 400)
    except Exception as e:
        return utils.flask_handle_exception(e)


@app.route('/user', methods=['DELETE'], strict_slashes=False)
@app.route('/record', methods=['DELETE'], strict_slashes=False)
@app.route('/event', methods=['DELETE'], strict_slashes=False)
@app.route('/user-event-link', methods=['DELETE'], strict_slashes=False)
@jwt_required
def delete_record():
    try:
        # Check object type based on endpoint and define filters accordingly.

        obj_type = get_obj_type(request.path)
        required_args = {}
        if obj_type is UserEventLink:
            required_args['event_id'] = str
        else:
            required_args['id'] = str

        filters = utils.get_args(received=request.args,
                                 required=required_args,
                                 )
        filters['user_id'] = get_jwt_identity()
        db_api.delete_row(obj_type, filters)
        return utils.flask_return_success('OK')
    except Exception as e:
        return utils.flask_handle_exception(e)


@app.route('/uuid', methods=['GET'], strict_slashes=False)
def get_uuid():
    try:
        args = utils.get_args(received=request.args,
                              defaultable={'count': 1},
                              )
        count = args['count']
        if 0 < count <= 1024:
            return utils.flask_return_success(utils.generate_uuid(count))
        else:
            return utils.flask_return_exception('The count parameter cannot be below 1 '
                                                'or greater than 1024.', 400)
    except Exception as e:
        return utils.flask_handle_exception(e)


@app.route('/whoami', methods=['GET'], strict_slashes=False)
@jwt_optional
def get_whoami():
    try:

        user = get_jwt_identity()
        if user is None:
            return utils.flask_return_success('Nobody')
        else:
            return utils.flask_return_success(user)
    except Exception as e:
        return utils.flask_handle_exception(e)


@app.route('/schema', methods=['GET'], strict_slashes=False)
@jwt_optional
def get_schema():
    try:
        jwt_id = get_jwt_identity()
        type_dict = dict()
        if jwt_id is not None:
            filters = {'user_id': str(jwt_id)}
            records = db_api.get_rows(Record, filters)

            # sort records based on user_id and creation date to pick most recent
            # result per user
            # TODO: sort in db.get_rows

            records.sort(key=lambda x: (x.type_id, x.created_at), reverse=True)
            lag_type_id = None
            for record in records:
                if lag_type_id != record.type_id:
                    lag_type_id = record.type_id
                    type_dict[record.type_id] = record

        rows = db_api.get_rows(RecordType, {})
        result_list = list()
        for row in rows:
            result = row.jsondict
            result['ask'] = 1 if jwt_id is not None and row.category_id == 2 and \
                row.category_id not in type_dict else 0
            result_list.append(result)
        return utils.flask_return_success(result_list)
    except Exception as e:
        return utils.flask_handle_exception(e)


@app.route('/user', methods=['GET'], strict_slashes=False)
@jwt_required
def get_user():
    filters = utils.get_args(received=request.args,
                             optional={'id': str, 'username': str},
                             )
    try:
        users = db_api.get_rows(User, filters)
        return utils.flask_return_success([i.jsondict for i in users])
    except Exception as e:
        return utils.flask_handle_exception(e)


@app.route('/user', methods=['POST'], strict_slashes=False)
def post_user():
    try:
        utils.flask_validate_request_is_json(request)
        now = datetime.datetime.now()
        uuid = str(utils.generate_uuid())
        in_user = utils.get_args(received=request.json,
                                 required={'username': str, 'password': str},
                                 defaultable={'id': uuid, 'created_at': now,
                                              'updated_at': now, 'payload': {}},
                                 )
        in_user['password'] = generate_password_hash(in_user['password'])
        user = db_api.add_row(User, in_user)
        identity = utils.create_jwt_identity(user)
        return utils.flask_return_success({'jwt': create_jwt(identity),
                                          'user': user.jsondict})
    except Exception as e:
        return utils.flask_handle_exception(e)


@app.route('/user', methods=['PUT'], strict_slashes=False)
@jwt_required
def put_user():
    try:
        utils.flask_validate_request_is_json(request)
        now = datetime.datetime.now()
        in_user = utils.get_args(received=request.json,
                                 optional={'username': str, 'password': str},
                                 defaultable={'created_at': now, 'updated_at': now,
                                              'payload': {}})
        in_user['password'] = generate_password_hash(in_user['password'])
        filters = {'id': get_jwt_identity()}
        user = db_api.update_row(User, filters, in_user)
        return utils.flask_return_success(user.jsondict)
    except Exception as e:
        return utils.flask_handle_exception(e)


@app.route('/user', methods=['PATCH'], strict_slashes=False)
@jwt_required
def patch_user():
    try:
        utils.flask_validate_request_is_json(request)
        now = datetime.datetime.now()
        in_user = utils.get_args(received=request.json,
                                 required={'id': str},
                                 defaultable={'updated_at': now},
                                 optional={'created_at': datetime.datetime,
                                           'username': str, 'password': str,
                                           'payload': dict})
        if 'password' in in_user:
            in_user['password'] = generate_password_hash(in_user['password'])
        filters = {'id': in_user.pop('id', None)}
        user = db_api.update_row(User, filters, in_user)
        return utils.flask_return_success(user.jsondict)
    except Exception as e:
        return utils.flask_handle_exception(e)


@app.route('/test/cooperstest/compstat', methods=['GET'], strict_slashes=False)
@jwt_required
def get_cooperstest_compstat():
    try:
        user_id = get_jwt_identity()
        filters = {'type_id': int(RecordTypeEnum.COOPERS_TEST)}
        records = db_api.get_rows(Record, filters)

        # sort records based on user_id and creation date to pick most recent
        # result per user
        # TODO: do sorting in db.get_rows
        records.sort(key=lambda x: (x.user_id, x.created_at), reverse=True)
        filtered_records = list()
        lag_user_id = None
        user_record = None
        for record in records:
            if lag_user_id != record.user_id:
                lag_user_id = record.user_id
                filtered_records.append(record)
                if user_id == str(record.user_id):
                    user_record = record

        # sort filtered records and get index for quantile calculation
        try:
            index = sorted(filtered_records,
                           key=lambda x: x.payload['distance']).index(user_record)
        except ValueError:
            index = None

        if index is None or len(filtered_records) == 0:
            quantile = 0
        else:
            quantile = (index + 1) / len(filtered_records)
        return utils.flask_return_success({'quantile': quantile})

    except Exception as e:
        return utils.flask_return_exception(e, 500)


@app.route('/test/pushup60test/compstat', methods=['GET'], strict_slashes=False)
@jwt_required
def get_pushup60test_compstat():
    try:
        user_id = get_jwt_identity()
        if user_id is None:
            return jsonify({'message': 'Undefined user id.'}), 400
        filters = {'type_id': int(RecordTypeEnum.PUSH_UP_60_TEST)}
        records = db_api.get_rows(Record, filters)

        # sort records based on user_id and creation date to pick most recent
        # result per user
        # TODO: sort in db.get_rows

        records.sort(key=lambda x: (x.user_id, x.created_at), reverse=True)
        filtered_records = list()
        lag_user_id = None
        user_record = None
        for record in records:
            if lag_user_id != record.user_id:
                lag_user_id = record.user_id
                filtered_records.append(record)
                if user_id == str(record.user_id):
                    user_record = record

        # sort filtered records and get index for quantile calculation
        filtered_records.sort(key=lambda x: x.payload['pushups'])
        try:
            index = filtered_records.index(user_record)
        except ValueError:
            index = None

        if index is None or len(filtered_records) == 0:
            quantile = 0
        else:
            quantile = (index + 1) / len(filtered_records)
        return jsonify({'result': {'quantile': quantile}}), 200

    except Exception as e:
        return utils.flask_return_exception(e, 500)


@app.route('/record', methods=['GET'], strict_slashes=False)
@jwt_required
def get_record():
    filters = utils.get_args(received=request.args,
                             optional={'id': str, 'user_id': str, 'event_id': str},
                             )
    try:
        rows = db_api.get_rows(Record, filters)
        return utils.flask_return_success([row.jsondict for row in rows])
    except Exception as e:
        return utils.flask_handle_exception(e)


@app.route('/record', methods=['POST'], strict_slashes=False)
@jwt_required
def post_record():
    try:
        utils.flask_validate_request_is_json(request)
        now = datetime.datetime.now()
        uuid = str(utils.generate_uuid())
        row = utils.get_args(received=request.json,
                             optional={'event_id': str},
                             defaultable={'id': uuid, 'created_at': now,
                                          'updated_at': now, 'payload': {},
                                          'type_id': 0,
                                          'user_id': get_jwt_identity()},
                             )

        # Add created_user which defaults to the user_id, merging it with the
        # main row object.
        user_id = row['user_id']
        created_user = utils.get_args(received=request.json,
                                      defaultable={'created_user_id': user_id},
                                      )
        row.update(created_user)

        # And finally add details of who validated the record and when if provided.
        validated = utils.get_args(received=request.json,
                                   defaultable={'validated_at': now},
                                   optional={'validated_user_id': str},
                                   )
        if 'validated_user_id' in validated:
            row.update(validated)

        record = db_api.add_row(Record, row)
        return utils.flask_return_success(record.jsondict)
    except Exception as e:
        return utils.flask_handle_exception(e)


@app.route('/record', methods=['PATCH'], strict_slashes=False)
@jwt_required
def patch_record():
    try:
        utils.flask_validate_request_is_json(request)
        now = datetime.datetime.now()
        row = utils.get_args(received=request.json,
                             required={'id': str},
                             defaultable={'updated_at': now},
                             optional={'created_at': datetime.datetime,
                                       'payload': dict, 'type_id': int,
                                       'event_id': str},
                             )

        # Add created_user which defaults to the user_id, merging it with the
        # main row object.
        user = get_jwt_identity()

        created_user = utils.get_args(received=request.json,
                                      defaultable={'created_user': user},
                                      )
        row.update(created_user)

        # And finally add details of who validated the record and when if provided.
        validated = utils.get_args(received=request.json,
                                   defaultable={'validated_at': now},
                                   optional={'validated_user_id': str},
                                   )
        if validated['validated_user_id'] is not None:
            row.update(validated)

        filters = {'id': row.pop('id', None)}
        record = db_api.update_row(Record, filters, row)
        return utils.flask_return_success(record.jsondict)
    except Exception as e:
        return utils.flask_handle_exception(e)


@app.route('/record', methods=['PUT'], strict_slashes=False)
@jwt_required
def put_record():
    try:
        utils.flask_validate_request_is_json(request)
        now = datetime.datetime.now()
        uuid = str(utils.generate_uuid())
        user = get_jwt_identity()
        row = utils.get_args(received=request.json,
                             defaultable={'id': uuid, 'created_at': now,
                                          'updated_at': now, 'payload': {},
                                          'type_id': 0,
                                          'user_id': user},
                             optional={'event_id': str},
                             )
        filters = {'id': row.pop('id', None)}

        # Add created_user which defaults to the user_id, merging it with the
        # main row object.
        created_user = utils.get_args(received=request.json,
                                      defaultable={'created_user': user},
                                      )
        row.update(created_user)

        # And finally add details of who validated the record and when if provided.
        validated = utils.get_args(received=request.json,
                                   defaultable={'validated_at': now},
                                   optional={'validated_user_id': str},
                                   )
        if validated['validated_user_id'] is not None:
            row.update(validated)

        record = db_api.update_row(Record, filters, row)
        return utils.flask_return_success(record.jsondict)
    except Exception as e:
        return utils.flask_handle_exception(e)


@app.route('/event', methods=['GET'], strict_slashes=False)
@jwt_required
def get_event():
    filters = utils.get_args(received=request.args,
                             optional={'id': str, 'user_id': str, 'type_id': int},
                             )
    try:
        rows = db_api.get_rows(Event, filters)
        return utils.flask_return_success([row.jsondict for row in rows])
    except Exception as e:
        return utils.flask_handle_exception(e)


@app.route('/event', methods=['POST'], strict_slashes=False)
@jwt_required
def post_event():
    try:
        utils.flask_validate_request_is_json(request)
        now = datetime.datetime.now()
        uuid = str(utils.generate_uuid())
        user = get_jwt_identity()
        row = utils.get_args(received=request.json,
                             required={'name': str, 'description': str,
                                       'address': str, 'postal_code': str,
                                       'event_at': datetime.datetime},
                             defaultable={'id': uuid, 'created_at': now,
                                          'updated_at': now, 'payload': {},
                                          'organization_id': 0, 'user_id': user},
                             )
        event = db_api.add_row(Event, row)
        return utils.flask_return_success(event.jsondict)
    except Exception as e:
        return utils.flask_handle_exception(e)


@app.route('/event', methods=['PUT'], strict_slashes=False)
@jwt_required
def put_event():
    try:
        utils.flask_validate_request_is_json(request)
        now = datetime.datetime.now()
        uuid = str(utils.generate_uuid())
        user = get_jwt_identity()
        row = utils.get_args(received=request.json,
                             required={'name': str, 'description': str,
                                       'address': str, 'postal_code': str,
                                       'event_at': datetime.datetime},
                             defaultable={'id': uuid, 'created_at': now,
                                          'updated_at': now, 'payload': {},
                                          'organization_id': 0, 'user_id': user},
                             )

        filters = {'id': row.pop('id', None)}
        event = db_api.update_row(Event, filters, row)
        return utils.flask_return_success(event.jsondict)
    except Exception as e:
        return utils.flask_handle_exception(e)


@app.route('/user-event-link', methods=['GET'], strict_slashes=False)
@jwt_required
def get_user_event_link():
    filters = utils.get_args(received=request.args,
                             optional={'user_id': str, 'event_id': str},
                             )
    try:
        rows = db_api.get_rows(UserEventLink, filters)
        return utils.flask_return_success([row.jsondict for row in rows])
    except Exception as e:
        return utils.flask_handle_exception(e)


@app.route('/user-event-link', methods=['POST'], strict_slashes=False)
@jwt_required
def post_user_event_link():
    try:
        utils.flask_validate_request_is_json(request)
        now = datetime.datetime.now()
        user = get_jwt_identity()
        row = utils.get_args(received=request.json,
                             required={'event_id': str},
                             defaultable={'created_at': now, 'updated_at': now,
                                          'user_id': user, 'payload': {}},
                             )

        obj = db_api.add_row(UserEventLink, row)
        return utils.flask_return_success(obj.jsondict)
    except Exception as e:
        return utils.flask_handle_exception(e)


@app.route("/")
def hello():
    return "Greetings from the Tikki API"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Tikki application backend')
    parser.add_argument('-r', '--runserver', help='start the server', action='store_true')
    parser.add_argument('-m', '--migrate', help='run database migrations',
                        choices=['up', 'down'])
    parser.add_argument('-v', '--validate', help='check if server can be started',
                        action='store_true')

    args = parser.parse_args()
    if args.validate:
        print('validate')
        quit()

    if args.migrate == 'up':
        print('migrate up')
        quit()
    elif args.migrate == 'down':
        print('migrate down')
        quit()

    if args.runserver:
        app.run()

    parser.print_help()
