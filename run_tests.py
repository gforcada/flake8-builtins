import ast
import sys
import textwrap
import unittest
from unittest import mock

import pytest

from flake8_builtins import BuiltinsChecker


class FakeOptions:
    builtins_ignorelist = []

    def __init__(self, ignore_list=''):
        if ignore_list:
            self.builtins_ignorelist = ignore_list


class TestBuiltins(unittest.TestCase):
    def check_code(self, source, expected_codes=None, ignore_list=None):
        """Check if the given source code generates the given flake8 errors

        If `expected_codes` is a string is converted to a list,
        if it is not given, then it is expected to **not** generate any error.

        If `ignore_list` is provided, it should be a list of names
        that will be ignored if found, as if they were a builtin.
        """
        if isinstance(expected_codes, str):
            expected_codes = [expected_codes]
        elif expected_codes is None:
            expected_codes = []
        if ignore_list is None:
            ignore_list = []
        tree = ast.parse(textwrap.dedent(source))
        checker = BuiltinsChecker(tree, '/home/script.py')
        checker.parse_options(FakeOptions(ignore_list=ignore_list), None)
        return_statements = list(checker.run())

        self.assertEqual(
            len(return_statements), len(expected_codes), f'Got {return_statements}'
        )

        for item, code in zip(return_statements, expected_codes):
            self.assertTrue(
                item[2].startswith(f'{code} '),
                f'Actually got {item[2]} rather than {code}',
            )

    def test_builtin_top_level(self):
        source = 'max = 4'
        self.check_code(source, 'A001')

    def test_ann_assign(self):
        source = 'list: int = 1'
        self.check_code(source, 'A001')

    @pytest.mark.skipif(
        sys.version_info < (3, 8),
        reason='NamedExpr appeared in 3.8',
    )
    def test_walrus_operator(self):
        source = '(dict := 1)'
        self.check_code(source, 'A001')

    def test_nested(self):
        source = """
        def bla():
            filter = 4
        """
        self.check_code(source, 'A001')

    def test_more_nested(self):
        source = """
        class Bla(object):
            def method(self):
                int = 4
        """
        self.check_code(source, 'A001')

    def test_line_number(self):
        source = """
        a = 2
        open = 4
        """
        tree = ast.parse(textwrap.dedent(source))
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = list(checker.run())
        self.assertEqual(ret[0][0], 3)

    def test_offset(self):
        source = """
        def bla():
            zip = 4
        """
        tree = ast.parse(textwrap.dedent(source))
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = list(checker.run())
        self.assertEqual(ret[0][1], 4)

    def test_assign_message(self):
        source = """
        def bla():
            object = 4
        """
        self.check_code(source, 'A001')

    def test_assignment_starred(self):
        source = 'bla, *int = range(4)'
        self.check_code(source, 'A001')

    def test_assignment_list(self):
        source = '[bla, int] = range(4)'
        self.check_code(source, 'A001')

    def test_class_attribute_message(self):
        source = """
        class TestClass():
            object = 4
        """
        self.check_code(source, 'A003')

    def test_argument_message(self):
        source = """
        def bla(list):
            a = 4"""
        self.check_code(source, 'A002')

    def test_keyword_argument_message(self):
        source = """
        def bla(dict=3):
            b = 4"""
        self.check_code(source, 'A002')

    def test_kwonly_argument_message(self):
        source = """
        def bla(*, list):
            a = 4
        """
        self.check_code(source, 'A002')

    @pytest.mark.skipif(
        sys.version_info < (3, 8),
        reason='This syntax is only valid in Python 3.8+',
    )
    def test_posonly_argument_message(self):
        source = """
        def bla(list, /):
            a = 4
        """
        self.check_code(source, 'A002')

    def test_no_error(self):
        source = """def bla(first):\n    b = 4"""
        self.check_code(source)

    def test_method_without_arguments(self):
        source = """
        def bla():
            b = 4
        """
        self.check_code(source)

    def test_method_only_normal_keyword_arguments(self):
        source = """
        def bla(k=4):
            b = 4
        """
        self.check_code(source)

    def test_report_all_arguments(self):
        source = """
        def bla(zip, object=4):
            b = 4
        """
        self.check_code(source, ['A002', 'A002'])

    def test_report_all_variables_within_a_line(self):
        source = """
        def bla():
            object = 4; zip = 3
        """
        self.check_code(source, ['A001', 'A001'])

    def test_default_ignored_names(self):
        source = """
        class MyClass(object):
            __name__ = 4
        """
        self.check_code(source)

    def test_custom_ignored_names(self):
        source = 'copyright = 4'
        self.check_code(source, ignore_list=('copyright',))

    def test_for_loop_variable(self):
        source = """
        for format in (1, 2, 3):
            continue
        """
        self.check_code(source, 'A001')

    def test_for_loop_multiple_variables(self):
        source = """
        for (index, format) in enumerate([1,2,3,]):
            continue
        """
        self.check_code(source, 'A001')

    def test_for_loop_list(self):
        source = """
        for [index, format] in enumerate([1,2,3,]):
            continue
        """
        self.check_code(source, 'A001')

    def test_for_loop_nested_tuple(self):
        source = """
        for index, (format, list) in enumerate([(1, "a"), (2, "b")]):
            continue
        """
        self.check_code(source, ['A001', 'A001'])

    def test_for_loop_starred(self):
        source = """
        for index, *int in enumerate([(1, "a"), (2, "b")]):
            continue
        """
        self.check_code(source, 'A001')

    def test_for_loop_starred_no_error(self):
        source = """
        for index, *other in enumerate([(1, "a"), (2, "b")]):
            continue
        """
        self.check_code(source)

    def test_with_statement(self):
        source = """
        with open("bla.txt") as dir:
            continue
        """
        self.check_code(source, 'A001')

    def test_with_statement_no_error(self):
        source = 'with open("bla.txt"): ...'
        self.check_code(source)

    def test_with_statement_multiple(self):
        source = 'with open("bla.txt") as dir, open("bla.txt") as int: ...'
        self.check_code(source, ['A001', 'A001'])

    def test_with_statement_unpack(self):
        source = 'with open("bla.txt") as (dir, bla): ...'
        self.check_code(source, 'A001')

    def test_with_statement_unpack_on_list(self):
        source = 'with open("bla.txt") as [dir, bla]: ...'
        self.check_code(source, 'A001')

    def test_with_statement_unpack_star(self):
        source = 'with open("bla.txt") as (bla, *int): ...'
        self.check_code(source, 'A001')

    def test_exception_py3(self):
        source = """
        try:
            a = 2
        except Exception as int: ...
        """
        self.check_code(source, 'A001')

    def test_exception_no_error(self):
        source = """
        try:
            a = 2
        except Exception: ...
        """
        self.check_code(source)

    def test_list_comprehension(self):
        source = 'a = [int for int in range(3,9)]'
        self.check_code(source, 'A001')

    def test_set_comprehension(self):
        source = 'a = {int for int in range(3,9)}'
        self.check_code(source, 'A001')

    def test_dict_comprehension(self):
        source = 'a = {int:"a" for int in range(3,9)}'
        self.check_code(source, 'A001')

    def test_gen_comprehension(self):
        source = 'a = (int for int in range(3,9))'
        self.check_code(source, 'A001')

    def test_list_comprehension_multiple(self):
        source = 'a = [(int, list) for int, list in enumerate(range(3,9))]\n'
        self.check_code(source, ['A001', 'A001'])

    def test_list_comprehension_nested(self):
        source = 'a = [(int, str) for int in some() for str in other()]'
        self.check_code(source, ['A001', 'A001'])

    def test_list_comprehension_multiple_as_list(self):
        source = 'a = [(int, a) for [int, a] in enumerate(range(3,9))]'
        self.check_code(source, 'A001')

    def test_import_as(self):
        source = 'import zope.component.getSite as int'
        self.check_code(source, 'A001')

    def test_import_from_as(self):
        source = 'from zope.component import getSite as int'
        self.check_code(source, 'A001')

    def test_import_as_nothing(self):
        source = 'import zope.component.getSite as something_else'
        self.check_code(source)

    def test_import_from_as_nothing(self):
        source = 'from zope.component import getSite as something_else'
        self.check_code(source)

    def test_class(self):
        source = 'class int(object): ...'
        self.check_code(source, 'A001')

    def test_class_nothing(self):
        source = 'class integer(object): ...'
        self.check_code(source)

    def test_function(self):
        source = 'def int(): ...'
        self.check_code(source, 'A001')

    def test_async_function(self):
        source = 'async def int(): ...'
        self.check_code(source, 'A001')

    def test_method(self):
        source = """
        class bla(object):
            def int(): ...
        """
        self.check_code(source, 'A003')

    def test_method_error_code(self):
        source = """
        class bla(object):
            def int(): ...
        """
        self.check_code(source, 'A003')

    def test_function_nothing(self):
        source = 'def integer(): ...'
        self.check_code(source)

    def test_async_for(self):
        source = """
        async def bla():
            async for int in range(4): ...
        """
        self.check_code(source, 'A001')

    def test_async_for_nothing(self):
        source = """
        async def bla():
            async for x in range(4): ...
        """
        self.check_code(source)

    def test_async_with(self):
        source = """
        async def bla():
            async with open("bla.txt") as int: ...
        """
        self.check_code(source, 'A001')

    def test_async_with_nothing(self):
        source = """
        async def bla():
            async with open("bla.txt") as x: ...
        """
        self.check_code(source)

    @mock.patch('flake8.utils.stdin_get_value')
    def test_stdin(self, stdin_get_value):
        source = 'max = 4'
        stdin_get_value.return_value = source
        checker = BuiltinsChecker('', 'stdin')
        ret = list(checker.run())
        self.assertEqual(
            len(ret),
            1,
        )

    def test_tuple_unpacking(self):
        source = 'a, *(b, c) = 1, 2, 3'
        self.check_code(source)
