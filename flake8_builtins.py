# -*- coding: utf-8 -*-
import ast
import inspect
import sys


try:
    from flake8.engine import pep8 as stdin_utils
except ImportError:
    from flake8 import utils as stdin_utils


WHITE_LIST = {
    '__name__',
    '__doc__',
    'credits',
    '_',
}


if sys.version_info >= (3, 0):
    import builtins
    BUILTINS = [
        a[0]
        for a in inspect.getmembers(builtins)
        if a[0] not in WHITE_LIST
    ]
    PY3 = True
else:
    import __builtin__
    BUILTINS = [
        a[0]
        for a in inspect.getmembers(__builtin__)
        if a[0] not in WHITE_LIST
    ]
    PY3 = False

if sys.version_info >= (3, 6):
    AnnAssign = ast.AnnAssign
else:  # There was no `AnnAssign` before python3.6
    AnnAssign = type('AnnAssign', (ast.AST, ), {})

if sys.version_info >= (3, 8):
    NamedExpr = ast.NamedExpr
else:  # There was no walrus operator before python3.8
    NamedExpr = type('NamedExpr', (ast.AST, ), {})


class BuiltinsChecker(object):
    name = 'flake8_builtins'
    version = '1.5.2'
    assign_msg = 'A001 variable "{0}" is shadowing a python builtin'
    argument_msg = 'A002 argument "{0}" is shadowing a python builtin'
    class_attribute_msg = 'A003 class attribute "{0}" is shadowing a python builtin'

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

        comprehension_nodes = (
            ast.ListComp,
            ast.SetComp,
            ast.DictComp,
            ast.GeneratorExp,
        )

        value = None
        for statement in ast.walk(tree):
            if isinstance(statement, (ast.Assign, AnnAssign, NamedExpr)):
                value = self.check_assignment(statement)

            elif isinstance(statement, function_nodes):
                value = self.check_function_definition(statement)

            elif isinstance(statement, for_nodes):
                value = self.check_for_loop(statement)

            elif isinstance(statement, with_nodes):
                value = self.check_with(statement)

            elif isinstance(statement, ast.excepthandler):
                value = self.check_exception(statement)

            elif isinstance(statement, comprehension_nodes):
                value = self.check_comprehension(statement)

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

        if isinstance(statement, ast.Assign):
            stack = list(statement.targets)
        else:  # This is `ast.AnnAssign` or `ast.NamedExpr`:
            stack = [statement.target]

        while stack:
            item = stack.pop()
            if isinstance(item, (ast.Tuple, ast.List)):
                stack.extend(list(item.elts))
            elif isinstance(item, ast.Name) and \
                    item.id in BUILTINS:
                yield self.error(item, message=msg, variable=item.id)
            elif PY3 and isinstance(item, ast.Starred):
                if hasattr(item.value, 'id') and item.value.id in BUILTINS:
                    yield self.error(
                        statement,
                        message=msg,
                        variable=item.value.id,
                    )
                elif hasattr(item.value, 'elts'):
                    stack.extend(list(item.value.elts))

    def check_function_definition(self, statement):
        if statement.name in BUILTINS:
            msg = self.assign_msg
            if type(statement.__flake8_builtins_parent) is ast.ClassDef:
                msg = self.class_attribute_msg

            yield self.error(statement, message=msg, variable=statement.name)

        if PY3:
            all_arguments = []
            all_arguments.extend(statement.args.args)
            all_arguments.extend(getattr(statement.args, 'kwonlyargs', []))
            all_arguments.extend(getattr(statement.args, 'posonlyargs', []))

            for arg in all_arguments:
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
                    yield self.error(arg, message=self.argument_msg)

    def check_for_loop(self, statement):
        stack = [statement.target]
        while stack:
            item = stack.pop()
            if isinstance(item, (ast.Tuple, ast.List)):
                stack.extend(list(item.elts))
            elif isinstance(item, ast.Name) and \
                    item.id in BUILTINS:
                yield self.error(statement, variable=item.id)
            elif PY3 and isinstance(item, ast.Starred):
                if hasattr(item.value, 'id') and item.value.id in BUILTINS:
                    yield self.error(
                        statement,
                        variable=item.value.id,
                    )
                elif hasattr(item.value, 'elts'):
                    stack.extend(list(item.value.elts))

    def check_with(self, statement):
        if not PY3:
            var = statement.optional_vars
            if isinstance(var, (ast.Tuple, ast.List)):
                for element in var.elts:
                    if isinstance(element, ast.Name) and \
                            element.id in BUILTINS:
                        yield self.error(statement, variable=element.id)

            elif isinstance(var, ast.Name) and var.id in BUILTINS:
                yield self.error(statement, variable=var.id)
        else:
            for item in statement.items:
                var = item.optional_vars
                if isinstance(var, (ast.Tuple, ast.List)):
                    for element in var.elts:
                        if isinstance(element, ast.Name) and \
                                element.id in BUILTINS:
                            yield self.error(statement, variable=element.id)
                        elif isinstance(element, ast.Starred) and \
                                element.value.id in BUILTINS:
                            yield self.error(
                                element,
                                variable=element.value.id,
                            )

                elif isinstance(var, ast.Name) and var.id in BUILTINS:
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

    def check_comprehension(self, statement):
        for generator in statement.generators:
            if isinstance(generator.target, ast.Name) \
                    and generator.target.id in BUILTINS:
                yield self.error(statement, variable=generator.target.id)

            elif isinstance(generator.target, (ast.Tuple, ast.List)):
                for tuple_element in generator.target.elts:
                    if isinstance(tuple_element, ast.Name) and \
                            tuple_element.id in BUILTINS:
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
            variable = statement.id
        if not line:
            line = statement.lineno
        if not column:
            column = statement.col_offset

        return (
            line,
            column,
            message.format(variable),
            type(self),
        )
