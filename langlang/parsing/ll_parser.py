import re
from typing import Any, Callable, Dict, Generic, List, NewType, Optional, Tuple, Type, TypeVar, Union

from . import syntax_tree as ast
from .tokenizer import tokenize, TokenStream

# In plain English - takes a list of tokens, returns a node
Parser = Callable[[TokenStream], Any]

# Parser combinators
def list_of(parser: Parser, minimum: int = 0, sep: Parser = None) -> Parser:
    def ret(tokens: TokenStream) -> List[ast.Node]:
        items: List[ast.Node] = []
        while True:
            backup = tokens.index
            try:
                # Statefully changes the index
                node = parser(tokens)
            except Exception as e:
                tokens.index = backup
                if len(items) < minimum:
                    raise Exception(f'Too few items. Last error: {e}')
                break
            items.append(node)


            if sep:
                backup = tokens.index
                try:
                    sep(tokens)
                except Exception as e:
                    tokens.index = backup
                    break
        return items

    return ret

def first_of(*parsers: Parser) -> Parser:
    def ret(tokens: TokenStream) -> ast.Node:
        err: Exception = None
        for parser in parsers:
            backup = tokens.index
            try:
                # Statefully changes the index
                return parser(tokens)
            except Exception as e:
                err = e
                tokens.index = backup

        raise err

    return ret

def optional(parser: Parser) -> Parser:
    def ret(tokens: TokenStream) -> Optional[ast.Node]:
        backup = tokens.index
        try:
            # Statefully changes the index
            return parser(tokens)
        except:
            tokens.index = backup
            return None

    return ret

def test(parser: Parser, cond: Callable[[Parser], str]) -> Parser:
    def ret(tokens: TokenStream):
        value = parser(tokens)
        if cond(value):
            return value
        else:
            raise Exception(f'Condition not met by value: {value}')

    return ret

def need(token: str) -> Parser:
    return lambda tokens: tokens.need(token)

def peek_type(token: str) -> Parser:
    return lambda tokens: tokens.peek_type(token)

def parse_literal_parser(tokens: TokenStream) -> ast.Node:
    parser = need('lit_parser')(tokens)
    value = parser.value[1:-1].replace('\\`', '`')
    return ast.LiteralParser(value=value)

def parse_regex_parser(tokens: TokenStream) -> ast.Node:
    parser = need('lit_regex')(tokens)
    value = parser.value[2:-1].replace('\\`', '`')
    return ast.RegexParser(value=value)

def parse_named_parser(tokens: TokenStream) -> ast.Node:
    need('obracket')(tokens)
    expr = parse_suffix(tokens)
    need('colon')(tokens)
    name = need('ident')(tokens)
    need('cbracket')(tokens)
    return ast.Named(expr=expr, name=name.value)

def parse_debug(tokens: TokenStream) -> ast.Node:
    need('kw_debug')(tokens)
    need('oparen')(tokens)
    expr = parse_suffix(tokens)
    need('cparen')(tokens)
    return ast.Debug(expr=expr)

def parse_peek(tokens: TokenStream) -> ast.Node:
    def parse_case(tokens: TokenStream) -> Tuple[Optional[ast.Node], ast.Node]:
        need('kw_case')(tokens)
        case = first_of(
            lambda tokens: need('under')(tokens) and None,
            parse_suffix)(tokens)
        need('arrow')(tokens)
        parser = parse_suffix(tokens)
        return (case, parser)

    need('kw_peek')(tokens)
    need('obrace')(tokens)
    cases = list_of(parse_case, minimum=1)(tokens)
    need('cbrace')(tokens)

    return ast.Peek(cases=cases)

# Order of operations, from least binding to most binding:
# 1. As expression (e.g. `foo` as "bar")
# 2. Sequence expression (e.g. `foo` `bar` `baz`)
# 3. Error expressions (e.g. `foo` ! "Fooerror!")
def parse_atom(tokens: TokenStream) -> ast.Node:
    return first_of(
        parse_literal_parser,
        parse_regex_parser,
        parse_var,
        parse_named_parser,
        parse_debug,
        parse_peek)(tokens)

def parse_error(tokens: TokenStream) -> ast.Node:
    def parse_error(tokens: TokenStream) -> str:
        need('bang')(tokens)
        return parse_string(tokens).value

    ret = parse_atom(tokens)

    error_message = optional(parse_error)(tokens)
    if error_message:
        ret = ast.Error(parser=ret, message=error_message)

    return ret

def parse_sequence(tokens: TokenStream) -> ast.Node:
    expr1 = parse_error(tokens)
    expr2 = optional(parse_sequence)(tokens)
    if expr2:
        return ast.Sequence(expr1=expr1, expr2=expr2)
    else:
        return expr1

def parse_suffix(tokens: TokenStream) -> ast.Node:
    def parse_as(tokens: TokenStream) -> ast.Node:
        need('kw_as')(tokens)
        return parse_value(tokens)

    ret = parse_sequence(tokens)

    result = optional(parse_as)(tokens)
    if result:
        ret = ast.As(parser=ret, result=result)

    return ret

def parse_parser(tokens: TokenStream) -> ast.Node:
    return parse_suffix(tokens)

def parse_def(tokens: TokenStream) -> ast.Node:
    if peek_type('kw_export')(tokens):
        export = tokens.next()
    else:
        export = None

    name = need('ident')(tokens).value
    need('doublecolon')(tokens)
    expr = parse_suffix(tokens)
    return ast.Def(name=name, expr=expr, export=export is not None)

def parse_statement(tokens: TokenStream) -> ast.Node:
    return first_of(parse_debug, parse_def)(tokens)

def parse_value(tokens: TokenStream) -> ast.Node:
    return first_of(parse_var, parse_struct, parse_string)(tokens)

def parse_var(tokens: TokenStream) -> ast.Node:
    backup = tokens.index
    name = need('ident')(tokens).value
    
    if peek_type('doublecolon')(tokens):
        tokens.index = backup
        raise Exception('Variables can\'t be followed by colons. That would be a definition.')

    return ast.Var(name=name)

def parse_struct(tokens: TokenStream) -> ast.Node:
    def parse_struct_entry(tokens: TokenStream) -> Tuple[str, str]:
        ident = need('ident')(tokens).value
        need('colon')(tokens)
        value = need('ident')(tokens).value
        return (ident, value)
    need('kw_struct')(tokens)
    name = optional(need('ident'))(tokens)
    if name:
        name = name.value
    need('obrace')(tokens)
    mapping = {k: v for k, v in list_of(parse_struct_entry, sep=need('comma'))(tokens)}
    need('cbrace')(tokens)
    return ast.Struct(name, mapping)

def parse_string(tokens: TokenStream) -> ast.LitStr:
    value = need('lit_string')(tokens).value
    return ast.LitStr(value=value)

def parse_file(tokens: TokenStream) -> ast.StatementSequence:
    stmts = list_of(parse_statement)(tokens)
    if not tokens.empty():
        # This should fail, but we're doing it for the error message.
        parse_statement(tokens)

    return ast.StatementSequence(stmts=stmts)

def parse(source: str) -> ast.Node:
    tokens = tokenize(source)
    return parse_file(tokens)