from langlang_tokenizer import tokenize
from langlang_parser import (
    parse_string,
    parse_regex,
    parse_name,
    parse_debug,
    parse_atom,
    parse_match,
    parse_sequence,
    parse_expr,
    parse_def,
    parse_statement,
    parse_file,
    parse)
import unittest

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

    def test_parse_debug(self):
        parse_debug(tokenize(r'debug(`foo`)'))

    def test_parse_atom(self):
        parse_atom(tokenize(r'`foo`'))
        parse_atom(tokenize(r'r`foo`'))
        parse_atom(tokenize(r'debug(`foo`)'))

    def test_parse_sequence(self):
        parse_sequence(tokenize(r'`foo` `bar`'))
        parse_sequence(tokenize(r'`foo` `bar` `baz` `bat`'))

    # def test_parse_expr(self):
    #     self.assertEqual(parse_expr(tokenize(r'')), '')
    #     self.assertRaises(Exception, parse_expr, tokenize(r''))

    def test_parse_def(self):
        parse_def(tokenize(r'foo :: `bar`'))
        parse_def(tokenize(r'export foo :: `bar`'))

    # def test_parse_statement(self):
    #     self.assertEqual(parse_statement(tokenize(r'')), '')
    #     self.assertRaises(Exception, parse_statement, tokenize(r''))

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