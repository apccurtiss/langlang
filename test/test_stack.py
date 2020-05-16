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
        console.log(JSON.stringify({
            output: exports.test(input)
        }));
        process.exit(0);
    }
    catch(e) {
        console.error(e.message);
        process.exit(1);
    }
});'''


class TestBasicPrograms(unittest.TestCase):
    def run_parser(self, name: str, source: str, tests: Dict[str, str], entrypoint='test'):
        parser = compile(source, None)
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

                stdout, stderr = compiler.communicate(input.encode(), timeout=1)

                if expected == Exception:
                    self.assertNotEqual(compiler.returncode, 0, 'Parser should have returned non-zero')
                elif isinstance(expected, Exception):
                    self.assertEqual(stderr.decode().rstrip('\n'), str(expected))
                else:
                    self.assertEqual(compiler.returncode, 0, 'Parser should have returned 0')
                    def are_equal(value1, value2):
                        if type(value1) != type(value2):
                            return False

                        if isinstance(value1, list):
                            return all(are_equal(e1, e2) for e1, e2 in zip(value1, value2))
                        elif isinstance(value1, dict):
                            return all(are_equal(value1[k], v) for k, v in value2.items())
                        else:
                            return value1 == value2

                    if expected:
                        decoded_stdout = json.loads(stdout)['output']
                        self.assertTrue(are_equal(decoded_stdout, expected), f'{decoded_stdout} != {expected}')

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
                'foo': 'foo',
                '  foo  ': 'foo',
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
                'fo': 'fo',
                'foooooo': 'foooooo',
                '  foooooo  ': 'foooooo',
                '': Exception,
                'foobar': Exception,
                'foo bar': Exception,
            }
        )

    def test_sequence(self):
        self.run_parser(
            'Complex tokens',
            '''
            export test :: `foo` `bar`
            ''',
            {
                'foo bar': 'bar',
                'foo': Exception,
                'bar': Exception,
            }
        )

    def test_complex_tokens(self):
        self.run_parser(
            'Complex tokens',
            '''
            ops :: `+` `*` `?` `^` `$`
            braces :: `[` `]` `(` `)` `{` `}`
            export test :: `i+` r`i+`
            ''',
            {
                'i+ i': 'i',
                'i+ iiiiii': 'iiiiii',
                'i i': Exception,
            }
        )

    # def test_debug(self):
    #     self.run_parser(
    #         'Debug',
    #         '''
    #         export test :: debug(`foo`)
    #         ''', 
    #         {
    #             'foo': {
    #                 'value': 'foo',
    #             },
    #             '  foo  ': {
    #                 'value': 'foo',
    #             },
    #             '': Exception,
    #             'foobar': Exception,
    #             'foo bar': Exception,
    #         }
    #     )

    def test_parser_names(self):
        self.run_parser(
            'Named Parsers',
            '''
            export test :: [`foo`: first] [`bar`: second]
            ''',
            {
                'foo bar': 'bar',
                '    foo        bar    ': 'bar',
                'foobar': 'bar',
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
                case _ => `default`
            }
            ''',
            {
                ' foo bar ': 'bar',
                ' baz bat ': 'bat',
                ' default ': 'default',
                ' foo ': Exception,
                ' foo default ': Exception,
                ' baz ': Exception,
                ' foo bat ': Exception,
                ' baz bar ': Exception,
                ' foo baz ': Exception,
            }
        )

    def test_nested_peek_parsers(self):
        self.run_parser(
            'Peek Parser',
            '''
            export test :: peek {
                case `foo` => `foo` peek {
                    case `bar` => `bar` `baz`
                }
                case `x` => `x` peek {
                    case `y` => `y` `z`
                }
            }
            ''',
            {
                ' foo bar baz ': 'baz',
                ' x y z ': 'z',
                ' foo y z ': Exception,
                ' bar baz ': Exception,
                ' x y ': Exception,
            }
        )

    def test_basic_exceptions(self):
        self.run_parser(
            'Value Parser',
            '''
            export test :: `foo` `bar` `baz` ! "Fooerror!"
            ''',
            {
                'foo bar baz': 'baz',
                'foo bar bar': Exception('Fooerror!'),
                'foo bar quux': Exception('Fooerror!'),
            }
        )

    def test_multiple_exceptions(self):
        self.run_parser(
            'Value Parser',
            '''
            export test :: `foo` ! "Fooerror!"
                           `bar` ! "Barerror!"
                           `baz` ! "Bazerror!"
            ''',
            {
                'foo bar baz': 'baz',
                'x bar baz': Exception('Fooerror!'),
                'foo x baz': Exception('Barerror!'),
                'foo bar x': Exception('Bazerror!'),
                'x x x': Exception('Fooerror!'),
            }
        )

    def test_values(self):
        self.run_parser(
            'Value Parser',
            '''
            export test :: [`foo`: foovalue]
                as struct FooNode { value: foovalue }
            ''',
            {
                'foo': {
                    '_type': 'FooNode',
                    'value': 'foo'
                }
            }
        )

    def test_multi_parsers(self):
        self.run_parser(
            'Value Parser',
            '''
            num :: r`\\d+`
            add :: num `+` num 
            export test :: add
            ''',
            {
                '1 + 2': '2'
            }
        )

    def test_basic_fraciton_parser(self):
        self.run_parser(
            'Value Parser',
            '''
            integer :: r`\\d+`
            export test :: [integer: num] `/` [integer: den]
                as struct Node { numerator: num, denominator: den }
            ''',
            {
                '123 / 456': {
                    '_type': 'Node',
                    'numerator': '123',
                    'denominator': '456'
                }
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