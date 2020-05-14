import argparse
from collections import namedtuple
import os
import re
import sys
from typing import Dict, List

from langlang_tokenizer import tokenize 
from langlang_parser import parse
from langlang_assembler import assemble


def compile(source):
    tokens = tokenize(source)
    ast = parse(tokens)
    return assemble(ast)


def main():
    parser = argparse.ArgumentParser(description='Compile langlang files.')
    parser.add_argument('filename', type=str, action='store', help='file to compile')
    parser.add_argument('-o', dest='outfile', type=str, action='store', help='output filename')

    args = parser.parse_args()

    with open(args.filename) as f:
        source = f.read()

    output = compile(source)

    filename = args.outfile or f'{os.path.splitext(args.filename)[0]}.js'
    with open(filename, 'w') as f:
        print(f'Writing output to {filename}')
        f.write(output)

if __name__ == '__main__':
    main()