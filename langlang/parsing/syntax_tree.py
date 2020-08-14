import re
from typing import Any, Dict, List, Mapping, Optional, Tuple

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

class Peek(Node):
    def __init__(self, cases: List[Tuple[Node, Node]]):
        self.cases = cases

# Values
class LitStr(Node):
    def __init__(self, value: str):
        self.value = value

class LitNum(Node):
    def __init__(self, value: float):
        self.value = value

class Var(Node):
    def __init__(self, name: str):
        self.name = name

class Struct(Node):
    def __init__(self, name: str, map: Mapping[str, str]):
        self.name = name
        self.map = map
    

# Language utilities
class Named(Node):
    def __init__(self, expr: Node, name: str):
        self.expr = expr
        self.name = name

class Error(Node):
    def __init__(self, parser: Node, message: str):
        self.parser = parser
        self.message = message

class As(Node):
    def __init__(self, parser: Node, result: Node):
        self.parser = parser
        self.result = result

class Debug(Node):
    def __init__(self, expr: Node):
        self.expr = expr

# File-level structures
class StatementSequence(Node):
    def __init__(self, stmts: List[Node]):
        self.stmts = stmts

class Def(Node):
    def __init__(self, name: str, expr: Node, export: bool):
        self.name = name
        self.expr = expr
        self.export = export