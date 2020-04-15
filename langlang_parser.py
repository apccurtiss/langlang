import re
from typing import Any, Callable, Dict, List, Union

from langlang_tokenizer import TokenStream

class Node:
    def assemble(self, context: Dict[str, Any]) -> str:
        raise Exception('Must implement assemble function!')

class ParserSequence(Node):
    def __init__(self, expr: Node):
        self.expr = expr

    def assemble(self, context: Dict[str, Any]) -> str:
        return ';\n'.join(map(lambda e: e.assemble(context), self.expr))

class StatementSequence(Node):
    def __init__(self, stmts: List[Node]):
        self.stmts = stmts

    def assemble(self, context: Dict[str, Any]) -> str:
        return '\n'.join(map(lambda s: s.assemble(context), self.stmts))

class ParseString(Node):
    def __init__(self, value: str):
        self.value = value

    def assemble(self, context: Dict[str, Any]) -> str:
        # Replace with literal regex that does the same thing.
        escaped_re = re.sub(r"[-[\]{}()*+?.,\\^$|#\\s]", r"\\\0", self.value[1:-1])
        as_re = f'/^{escaped_re}/'
        context.setdefault('tokens', {})[self.value] = as_re
        return f'this.__require({self.value})'

class ParseRegex(Node):
    def __init__(self, value: str):
        self.value = value

    def assemble(self, context: Dict[str, Any]) -> str:
        as_str = f'"{self.value[1:-1]}"'
        as_re = f'/^{self.value[1:-1]}/'
        context.setdefault('tokens', {})[as_str] = as_re
        return f'this.__require({as_str})'

class ParseSequence(Node):
    def __init__(self, expr1: Node, expr2: Node):
        self.expr1 = expr1
        self.expr2 = expr2

    def assemble(self, context: Dict[str, Any]) -> str:
        return f'{self.expr1.assemble(context)}, {self.expr2.assemble(context)}'
    
class Debug(Node):
    def __init__(self, expr: Node):
        self.expr = expr

    def assemble(self, context: Dict[str, Any]) -> str:
        return f'console.log({self.expr.assemble(context)})'

class Def(Node):
    def __init__(self, name: str, expr: Node, export: bool):
        self.name = name
        self.expr = expr
        self.export = export

    def assemble(self, context: Dict[str, Any]) -> str:
        # {}.setdefault()
        if self.export:
            context.setdefault('exports', set()).add(self.name)
        return f'{self.name}() {{ return {self.expr.assemble(context)} }}'

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

def optional(parser: Parser) -> Parser:
    def ret(tokens: TokenStream) -> Node:
        backup = tokens.index
        try:
            # Statefully changes the index
            return parser(tokens)
        except:
            tokens.index = backup
            return None

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
        except Exception as e:
            tokens.index = backup
            raise e

    return ret

def parse_string(tokens: TokenStream) -> Node:
    parser = tokens.need('string')
    return ParseString(value=parser.value)

def parse_regex(tokens: TokenStream) -> Node:
    parser = tokens.need('regex')
    return ParseRegex(value=parser.value)

def parse_sequence(tokens: TokenStream) -> Node:
    expr1 = first_of(parse_string, parse_regex)(tokens)
    expr2 = optional(parse_sequence)(tokens)
    if expr2:
        return ParseSequence(expr1=expr1, expr2=expr2)
    else:
        return expr1

def parse_expr(tokens: TokenStream) -> Node:
    return parse_sequence(tokens)

def parse_def(tokens: TokenStream) -> Node:
    if tokens.peek_type('kw_export'):
        export = tokens.next()
    else:
        export = None

    return multi('ident', 'doublecolon', parse_expr)(tokens, lambda name, _b, expr: Def(name=name.value, expr=expr, export=export is not None))

def parse_debug(tokens: TokenStream) -> Node:
    return multi('kw_debug', 'oparen', parse_expr, 'cparen')(tokens, lambda _a, _b, x, _c: Debug(expr=x))

def parse_statement(tokens: TokenStream) -> Node:
    return first_of(parse_debug, parse_def)(tokens)

def parse_file(tokens: TokenStream) -> Node:
    return list_of(parse_statement)(tokens, lambda stmts: StatementSequence(stmts=stmts))

def parse(tokens: TokenStream) -> Node:
    ret = parse_file(tokens)
    if not tokens.empty():
        raise Exception(f'Remaining tokens: {tokens.remaining()}')
    return ret