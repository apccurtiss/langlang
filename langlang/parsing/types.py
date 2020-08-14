from dataclasses import dataclass
from typing import Dict

class LLType:
    pass

@dataclass
class Null(LLType):
    pass

@dataclass
class String(LLType):
    pass

@dataclass
class Parser(LLType):
    ret: LLType

@dataclass
class Struct(LLType):
    fields: Dict[str, LLType]

    def __eq__(self, other):
        if not isinstance(other, Struct):
            return False

        return all(self.fields[k] == other.fields[k] 
            for k in set(self.fields.keys() + other.fields.keys()))