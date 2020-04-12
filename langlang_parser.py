from langlang_tokenizer import TokenStream
from typing import Any, Callable, Dict, List, Union

# We should write a custom constructor for each AST node, but this is better for rapid iteration.
# The naming convetion of children will be 'expr', 'stmt', and 'lit' for expression, statement, and
# literal children. There will be an 's' after them if the child is a list, and numbers if there
# are multiple children of the same type.
class Node:
    def __init__(self, **children: Dict[str, str]):
        for name, child in children.items():
            setattr(self, name, child)

class ParserSequence(Node):
    def __str__(self):
        return ';\n'.join(map(str, self.expr))

class StatementSequence(Node):
    def __str__(self):
        return '\n'.join(map(str, self.stmts))

class ParseString(Node):
    def __str__(self):
        return f'parseString({self.value})'

class ParseRegex(Node):
    def __str__(self):
        return f'parseRegex({self.value})'

class ParseSequence(Node):
    def __str__(self):
        return f'{self.expr1}, {self.expr2}'
    
class Debug(Node):
    def __str__(self):
        return f'console.log({str(self.expr)})'

class Def(Node):
    def __str__(self):
        return f'console.log({str(self.expr)})'

# In plain English - takes a list of tokens, returns a node
Parser = Callable[[TokenStream], Node]

# Parser combinators
def list_of(parser: Parser) -> Callable[[TokenStream, Callable[[List[Node]], Node]], Node]:
    def ret(tokens: TokenStream, f: Callable[[List[Node]], Node]) -> Node:
        items = []
        while True:
            backup = tokens.index
            try:
                # Statefully changes the index
                node = parser(tokens)
            except:
                tokens.index = backup
                break
            items.append(node)
        return f(items)

    return ret

def first_of(*parsers: List[Parser]) -> Parser:
    def ret(tokens: TokenStream) -> Node:
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

def multi(*parsers: List[Union[Parser, str]]) -> Callable[[TokenStream, Callable[[Any], Node]], Node]:
    def ret(tokens: TokenStream, f: Callable[[Any], Node]) -> Node:
        backup = tokens.index

        try:
            args = []
            for parser in parsers:
                if isinstance(parser, str):
                    args.append(tokens.need(parser))
                else:
                    args.append(parser(tokens))
            return f(*args)
        finally:
            backup = tokens.index

    return ret

def parse_string(tokens: TokenStream) -> Node:
    parser = tokens.need('string')
    return ParseString(value=parser.value)

def parse_regex(tokens: TokenStream) -> Node:
    parser = tokens.need('regex')
    return ParseRegex(value=parser.value)

def parse_sequence(tokens: TokenStream) -> Node:
    expr1 = first_of(parse_string, parse_regex)(tokens)
    expr2 = first_of(parse_string, parse_regex, parse_sequence)(tokens)
    return ParseSequence(expr1=expr1, expr2=expr2)

def parse_expr(tokens: TokenStream) -> Node:
    return parse_sequence(tokens)

def parse_def(tokens: TokenStream) -> Node:
    if tokens.peek_type('kw_export'):
        export = tokens.next()
    else:
        export = None

    return multi('ident', 'doublecolon', parse_expr)(tokens, lambda name, _b, expr: Def(name=name, expr=expr))

def parse_debug(tokens: TokenStream) -> Node:
    return multi('kw_debug', 'oparen', 'string', 'cparen')(tokens, lambda _a, _b, x, _c: Debug(expr=x))

def parse_statement(tokens: TokenStream) -> Node:
    return first_of(parse_debug, parse_def)(tokens)

def parse_file(tokens: TokenStream) -> Node:
    return list_of(parse_statement)(tokens, lambda stmts: StatementSequence(stmts=stmts))

def parse(tokens: TokenStream) -> Node:
    ret = parse_file(tokens)
    if not tokens.empty():
        raise Exception(f'Remaining tokens: {tokens.remaining()}')
    return ret