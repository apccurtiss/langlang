from jinja2 import Template

RUNTIME_TEMPLATE_FILE = 'runtime.js'


# Dunno' if this is a misnomer, as it's not assembly.
def assemble(ast):
    with open(RUNTIME_TEMPLATE_FILE) as f:
        output_template = Template(f.read())

    return output_template.render(
        help_url='github.com/apccurtiss/langlang',
        parsers=str(ast),
        exports='foo',
    )