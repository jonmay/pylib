#! /usr/bin/env python
import argparse
import sys
import codecs
from collections import defaultdict as dd
import re

def main():
  parser = argparse.ArgumentParser(description="Given data with a key and the keys in an order, put the data in order")
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input file")
  parser.add_argument("--keyfile", "-k", type=argparse.FileType('r'), help="key file")
  parser.add_argument("--field", "-f", default=0, help="which field has the key? (default 0)")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")



  try:
    args = parser.parse_args()
  except IOError, msg:
    parser.error(str(msg))

  reader = codecs.getreader('utf8')
  writer = codecs.getwriter('utf8')
  infile = reader(args.infile)
  keyfile = reader(args.keyfile)
  outfile = writer(args.outfile)

  data = dict()
  for line in infile:
      data[line.strip().split()[args.field]]=line
  for line in keyfile:
      outfile.write(data[line.strip()])

if __name__ == '__main__':
  main()
