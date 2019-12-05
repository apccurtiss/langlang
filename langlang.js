const fs = require('fs');

if (process.argv.length != 3) {
    console.log('Usage: node langlang.js source_file');
}

const filename = process.argv[2];

const tokens = {
    'kw_print': /print/,
    'oparen': /\(/,
    'cparen': /\)/,
    'lit_str': /"((\\")|([^"]))*?"/,
    'whitespace': /\s+/,
    'ident': /\w+/,
    'dcolon': /::/,
    'obracket': /\[/,
    'cbracket': /\]/,
    'or': /\|/,
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

function tokenize(str) {
    let index = 0;
    let tokens = [];
    while (index < str.length) {
        const [value, type] = nextToken(str.slice(index));
        index += value.length;
        tokens.push([value, type]);
    }
    return tokens.filter((token) => token[1] != 'whitespace');
}

function parse(tokens) {
    function consume(expected_type) {
        if (tokens.length == 0) {
            throw Error('Hit EOF too early')
        }
        const [value, actual_type] = tokens[0];
        if (expected_type == actual_type) {
            tokens.shift()
            return value;
        }
        throw Error('Expected ' + expected_type + ', got ' + actual_type);
    }
    
    function parsePrint() {
        consume('kw_print');
        consume('oparen');
        const expr = parseExpr();
        consume('cparen');

        return {
            exec: () => console.log(expr.exec()),
            compile: () => 'console.log(' + expr.compile() + ')'
        }
    }

    function parseLitStr() {
        const str = consume('lit_str');
        return {
            exec: () => str.slice(1, -1).replace('\\n', '\n'),
            compile: () => str
        }
    }

    function parseExpr() {
        const expr = parseLitStr();
        return {
            exec: expr.exec,
            compile: expr.compile
        }
    }

    function parseStatement() {
        const statement = parsePrint();
        return {
            exec: statement.exec,
            compile: statement.compile
        }
    }

    function parseFile(tokens) {
        let statements = [];
        console.log(tokens)
        while (tokens.length > 0) {
            const statement = parseStatement();
            statements.push(statement);
        }
        return {
            exec: () => statements.forEach((statement) => statement.exec()),
            compile: () => statements.map((statement) => statement.compile()).join(';\n')
        }
    }

    return parseFile(tokens);
}

function compile(err, data) {
    if (err != null) {
        console.log(err);
        return;
    }

    const source = String(data);
    const tokens = tokenize(source);
    const ast = parse(tokens);
    // ast.exec();
    fs.writeFile('langlang.out.js', ast.compile(), (err) => {
        if (err) throw err;
    });
}

fs.readFile(filename, compile);