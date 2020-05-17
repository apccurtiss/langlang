Getting started:
----------------

Almost everything in langlang is a parser: a function that takes a string as input, reads characters from the front, and either returns a value or throws an error. There are two basic parsers, both of which return the exact text they match:
```
lit :: `foo` # Literal parser - matches the string "foo"
re :: r`fo+` # Regex parser - matches the string "fo", "foo", "fooo", etc.
```

These parsers can be chained into a sequence, which will run each one in turn and return the result of the last one. Importantly, any whitespace between the parsers is ignored.
```
sequence :: `foo` `bar` `baz` # Sequence parser - matches "foobarbaz", "foo bar baz", etc. and returns "baz"
```

Branching is done through peek parsers, which will test a list of parsers until one matches:
```
branch :: peek {
    case `foo` => `foo` `bar` `baz`
    case `x` => `x` `y` `z`
    case _ => `default`
} # Peek parser - matches `foo bar baz`, `x y z`, or `default`.
```

You probably don't want to return the exact input though. Instead, you can change what a parser returns with the `as` keyword:
```
str :: `foo` as "cow" # Parses "foo", but returns "cow"
num :: `foo` as struct Literal {
    value: "moose"
} # Parses "foo", but returns a struct of type "Literal" with the key "value" equal to "moose"
```

You can put everything together with named parsers, which let you assign names to be referenced in later `as` statements:
```
number :: r`[0-9]+`

parened :: `(` [number: n] `)` as n # Parses "(1)" and returns "1"

add :: [number: left] `+` [number: right] as struct Add {
    left: left,
    right: right
} # Parses "1 + 2" and returns a struct of type "Add" with the values "left": "1" and "right": "2"
```

Finally, you can make custom error messages by using a `!` followed by a string. It binds only to the closest parser.
```
paren :: `(` ! "Opening parenthesis required"
         number
         `)` ! "Closing parenthesis required"
    as number
```