import ast
import builtins
import inspect
import sys

from flake8 import utils as stdin_utils

IGNORE_LIST = {
    '__name__',
    '__doc__',
    'credits',
    '_',
}


# Will be initialized in `BuiltinsChecker.parse_options`
BUILTINS = None

if sys.version_info >= (3, 8):
    NamedExpr = ast.NamedExpr
else:  # There was no walrus operator before python3.8
    NamedExpr = type('NamedExpr', (ast.AST,), {})


class BuiltinsChecker:
    name = 'flake8_builtins'
    version = '1.5.2'
    assign_msg = 'A001 variable "{0}" is shadowing a python builtin'
    argument_msg = 'A002 argument "{0}" is shadowing a python builtin'
    class_attribute_msg = 'A003 class attribute "{0}" is shadowing a python builtin'

    def __init__(self, tree, filename):
        self.tree = tree
        self.filename = filename

    def add_options(option_manager):
        option_manager.add_option(
            '--builtins-ignorelist',
            metavar='builtins',
            parse_from_config=True,
            comma_separated_list=True,
            help='A comma separated list of builtins to skip checking',
        )

    def parse_options(option_manager, options, args):
        global BUILTINS

        if options.builtins_ignorelist is not None:
            IGNORE_LIST.update(options.builtins_ignorelist)

        BUILTINS = [
            a[0] for a in inspect.getmembers(builtins) if a[0] not in IGNORE_LIST
        ]

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
            if isinstance(statement, (ast.Assign, ast.AnnAssign, NamedExpr)):
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
            elif isinstance(item, ast.Name) and item.id in BUILTINS:
                yield self.error(item, message=msg, variable=item.id)
            elif isinstance(item, ast.Starred):
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

        all_arguments = []
        all_arguments.extend(statement.args.args)
        all_arguments.extend(getattr(statement.args, 'kwonlyargs', []))
        all_arguments.extend(getattr(statement.args, 'posonlyargs', []))

        for arg in all_arguments:
            if isinstance(arg, ast.arg) and arg.arg in BUILTINS:
                yield self.error(
                    arg,
                    message=self.argument_msg,
                    variable=arg.arg,
                )

    def check_for_loop(self, statement):
        stack = [statement.target]
        while stack:
            item = stack.pop()
            if isinstance(item, (ast.Tuple, ast.List)):
                stack.extend(list(item.elts))
            elif isinstance(item, ast.Name) and item.id in BUILTINS:
                yield self.error(statement, variable=item.id)
            elif isinstance(item, ast.Starred):
                if hasattr(item.value, 'id') and item.value.id in BUILTINS:
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
                    if isinstance(element, ast.Name) and element.id in BUILTINS:
                        yield self.error(statement, variable=element.id)
                    elif (
                        isinstance(element, ast.Starred)
                        and element.value.id in BUILTINS
                    ):
                        yield self.error(
                            element,
                            variable=element.value.id,
                        )

            elif isinstance(var, ast.Name) and var.id in BUILTINS:
                yield self.error(statement, variable=var.id)

    def check_exception(self, statement):
        exception_name = statement.name
        if exception_name is None:
            return

        if exception_name in BUILTINS:
            yield self.error(statement, variable=exception_name)

    def check_comprehension(self, statement):
        for generator in statement.generators:
            if (
                isinstance(generator.target, ast.Name)
                and generator.target.id in BUILTINS
            ):
                yield self.error(statement, variable=generator.target.id)

            elif isinstance(generator.target, (ast.Tuple, ast.List)):
                for tuple_element in generator.target.elts:
                    if (
                        isinstance(tuple_element, ast.Name)
                        and tuple_element.id in BUILTINS
                    ):
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
