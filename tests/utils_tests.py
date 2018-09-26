"""
Tests for utils module
"""
from unittest import TestCase
from uuid import UUID

import exceptions
import utils

received = {'a': 1, 'b': 'c'}
required = {'a': int}
defaultable = {'a': 3, 'c': 2}
optional = {'a': int, 'b': str}
constant = {'a': 2}


class UtilsGetArgsTestCase(TestCase):
    def test_get_args_missing_args(self):
        self.assertRaises(exceptions.AppException, utils.get_args, received)

    def test_get_args_missing_keys(self):
        received_truncated = {'b': 'c'}
        self.assertRaises(exceptions.AppException, utils.get_args, received_truncated)

    def test_get_args_required(self):
        expected = {'a': 1}
        self.assertDictEqual(utils.get_args(received, required=required), expected)

    def test_get_args_defaultable(self):
        expected = {'a': 1, 'c': 2}
        self.assertDictEqual(utils.get_args(received, defaultable=defaultable), expected)

    def test_get_args_optional(self):
        expected = {'a': 1, 'b': 'c'}
        self.assertDictEqual(utils.get_args(received, optional=optional), expected)

    def test_get_args_constant(self):
        expected = {'a': 2}
        self.assertDictEqual(utils.get_args(received, constant=constant), expected)

    def test_get_args_all(self):
        expected = {'a': 2, 'c': 2, 'b': 'c'}
        self.assertDictEqual(utils.get_args(received,
                                            required=required,
                                            defaultable=defaultable,
                                            optional=optional,
                                            constant=constant), expected)


class UuidTestCase(TestCase):
    def test_generate_uuid_default(self):
        val = utils.generate_uuid()
        self.assertIsInstance(val, UUID)

    def test_generate_uuid_many(self):
        obj_count = 10
        val = utils.generate_uuid(obj_count)
        self.assertEqual(len(val), obj_count)

    def test_generate_uuid_zero(self):
        self.assertIsNone(utils.generate_uuid(0))
