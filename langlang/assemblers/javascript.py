import copy
from dataclasses import dataclass
import enum
import os
import re
from typing import Any, Dict, Set, Tuple, Type, Union

from jinja2 import Template

from parsing import storage_methods
from parsing import types
from parsing import syntax_tree as ast

RUNTIME_DIR = '../runtimes'
MAIN_TEMPLATE_FILE = 'runtime.js'
STANDALONE_TEMPLATE_FILE = 'standalone_runtime.js'

current_dir = os.path.dirname(__file__)
runtime_template_filepath = os.path.join(current_dir, RUNTIME_DIR, MAIN_TEMPLATE_FILE)
standalone_template_filepath = os.path.join(current_dir, RUNTIME_DIR, STANDALONE_TEMPLATE_FILE)

INDENT_SIZE = '    '


class Context:
    def __init__(self):
        self.tokens = {}
        self.exports: Set[str] = set()

def assemble_into_js(node: ast.Node, ctx: Context, indent='') -> str:
    # Basic parsers
    if isinstance(node, ast.LiteralParser):
        # Replace with literal regex that does the same thing.
        token_name = f'lit_{node.value}'
        escaped_re = re.sub(r'([-/[\]{}()*+?.,\\^$|#\\s])', r'\\\1', node.value)
        as_re = f'/^{escaped_re}/'
        ctx.tokens[token_name] = as_re
        return f'{indent}{node.storage_method.as_prefix()}this.__require("{token_name}").value;'

    elif isinstance(node, ast.RegexParser):
        token_name = node.value.replace('"', '\\"')
        escaped_re = node.value.replace('/',  '\\/')
        as_re = f'/^{escaped_re}/'
        ctx.tokens[token_name] = as_re
        return f'{indent}{node.storage_method.as_prefix()}this.__require("{token_name}").value;'

    # Parser combinators
    elif isinstance(node, ast.Sequence):
        e1 = assemble_into_js(node.expr1, ctx, indent=indent)
        e2 = assemble_into_js(node.expr2, ctx, indent=indent)
        return f'{e1}\n{e2}'

    elif isinstance(node, ast.Peek):
        statements = ''
        for i, (cond_node, parser_node) in enumerate(node.cases, 1):
            indent_1 = indent + INDENT_SIZE

            # This won't happen in the default case.
            if cond_node:
                cond = assemble_into_js(cond_node, ctx, indent=indent_1 + INDENT_SIZE)
                parser = assemble_into_js(parser_node, ctx, indent=indent_1 + INDENT_SIZE)
                statement = (
                    f'{indent_1}function __test_case_{i}() {{\n'
                    f'{cond}\n'
                    f'{indent_1}}}\n'
                    f'{indent_1}if (this.__test(__test_case_{i})) {{\n'
                    f'{parser}\n'
                    f'{indent_1}}}\n')
            
            else:
                statement = assemble_into_js(parser_node, ctx, indent=indent_1)

            statements += statement
        
        return (
            f'{indent}{node.storage_method.as_prefix()}(function match() {{\n'
            f'{statements}\n'
            f'{indent}}}).call(this);\n'
        )

    # Language utilities
    elif isinstance(node, ast.Named):
        if node.storage_method is storage_methods.Ignore:
            suffix = ''
        else:
            suffix = f';\n{indent}{node.storage_method.as_prefix()}{node.name};'

        expr = assemble_into_js(node.expr, ctx, indent=indent)

        return f'{expr}{suffix}'

    elif isinstance(node, ast.As):
        parser = assemble_into_js(node.parser, ctx, indent=indent)
        result = assemble_into_js(node.result, ctx, indent=indent)

        return f'{parser}\n{result}'

    elif isinstance(node, ast.Error):
        indent1 = indent + INDENT_SIZE

        parser = assemble_into_js(node.parser, ctx, indent=indent1)

        return (
            f'{indent}try {{\n'
            f'{parser}\n'
            f'{indent}}} catch (e) {{\n'
            f'{indent1}throw Error({node.message})\n'
            f'{indent}}}'
        )

    elif isinstance(node, ast.Debug):
        if node.storage_method is storage_methods.Ignore:
            var_name = '__debug'
            suffix = ''
        elif node.storage_method is storage_methods.Return:
            var_name = 'ret'
            suffix = f'\n{indent}{node.storage_method.as_prefix()}ret;'
        elif isinstance(node.storage_method, storage_methods.Var):
            var_name = node.storage_method.name
            suffix = ''
        else:
            raise Exception('Unknown storage method')

        e = assemble_into_js(node.expr, ctx, indent=indent)
        return f'{e}\n{indent}console.log(JSON.stringify({var_name}));{suffix}'

    # Values
    elif isinstance(node, ast.Var):
        if isinstance(node.type, types.Parser):
            return f'{indent}{node.storage_method.as_prefix()}this.{node.name}();'
        else:
            return f'{indent}{node.storage_method.as_prefix()}{node.name};'


    elif isinstance(node, ast.Struct):
        indent1 = indent + INDENT_SIZE
        item_map = f',\n{indent1}'.join(f'"{key}": {value}' for key, value in node.map.items())
        if node.name:
            item_map += f',\n{indent1}"_type": "{node.name}"'

        return (
            f'{indent}{node.storage_method.as_prefix()}{{\n'
            f'{indent1}{item_map}\n'
            f'{indent}}}'
        )

    # File-level structures
    elif isinstance(node, ast.StatementSequence):
        return '\n'.join(assemble_into_js(s, ctx=ctx, indent=indent) for s in node.stmts)

    elif isinstance(node, ast.Def):
        if node.export:
            ctx.exports.add(node.name)

        assembled_js = assemble_into_js(node.expr, ctx, indent=indent + INDENT_SIZE)
        return (
            f'{indent}{node.name}() {{\n'
            f'{assembled_js}\n'
            f'{indent}}}'
        )
    
    else:
        raise Exception(f'Unknown AST node: {node}')


# Dunno' if this is a misnomer, as it's not assembly.
def assemble(ast, standalone_parser_entrypoint=None):
    context = Context()

    # Statefully changes context
    javascript = assemble_into_js(ast, context, indent=INDENT_SIZE)

    with open(runtime_template_filepath) as f:
        output_template = Template(f.read())

    output = output_template.render(
        help_url='github.com/apccurtiss/langlang',
        parsers=javascript,
        exports='\n'.join(
                f'exports.{name} = (input) => new Parser(input).__consume_all("{name}");' 
                for name in context.exports),
        tokens='\n'.join(f'        "{k}": {v},' for k, v in context.tokens.items()),
    )

    if standalone_parser_entrypoint:
        if standalone_parser_entrypoint not in context.exports:
            raise Exception(f'The parser "{standalone_parser_entrypoint}" is not exported.')

        with open(standalone_template_filepath) as f:
            standalone_template = Template(f.read())

        output += standalone_template.render(entrypoint=standalone_parser_entrypoint)

    return output