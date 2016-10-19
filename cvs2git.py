#! /usr/bin/env python
import argparse
import sys
import codecs
from itertools import izip
from collections import defaultdict as dd
import os
import re

efile=os.path.join("CVS", "Entries")

def findfiles(path, outfile):
    ''' recursively traverse CVS tree and add files to the list '''
    manifest=os.path.join(path, efile)
    # special case: if no CVS, just traverse
    if not os.path.exists(manifest):
        pathlist = filter (lambda x: (not x.startswith('.')) and os.path.isdir(os.path.join(path, x)), os.listdir(path))
        for item in pathlist:
            findfiles(os.path.join(path, item), outfile)
        return
    fh = open(manifest, 'r')
    for line in fh:
        toks = line.strip().split('/')
        if len(toks) >= 2:
            newpath = os.path.join(path, toks[1])
            if not os.path.exists(newpath):
                sys.stderr.write("Warning: "+newpath+" does not exist; skipping\n")
                continue
            if toks[0] == "D":
                findfiles(newpath, outfile)
            else:
                outfile.write(newpath+"\n")

def main():
  parser = argparse.ArgumentParser(description="use CVS directory tree to add files to git")
  parser.add_argument("--indir", "-i", help="project directory")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")



  try:
    args = parser.parse_args()
  except IOError, msg:
    parser.error(str(msg))

  writer = codecs.getwriter('utf8')
  outfile = writer(args.outfile)

  files = []
  findfiles(args.indir, outfile)

if __name__ == '__main__':
  main()

