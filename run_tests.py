import ast
import sys
import textwrap
from unittest import mock

import pytest

from flake8_builtins import BuiltinsChecker


class FakeOptions:
    builtins_ignorelist = []
    builtins = None

    def __init__(self, ignore_list='', builtins=None):
        if ignore_list:
            self.builtins_ignorelist = ignore_list
        if builtins:
            self.builtins = builtins


def check_code(source, expected_codes=None, ignore_list=None, builtins=None):
    """Check if the given source code generates the given flake8 errors

    If `expected_codes` is a string is converted to a list,
    if it is not given, then it is expected to **not** generate any error.

    If `ignore_list` is provided, it should be a list of names
    that will be ignored if found, as if they were a builtin.

    If `builtins` is provided, it should be a list of names
    that will be reported if found, as if they were a builtin.
    """
    if isinstance(expected_codes, str):
        expected_codes = [expected_codes]
    elif expected_codes is None:
        expected_codes = []
    if ignore_list is None:
        ignore_list = []
    tree = ast.parse(textwrap.dedent(source))
    checker = BuiltinsChecker(tree, '/home/script.py')
    checker.parse_options(FakeOptions(ignore_list=ignore_list, builtins=builtins))
    return_statements = list(checker.run())

    assert len(return_statements) == len(expected_codes)

    for item, code in zip(return_statements, expected_codes):
        assert item[2].startswith(f'{code} ')


def test_builtin_top_level():
    source = 'max = 4'
    check_code(source, 'A001')


def test_ann_assign():
    source = 'list: int = 1'
    check_code(source, 'A001')


@pytest.mark.skipif(
    sys.version_info < (3, 8),
    reason='NamedExpr appeared in 3.8',
)
def test_walrus_operator():
    source = '(dict := 1)'
    check_code(source, 'A001')


def test_nested():
    source = """
    def bla():
        filter = 4
    """
    check_code(source, 'A001')


def test_more_nested():
    source = """
    class Bla(object):
        def method(self):
            int = 4
    """
    check_code(source, 'A001')


def test_line_number():
    source = """
    a = 2
    open = 4
    """
    tree = ast.parse(textwrap.dedent(source))
    checker = BuiltinsChecker(tree, '/home/script.py')
    checker.parse_options(FakeOptions())
    ret = list(checker.run())
    assert ret[0][0] == 3


def test_offset():
    source = """
    def bla():
        zip = 4
    """
    tree = ast.parse(textwrap.dedent(source))
    checker = BuiltinsChecker(tree, '/home/script.py')
    checker.parse_options(FakeOptions())
    ret = list(checker.run())
    assert ret[0][1] == 4


def test_assign_message():
    source = """
    def bla():
        object = 4
    """
    check_code(source, 'A001')


def test_assignment_starred():
    source = 'bla, *int = range(4)'
    check_code(source, 'A001')


def test_assignment_list():
    source = '[bla, int] = range(4)'
    check_code(source, 'A001')


def test_class_attribute_message():
    source = """
    class TestClass():
        object = 4
    """
    check_code(source, 'A003')


def test_argument_message():
    source = """
    def bla(list):
        a = 4"""
    check_code(source, 'A002')


def test_keyword_argument_message():
    source = """
    def bla(dict=3):
        b = 4"""
    check_code(source, 'A002')


def test_kwonly_argument_message():
    source = """
    def bla(*, list):
        a = 4
    """
    check_code(source, 'A002')


@pytest.mark.skipif(
    sys.version_info < (3, 8),
    reason='This syntax is only valid in Python 3.8+',
)
def test_posonly_argument_message():
    source = """
    def bla(list, /):
        a = 4
    """
    check_code(source, 'A002')


def test_no_error():
    source = """def bla(first):\n    b = 4"""
    check_code(source)


def test_method_without_arguments():
    source = """
    def bla():
        b = 4
    """
    check_code(source)


def test_method_only_normal_keyword_arguments():
    source = """
    def bla(k=4):
        b = 4
    """
    check_code(source)


def test_report_all_arguments():
    source = """
    def bla(zip, object=4):
        b = 4
    """
    check_code(source, ['A002', 'A002'])


def test_report_all_variables_within_a_line():
    source = """
    def bla():
        object = 4; zip = 3
    """
    check_code(source, ['A001', 'A001'])


def test_default_ignored_names():
    source = """
    class MyClass(object):
        __name__ = 4
    """
    check_code(source)


def test_custom_ignored_names():
    source = 'copyright = 4'
    check_code(source, ignore_list=('copyright',))


def test_flake8_builtins():
    source = 'consider_this_builtin = 4'
    check_code(source, ['A001'], builtins=('consider_this_builtin',))


def test_for_loop_variable():
    source = """
    for format in (1, 2, 3):
        continue
    """
    check_code(source, 'A001')


def test_for_loop_multiple_variables():
    source = """
    for (index, format) in enumerate([1,2,3,]):
        continue
    """
    check_code(source, 'A001')


def test_for_loop_list():
    source = """
    for [index, format] in enumerate([1,2,3,]):
        continue
    """
    check_code(source, 'A001')


def test_for_loop_nested_tuple():
    source = """
    for index, (format, list) in enumerate([(1, "a"), (2, "b")]):
        continue
    """
    check_code(source, ['A001', 'A001'])


def test_for_loop_starred():
    source = """
    for index, *int in enumerate([(1, "a"), (2, "b")]):
        continue
    """
    check_code(source, 'A001')


def test_for_loop_starred_no_error():
    source = """
    for index, *other in enumerate([(1, "a"), (2, "b")]):
        continue
    """
    check_code(source)


def test_with_statement():
    source = """
    with open("bla.txt") as dir:
        continue
    """
    check_code(source, 'A001')


def test_with_statement_no_error():
    source = 'with open("bla.txt"): ...'
    check_code(source)


def test_with_statement_multiple():
    source = 'with open("bla.txt") as dir, open("bla.txt") as int: ...'
    check_code(source, ['A001', 'A001'])


def test_with_statement_unpack():
    source = 'with open("bla.txt") as (dir, bla): ...'
    check_code(source, 'A001')


def test_with_statement_unpack_on_list():
    source = 'with open("bla.txt") as [dir, bla]: ...'
    check_code(source, 'A001')


def test_with_statement_unpack_star():
    source = 'with open("bla.txt") as (bla, *int): ...'
    check_code(source, 'A001')


def test_exception_py3():
    source = """
    try:
        a = 2
    except Exception as int: ...
    """
    check_code(source, 'A001')


def test_exception_no_error():
    source = """
    try:
        a = 2
    except Exception: ...
    """
    check_code(source)


def test_list_comprehension():
    source = 'a = [int for int in range(3,9)]'
    check_code(source, 'A001')


def test_set_comprehension():
    source = 'a = {int for int in range(3,9)}'
    check_code(source, 'A001')


def test_dict_comprehension():
    source = 'a = {int:"a" for int in range(3,9)}'
    check_code(source, 'A001')


def test_gen_comprehension():
    source = 'a = (int for int in range(3,9))'
    check_code(source, 'A001')


def test_list_comprehension_multiple():
    source = 'a = [(int, list) for int, list in enumerate(range(3,9))]\n'
    check_code(source, ['A001', 'A001'])


def test_list_comprehension_nested():
    source = 'a = [(int, str) for int in some() for str in other()]'
    check_code(source, ['A001', 'A001'])


def test_list_comprehension_multiple_as_list():
    source = 'a = [(int, a) for [int, a] in enumerate(range(3,9))]'
    check_code(source, 'A001')


def test_import_as():
    source = 'import zope.component.getSite as int'
    check_code(source, 'A001')


def test_import_from_as():
    source = 'from zope.component import getSite as int'
    check_code(source, 'A001')


def test_import_as_nothing():
    source = 'import zope.component.getSite as something_else'
    check_code(source)


def test_import_from_as_nothing():
    source = 'from zope.component import getSite as something_else'
    check_code(source)


def test_class():
    source = 'class int(object): ...'
    check_code(source, 'A001')


def test_class_nothing():
    source = 'class integer(object): ...'
    check_code(source)


def test_function():
    source = 'def int(): ...'
    check_code(source, 'A001')


def test_async_function():
    source = 'async def int(): ...'
    check_code(source, 'A001')


def test_method():
    source = """
    class bla(object):
        def int(): ...
    """
    check_code(source, 'A003')


def test_method_error_code():
    source = """
    class bla(object):
        def int(): ...
    """
    check_code(source, 'A003')


def test_function_nothing():
    source = 'def integer(): ...'
    check_code(source)


def test_async_for():
    source = """
    async def bla():
        async for int in range(4): ...
    """
    check_code(source, 'A001')


def test_async_for_nothing():
    source = """
    async def bla():
        async for x in range(4): ...
    """
    check_code(source)


def test_async_with():
    source = """
    async def bla():
        async with open("bla.txt") as int: ...
    """
    check_code(source, 'A001')


def test_async_with_nothing():
    source = """
    async def bla():
        async with open("bla.txt") as x: ...
    """
    check_code(source)


@mock.patch('flake8.utils.stdin_get_value')
def test_stdin(stdin_get_value):
    source = 'max = 4'
    stdin_get_value.return_value = source
    checker = BuiltinsChecker('', 'stdin')
    checker.parse_options(FakeOptions())
    ret = list(checker.run())
    assert len(ret) == 1


def test_tuple_unpacking():
    source = 'a, *(b, c) = 1, 2, 3'
    check_code(source)
