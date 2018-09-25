"""
Tests for utils module
"""
from unittest import TestCase

import exceptions
import utils


class UtilsTestCase(TestCase):
    def test_get_args(self):
        received = {'a': 1, 'b': 'c'}
        required = {'a': int}
        defaultable = {'a': 3, 'c': 2}
        optional = {'a': int, 'b': str}
        constant = {'a': 2}
        self.assertRaises(exceptions.AppException, utils.get_args, received)
        expected = {'a': 1}
        self.assertDictEqual(utils.get_args(received, required=required), expected)
        expected = {'a': 1, 'c': 2}
        self.assertDictEqual(utils.get_args(received, defaultable=defaultable), expected)
        expected = {'a': 1, 'b': 'c'}
        self.assertDictEqual(utils.get_args(received, optional=optional), expected)
        expected = {'a': 2}
        self.assertDictEqual(utils.get_args(received, constant=constant), expected)
        expected = {'a': 2, 'c': 2, 'b': 'c'}
        self.assertDictEqual(utils.get_args(received,
                                            required=required,
                                            defaultable=defaultable,
                                            optional=optional,
                                            constant=constant), expected)
