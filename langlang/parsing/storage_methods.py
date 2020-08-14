from dataclasses import dataclass

class StorageMethod:
    pass

@dataclass
class Ignore(StorageMethod):
    def as_prefix(self):
        return ''

@dataclass
class Return(StorageMethod):
    def as_prefix(self):
        return 'return '

@dataclass
class Var(StorageMethod):
    name: str

    def as_prefix(self):
        return 'let {} = '.format(self.name)