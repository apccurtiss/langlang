import re
from typing import Any, Dict, List, Tuple

class Node:
    def __init__(self, *pargs, **kwargs):
        raise Exception('Must implement constructor!')

# Basic parsers
class LiteralParser(Node):
    def __init__(self, value: str):
        self.value = value

class RegexParser(Node):
    def __init__(self, value: str):
        self.value = value

# Parser combinators
class Sequence(Node):
    def __init__(self, expr1: Node, expr2: Node):
        self.expr1 = expr1
        self.expr2 = expr2

class Match(Node):
    def __init__(self, cases: List[Tuple[Node, Node]]):
        self.cases = cases

# Language   utilities
class Named(Node):
    def __init__(self, expr: Node, name: str):
        self.expr = expr
        self.name = name

class ParserExpr(Node):
    def __init__(self, parser_expr: Node, as_expr: Node):
        self.parser_expr = parser_expr
        self.as_expr = as_expr

class Debug(Node):
    def __init__(self, expr: Node):
        self.expr = expr

# Expressions
class Var(Node):
    def __init__(self, name: str):
        self.name = name

# File-level structures
class StatementSequence(Node):
    def __init__(self, stmts: List[Node]):
        self.stmts = stmts

class Def(Node):
    def __init__(self, name: str, expr: Node, export: bool):
        self.name = name
        self.expr = expr
        self.export = export