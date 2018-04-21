# -*- coding: utf-8 -*-
import ast
import inspect
import sys


try:
    from flake8.engine import pep8 as stdin_utils
except ImportError:
    from flake8 import utils as stdin_utils


WHITE_LIST = [
    '__name__',
    '__doc__',
    'credits',
    '_',
]


if sys.version_info >= (3, 0):
    import builtins
    int_types = (int,)
    BUILTINS = [
        a[0]
        for a in inspect.getmembers(builtins)
        if a[0] not in WHITE_LIST
    ]
else:
    import __builtin__
    int_types = (int, long)
    BUILTINS = [
        a[0]
        for a in inspect.getmembers(__builtin__)
        if a[0] not in WHITE_LIST
    ]


class BuiltinsChecker(object):
    name = 'flake8_builtins'
    version = '1.3'
    assign_msg = 'A001 "{0}" is a python builtin and is being shadowed, ' \
                 'consider renaming the variable'
    argument_msg = 'A002 "{0}" is used as an argument and thus shadows a ' \
                   'python builtin, consider renaming the argument'
    class_attribute_msg = 'A003 "{0}" is a python builtin, consider ' \
                          'renaming the class attribute'

    def __init__(self, tree, filename):
        self.tree = tree
        self.filename = filename

    def run(self):
        tree = self.tree

        if self.filename == 'stdin':
            lines = stdin_utils.stdin_get_value()
            tree = ast.parse(lines)

        for statement in ast.walk(tree):
            for child in ast.iter_child_nodes(statement):
                child.__flake8_builtins_parent = statement

        function_nodes = [ast.FunctionDef]
        if getattr(ast, 'AsyncFunctionDef', None):
            function_nodes.append(ast.AsyncFunctionDef)
        function_nodes = tuple(function_nodes)

        for_nodes = [ast.For]
        if getattr(ast, 'AsyncFor', None):
            for_nodes.append(ast.AsyncFor)
        for_nodes = tuple(for_nodes)

        with_nodes = [ast.With]
        if getattr(ast, 'AsyncWith', None):
            with_nodes.append(ast.AsyncWith)
        with_nodes = tuple(with_nodes)

        for statement in ast.walk(tree):
            value = None
            if isinstance(statement, ast.Assign):
                value = self.check_assignment(statement)

            elif isinstance(statement, function_nodes):
                value = self.check_function_definition(statement)

            elif isinstance(statement, for_nodes):
                value = self.check_for_loop(statement)

            elif isinstance(statement, with_nodes):
                value = self.check_with(statement)

            elif isinstance(statement, ast.excepthandler):
                value = self.check_exception(statement)

            elif isinstance(statement, ast.ListComp):
                value = self.check_list_comprehension(statement)

            elif isinstance(statement, (ast.Import, ast.ImportFrom)):
                value = self.check_import(statement)

            elif isinstance(statement, ast.ClassDef):
                value = self.check_class(statement)

            if value:
                for line, offset, msg, rtype in value:
                    yield line, offset, msg, rtype

    def check_assignment(self, statement):
        msg = self.assign_msg
        if type(statement.__flake8_builtins_parent) is ast.ClassDef:
            msg = self.class_attribute_msg

        for element in statement.targets:
            if isinstance(element, ast.Name) and \
                    element.id in BUILTINS:

                yield self.error(element, message=msg, variable=element.id)

    def check_function_definition(self, statement):
        if statement.name in BUILTINS:
            msg = self.assign_msg
            if type(statement.__flake8_builtins_parent) is ast.ClassDef:
                msg = self.class_attribute_msg

            yield self.error(statement, message=msg, variable=statement.name)

        if sys.version_info >= (3, 0):
            for arg in statement.args.args:
                if isinstance(arg, ast.arg) and \
                        arg.arg in BUILTINS:
                    yield self.error(
                        arg,
                        message=self.argument_msg,
                        variable=arg.arg,
                    )
        else:
            for arg in statement.args.args:
                if isinstance(arg, ast.Name) and \
                        arg.id in BUILTINS:
                    yield self.error(
                        arg,
                        message=self.argument_msg,
                        variable=arg.id
                    )

    def check_for_loop(self, statement):
        stack = [statement.target]
        while stack:
            item = stack.pop()
            if isinstance(item, (ast.Tuple, ast.List)):
                stack.extend(list(item.elts))
            elif isinstance(item, ast.Attribute):
                if item.attr in BUILTINS:
                    yield self.error(statement, variable=item.attr)
            else:
                if item.id in BUILTINS:
                    yield self.error(statement, variable=item.id)

    def check_with(self, statement):
        if getattr(statement, 'optional_vars', None):
            var = statement.optional_vars
            if isinstance(var, ast.Tuple):
                for element in var.elts:
                    if element.id in BUILTINS:
                        yield self.error(statement, variable=element.id)

            elif var.id in BUILTINS:
                yield self.error(statement, variable=var.id)

        if getattr(statement, 'items', None):
            for item in statement.items:
                var = item.optional_vars
                if isinstance(var, ast.Tuple):
                    for element in var.elts:
                        if element.id in BUILTINS:
                            yield self.error(statement, variable=element.id)
                elif var and var.id in BUILTINS:
                    yield self.error(statement, variable=var.id)

    def check_exception(self, statement):
        exception_name = statement.name
        value = ''
        if isinstance(exception_name, ast.Name):
            value = exception_name.id
        elif isinstance(exception_name, str):  # Python +3.x
            value = exception_name

        if value in BUILTINS:
            yield self.error(statement, variable=value)

    def check_list_comprehension(self, statement):
        for generator in statement.generators:
            if isinstance(generator.target, ast.Name) \
                    and generator.target.id in BUILTINS:
                yield self.error(statement, variable=generator.target.id)

            elif isinstance(generator.target, ast.Tuple):
                for tuple_element in generator.target.elts:
                    if tuple_element.id in BUILTINS:
                        yield self.error(statement, variable=tuple_element.id)

    def check_import(self, statement):
        for name in statement.names:
            if name.asname in BUILTINS:
                yield self.error(statement, variable=name.asname)

    def check_class(self, statement):
        if statement.name in BUILTINS:
            yield self.error(statement, variable=statement.name)

    def error(
        self,
        statement,
        message=None,
        variable=None,
        line=None,
        column=None,
    ):
        if not message:
            message = self.assign_msg
        if not variable:
            column = statement.id
        if not line:
            line = statement.lineno
        if not column:
            column = statement.col_offset

        # column and line should be integers
        assert(isinstance(line, int_types))
        assert(isinstance(column, int_types))

        return (
            line,
            column,
            message.format(variable),
            type(self),
        )
