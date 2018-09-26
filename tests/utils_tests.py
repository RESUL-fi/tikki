"""
Tests for utils module
"""
from unittest import TestCase, mock
from uuid import UUID

import exceptions
import utils


class UtilsGetArgsTestCase(TestCase):
    received = {'a': 1, 'b': 'c'}
    required = {'a': int}
    defaultable = {'a': 3, 'c': 2}
    optional = {'a': int, 'b': str}
    constant = {'a': 2}

    def test_get_args_missing_args(self):
        self.assertRaises(exceptions.AppException, utils.get_args, self.received)

    def test_get_args_missing_required_keys(self):
        required_missing = {'q': str}
        self.assertRaises(exceptions.AppException, utils.get_args, self.received,
                          required=required_missing)

    def test_get_args_required(self):
        expected = {'a': 1}
        self.assertDictEqual(utils.get_args(self.received,
                                            required=self.required), expected)

    def test_get_args_defaultable(self):
        expected = {'a': 1, 'c': 2}
        self.assertDictEqual(utils.get_args(self.received,
                                            defaultable=self.defaultable), expected)

    def test_get_args_optional(self):
        expected = {'a': 1, 'b': 'c'}
        self.assertDictEqual(utils.get_args(self.received,
                                            optional=self.optional), expected)

    def test_get_args_constant(self):
        expected = {'a': 2}
        self.assertDictEqual(utils.get_args(self.received,
                                            constant=self.constant), expected)

    def test_get_args_all(self):
        expected = {'a': 2, 'c': 2, 'b': 'c'}
        self.assertDictEqual(utils.get_args(self.received,
                                            required=self.required,
                                            defaultable=self.defaultable,
                                            optional=self.optional,
                                            constant=self.constant), expected)


class UuidTestCase(TestCase):
    def test_generate_uuid_default(self):
        val = utils.generate_uuid()
        self.assertIsInstance(val, UUID)

    def test_generate_uuid_many(self):
        obj_count = 10
        val = utils.generate_uuid(obj_count)
        self.assertEqual(len(val), obj_count)
        self.assertIsInstance(val[0], UUID)

    def test_generate_uuid_zero(self):
        self.assertIsNone(utils.generate_uuid(0))


class RequestTestCase(TestCase):
    @staticmethod
    def get_request_mock() -> mock.Mock:
        return mock.Mock()

    def test_validate_request_is_not_json(self):
        request = self.get_request_mock()
        request.is_json = False
        self.assertRaises(exceptions.Flask400Exception,
                          utils.flask_validate_request_is_json, request)

    def test_validate_request_is_json(self):
        request = self.get_request_mock()
        request.is_json = True
        self.assertIsNone(utils.flask_validate_request_is_json(request))
