import re
from typing import Any, Dict, List, Tuple

class Node:
    def assemble(self, context: Dict[str, Any]) -> str:
        raise Exception('Must implement assemble function!')

# Basic parsers
class LiteralParser(Node):
    def __init__(self, value: str):
        self.value = value

    def assemble(self, context: Dict[str, Any]) -> str:
        # Replace with literal regex that does the same thing.
        escaped_re = re.sub(r"[-[\]{}()*+?.,\\^$|#\\s]", r"\\\0", self.value)
        as_re = f'/^{escaped_re}/'
        context.setdefault('tokens', {})[self.value] = as_re
        return f'this.__require("{self.value}")'

class RegexParser(Node):
    def __init__(self, value: str):
        self.value = value

    def assemble(self, context: Dict[str, Any]) -> str:
        as_str = f'{self.value}'
        as_re = f'/^{self.value}/'
        context.setdefault('tokens', {})[as_str] = as_re
        return f'this.__require("{as_str}")'

# Parser combinators
class Sequence(Node):
    def __init__(self, expr1: Node, expr2: Node):
        self.expr1 = expr1
        self.expr2 = expr2

    def assemble(self, context: Dict[str, Any]) -> str:
        return (f'{self.expr1.assemble(context)};\n'
                f'{self.expr2.assemble(context)}')

class Match(Node):
    def __init__(self, cases: List[Tuple[Node, Node]]):
        self.cases = cases

    def assemble(self, context: Dict[str, Any]) -> str:
        statements = ';\n'.join(
            (f'if (this.__test({cond.assemble(context)})) {{\n'
             f'    return {parser.assemble(context)};\n'
             f'}}')
        for cond, parser in self.cases)
        return (f'(() => {{\n'
                f'    {statements}'
                f'}})()')

# Language   utilities
class Named(Node):
    def __init__(self, expr: Node, name: str):
        self.expr = expr
        self.name = name

    def assemble(self, context: Dict[str, Any]) -> str:
        return f'let {self.name} = {self.expr.assemble(context)}'

class ParserExpr(Node):
    def __init__(self, parser_expr: Node, as_expr: Node):
        self.parser_expr = parser_expr
        self.as_expr = as_expr

    def assemble(self, context: Dict[str, Any]) -> str:
        if self.as_expr:
            return (f'{self.parser_expr.assemble(context)}\n'
                    f'return {self.as_expr.assemble(context)}\n')
        else:
            return f'{self.parser_expr.assemble(context)}\n'

class Debug(Node):
    def __init__(self, expr: Node):
        self.expr = expr

    def assemble(self, context: Dict[str, Any]) -> str:
        return f'console.log(JSON.stringify({self.expr.assemble(context)}))'

# Expressions
class Var(Node):
    def __init__(self, name: str):
        self.name = name

    def assemble(self, context: Dict[str, Any]) -> str:
        if self.name not in context.setdefault('scope', set()):
            raise Exception(f'"{self.name}" is not defined!')
        return self.name

# File-level structures
class StatementSequence(Node):
    def __init__(self, stmts: List[Node]):
        self.stmts = stmts

    def assemble(self, context: Dict[str, Any]) -> str:
        return '\n'.join(map(lambda s: s.assemble(context), self.stmts))

class Def(Node):
    def __init__(self, name: str, expr: Node, export: bool):
        self.name = name
        self.expr = expr
        self.export = export

    def assemble(self, context: Dict[str, Any]) -> str:
        if self.export:
            context.setdefault('exports', set()).add(self.name)
        return (f'{self.name}() {{\n'
                f'  {self.expr.assemble(context)}'
                f'}}')