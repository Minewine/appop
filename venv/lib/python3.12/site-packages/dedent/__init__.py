"""
Dedent the next program on the command line and execute it.

This has the nice effect that the inline code can be freely indented.

The script replaces the "-c" parameter.
Alternatively, you can also use "-m" without ".py".

There is no shebang line by intent. It is not meant as a standalone script.

Inspired by a comment from Frederik Gladhorn.
"""

import sys
import os
import traceback
import textwrap


def modname(path):
    name = os.path.basename(path)
    pre, post = os.path.splitext(name)
    return pre

name = modname(os.path.dirname(__file__))

arg = sys.argv[0]
if arg == "-c" or arg == "-m":
    pos = 0
else:
    for idx, arg in enumerate(sys.argv):
        if modname(arg) == name:
            pos = idx
            break
    else:
        pos = -1

if (pos < 0 or pos+1 >= len(sys.argv)):
    raise ValueError("""you need a string like in 'python -c "..."'""")

prog = sys.argv[pos+1]
text = textwrap.dedent(prog + "\n")
__name__ = "__main__"
try:
    exec(text)
except:
    # we want to format the exception as if no frame was on top.
    exp, val, tb = sys.exc_info()
    listing = traceback.format_exception(exp, val, tb)
    # remove the entry for the first frame
    del listing[1]
    files = [line for line in listing if line.startswith("  File")]
    if len(files) == 1:
        # only one file, remove the header.
        del listing[0]
    sys.stderr.write("".join(listing))
    sys.exit(1)
