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
  entryre=re.compile(r"\s*(\S+)=((?:[^\s{}]+)|(?:{{{[^\}]*}}}))\s*")
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
  input can have "(" or ")" quoted lexical items but trickier stuff will bomb out
  '''
  string = re.sub(r'"\("', r'"-LRBJM-"', string)
  string = re.sub(r'"\)"', r'"-RRBJM-"', string)
  string = re.sub('\(', r' ( ', string).split(' ')
#  print string
  for idx, tok in enumerate(string):
    if tok == "(":
      string[idx-1], string[idx] = string[idx], string[idx-1]
#  print ' '.join(string)
  ptree = tree.str_to_tree(' '.join(string))
  for node in ptree.frontier():
    if node.label == '"-LRBJM-"':
      node.label = '"("'
    if node.label == '"-RRBJM-"':
      node.label = '")"'
  return ptree

def get_var_position(string):
  '''
  given a string that might contain a variable position (e.g. x0:NNP)
  return the position as an integer, if it does, or None if it does not.
  '''
  match = re.match(r'x(\d+)', string)
  return int(match.group(1)) if match is not None else None

def target_order_map(string):
  '''
  given a source string with variables contiguous from x0,
  return a source-to-target map.
  e.g. x2 "the" "cow" x0 x1 => (0:2) (1:0) (2:1)
  '''
  ret={}
  nextidx=0
  for tok in string.split():
    pos = get_var_position(tok)
    if pos is not None:
      ret[nextidx]=pos
      nextidx+=1
  return ret


def clean_heads(tree):
  if 'head' in tree.__dict__:
    foo=tree.__dict__.pop('head')
  newchildren=[]
  for c in tree.children:
    newchildren.append(clean_heads(c))
  tree.children = newchildren
  return tree


def head_annotate_tree_from_rule(rule, local=True):
  ''' assume headmarker and TARGET field. create a target tree and annotate with heads.
      if local, local relative. if not, global to root relative '''
  target = parse_rule_tree(rule['TARGET'].strip())
  # head tree is compressed; open it up, but remove whitespace before open paren
  head_tree_text = ' '.join(list(rule['headmarker'].strip('{}').strip()))
  head_tree_text = re.sub(r' +\(', r'(', head_tree_text)
  heads = parse_rule_tree(head_tree_text)
  target = head_annotate_tree(heads, target, relative=None if local else target)
  return target

def head_annotate_tree(heads, target, relative=None):
  '''
  given a RHV head tree and a chiang tree that matches in form, set a boolean "head"
  flag if a child is the head of its immediate parent. If relative is a node in target.
  set the head flag if children are in the head *path* of the root
  '''
  target = clean_heads(target)
  if heads.label != "R":
    raise Exception("Expected root of heads tree to be 'R'")
  if target.is_terminal() or target.is_preterminal():
    # special case: single node. label head and return
    target.head=True
    if target.is_preterminal(): target.children[0].head=True
    return target
  if len(heads.children) != len(target.children):
    raise Exception("Heads tree doesn't match target: "+str(heads)+" vs "+str(target))
  newchildren = []
  for (label, node) in zip(heads.children, target.children):
    # if relative isn't here, no label of any kind
    if relative is None or relative == target:
      node.head = True if label.label == "H" else False
#      print "Setting "+node.label+" to "+str(node.head)+" (top level)"
    newchildren.append(head_annotate_tree_inner(label, node, relative))
  target.children = newchildren
  return target

def head_annotate_tree_inner(heads, target, relative):
  # if not relative, label children based on heads
  # if relative, if parent is head or parent is relative, label children based on heads
  #              if parent is not head, label all children not head
  #              if parent is not labeled, no labels
  if target.is_terminal() or target.is_preterminal():
    if target.is_preterminal() and 'head' in target.__dict__:
      target.children[0].head=target.head
#    print "Short cut for pre/terminal target "+str(target)
    return target
  if len(heads.children) != len(target.children):
    raise Exception("Heads tree doesn't match target: "+str(heads)+" vs "+str(target))
  newchildren=[]
  for (label, node) in zip(heads.children, target.children):
    if relative is None or relative == target or ('head' in target.__dict__ and target.head):
      node.head = True if label.label == "H" else False
#      print "Setting "+node.label+" to "+str(node.head)
    elif ('head' in target.__dict__ and not target.head):
#      print "Setting "+node.label+" to False unilaterally"
      node.head = False
    newchildren.append(head_annotate_tree_inner(label, node, relative))
  target.children=newchildren
  return target
