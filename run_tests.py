# -*- coding: utf-8 -*-
from flake8_builtins import BuiltinsChecker

import ast
import mock
import unittest


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

    def test_except_variable(self):
        tree = ast.parse(
            'try:\n'
            '    1 / 0\n'
            'except ZeroDivisionError as sum:\n'
            '    print(sum)'
        )
        checker = BuiltinsChecker(tree, '/home/script.py')
        ret = [c for c in checker.run()]
        self.assertEqual(len(ret), 1)

    @mock.patch('flake8.utils.stdin_get_value')
    def test_stdin(self, stdin_get_value):
        code = u'max = 4'
        stdin_get_value.return_value = code
        tree = ast.parse(code)
        checker = BuiltinsChecker(tree, 'stdin')
        ret = [c for c in checker.run()]
        self.assertEqual(
            len(ret),
            1,
        )


if __name__ == '__main__':
    unittest.main()
