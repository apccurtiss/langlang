from jinja2 import Template

RUNTIME_TEMPLATE_FILE = 'runtime.js'


# Dunno' if this is a misnomer, as it's not assembly.
def assemble(ast):
    context = {}
    # Statefully changes context
    parsers = ast.assemble(context)
    context['tokens']['__whitespace'] = r'/^(?:\s|\n)+/'

    with open(RUNTIME_TEMPLATE_FILE) as f:
        output_template = Template(f.read())

    return output_template.render(
        help_url='github.com/apccurtiss/langlang',
        parsers=parsers,
        exports='\n'.join(
                f'exports.{name} = (input) => new Parser(input).__consume_all("{name}");' 
                for name in context['exports']),
        tokens='\n'.join(f'"{k}": {v},' for k, v in context['tokens'].items()),
    )