import re
from typing import Any, Callable, Dict, Generic, List, NewType, Optional, Tuple, Type, TypeVar, Union

from . import langlang_ast as ast
from .langlang_tokenizer import TokenStream

# In plain English - takes a list of tokens, returns a node
Parser = Callable[[TokenStream], Any]

# Parser combinators
def list_of(parser: Parser, min: int = 0) -> Parser:
    def ret(tokens: TokenStream) -> List[ast.Node]:
        items: List[ast.Node] = []
        while True:
            backup = tokens.index
            try:
                # Statefully changes the index
                node = parser(tokens)
            except Exception as e:
                tokens.index = backup
                if len(items) < min:
                    raise Exception(f'Too few items. Last error: {e}')
                break
            items.append(node)
        return items

    return ret

def first_of(*parsers: Parser) -> Parser:
    def ret(tokens: TokenStream) -> ast.Node:
        for parser in parsers:
            backup = tokens.index
            try:
                # Statefully changes the index
                return parser(tokens)
            except:
                tokens.index = backup

        raise Exception(f'Unable to parse input with any of these parsers: '
                        f'[{", ".join([p.__name__ for p in parsers])}]')

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

def parse_string(tokens: TokenStream) -> ast.Node:
    parser = tokens.need('lit_parser')
    value = parser.value[1:-1].replace('\\`', '`')
    return ast.LiteralParser(value=value)

def parse_regex(tokens: TokenStream) -> ast.Node:
    parser = tokens.need('lit_regex')
    value = parser.value[2:-1].replace('\\`', '`')
    return ast.RegexParser(value=value)

def parse_name(tokens: TokenStream) -> ast.Node:
    tokens.need('obracket')
    expr = parse_parser_expr(tokens)
    tokens.need('colon')
    name = tokens.need('ident')
    tokens.need('cbracket')
    return ast.Named(expr=expr, name=name.value)

def parse_debug(tokens: TokenStream) -> ast.Node:
    tokens.need('kw_debug')
    tokens.need('oparen')
    expr = parse_parser_expr(tokens)
    tokens.need('cparen')
    return ast.Debug(expr=expr)

def parse_atom(tokens: TokenStream) -> ast.Node:
    return first_of(parse_string, parse_regex, parse_name, parse_debug, parse_peek)(tokens)

def parse_peek(tokens: TokenStream) -> ast.Node:
    def parse_case(tokens: TokenStream) -> Tuple[Optional[ast.Node], ast.Node]:
        tokens.need('kw_case')
        case = first_of(
            lambda tokens: tokens.need('under') and None,
            parse_parser_expr)(tokens)
        tokens.need('arrow')
        parser = parse_parser_expr(tokens)
        return (case, parser)

    tokens.need('kw_peek')
    tokens.need('obrace')
    cases = list_of(parse_case, min=1)(tokens)
    tokens.need('cbrace')
    return ast.Match(cases=cases)

def parse_sequence(tokens: TokenStream) -> ast.Node:
    expr1 = parse_atom(tokens)
    expr2 = optional(parse_sequence)(tokens)
    if expr2:
        return ast.Sequence(expr1=expr1, expr2=expr2)
    else:
        return expr1

def parse_as_expr(tokens: TokenStream) -> ast.Node:
    name = tokens.need('ident').value
    return ast.Var(name=name)

def parse_parser_expr(tokens: TokenStream) -> ast.Node:
    def parse_as(tokens: TokenStream) -> ast.Node:
        tokens.need('kw_as')
        return parse_as_expr(tokens)

    parser_expr = parse_sequence(tokens)
    as_expr = optional(parse_as)(tokens)
    return ast.ParserExpr(parser_expr=parser_expr, as_expr=as_expr)

def parse_def(tokens: TokenStream) -> ast.Node:
    if tokens.peek_type('kw_export'):
        export = tokens.next()
    else:
        export = None

    name = tokens.need('ident').value
    tokens.need('doublecolon')
    expr = parse_parser_expr(tokens)
    return ast.Def(name=name, expr=expr, export=export is not None)

def parse_statement(tokens: TokenStream) -> ast.Node:
    return first_of(parse_debug, parse_def)(tokens)

def parse_file(tokens: TokenStream) -> ast.Node:
    return ast.StatementSequence(stmts=list_of(parse_statement)(tokens))

def parse(tokens: TokenStream) -> ast.Node:
    ret = parse_file(tokens)
    if not tokens.empty():
        raise Exception(f'Remaining tokens: {tokens.remaining()}')
    return ret