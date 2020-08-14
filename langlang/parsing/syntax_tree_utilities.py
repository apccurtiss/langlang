import copy
from typing import Dict

from . import types
from . import syntax_tree as ast
from . import storage_methods as storage


def set_types_and_storage_methods(
    node: ast.Node,
    scope: Dict[str, ast.Node],
    storage_method: storage.StorageMethod):

    node.storage_method = storage_method

    if isinstance(node, ast.LiteralParser):
        node.type = types.String()

    elif isinstance(node, ast.RegexParser):
        node.type = types.String()

    elif isinstance(node, ast.Sequence):
        set_types_and_storage_methods(node.expr1, scope, storage.Ignore())
        set_types_and_storage_methods(node.expr2, scope, storage_method)
        node.type = node.expr2.type

    elif isinstance(node, ast.Peek):
        for (case_test, case_value) in node.cases:
            if case_test:
                set_types_and_storage_methods(case_test, scope, storage.Ignore())

            set_types_and_storage_methods(case_value, scope, storage_method)

            # TODO: Figure out type rules for cases
            node.type = case_value.type
        
    elif isinstance(node, ast.Named):
        set_types_and_storage_methods(node.expr, scope, storage.Var(node.name))
        node.type = node.expr.type

        if isinstance(node.type, types.Parser):
            # Naming a parser applies the name to the return value, not the parser itself.
            scope[node.name] = node.type.ret
        else:
            scope[node.name] = node.type

    elif isinstance(node, ast.As):
        set_types_and_storage_methods(node.parser, scope, storage.Ignore())
        set_types_and_storage_methods(node.result, scope, storage_method)
        node.type = node.result.type

    elif isinstance(node, ast.Error):
        set_types_and_storage_methods(node.parser, scope, storage_method)
        node.type = node.parser.type

    elif isinstance(node, ast.Debug):
        set_types_and_storage_methods(node.expr, scope, storage_method)
        node.type = node.expr.type

    elif isinstance(node, ast.Var):
        if node.name not in scope:
            raise Exception('Undefined variable: {}'.format(node.name))

        node.type = scope[node.name]

    elif isinstance(node, ast.Struct):
        node.type = types.Struct(node.map)

    elif isinstance(node, ast.StatementSequence):
        for stmt in node.stmts:
            set_types_and_storage_methods(stmt, scope, storage.Ignore())

        node.type = types.Null

    elif isinstance(node, ast.Def):
        # TODO: Figure out recursion
        inner_scope = copy.copy(scope)
        inner_scope[node.name] = types.Parser(...)
        set_types_and_storage_methods(node.expr, inner_scope, storage.Return())
        node.type = types.Parser(node.expr.type)
        scope[node.name] = node.type

    else:
        raise Exception('Unknown node: {}'.format(type(node)))


def set_additional_properties(ast: ast.Node):
    set_types_and_storage_methods(ast, {}, storage.Ignore())