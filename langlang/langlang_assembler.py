import os
import re
from typing import Any, Dict

from jinja2 import Template

from . import langlang_ast as ast

RUNTIME_TEMPLATE_FILE = 'runtime.js'

current_dir = os.path.dirname(__file__)
runtime_template_filepath = os.path.join(current_dir, RUNTIME_TEMPLATE_FILE)


def assemble_into_js(node: ast.Node, context: Dict[str, Any], indent='') -> str:
    # Basic parsers
    if isinstance(node, ast.LiteralParser):
        # Replace with literal regex that does the same thing.
        escaped_re = re.sub(r"[-[\]{}()*+?.,\\^$|#\\s]", r"\\\0", node.value)
        as_re = f'/^{escaped_re}/'
        context.setdefault('tokens', {})[node.value] = as_re
        return f'{indent}this.__require("{node.value}")'

    elif isinstance(node, ast.RegexParser):
        as_str = f'{node.value}'
        as_re = f'/^{node.value}/'
        context.setdefault('tokens', {})[as_str] = as_re
        return f'{indent}this.__require("{as_str}")'

    # Parser combinators
    elif isinstance(node, ast.Sequence):
        e1 = assemble_into_js(node.expr1, context=context, indent=indent)
        e2 = assemble_into_js(node.expr2, context=context, indent=indent)
        return (f'{e1}\n{e2}')

    # elif isinstance(node, ast.Match):
    #     for cond, parser in node.cases:
    #         cond = assemble_into_js(cond, context=context, indent='')
    #         parser = assemble_into_js(parser, context=context, indent='')
    #         statements = ';\n'.join(
    #             f'{indent}if (this.__test({cond})) {{\n'
    #             f'{indent}    return {parser};\n'
    #             f'{indent}}}'
            
    #     )
    #     return (f'{indent}(() => {{\n'
    #             f'{statements}'
    #             f'{indent}}})()')

    # Language   utilities
    elif isinstance(node, ast.Named):
        return f'{indent}let {node.name} = {assemble_into_js(node.expr, context=context, indent=indent)}'

    elif isinstance(node, ast.ParserExpr):
        if node.as_expr:
            return (f'{assemble_into_js(node.parser_expr, context=context, indent=indent)}\n'
                    f'{indent}return {assemble_into_js(node.as_expr, context=context, indent="")}\n')
        else:
            return f'{assemble_into_js(node.parser_expr, context=context, indent=indent)}\n'

    elif isinstance(node, ast.Debug):
        return f'{indent}console.log(JSON.stringify({assemble_into_js(node.expr, context=context, indent=indent)}))'

    # Expressions
    elif isinstance(node, ast.Var):
        if node.name not in context.setdefault('scope', set()):
            raise Exception(f'"{node.name}" is not defined!')
        return node.name

    # File-level structures
    elif isinstance(node, ast.StatementSequence):
        return '\n'.join(assemble_into_js(s, context=context, indent=indent) for s in node.stmts)

    elif isinstance(node, ast.Def):
        if node.export:
            context.setdefault('exports', set()).add(node.name)
        return (f'{indent}{node.name}() {{\n'
                f'{assemble_into_js(node.expr, context=context, indent=indent + "    ")}'
                f'{indent}}}')


# Dunno' if this is a misnomer, as it's not assembly.
def assemble(ast):
    context = {
        'tokens': {}
    }
    # Statefully changes context
    parsers = assemble_into_js(ast, context=context, indent='    ')
    context['tokens']['__whitespace'] = r'/^(?:\s|\n)+/'

    with open(runtime_template_filepath) as f:
        output_template = Template(f.read())

    return output_template.render(
        help_url='github.com/apccurtiss/langlang',
        parsers=parsers,
        exports='\n'.join(
                f'exports.{name} = (input) => new Parser(input).__consume_all("{name}");' 
                for name in context.get('exports', [])),
        tokens='\n'.join(f'        "{k}": {v},' for k, v in context['tokens'].items()),
    )