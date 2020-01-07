const parser = require('./langlang_parser.js');
const fs = require('fs');

if (process.argv.length < 3 || process.argv.length > 4) {
    console.log('Usage: node langlang.js source_file [dest_file]');
}
const infile = process.argv[2];
const outfile = process.argv[3] || 'langlang.out.js';

function walk(ast, oneach) {
    oneach(ast);
    ast.children.forEach((n) => walk(n, oneach));
}

function compile(ast) {
    const tokens = {
        '__whitespace': /\s+/,
        '__word': /\w+/,
    };

    function eval(node, state) {
        if(node.type == 'assign') {
            const [value, value_state] = eval(node.value, {names: []});
            const parser = 'function ' + node.name + '() {' + value + ';return {' + value_state.names.map((name) => name + ': ' + name).join(',') + '};}';
            state.parsers[node.name] = parser;
            return [parser, state];
        }
        else if(node.type == 'lit_str') {
            function escape(regex) {
                return regex.replace(/[^\w]/, (match) => '\\' + match)
            }
            tokens[node.value] = new RegExp(escape(node.value));
            return ['__consume("' + node.value + '")', state];
        }
        else if(node.type == 'seq') {
            let [valuesp, statep] = node.values.reduce((acc, value) => {
                const [vals, state] = acc;
                const [valuep, statep] = eval(value, state);
                return [vals.concat([valuep]), statep];
            }, [[], state]);
            return [valuesp.join(';'), statep];
        }
        else if(node.type == 'file') {
            return eval(node.contents, state);
        }
        else if(node.type == 'ident') {
            var fn = node.value + '()';
            if (node.value == 'WORD') {
                fn = '__consume("__word")';
            }
            if(node.name != undefined) {
                state.names.push(node.name);
                return ['var ' + node.name + '=' + fn, state];
            }
            return [fn, state];
        }
        throw Error('Unimplemented node type: ' + node.type)
    }
    var [_, state] = eval(ast, {parsers:[]});
    var parsers = state.parsers;

    function __tokenize() {
        function __parse_next_token(substr) {
            for (const name in tokens) {
                const match = tokens[name].exec(substr);
                if (match && match.index == 0) {
                    return [match[0], name];
                }
            }
            throw Error('Unknown token: ' + substr);
        }

        let index = 0;
        let token_stream = [];
        while (index < str.length) {
            const [value, type] = __parse_next_token(str.slice(index));
            index += value.length;
            if(type != '__whitespace') {
                token_stream.push([value, type]);
            }
        }
        return token_stream;
    }

    function __consume(expected_type) {
        if (token_index == token_stream.length) {
            throw Error('Hit EOF too early')
        }
        const [value, actual_type] = token_stream[token_index];
        if (expected_type == actual_type) {
            token_index++;
            return value;
        }
        throw Error('Expected ' + expected_type + ', got ' + actual_type + ' at "' + value + '"');
    }

    var ret = '';
    ret += 'const tokens={\n';
    for (token in tokens) {
        ret += '    "' + token + '":' + tokens[token].toString() + ',\n';
    }
    ret += '}\n';
    
    
    ret += 'function parse(str) {\n'
    ret += '    ' + __tokenize.toString() + '\n';
    ret += '    const token_stream = __tokenize(str);\n'
    ret += '    var token_index = 0;\n'
    ret += '    ' + __consume.toString() + '\n';
    for (var parser in parsers) {
        ret += '    ' + parsers[parser] + '\n';
    }
    ret += '    return plus();\n';
    ret += '}\n'
    ret += 'console.log(parse("1 * 2 + 3 * 4"));'

    return ret;
}

function main(err, data) {
    if (err != null) {
        console.log(err);
        return;
    }

    const source = String(data);
    const ast = parser.parse(source);
    const target = compile(ast);
    fs.writeFile(outfile, target, (err) => {
        if (err) throw err;
    });
}

fs.readFile(infile, main);