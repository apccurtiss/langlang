import copy
import os
import re
from typing import Any, Dict, Set, Tuple, Type, Union

from jinja2 import Template

from . import langlang_ast as ast

RUNTIME_TEMPLATE_FILE = 'runtime.js'
INDENT_SIZE = '    '

current_dir = os.path.dirname(__file__)
runtime_template_filepath = os.path.join(current_dir, RUNTIME_TEMPLATE_FILE)


# Result storage methods
class Ignore:
    @classmethod
    def as_prefix(self):
        return f''

class Return:
    @classmethod
    def as_prefix(self):
        return 'return '

class Var:
    def __init__(self, name):
        self.name = name
    
    def as_prefix(self):
        return f'let {self.name} = '

class Context:
    def __init__(self):
        self.tokens = {
            '__whitespace': r'/^(?:\s|\n)+/'
        }
        self.storage_method: Union[Type[Ignore], Type[Return], Var] = Ignore
        self.exports: Set[str] = set()
        self.scope: Set[str] = set()
        

def assemble_into_js(node: ast.Node, ctx: Context, indent='') -> str:
    # Basic parsers
    if isinstance(node, ast.LiteralParser):
        # Replace with literal regex that does the same thing.
        escaped_re = re.sub(r"[-[\]{}()*+?.,\\^$|#\\s]", r"\\\0", node.value)
        as_re = f'/^{escaped_re}/'
        ctx.tokens[node.value] = as_re
        return f'{indent}{ctx.storage_method.as_prefix()}runtime.__require("{node.value}");'

    elif isinstance(node, ast.RegexParser):
        as_str = f'{node.value}'
        as_re = f'/^{node.value}/'
        ctx.tokens[as_str] = as_re
        return f'{indent}{ctx.storage_method.as_prefix()}runtime.__require("{as_str}");'

    # Parser combinators
    elif isinstance(node, ast.Sequence):
        original_storage_method = ctx.storage_method
        ctx.storage_method = Ignore
        e1 = assemble_into_js(node.expr1, ctx, indent=indent)

        ctx.storage_method = original_storage_method
        e2 = assemble_into_js(node.expr2, ctx, indent=indent)
        return f'{e1}\n{e2}'

    elif isinstance(node, ast.Match):
        original_storage_method = ctx.storage_method
        
        statements = ''
        for i, (cond_node, parser_node) in enumerate(node.cases, 1):
            indent_1 = indent + INDENT_SIZE

            ctx.storage_method = Ignore
            cond = assemble_into_js(cond_node, ctx, indent=indent_1 + INDENT_SIZE)
            ctx.storage_method = Return
            parser = assemble_into_js(parser_node, ctx, indent=indent_1 + INDENT_SIZE)
            statement = (
                f'{indent_1}function __test_case_{i}() {{\n'
                f'{cond}\n'
                f'{indent_1}}}\n'
                f'{indent_1}if (runtime.__test(__test_case_{i})) {{\n'
                f'{parser}\n'
                f'{indent_1}}}\n')
            
            statements += statement
        
        return (f'{indent}{original_storage_method.as_prefix()}(function match() {{\n'
                f'{statements}'
                f'{indent}}})();\n')

    # Language utilities
    elif isinstance(node, ast.Named):
        if ctx.storage_method is Ignore:
            suffix = ''
        else:
            suffix = f'\n;{indent}{ctx.storage_method.as_prefix()}{node.name}'

        ctx.storage_method = Var(node.name)
        return f'{assemble_into_js(node.expr, ctx, indent=indent)}{suffix}'

    elif isinstance(node, ast.ParserExpr):
        if node.as_expr:
            original_storage_method = ctx.storage_method
            ctx.storage_method = Ignore
            parser_expr = assemble_into_js(node.parser_expr, ctx, indent=indent)
            ctx.storage_method = original_storage_method
            as_expr = assemble_into_js(node.as_expr, ctx, indent=indent)
            return f'{parser_expr}\n{as_expr}'
        else:
            return assemble_into_js(node.parser_expr, ctx, indent=indent)

    elif isinstance(node, ast.Debug):
        if ctx.storage_method is Ignore:
            var_name = '__debug'
            suffix = ''
        elif ctx.storage_method is Return:
            var_name = 'ret'
            suffix = f'\n{indent}{ctx.storage_method.as_prefix()}ret;'
        elif isinstance(ctx.storage_method, Var):
            var_name = ctx.storage_method.name
            suffix = ''
        else:
            raise Exception('Unknown storage method')

        ctx.storage_method = Var(var_name)
        e = assemble_into_js(node.expr, ctx, indent=indent)
        return f'{e}\n{indent}console.log(JSON.stringify({var_name}));{suffix}'

    # Expressions
    elif isinstance(node, ast.Var):
        if node.name not in ctx.scope:
            raise Exception(f'"{node.name}" is not defined!')
        return node.name

    # File-level structures
    elif isinstance(node, ast.StatementSequence):
        return '\n'.join(assemble_into_js(s, ctx=ctx, indent=indent) for s in node.stmts)

    elif isinstance(node, ast.Def):
        if node.export:
            ctx.exports.add(node.name)
        ctx.storage_method = Return
        return (f'{indent}{node.name}() {{\n'
                f'{indent}let runtime = this;\n'
                f'{assemble_into_js(node.expr, ctx, indent=indent + INDENT_SIZE)}'
                f'{indent}}}')
    
    else:
        raise Exception(f'Unknown AST node: {node}')


# Dunno' if this is a misnomer, as it's not assembly.
def assemble(ast):
    context = Context()
    print(context.tokens)

    # Statefully changes context
    parsers = assemble_into_js(ast, context, indent=INDENT_SIZE)

    with open(runtime_template_filepath) as f:
        output_template = Template(f.read())

    return output_template.render(
        help_url='github.com/apccurtiss/langlang',
        parsers=parsers,
        exports='\n'.join(
                f'exports.{name} = (input) => new Parser(input).__consume_all("{name}");' 
                for name in context.exports),
        tokens='\n'.join(f'        "{k}": {v},' for k, v in context.tokens.items()),
    )