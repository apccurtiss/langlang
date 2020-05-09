"use strict"

// This file autogenerated by langlang.
// For details, see {{ help_url }}.

class Parser {
    __tokens = {
{{ tokens }}
    }

    __tokenize(s) {
        let tokens = [];
        nextToken: while (s.length > 0) {
            for (let type in this.__tokens) {
                let result = this.__tokens[type].exec(s);
                if (result !== null) {
                    if (type != '__whitespace') {
                        tokens.push({
                            type: type,
                            value: result[0],
                        });
                    }
                    s = s.slice(result[0].length);
                    continue nextToken;
                }
            }
            throw Error(`Unknown token: ${s}`)
        }
        return tokens;
    }

    constructor(input) {
        this.tokens = this.__tokenize(input);
        this.index = 0;
    }

    __next() {
        let token = this.tokens[this.index];
        if (token === undefined) {
            throw Error('Unexpected end of file.')
        }
        this.index++;
        return token;
    }

    __require(type) {
        // console.debug(`Requiring: ${type}`)
        let token = this.__next();
        if (token.type !== type) {
            throw Error(`Expected ${type}, got ${token.type}`)
        }
        return token;
    }

    __consume_all(parser) {
        this[parser]();
        if (this.index < this.tokens.length) {
            throw Error(`Remaining tokens: ${this.tokens.slice(this.index).map((t) => t.type)}`)
        }
    }

    // Parser helper functions
    __test(parser) {
        let backup = this.index;
        try {
            parser();
            return true;
        }
        catch (e) {
            return false;
        }
        finally {
            this.index = backup;
        }
    }

{{ parsers }}
}

{{ exports }}