import argparse
from collections import namedtuple
import logging
import os
import re
import sys
import time
from typing import Dict, List
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler 

from langlang_tokenizer import tokenize 
from langlang_parser import parse
from langlang_assembler import assemble


def compile(filename, outfile):
    with open(filename) as f:
        source = f.read()

    tokens = tokenize(source)
    ast = parse(tokens)
    output = assemble(ast)

    filename = outfile or f'{os.path.splitext(filename)[0]}.js'
    with open(filename, 'w') as f:
        print(f'Writing output to {filename}')
        f.write(output)
  

# class OnMyWatch: 
#     # Set the directory on watch 
#     watchDirectory = "/give / the / address / of / directory"
  
#     def __init__(self): 
#         self.observer = Observer() 
  
#     def run(self): 
#         event_handler = Handler() 
#         self.observer.schedule(event_handler, self.watchDirectory, recursive = True) 
#         self.observer.start() 
#         try: 
#             while True: 
#                 time.sleep(5) 
#         except: 
#             self.observer.stop() 
#             print("Observer Stopped") 
  
#         self.observer.join()
# class Handler(FileSystemEventHandler): 
#     def __init__(self, filename, callback):
#         self.callback = callback
#         super.__init__()

#     @staticmethod
#     def on_any_event(event):
#         if event.is_directory:
#             return None

#         elif event.event_type == 'modified' and event.src_path == self.filename: 
#             print(f'Update to {self.filename}')
#             return self.callback() 


def watch(filename, outfile):
    class Handler(FileSystemEventHandler): 
        @staticmethod
        def on_any_event(event):
            if event.event_type == 'modified' and event.src_path == filename: 
                print(f'Recompiling {filename}')
                compile(filename, outfile)

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
    parser.add_argument('--watch', dest='watch', action='store_true', help='watch a file')

    args = parser.parse_args()

    if args.watch:
        watch(args.filename, args.outfile)
    else:
        compile(args.filename, args.outfile)

if __name__ == '__main__':
    main()