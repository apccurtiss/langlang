from . import types
from . import syntax_tree as ast
from . import storage_methods as storage


def set_types_and_storage_methods(node: ast.Node, storage_method: storage.StorageMethod):
    if isinstance(node, ast.LiteralParser):
        node.type = types.String()

    elif isinstance(node, ast.RegexParser):
        node.type = types.String()

    elif isinstance(node, ast.Sequence):
        set_types_and_storage_methods(node.expr1, storage.Ignore())
        set_types_and_storage_methods(node.expr2, storage_method)
        node.type = node.expr2.type

    elif isinstance(node, ast.Peek):
        node.type = None
        for (case_test, case_value) in node.cases:
            if case_test:
                set_types_and_storage_methods(case_test, storage.Ignore())

            set_types_and_storage_methods(case_value, storage_method)

            if not node.type:
                node.type = case_value.type
            
            if node.type != case_value.type:
                # TODO: Better errors
                raise Exception('Type error: Peek cases have different types.')
        
    elif isinstance(node, ast.Named):
        set_types_and_storage_methods(node.expr, storage_method)
        node.type = node.expr.type

    elif isinstance(node, ast.As):
        set_types_and_storage_methods(node.parser, storage.Ignore())
        set_types_and_storage_methods(node.result, storage_method)
        node.type = node.result.type

    elif isinstance(node, ast.Error):
        set_types_and_storage_methods(node.parser, storage_method)
        node.type = node.parser.type

    elif isinstance(node, ast.Debug):
        set_types_and_storage_methods(node.expr, storage_method)
        node.type = node.expr.type

    elif isinstance(node, ast.Var):
        raise ...

    elif isinstance(node, ast.Struct):
        raise ...

    elif isinstance(node, ast.StatementSequence):
        for stmt in node.stmts:
            set_types_and_storage_methods(stmt, storage.Ignore())

    elif isinstance(node, ast.Def):
        set_types_and_storage_methods(node.expr, storage.Return())

    else:
        raise Exception('Unknown node: {}'.format(type(node)))

    node.storage_method = storage_method
    return node

def fill_out_tree(ast: ast.Node):
    set_types_and_storage_methods(ast, storage.Ignore())