

const tokens = {
    'kw_return': /return/,
    'kw_print': /print/,
    'kw_match': /match/,
    'kw_peek': /peek/,
    'kw_pop': /pop/,
    'kw_abstract': /abstract/,
    'kw_instance': /instance/,
    'oparen': /\(/,
    'cparen': /\)/,
    'lit_str': /"((\\")|([^"]))*?"/,
    'whitespace': /\s+/,
    'comment': /--.*/,
    'comma': /,/,
    'semi': /;/,
    'ident': /\w+/,
    'dcolon': /::/,
    'colon': /:/,
    'obracket': /\[/,
    'cbracket': /\]/,
    'or': /\|/,
}

function tokenize(str) {
    let index = 0;
    let tokens = [];
    while (index < str.length) {
        const [value, type] = nextToken(str.slice(index));
        index += value.length;
        tokens.push([value, type]);
    }
    return tokens.filter((token) => token[1] != 'whitespace' && token[1] != 'comment');
}

function nextToken(str) {
    for (const name in tokens) {
        const match = tokens[name].exec(str);
        if (match && match.index == 0) {
            return [match[0], name];
        }
    }
    throw Error('Unknown token: ' + str);
}

module.exports.parse = function parse(source) {
    const tokens = tokenize(source);
    var tokenIndex = 0;
    function consume(expected_type) {
        if (tokenIndex == tokens.length) {
            throw Error('Hit EOF too early')
        }
        const [value, actual_type] = tokens[tokenIndex];
        if (expected_type == actual_type) {
            tokenIndex++;
            return value;
        }
        throw Error('Expected ' + expected_type + ', got ' + actual_type + ' at "' + value + '"');
    }

    function optional(fn) {
        var index = tokenIndex;
        try {
            return fn();
        }
        catch (e) {
            tokenIndex = index;
            return null;
        }
    }
    function or(...fns) {
        return () => {
            var errs = []
            for (const fn of fns) {
                try {
                    return fn();
                }
                catch (e) {
                    errs.push(e);
                }
            }
            throw Error("Got errors:\n   " + errs.join('\n   '));
        }
    }

    function oneOrMore(fn) {
        return () => {
            var ret = [];
            while (true) {
                var oldTokenIndex = tokenIndex;
                try {
                    ret.push(fn());
                }
                catch (e) {
                    if (ret.length == 0) {
                        throw e;
                    }
                    else {
                        tokenIndex = oldTokenIndex;
                        return {
                            type: "seq",
                            values: ret,
                            children: ret,
                        }
                    }
                }
            }
        }
    }
    
    function parsePrint() {
        consume('kw_print');
        consume('oparen');
        const expr = parseExpr();
        consume('cparen');

        return {
            type: 'print',
            value: expr,
            children: [expr]
        }
    }

    function parseLitStr() {
        const str = consume('lit_str');
        return {
            type: 'lit_str',
            value: str.slice(1, str.length - 1),
            children: []
        }
    }

    function parseIdent() {
        const ident = consume('ident');
        return {
            type: 'ident',
            value: ident,
            children: []
        }
    }

    function parseExpr() {
        return oneOrMore(() => {
            var expr = or(parseIdent, parseLitStr)();
            var name = optional(() => {
                consume('colon');
                return consume('ident');
            });
            expr['name'] = name;
            return expr;
        })();
    }

    function parseAssign() {
        // const keyword = parse(or(() => consume('kw_abstract'), () => consume('kw_instance')));
        const varname = consume('ident');
        consume('dcolon');
        const value = parseExpr();
        return {
            type: 'assign',
            name: varname,
            value: value,
            children: [value]
        }
    }

    function parseReturn() {
        consume('kw_return');
        const value = parseExpr();
        return {
            type: 'return',
            value: value,
            children: [value]
        }
    }

    function parseStatement() {
        const statement = or(parseAssign, parseReturn)();
        consume('semi');
        return statement;
    }

    function parseFile(tokens) {
        // let statements = [];
        // while (tokenIndex < tokens.length) {
        //     const statement = parseStatement();
        //     statements.push(statement);
        // }
        let statements = oneOrMore(parseStatement)();
        return {
            type: 'file',
            contents: statements,
            children: statements
        }
    }

    return parseFile(tokens);
}