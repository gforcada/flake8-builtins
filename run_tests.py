# -*- coding: utf-8 -*-
from flake8_builtins import BuiltinsChecker

import ast
import pytest
import sys
import unittest


try:
    from unittest import mock
except ImportError:
    import mock


if sys.version_info >= (3, 6):
    from hypothesis import given
    from hypothesis import reject
    import hypothesmith


class TestBuiltins(unittest.TestCase):
    def assert_codes(self, ret, codes):
        self.assertEqual(len(ret), len(codes))
        for item, code in zip(ret, codes):
            self.assertTrue(item[2].startswith(code + ' '))

    def test_builtin_top_level(self):
        tree = ast.parse('max = 4')
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assert_codes(ret, ['A001'])

    @pytest.mark.skipif(
        sys.version_info < (3, 6),
        reason='AnnAssign appeared in 3.6',
    )
    def test_ann_assign(self):
        tree = ast.parse('list: int = 1')
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assert_codes(ret, ['A001'])

    @pytest.mark.skipif(
        sys.version_info < (3, 8),
        reason='NamedExpr appeared in 3.8',
    )
    def test_walrus_operator(self):
        tree = ast.parse('(dict := 1)')
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assert_codes(ret, ['A001'])

    def test_nested(self):
        tree = ast.parse(
            'def bla():\n'
            '    filter = 4',
        )
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assert_codes(ret, ['A001'])

    def test_more_nested(self):
        tree = ast.parse(
            'class Bla(object):\n'
            '    def method(self):\n'
            '        int = 4',
        )
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assert_codes(ret, ['A001'])

    def test_line_number(self):
        tree = ast.parse(
            'a = 2\n'
            'open = 4',
        )
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(ret[0][0], 2)

    def test_offset(self):
        tree = ast.parse(
            'def bla():\n'
            '    zip = 4',
        )
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(ret[0][1], 4)

    def test_assign_message(self):
        tree = ast.parse('def bla():\n    object = 4')
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assert_codes(ret, ['A001'])

    @pytest.mark.skipif(
        sys.version_info < (3, 0),
        reason='This syntax is only valid in Python 3.x',
    )
    def test_assignment_starred(self):
        tree = ast.parse('bla, *int = range(4)')
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assert_codes(ret, ['A001'])

    def test_assignment_list(self):
        tree = ast.parse('[bla, int] = range(4)')
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assert_codes(ret, ['A001'])

    def test_class_attribute_message(self):
        tree = ast.parse('class TestClass():\n    object = 4')
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assert_codes(ret, ['A003'])

    def test_argument_message(self):
        tree = ast.parse('def bla(list):\n    a = 4')
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assert_codes(ret, ['A002'])

    def test_keyword_argument_message(self):
        tree = ast.parse('def bla(dict=3):\n    b = 4')
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assert_codes(ret, ['A002'])

    @pytest.mark.skipif(
        sys.version_info < (3, 6),
        reason='This syntax is only valid in Python 3.6+',
    )
    def test_kwonly_argument_message(self):
        tree = ast.parse('def bla(*, list):\n    a = 4')
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assert_codes(ret, ['A002'])

    @pytest.mark.skipif(
        sys.version_info < (3, 8),
        reason='This syntax is only valid in Python 3.8+',
    )
    def test_posonly_argument_message(self):
        tree = ast.parse('def bla(list, /):\n    a = 4')
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assert_codes(ret, ['A002'])

    def test_no_error(self):
        tree = ast.parse('def bla(first):\n    b = 4')
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 0)

    def test_method_without_arguments(self):
        tree = ast.parse('def bla():\n    b = 4')
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 0)

    def test_method_only_normal_keyword_arguments(self):
        tree = ast.parse('def bla(k=4):\n    b = 4')
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 0)

    def test_report_all_arguments(self):
        tree = ast.parse('def bla(zip, object=4):\n    b = 4')
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assert_codes(ret, ['A002', 'A002'])

    def test_report_all_variables_within_a_line(self):
        tree = ast.parse('def bla():\n    object = 4; zip = 3')
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assert_codes(ret, ['A001', 'A001'])

    def test_ignore_whitelisted_names(self):
        tree = ast.parse(
            'class MyClass(object):\n'
            '    __name__ = 4\n',
        )
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 0)

    def test_for_loop_variable(self):
        tree = ast.parse(
            'for format in (1, 2, 3):\n'
            '        continue\n',
        )
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 1)

    def test_for_loop_multiple_variables(self):
        tree = ast.parse(
            'for (index, format) in enumerate([1,2,3,]):\n'
            '        continue\n',
        )
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 1)

    def test_for_loop_list(self):
        tree = ast.parse(
            'for [index, format] in enumerate([1,2,3,]):\n'
            '        continue\n',
        )
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 1)

    def test_for_loop_nested_tuple(self):
        tree = ast.parse(
            'for index, (format, list) in enumerate([(1, "a"), (2, "b")]):\n'
            '        continue\n',
        )
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 2)

    @pytest.mark.skipif(
        sys.version_info < (3, 0),
        reason='This syntax is only valid in Python 3.x',
    )
    def test_for_loop_starred(self):
        tree = ast.parse(
            'for index, *int in enumerate([(1, "a"), (2, "b")]):\n'
            '        continue\n',
        )
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 1)

    @pytest.mark.skipif(
        sys.version_info < (3, 0),
        reason='This syntax is only valid in Python 3.x',
    )
    def test_for_loop_starred_no_error(self):
        tree = ast.parse(
            'for index, *other in enumerate([(1, "a"), (2, "b")]):\n'
            '        continue\n',
        )
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 0)

    def test_with_statement(self):
        tree = ast.parse(
            'with open("bla.txt") as dir:\n'
            '    continue\n',
        )
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 1)

    def test_with_statement_no_error(self):
        tree = ast.parse(
            'with open("bla.txt"):\n'
            '    continue\n',
        )
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 0)

    def test_with_statement_multiple(self):
        tree = ast.parse(
            'with open("bla.txt") as dir, open("bla.txt") as int:\n'
            '    continue\n',
        )
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 2)

    def test_with_statement_unpack(self):
        tree = ast.parse(
            'with open("bla.txt") as (dir, bla):\n'
            '    continue\n',
        )
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 1)

    def test_with_statement_unpack_on_list(self):
        tree = ast.parse(
            'with open("bla.txt") as [dir, bla]:\n'
            '    continue\n',
        )
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 1)

    @pytest.mark.skipif(
        sys.version_info < (3, 0),
        reason='This syntax is only valid in Python 3.x',
    )
    def test_with_statement_unpack_star(self):
        tree = ast.parse(
            'with open("bla.txt") as (bla, *int):\n'
            '    continue\n',
        )
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 1)

    @pytest.mark.skipif(
        sys.version_info < (3, 0),
        reason='This syntax is only valid in Python 3.x',
    )
    def test_exception_py3(self):
        tree = ast.parse(
            'try:\n'
            '    a = 2\n'
            'except Exception as int:\n'
            '    print("ooops")\n',
        )
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 1)

    @pytest.mark.skipif(
        sys.version_info > (3, 0),
        reason='This syntax is only valid in Python 2.x',
    )
    def test_exception_py2(self):
        tree = ast.parse(
            'try:\n'
            '    a = 2\n'
            'except Exception, int:\n'
            '    print("ooops")\n',
        )
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 1)

    def test_exception_no_error(self):
        tree = ast.parse(
            'try:\n'
            '    a = 2\n'
            'except Exception:\n'
            '    print("ooops")\n',
        )
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 0)

    def test_list_comprehension(self):
        tree = ast.parse('a = [int for int in range(3,9)]')
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 1)

    def test_set_comprehension(self):
        tree = ast.parse('a = {int for int in range(3,9)}')
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 1)

    def test_dict_comprehension(self):
        tree = ast.parse('a = {int:"a" for int in range(3,9)}')
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 1)

    def test_gen_comprehension(self):
        tree = ast.parse('a = (int for int in range(3,9))')
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 1)

    def test_list_comprehension_multiple(self):
        tree = ast.parse(
            'a = [(int, list) for int, list in enumerate(range(3,9))]\n',
        )
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 2)

    def test_list_comprehension_nested(self):
        tree = ast.parse(
            'a = [(int, str) for int in some() for str in other()]\n',
        )
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 2)

    def test_list_comprehension_multiple_as_list(self):
        tree = ast.parse(
            'a = [(int, a) for [int, a] in enumerate(range(3,9))]\n',
        )
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 1)

    def test_import_as(self):
        tree = ast.parse(
            'import zope.component.getSite as int\n',
        )
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 1)

    def test_import_from_as(self):
        tree = ast.parse(
            'from zope.component import getSite as int\n',
        )
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 1)

    def test_import_as_nothing(self):
        tree = ast.parse(
            'import zope.component.getSite as something_else\n',
        )
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 0)

    def test_import_from_as_nothing(self):
        tree = ast.parse(
            'from zope.component import getSite as something_else\n',
        )
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 0)

    def test_class(self):
        tree = ast.parse(
            'class int(object): pass\n',
        )
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 1)

    def test_class_nothing(self):
        tree = ast.parse(
            'class integer(object): pass\n',
        )
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 0)

    def test_function(self):
        tree = ast.parse(
            'def int(): pass\n',
        )
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 1)

    @pytest.mark.skipif(
        sys.version_info < (3, 5),
        reason='This syntax is only valid in Python 3.5',
    )
    def test_async_function(self):
        tree = ast.parse(
            'async def int(): pass\n',
        )
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 1)

    def test_method(self):
        tree = ast.parse(
            'class bla(object):\n'
            '    def int(): pass\n',
        )
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 1)

    def test_method_error_code(self):
        tree = ast.parse(
            'class bla(object):\n'
            '    def int(): pass\n',
        )
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        error_code = ret[0][2][:4]
        self.assertEqual(error_code, 'A003')

    def test_function_nothing(self):
        tree = ast.parse(
            'def integer(): pass\n',
        )
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 0)

    @pytest.mark.skipif(
        sys.version_info < (3, 5),
        reason='This syntax is only valid in Python 3.x',
    )
    def test_async_for(self):
        tree = ast.parse(
            'async def bla():\n'
            '    async for int in range(4):\n'
            '        pass\n',
        )
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 1)

    @pytest.mark.skipif(
        sys.version_info < (3, 5),
        reason='This syntax is only valid in Python 3.x',
    )
    def test_async_for_nothing(self):
        tree = ast.parse(
            'async def bla():\n'
            '    async for x in range(4):\n'
            '        pass\n',
        )
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 0)

    @pytest.mark.skipif(
        sys.version_info < (3, 5),
        reason='This syntax is only valid in Python 3.x',
    )
    def test_async_with(self):
        tree = ast.parse(
            'async def bla():\n'
            '    async with open("bla.txt") as int:\n'
            '        pass\n',
        )
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 1)

    @pytest.mark.skipif(
        sys.version_info < (3, 5),
        reason='This syntax is only valid in Python 3.x',
    )
    def test_async_with_nothing(self):
        tree = ast.parse(
            'async def bla():\n'
            '    async with open("bla.txt") as x:\n'
            '        pass\n',
        )
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 0)

    @mock.patch('flake8.utils.stdin_get_value')
    def test_stdin(self, stdin_get_value):
        code = u'max = 4'
        stdin_get_value.return_value = code
        checker = BuiltinsChecker('', 'stdin')
        ret = [c for c in checker.run()]
        self.assertEqual(
            len(ret),
            1,
        )

    @pytest.mark.skipif(
        sys.version_info < (3, 5),
        reason='This syntax is only valid in Python 3.x',
    )
    def test_tuple_unpacking(self):
        tree = ast.parse('a, *(b, c) = 1, 2, 3')
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 0)


if sys.version_info >= (3, 6):
    @given(source_code=hypothesmith.from_grammar())
    def test_builtin_works_on_many_examples(source_code):
        try:
            source = source_code.encode('utf-8-sig')
        except UnicodeEncodeError:
            reject()
            raise
        tree = ast.parse(source)
        checker = BuiltinsChecker(tree, '/home/script.py')
        for c in checker.run():
            assert isinstance(c, list)
