from collections import namedtuple
import re
from typing import List

Token = namedtuple('Token', ['type', 'value'])
token_types = {
    # Ignored tokens
    'whitespace': re.compile(r'(?:\s|\n)+'),

    # Keywords
    'kw_peek': re.compile(r'\bpeek\b'),
    'kw_match': re.compile(r'\bmatch\b'),
    'kw_case': re.compile(r'\bcase\b'),
    'kw_export': re.compile(r'\bexport\b'),
    'kw_debug': re.compile(r'\bdebug\b'),
    'kw_template': re.compile(r'\btemplate\b'),
    'kw_as': re.compile(r'\bas\b'),

    # Symbols
    'oparen': re.compile(r'\('),
    'cparen': re.compile(r'\)'),
    'obrace': re.compile(r'\{'),
    'cbrace': re.compile(r'\}'),
    'obracket': re.compile(r'\['),
    'cbracket': re.compile(r'\]'),
    'arrow': re.compile(r'=>'),
    'comma': re.compile(r','),
    'doublecolon': re.compile(r'::'),
    'colon': re.compile(r':'),

    # Literals
    'lit_parser': re.compile(r'`(?:\\`|[^`])*`'),
    'lit_regex': re.compile(r'r`(?:\\`|[^`])*`'),
    'lit_string': re.compile(r'"(?:\\"|[^"])*"'),

    # Other
    'ident': re.compile(r'\w+'),
}


class TokenStream:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.index = 0

    def empty(self):
        return self.index >= len(self.tokens)

    def remaining(self):
        return self.tokens[self.index:]

    def peek(self):
        if self.index >= len(self.tokens):
            raise Exception('Unexpected EOF!')

        return self.tokens[self.index]

    def peek_type(self, type):
        return self.peek().type == type

    def next(self):
        token = self.peek()

        self.index += 1
        return token
        
    def need(self, required_type: str):
        token = self.peek()

        if token.type != required_type:
            raise Exception(f'Unexpected {token.type} ({token.value}); needed {required_type}')
        
        self.index += 1
        return token


def tokenize(source: str) -> TokenStream:
    index = 0
    tokens = []
    # While there's still source left to consume...
    while index < len(source):
        # ...search through every available token...
        for token_type, regex in token_types.items():
            match = regex.match(source[index:])
            # ...and if it matches the remaining text, add it to the list.
            if match:
                if token_type != 'whitespace':
                    tokens.append(Token(token_type, match.group(0)))
                index += len(match.group(0))
                break
        else:
            # Error case if no tokens matched.
            line_start = source.rfind('\n', 0, index) + 1 # Off-by-one also fixes the not-found case!
            line_end = source.find('\n', index)
            if line_end is -1:
                line_end = len(source) - 1
            column = index - line_start
            
            raise ValueError(f'Unknown token: Column {column} of {source[line_start:line_end]} ("{source[index]}")')

    return TokenStream(tokens)