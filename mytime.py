#!/usr/bin/env python

# from http://www.daniweb.com/code/snippet216610.html

#
# time a function using time.time() and the a @ function decorator
#
# tested with Python24 vegaseat 21aug2005
#
 
#
import time
#
 
#
def print_timing(func):
    def wrapper(*arg):
        t1 = time.time()
        res = func(*arg)
        t2 = time.time()
        print '%s took %0.3f ms' % (func.func_name, (t2-t1)*1000.0)
        return res
    return wrapper
