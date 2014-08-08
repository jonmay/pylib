#!/usr/bin/env python
import jmutil
import sys

if __name__ == '__main__':
  vec = map(float, sys.stdin.readlines())
  jmutil.get_stats(vec)

