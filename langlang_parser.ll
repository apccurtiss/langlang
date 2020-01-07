BasicParser :: WORD:ident
Parser :: 
        | STRLIT
        | Parser "|" Parser
        | 
NamedParser :: Parser {":" WORD:name}
Assign :: WORD:name "::" Parser:value