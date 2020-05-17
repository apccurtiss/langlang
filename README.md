Langlang
========

Langlang (the language language) is a small programming language meant to make it easy to write parsers for new languages. It compiles to JavaScript, and some day maybe other languages if I get around to implementing them.

Usage
-----

See the [getting started page](./getting_started.md) for details on the language. 

Running the compiler on a langlang file will generate a library that can be included by your code:
```
$ python langlang.py myfile.ll
Writing output to ./myfile.js
$ node
> var parser = require('./myfile.js')
> parser.add('1 + 2')
{ left: '1', right: '2', _type: 'Add' }
```

If you want a stand-alone "binary" for testing purposes or whatever, you can specify an parser that will take its input from stdin and print the output as JSON:
```
$ python langlang.py myfile.ll --stdin add
Writing output to ./myfile.js
$ echo "1 + 2" | node myfile.js
{
  "left": "1",
  "right": "2",
  "_type": "Add"
}
```

FAQ
---

*There are, like, a billion parser generators. Why does this exist?*  
I needed something that allowed for fine-graned controls on the error messages and recovery patterns, because most parser error messages suck and we as a society can do better.

*If this "langlang" is so great, why isn't it written in itself?*  
One day it will target Python and this will happen. One day...

*This doesn't have the "fine grained" features you said earlier in the FAQ. What gives?*  
It's a work in progress. Even the syntax changes a couple times a week.

*How can I contribute?*  
My emails is in [my bio](https://github.com/apccurtiss). If anyone's interested in contributing, send me a message and I'll add contribution directions. I haven't yet because they take time and I'm guessing nobody will want them.

*I want changes, but I don't want to contribute.*  
File an issue and I'll see what I can do.
