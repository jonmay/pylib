#!/usr/bin/env python
# from david chiang
import sys

level = 1
file = sys.stderr

def writeln(s=""):
    file.write("%s\n" % s)
    file.flush()

def write(s):
    file.write(s)
    file.flush()


    
    
