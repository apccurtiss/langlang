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

from parsing.ll_parser import parse
from assemblers.javascript import assemble


def version(args):
    print('Langlang 0.0.1')
    exit(0)


def compile_source(source, entrypoint=None):
    ast = parse(source)
    return assemble(ast, standalone_parser_entrypoint=entrypoint)


def compile_file(args):
    with open(args.filename) as f:
        source = f.read()

    output = compile_source(source, args.entrypoint)

    outfile = args.outfile or f'{os.path.splitext(args.filename)[0]}.js'
    with open(outfile, 'w') as f:
        print(f'Writing output to {outfile}')
        f.write(output)


def watch_file(args):
    filename = args.filename

    class Handler(FileSystemEventHandler): 
        @staticmethod
        def on_any_event(event):
            if event.event_type == 'modified' and event.src_path == filename: 
                print(f'Recompiling {filename}')
                compile_file(args)

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
    parser.add_argument('filename', type=str, nargs='?', action='store', help='file to compile')
    parser.add_argument('-o', dest='outfile', type=str, action='store', help='output filename')
    parser.add_argument('--watch', dest='watch', action='store_true',
        help='watch a file and recompile on changes')
    parser.add_argument('--version', dest='version', action='store_true',
        help='print version and exit')
    parser.add_argument('--stdin', dest='entrypoint', type=str, action='store',
        help='compile the output file to pass data from stdin to <entrypoint> and print the result')

    args = parser.parse_args()

    if args.version:
        version(args)
    if not args.filename:
        parser.print_help()
        exit(0)
    elif args.watch:
        watch_file(args)
    else:
        compile_file(args)

if __name__ == '__main__':
    main()