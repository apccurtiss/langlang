import json
import os
import subprocess
from typing import Dict
import unittest

from langlang import compile

from jinja2 import Template

TEMP_FILEPATH = 'tmp.js'
TEST_RUNTIME = Template('''


// ===============
// Test runtime
// ===============
process.stdin.setEncoding('utf8');

// I just want to say - Node IO is stupid.
process.stdin.on('readable', () => {
    let input = '';
    let chunk;
    while ((chunk = process.stdin.read()) !== null) {
        input += chunk;
    }
    try {
        exports.test(input);
        process.exit(0);
    }
    catch(e) {
        process.exit(1);
    }
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

                stdout, stderr = compiler.communicate(input.encode())

                if expected == Exception:
                    self.assertNotEqual(compiler.returncode, 0)
                else:
                    self.assertEqual(compiler.returncode, 0)
                    self.assertEqual(expected.encode(), stdout)

        finally:
            pass
            # os.remove(TEMP_FILEPATH)

    def test_literal_parser(self):
        self.run_parser(
            '''
            export test :: "foo"
            ''', 
            {
                'foo': '',
                '  foo  ': '',
                '': Exception,
                'foobar': Exception,
                'foo bar': Exception,
            }
        )

    # def test_regex_parser(self):
    #     self.run_parser(
    #         '''
    #         export test :: /fo+/
    #         ''', 
    #         {
    #             'fo': '',
    #             'foooooo': '',
    #             '  foooooo  ': '',
    #             '': Exception,
    #             'foobar': Exception,
    #             'foo bar': Exception,
    #         }
    #     )

    # def test_debug(self):
    #     self.run_parser(
    #         '''
    #         export test :: debug("foo")
    #         ''', 
    #         {
    #             'foo': 'foo',
    #             '  foo  ': '  foo  ',
    #             '': Exception,
    #             'foobar': Exception,
    #             'foo bar': Exception,
    #         }
    #     )

    # def test_sequence_parser(self):
    #     self.run_parser(
    #         '''
    #         export test :: "foo" "bar"
    #         ''',
    #         {
    #             'foo bar': '',
    #             '    foo        bar    ': '',
    #             'foo': Exception,
    #             'bar': Exception,
    #             'foobar': Exception,
    #             'foo bar baz': Exception,
    #         }
    #     )

    # def test_debug(self):
    #     pass

    # def test_template_parser(self):
    #     self.run_parser(
    #         '''
    #         template BinaryOperator(op, next) :: next:left op next:right

    #         Atom :: /\\d+/;
    #         Times :: BinaryOperator("*" | "/", Atom);
    #         Plus :: BinaryOperator("+" | "-", Times);
    #         export test :: Plus
    #         ''',
    #         {
    #             '': Exception,
    #             'foobar': Exception,
    #             '1': '',
    #             '1 + 2': '',
    #             '1 +': Exception,
    #             '+ 1': Exception,
    #             '1 + + 2': Exception,
    #             '1 * 2': '',
    #             '1 + 2 * 2': '',
    #             '1 + *': Exception,
    #             '1 + * 2': Exception,
    #             ' 1 + 2 * 3 * 4 * 5 ': '',
    #         }
    #     )
