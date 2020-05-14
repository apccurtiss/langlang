import argparse
from collections import namedtuple
import logging
import os
import re
import sys
import time
from typing import Dict, List, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler 

from langlang_tokenizer import tokenize 
from langlang_parser import parse
from langlang_assembler import assemble


def compile(args):
    with open(args.filename) as f:
        source = f.read()

    tokens = tokenize(source)
    ast = parse(tokens)
    output = assemble(ast, standalone_parser=args.entrypoint)

    outfile = args.outfile or f'{os.path.splitext(args.filename)[0]}.js'
    with open(outfile, 'w') as f:
        print(f'Writing output to {outfile}')
        f.write(output)


def watch(args):
    filename = args.filename

    class Handler(FileSystemEventHandler): 
        @staticmethod
        def on_any_event(event):
            if event.event_type == 'modified' and event.src_path == filename: 
                print(f'Recompiling {filename}')
                compile(args)

    watchpath = os.path.dirname(filename)

    # Initialize Observer 
    observer = Observer() 
    observer.schedule(Handler(), watchpath)
  
    # Start the observer
    print(f'Watching for changes to {watchpath}')
    observer.start() 
    try: 
        while True: 
            # Set the thread sleep time 
            time.sleep(1)
    except KeyboardInterrupt: 
        observer.stop()
    observer.join() 


def main():
    parser = argparse.ArgumentParser(description='Compile langlang files.')
    parser.add_argument('filename', type=str, action='store', help='file to compile')
    parser.add_argument('-o', dest='outfile', type=str, action='store', help='output filename')
    parser.add_argument('--watch', dest='watch', action='store_true',
        help='watch a file and recompile on changes')
    parser.add_argument('--stdin', dest='entrypoint', type=str, action='store',
        help='compile the output file to pass data from stdin to <entrypoint> and print the result')

    args = parser.parse_args()

    if args.watch:
        watch(args)
    else:
        compile(args)

if __name__ == '__main__':
    main()