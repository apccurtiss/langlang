import unittest


import langlang_ast as ast
from langlang_tokenizer import tokenize
from langlang_parser import (
    parse_atom,
    parse_debug,
    parse_def,
    parse_file,
    parse_literal_parser,
    parse_named_parser,
    parse_parser,
    parse_peek,
    parse_regex_parser,
    parse_sequence,
    parse_string,
    parse_struct,
    parse_suffix,
    parse_value
)

class TestParser(unittest.TestCase):
    def test_parse_literal_parser(self):
        self.assertEqual(parse_literal_parser(tokenize(r'`foo`')).value, r'foo')
        self.assertEqual(parse_literal_parser(tokenize(r'`f\`oo`')).value, r'f`oo')
        self.assertRaises(Exception, parse_literal_parser, tokenize(r'foo'))
        self.assertRaises(Exception, parse_literal_parser, tokenize(r'"foo"'))
        self.assertRaises(Exception, parse_literal_parser, tokenize(r'r`foo`'))
        self.assertRaises(Exception, parse_literal_parser, tokenize(r''))

    def test_parse_regex(self):
        self.assertEqual(parse_regex_parser(tokenize(r'r`foo`')).value, r'foo')
        self.assertEqual(parse_regex_parser(tokenize(r'r`f\`oo`')).value, r'f`oo')
        self.assertRaises(Exception, parse_regex_parser, tokenize(r'`foo`'))
        self.assertRaises(Exception, parse_regex_parser, tokenize(r'"foo"'))
        self.assertRaises(Exception, parse_regex_parser, tokenize(r'foo'))
        self.assertRaises(Exception, parse_regex_parser, tokenize(r''))

    def test_parse_name(self):
        parse_named_parser(tokenize(r'[`foo`: bar]'))
        parse_named_parser(tokenize(r'[`foo` `bar` `baz`: bat]'))
        self.assertRaises(Exception, parse_named_parser, tokenize(r'[`foo`]'))
        self.assertRaises(Exception, parse_named_parser, tokenize(r'`foo`: bar'))

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

    def test_basic_suffixes(self):
        parse_suffix(tokenize(r'[`foo`: bar] as bar'))
        parse_suffix(tokenize(r'`foo` [`bar`: baz] `bat` as baz'))
        parse_suffix(tokenize(r'[`foo`: bar] ! "Something went wrong!"'))
        parse_suffix(tokenize(r'`foo` [`bar`: baz] `bat` ! "Something went wrong!"'))

    def test_parse_def(self):
        parse_def(tokenize(r'foo :: `bar` `baz`'))
        parse_def(tokenize(r'export foo :: `bar` `baz`'))

    def test_parse_parser(self):
        self.assertIsInstance(parse_parser(tokenize(r'`foo`')), ast.LiteralParser)
        self.assertIsInstance(parse_parser(tokenize(r'r`foo`')), ast.RegexParser)
        self.assertIsInstance(parse_parser(tokenize(r'foo')), ast.Var)
        self.assertIsInstance(parse_parser(tokenize(r'peek { case `foo` => `foo` }')), ast.Peek)
        self.assertIsInstance(parse_parser(tokenize(r'`foo` `bar`')), ast.Sequence)
        self.assertIsInstance(parse_parser(tokenize(r'`foo` as "bar"')), ast.As)
        self.assertIsInstance(parse_parser(tokenize(r'`foo` ! "Error!"')), ast.Error)

    def test_parse_peek(self):
        parse_peek(tokenize(r'peek { case `foo` => `bar` }'))
        parse_peek(tokenize(r'peek { case _ => `bar` }'))
        parse_peek(tokenize(r'''peek {
            case `foo` => `bar`
            case `baz` => `bat`
        }'''))
        parse_peek(tokenize(r'''peek {
            case `foo` => `bar`
            case _ => `bat`
        }'''))
        parse_peek(tokenize(r'''peek {
            case `foo` `bar` => `baz` `bat`
            case `baz` => peek {
                case `x` => `y`
            }
        }'''))

    def test_parse_struct(self):
        parse_struct(tokenize(r'struct { }'))
        parse_struct(tokenize(r'struct { foo : bar , baz : bat }'))
        parse_struct(tokenize(r'struct { foo : bar , baz : bat , }'))
        parse_struct(tokenize(r'struct Node { foo : bar , baz : bat }'))
        self.assertRaises(Exception, parse_struct, tokenize(r'struct { foo }'))

    def test_parse_string(self):
        parse_string(tokenize(r'"Hello world!"'))
        parse_string(tokenize(r'"And I said, \"What seems to be the problem officer?\""'))

    def test_parse_value(self):
        parse_value(tokenize(r'foo'))
        parse_value(tokenize(r'"I like cows!"'))
        parse_value(tokenize(r'struct { foo : bar }'))
        parse_value(tokenize(r'struct FooNode { value: foovalue }'))

    def test_as(self):
        parse_parser(tokenize(r'[`foo`: foovalue] as struct FooNode { value: foovalue }'))
        parse_file(tokenize(r'export test :: [`foo`: foovalue] as struct FooNode { value: foovalue }'))

    def test_parse_file(self):
        parse_file(tokenize(r'''
            num :: r`\d+`
            add :: num `+` num
            export expression :: add
        '''))

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