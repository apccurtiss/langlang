import os
import subprocess
import unittest
from typing import Dict

from langlang import compile

from jinja2 import Template

TEMP_FILEPATH = 'tmp.js'
TEST_RUNTIME = Template('''// Test runtime
process.stdin.setEncoding('utf8');

// I just want to say - Node IO is stupid.
process.stdin.on('readable', () => {
    let input = '';
    let chunk;
    while ((chunk = process.stdin.read()) !== null) {
        input += chunk;
    }
    {{ entrypoint }}(input)
});''')

class TestParser(unittest.TestCase):
    def run_parser(self, source: str, tests: Dict[str, str], entrypoint='test'):
        parser = compile(source)
        
        with open(TEMP_FILEPATH, 'w') as f:
            f.write(parser + TEST_RUNTIME.render(entrypoint=entrypoint))
        
        try:
            for input, expected in tests.items():
                compiler = subprocess.Popen(
                    [
                        'node',
                        TEMP_FILEPATH
                    ],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)

                stdout, _stderr = compiler.communicate(input.encode())

                if expected == Exception:
                    self.assertNotEqual(compiler.returncode, 0)
                else:
                    self.assertEqual(expected.encode(), stdout)

        finally:
            os.remove(TEMP_FILEPATH)

    def test_basic_parser(self):
        self.run_parser(
            '''
            export test :: "foo" "bar"
            ''',
            {
                'foo bar': '',
                '    foo        bar    ': '',
                'foo': Exception,
                'bar': Exception,
                'foobar': Exception,
                'foo bar baz': Exception,
            }
        )

    def test_template_parser(self):
        self.run_parser(
            '''
            template BinaryOperator(op, next) :: next:left op next:right

            Atom :: /\\d+/;
            Times :: BinaryOperator("*" | "/", Atom);
            Plus :: BinaryOperator("+" | "-", Times);
            export test :: Plus
            ''',
            {
                '': Exception,
                'foobar': Exception,
                '1': '',
                '1 + 2': '',
                '1 +': Exception,
                '+ 1': Exception,
                '1 + + 2': Exception,
                '1 * 2': '',
                '1 + 2 * 2': '',
                '1 + *': Exception,
                '1 + * 2': Exception,
                ' 1 + 2 * 3 * 4 * 5 ': '',
            }
        )
