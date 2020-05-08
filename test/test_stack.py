import json
import os
import string
import subprocess
from typing import Dict
import unittest

from langlang.langlang import compile

from jinja2 import Template

FAILURE_OUTPUT_DIR = 'failed_tests'
TEST_RUNTIME = '''


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
        console.error(e);
        process.exit(1);
    }
});'''


class TestBasicPrograms(unittest.TestCase):
    def run_parser(self, name: str, source: str, tests: Dict[str, str], entrypoint='test'):
        parser = compile(source)
        filepath = ''.join(c for c in name.lower() if c in string.ascii_letters) + '.js'
        
        with open(filepath, 'w') as f:
            f.write(parser + TEST_RUNTIME)
        
        failures = {}
        for input, expected in tests.items():
            try:
                compiler = subprocess.Popen(
                    [
                        'node',
                        filepath
                    ],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)

                stdout, stderr = compiler.communicate(input.encode(), timeout=0.5)

                if expected == Exception:
                    self.assertNotEqual(compiler.returncode, 0, 'Parser should have returned non-zero')
                else:
                    self.assertEqual(compiler.returncode, 0, 'Parser should have returned 0')
                    if expected:
                        self.assertTrue(stdout, 'Parser failed to print anything')
                        stdout_json = json.loads(stdout)
                        for k, v in expected.items():
                            self.assertEqual(stdout_json.get(k), v)

            except subprocess.TimeoutExpired as e:
                failures[input] = (e, b'', b'')
            except Exception as e:
                failures[input] = (e, stdout, stderr)

        if failures:
            raise Exception(
                f'Failures for {len(failures)} inputs (see {filepath} for compiled parser):\n' +
                '\n'.join(
                    f'"{input}": {err}\n'
                    f'stdout:\n{stdout.decode()}\n'
                    f'stderr:\n{stderr.decode()}\n'
                    '\n==================\n' for input, (err, stdout, stderr) in failures.items()
                ))
        else:
            os.remove(filepath)

    def test_literals(self):
        self.run_parser(
            'Literal Parser',
            '''
            export test :: `foo`
            ''',
            {
                'foo': None,
                '  foo  ': None,
                '': Exception,
                'foobar': Exception,
                'foo bar': Exception,
            }
        )

    def test_regex(self):
        self.run_parser(
            'Regex Parser',
            '''
            export test :: r`fo+`
            ''', 
            {
                'fo': None,
                'foooooo': None,
                '  foooooo  ': None,
                '': Exception,
                'foobar': Exception,
                'foo bar': Exception,
            }
        )

    def test_debug(self):
        self.run_parser(
            'Debug',
            '''
            export test :: debug(`foo`)
            ''', 
            {
                'foo': {
                    'value': 'foo',
                },
                '  foo  ': {
                    'value': 'foo',
                },
                '': Exception,
                'foobar': Exception,
                'foo bar': Exception,
            }
        )

    def test_parser_names(self):
        self.run_parser(
            'Sequence Parser',
            '''
            export number :: r`\\d+`
            export test :: [`foo`: first] [`bar`: second]
            ''',
            {
                'foo bar': '',
                '    foo        bar    ': '',
                'foobar': '',
                'foo': Exception,
                'bar': Exception,
                'foo bar baz': Exception,
            }
        )

    def test_peek_parser(self):
        self.run_parser(
            'Peek Parser',
            '''
            export test :: peek {
                case `foo` => `foo` `bar`
                case `baz` => `baz` `bat`
            }
            ''',
            {
                ' foo bar ': '',
                ' baz bat ': '',
                ' foo ': Exception,
                ' baz ': Exception,
                ' foo bat ': Exception,
                ' baz bar ': Exception,
                ' foo baz ': Exception,
            }
        )

    # def test_template_parser(self):
    #     self.run_parser(
    #         'Template Parser',
    #         '''
    #         template Paren(expr) :: "(" expr ")"

    #         export test :: Paren("foo")
    #         ''',
    #         {
    #             '': Exception,
    #             'foo': Exception,
    #             '( )': Exception,
    #             ' ( foo ) ': '',
    #             ' ( foo ': Exception,
    #             ' foo ) ': Exception,
    #         }
    #     )

if __name__ == '__main__':
    unittest.main()