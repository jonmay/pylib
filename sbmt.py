#! /usr/bin/env python
import argparse
import sys
import re
import tree

# class ParseError(Exception):
#   ''' print out context and point of error in context '''
#   def __init__(self, info, ctxt="", point=-1):
#     Exception.__init__(self, info)
#     self.info=info
#     self.ctxt=ctxt
#     self.point=point
#     print self.ctxt
#     print self.info
#     print self.point
#   def __str__(self):
#     ctxt=self.info
#     if self.point >=0:
#       blocklen=max(self.point, len(self.ctxt))
#       rem=blocklen-self.point-1
#       ctxt=ctxt+"\n"+self.ctxt+"\n"+(" "*self.point)+"^"+(" "*rem)
#     return ctxt

def parse_feat_string(string):
  '''
  given an isi-style string of space separated key=val pairs and key={{{entry with spaces}}} pairs, return
  a dict of those entries. meant to be used by various flavors, i.e. nbest list, rule
  '''
  feats={}
  spos=0
  keyre=re.compile(r"\s*(\S+)=")
  valre=re.compile(r"((?:[^\s{}]+)|(?:{{{[^\}]+}}}))\s*")
  entryre=re.compile(r"\s*(\S+)=((?:[^\s{}]+)|(?:{{{[^\}]+}}}))\s*")
  for match in entryre.findall(string):
    feats[match[0]]=match[1]
  return feats


def parse_nbest(string):
  '''
  given an isi-style nbest entry headed with NBEST, return the feature dictionary
  '''
  fields=string.split()
  if fields[0] != "NBEST":
    raise Exception("String should start with NBEST but starts with "+fields[0])
  return parse_feat_string(' '.join(fields[1:]))

def parse_rule(string):
  '''
  given an isi syntax rule, return the feature dictionary including "SOURCE" and "TARGET"
  '''
  try:
    (rule, rest) = string.split(" ### ")
    feats = parse_feat_string(rest)
    (target, source) = rule.split(" -> ")
    feats['SOURCE'] = source
    feats['TARGET'] = target
    return feats
  except Exception as e:
    raise Exception("could not parse "+string, e)

def parse_rule_tree(string):
  '''
  given a paren-safe a(b c(d e)) tree, return a chiang tree
  '''
  string=re.sub('\(', r' ( ', string).split(' ')
  for idx, tok in enumerate(string):
    if tok == "(":
      string[idx-1], string[idx] = string[idx], string[idx-1]
  return tree.str_to_tree(' '.join(string))

def target_order_map(string):
  '''
  given a source string with variables contiguous from x0,
  return a source-to-target map.
  e.g. x2 "the" "cow" x0 x1 => (0:2) (1:0) (2:1)
  '''
  ret={}
  nextidx=0
  for tok in string.split():
    match = re.match(r'x(\d+)', tok)
    if match is not None:
      ret[nextidx]=int(match.group(1))
      nextidx+=1
  return ret
