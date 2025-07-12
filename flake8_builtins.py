from flake8 import utils as stdin_utils
from pathlib import Path

import ast
import builtins
import inspect
import sys


class BuiltinsChecker:
    name = 'flake8_builtins'
    version = '1.5.2'
    assign_msg = 'A001 variable "{0}" is shadowing a Python builtin'
    argument_msg = 'A002 argument "{0}" is shadowing a Python builtin'
    class_attribute_msg = 'A003 class attribute "{0}" is shadowing a Python builtin'
    import_msg = 'A004 import statement "{0}" is shadowing a Python builtin'
    module_name_msg = 'A005 the module is shadowing a Python builtin module "{0}"'
    lambda_argument_msg = 'A006 lambda argument "{0}" is shadowing a Python builtin'

    default_line_number = 1
    default_column_offset = 1

    names = []
    ignore_list = {
        '__name__',
        '__doc__',
        'credits',
        '_',
    }
    ignored_module_names = set()

    def __init__(self, tree, filename):
        self.tree = tree
        self.filename = filename

    @classmethod
    def add_options(cls, option_manager):
        option_manager.add_option(
            '--builtins-ignorelist',
            metavar='builtins',
            parse_from_config=True,
            comma_separated_list=True,
            help='A comma separated list of builtins to skip checking',
        )
        option_manager.add_option(
            '--builtins-allowed-modules',
            metavar='builtins',
            parse_from_config=True,
            comma_separated_list=True,
            help='A comma separated list of builtin module names to allow',
        )

    @classmethod
    def parse_options(cls, options):
        if options.builtins_ignorelist is not None:
            cls.ignore_list.update(options.builtins_ignorelist)

        cls.names = {
            a[0] for a in inspect.getmembers(builtins) if a[0] not in cls.ignore_list
        }
        flake8_builtins = getattr(options, 'builtins', None)
        if flake8_builtins:
            cls.names.update(flake8_builtins)

        if options.builtins_allowed_modules is not None:
            cls.ignored_module_names.update(options.builtins_allowed_modules)

        if hasattr(sys, 'stdlib_module_names'):
            # stdlib_module_names is only available in Python 3.10+
            known_module_names = sys.stdlib_module_names
            cls.module_names = {
                m for m in known_module_names if m not in cls.ignored_module_names
            }
        else:
            cls.module_names = set()

    def run(self):
        tree = self.tree

        if self.filename == 'stdin':
            lines = stdin_utils.stdin_get_value()
            tree = ast.parse(lines)
        else:
            yield from self.check_module_name(self.filename)

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
            if isinstance(statement, (ast.Assign, ast.AnnAssign, ast.NamedExpr)):
                value = self.check_assignment(statement)

            elif isinstance(statement, function_nodes):
                value = self.check_function_definition(statement)

            elif isinstance(statement, ast.Lambda):
                value = self.check_lambda_definition(statement)

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
                yield from value

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
            elif isinstance(item, ast.Name) and item.id in self.names:
                yield self.error(item, message=msg, variable=item.id)
            elif isinstance(item, ast.Starred):
                if hasattr(item.value, 'id') and item.value.id in self.names:
                    yield self.error(
                        statement,
                        message=msg,
                        variable=item.value.id,
                    )
                elif hasattr(item.value, 'elts'):
                    stack.extend(list(item.value.elts))

    def check_function_definition(self, statement):
        if statement.name in self.names:
            msg = self.assign_msg
            if type(statement.__flake8_builtins_parent) is ast.ClassDef:
                msg = self.class_attribute_msg

            yield self.error(statement, message=msg, variable=statement.name)

        all_arguments = []
        all_arguments.extend(statement.args.args)
        all_arguments.extend(getattr(statement.args, 'kwonlyargs', []))
        all_arguments.extend(getattr(statement.args, 'posonlyargs', []))

        for arg in all_arguments:
            if isinstance(arg, ast.arg) and arg.arg in self.names:
                yield self.error(
                    arg,
                    message=self.argument_msg,
                    variable=arg.arg,
                )

    def check_lambda_definition(self, statement):
        all_arguments = []
        all_arguments.extend(statement.args.args)
        all_arguments.extend(getattr(statement.args, 'kwonlyargs', []))
        all_arguments.extend(getattr(statement.args, 'posonlyargs', []))

        for arg in all_arguments:
            if isinstance(arg, ast.arg) and arg.arg in self.names:
                yield self.error(
                    arg,
                    message=self.lambda_argument_msg,
                    variable=arg.arg,
                )

    def check_for_loop(self, statement):
        stack = [statement.target]
        while stack:
            item = stack.pop()
            if isinstance(item, (ast.Tuple, ast.List)):
                stack.extend(list(item.elts))
            elif isinstance(item, ast.Name) and item.id in self.names:
                yield self.error(statement, variable=item.id)
            elif isinstance(item, ast.Starred):
                if hasattr(item.value, 'id') and item.value.id in self.names:
                    yield self.error(
                        statement,
                        variable=item.value.id,
                    )
                elif hasattr(item.value, 'elts'):
                    stack.extend(list(item.value.elts))

    def check_with(self, statement):
        for item in statement.items:
            var = item.optional_vars
            if isinstance(var, (ast.Tuple, ast.List)):
                for element in var.elts:
                    if isinstance(element, ast.Name) and element.id in self.names:
                        yield self.error(statement, variable=element.id)
                    elif (
                        isinstance(element, ast.Starred)
                        and element.value.id in self.names
                    ):
                        yield self.error(
                            element,
                            variable=element.value.id,
                        )

            elif isinstance(var, ast.Name) and var.id in self.names:
                yield self.error(statement, variable=var.id)

    def check_exception(self, statement):
        exception_name = statement.name
        if exception_name is None:
            return

        if exception_name in self.names:
            yield self.error(statement, variable=exception_name)

    def check_comprehension(self, statement):
        for generator in statement.generators:
            if (
                isinstance(generator.target, ast.Name)
                and generator.target.id in self.names
            ):
                yield self.error(statement, variable=generator.target.id)

            elif isinstance(generator.target, (ast.Tuple, ast.List)):
                for tuple_element in generator.target.elts:
                    if (
                        isinstance(tuple_element, ast.Name)
                        and tuple_element.id in self.names
                    ):
                        yield self.error(statement, variable=tuple_element.id)

    def check_import(self, statement):
        for name in statement.names:
            collision = None
            if name.name in self.names and name.asname is None:
                collision = name.name
            elif name.asname in self.names:
                collision = name.asname
            if collision:
                yield self.error(
                    statement,
                    message=self.import_msg,
                    variable=collision,
                )

    def check_class(self, statement):
        if statement.name in self.names:
            yield self.error(statement, variable=statement.name)

    def error(self, statement=None, variable=None, message=None):
        if not message:
            message = self.assign_msg

        # lineno and col_offset must be integers
        return (
            statement.lineno if statement else self.default_line_number,
            statement.col_offset if statement else self.default_column_offset,
            message.format(variable),
            type(self),
        )

    def check_module_name(self, filename: str):
        if not self.module_names:
            return
        path = Path(filename)
        if path.name == '__init__.py':
            module_name = path.parent.name
        else:
            module_name = path.name.removesuffix('.py')
        if module_name in self.module_names:
            yield self.error(
                None,
                module_name,
                message=self.module_name_msg,
            )
