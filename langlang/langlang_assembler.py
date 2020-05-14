import copy
import enum
import os
import re
from typing import Any, Dict, Set, Tuple, Type, Union

from jinja2 import Template

import langlang_ast as ast

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

# Modes
class Mode(enum.Enum):
    parser = 1
    value = 2

class Context:
    def __init__(self):
        self.tokens = {}
        self.storage_method: Union[Type[Ignore], Type[Return], Var] = Ignore
        self.exports: Set[str] = set()
        self.scope: Set[str] = set()
        self.mode: Mode = Mode.parser
        

def assemble_into_js(node: ast.Node, ctx: Context, indent='') -> str:
    # Basic parsers
    if isinstance(node, ast.LiteralParser):
        # Replace with literal regex that does the same thing.
        token_name = f'lit_{node.value}'
        escaped_re = re.sub(r"([-/[\]{}()*+?.,\\^$|#\\s])", r"\\\1", node.value)
        as_re = f'/^{escaped_re}/'
        ctx.tokens[token_name] = as_re
        return f'{indent}{ctx.storage_method.as_prefix()}this.__require("{token_name}").value;'

    elif isinstance(node, ast.RegexParser):
        token_name = f're_{node.value}'
        escaped_re = node.value.replace('/', '\\/')
        as_re = f'/^{escaped_re}/'
        ctx.tokens[token_name] = as_re
        return f'{indent}{ctx.storage_method.as_prefix()}this.__require("{token_name}").value;'

    # Parser combinators
    elif isinstance(node, ast.Sequence):
        original_storage_method = ctx.storage_method
        ctx.storage_method = Ignore
        e1 = assemble_into_js(node.expr1, ctx, indent=indent)

        ctx.storage_method = original_storage_method
        e2 = assemble_into_js(node.expr2, ctx, indent=indent)
        return f'{e1}\n{e2}'

    elif isinstance(node, ast.Peek):
        original_storage_method = ctx.storage_method
        
        statements = ''
        for i, (cond_node, parser_node) in enumerate(node.cases, 1):
            indent_1 = indent + INDENT_SIZE

            # This won't happen in the default case.
            if cond_node:
                ctx.storage_method = Ignore
                cond = assemble_into_js(cond_node, ctx, indent=indent_1 + INDENT_SIZE)

            ctx.storage_method = original_storage_method
            parser = assemble_into_js(parser_node, ctx, indent=indent_1 + INDENT_SIZE)

            # Neither will this.
            if cond_node:
                statement = (
                    f'{indent_1}function __test_case_{i}() {{\n'
                    f'{cond}\n'
                    f'{indent_1}}}\n'
                    f'{indent_1}if (this.__test(__test_case_{i})) {{\n'
                    f'{parser}\n'
                    f'{indent_1}}}\n')
            
            else:
                statement = parser

            statements += statement
        
        return (f'{indent}{original_storage_method.as_prefix()}(function match() {{\n'
                f'{statements}'
                f'{indent}}}).call(this);\n')

    # Language utilities
    elif isinstance(node, ast.Named):
        if ctx.storage_method is Ignore:
            suffix = ''
        else:
            suffix = f'\n;{indent}{ctx.storage_method.as_prefix()}{node.name}'

        ctx.storage_method = Var(node.name)
        return f'{assemble_into_js(node.expr, ctx, indent=indent)}{suffix}'

    elif isinstance(node, ast.As):
        original_storage_method = ctx.storage_method

        ctx.storage_method = Ignore
        parser = assemble_into_js(node.parser, ctx, indent=indent)

        ctx.storage_method = original_storage_method
        ctx.mode = Mode.value
        result = assemble_into_js(node.result, ctx, indent=indent)
        ctx.mode = Mode.parser

        return f'{parser}\n{result}'

    elif isinstance(node, ast.Error):
        indent1 = indent + INDENT_SIZE

        parser = assemble_into_js(node.parser, ctx, indent=indent1)

        return (f'{indent}try {{\n'
                f'{parser}\n'
                f'{indent}}} catch (e) {{\n'
                f'{indent1}throw Error({node.message})\n'
                f'{indent}}}')

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

    # Values
    elif isinstance(node, ast.Var):
        if node.name not in ctx.scope:
            raise Exception(f'"{node.name}" is not defined!')

        if ctx.mode == Mode.parser:
            return f'{indent}{ctx.storage_method.as_prefix()}this.{node.name}()'
        elif ctx.mode == Mode.value:
            return f'{indent}{ctx.storage_method.as_prefix()}{node.name}'
        else:
            raise Exception(f'Unknown mode: "{ctx.mode}"')


    elif isinstance(node, ast.Struct):
        indent1 = indent + INDENT_SIZE
        item_map = f',\n{indent1}'.join(f'"{key}": {value}' for key, value in node.map.items())
        if node.name:
            item_map += f',\n{indent1}"_type": "{node.name}"'
        return (f'{indent}{ctx.storage_method.as_prefix()}{{\n'
                f'{indent1}{item_map}\n'
                f'{indent}}}')

    # File-level structures
    elif isinstance(node, ast.StatementSequence):
        return '\n'.join(assemble_into_js(s, ctx=ctx, indent=indent) for s in node.stmts)

    elif isinstance(node, ast.Def):
        if node.export:
            ctx.exports.add(node.name)
        ctx.scope.add(node.name)
        ctx.storage_method = Return
        return (f'{indent}{node.name}() {{\n'
                f'{assemble_into_js(node.expr, ctx, indent=indent + INDENT_SIZE)}\n'
                f'{indent}}}')
    
    else:
        raise Exception(f'Unknown AST node: {node}')


# Dunno' if this is a misnomer, as it's not assembly.
def assemble(ast):
    context = Context()

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