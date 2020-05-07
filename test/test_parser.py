import unittest

from langlang import langlang_ast as ast
from langlang.langlang_tokenizer import tokenize
from langlang.langlang_parser import *

class TestParser(unittest.TestCase):
    def test_parse_string(self):
        self.assertEqual(parse_string(tokenize(r'`foo`')).value, r'foo')
        self.assertEqual(parse_string(tokenize(r'`f\`oo`')).value, r'f`oo')
        self.assertRaises(Exception, parse_string, tokenize(r'foo'))
        self.assertRaises(Exception, parse_string, tokenize(r''))

    def test_parse_regex(self):
        self.assertEqual(parse_regex(tokenize(r'r`foo`')).value, r'foo')
        self.assertEqual(parse_regex(tokenize(r'r`f\`oo`')).value, r'f`oo')
        self.assertRaises(Exception, parse_regex, tokenize(r'`foo`'))
        self.assertRaises(Exception, parse_regex, tokenize(r'foo'))
        self.assertRaises(Exception, parse_regex, tokenize(r''))

    def test_parse_name(self):
        parse_name(tokenize(r'[`foo`: bar]'))
        parse_name(tokenize(r'[`foo` `bar` `baz`: bat]'))
        self.assertRaises(Exception, parse_name, tokenize(r'[`foo`]'))
        self.assertRaises(Exception, parse_name, tokenize(r'`foo`: bar'))

    def test_parse_debug(self):
        parse_debug(tokenize(r'debug(`foo`)'))
        parse_debug(tokenize(r'debug(`foo` `bar` `baz`)'))

    def test_parse_atom(self):
        parse_atom(tokenize(r'`foo`'))
        parse_atom(tokenize(r'r`foo`'))
        parse_atom(tokenize(r'debug(`foo`)'))

    def test_parse_sequence(self):
        parse_sequence(tokenize(r'`foo` `bar`'))
        parse_sequence(tokenize(r'`foo` `bar` `baz` `bat`'))
        parse_sequence(tokenize(r'`foo` debug(`bar`) [r`baz`: x]  `bat`'))

    def test_as(self):
        parse_parser_expr(tokenize(r'[`foo`: bar] as bar'))
        parse_parser_expr(tokenize(r'`foo` [`bar`: baz] `bat` as baz'))

    def test_parse_def(self):
        parse_def(tokenize(r'foo :: `bar` `baz`'))
        parse_def(tokenize(r'export foo :: `bar` `baz`'))

    def test_parse_parser_expr(self):
        self.assertIsInstance(parse_parser_expr(tokenize(r'`foo` `bar`')).parser_expr, ast.Sequence)
        self.assertIsInstance(parse_parser_expr(tokenize(r'`foo`')).parser_expr, ast.LiteralParser)

    def test_parse_peek(self):
        parse_peek(tokenize(r'peek { case `foo` => `bar` }'))
        parse_peek(tokenize(r'''peek {
            case `foo` => `bar`
            case `baz` => `bat`
        }'''))
        parse_peek(tokenize(r'''peek {
            case `foo` `bar` => `baz` `bat`
            case `baz` => peek {
                case `x` => `y`
            }
        }'''))
        # self.assertRaises(Exception, parse_statement, tokenize(r''))

    # def test_parse_file(self):
    #     self.assertEqual(parse_file(tokenize(r'')), '')
    #     self.assertRaises(Exception, parse_file, tokenize(r''))

    # def test_basic_def(self):
    #     parse(tokenize('export example :: `foo`'))
    #     parse(tokenize('export example :: r`foo`'))

    # def test_multi_parser(self):
    #     parse(tokenize('export a :: `foo`'
    #           'export b :: a'
    #           'export c :: b'))

    # def test_sequence_parser(self):
    #     parse(tokenize('export test :: debug(`foo`)'))

    # def test_parser_names(self):
    #     parse(tokenize('export test :: ["foo": first] ["bar": second]'))