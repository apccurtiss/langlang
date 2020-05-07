import os

from jinja2 import Template

RUNTIME_TEMPLATE_FILE = 'runtime.js'

current_dir = os.path.dirname(__file__)
runtime_template_filepath = os.path.join(current_dir, RUNTIME_TEMPLATE_FILE)


# Dunno' if this is a misnomer, as it's not assembly.
def assemble(ast):
    context = {
        'tokens': {}
    }
    # Statefully changes context
    parsers = ast.assemble(context)
    context['tokens']['__whitespace'] = r'/^(?:\s|\n)+/'

    with open(runtime_template_filepath) as f:
        output_template = Template(f.read())

    return output_template.render(
        help_url='github.com/apccurtiss/langlang',
        parsers=parsers,
        exports='\n'.join(
                f'exports.{name} = (input) => new Parser(input).__consume_all("{name}");' 
                for name in context['exports']),
        tokens='\n'.join(f'"{k}": {v},' for k, v in context['tokens'].items()),
    )