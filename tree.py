# tree.py
# David Chiang <chiang@isi.edu>

# Copyright (c) 2004-2006 University of Maryland. All rights
# reserved. Do not redistribute without permission from the
# author. Not for commercial use.

import sgmllib, xml.sax.saxutils
import re

class TreeDeleted(Exception):
    pass

class Node:
    "Tree node"
    def __init__(self, label, children=None):
        self.label = label
        if children is None:
            self.children = []
        else:
            self.children = children
        self.length = 0
        for i in range(len(self.children)):
            self.children[i].parent = self
            self.children[i].order = i
            self.length += self.children[i].length
        if len(self.children) == 0:
            self.length = 1
        self.parent = None
        self.order = 0

    def __str__(self):
        if len(self.children) != 0:
            s = "(" + str(self.label)
            for child in self.children:
                s += " " + child.__str__()
            s += ")"
            return s
        else:
            s = self.label
            s = s.replace("(", "-LRB-")
            s = s.replace(")", "-RRB-")
            return s

    def is_terminal(self):
        return len(self.children) == 0

    def is_preterminal(self):
        return len(self.children) == 1 and self.children[0].is_terminal()

    def descendant(self, addr):
        if len(addr) == 0:
            return self
        else:
            return self.children[addr[0]].descendant(addr[1:])
    
    def _adjust_length(self, delta):
        self.length += delta
        if self.parent is not None:
            self.parent._adjust_length(delta)

    def insert_child(self, i, child):
        child.parent = self
        self.children[i:i] = [child]
        for j in range(i,len(self.children)):
            self.children[j].order = j
        if len(self.children) > 1:
            self._adjust_length(child.length)
        else:
            self._adjust_length(child.length-1) # because self.label changes into nonterminal

    def append_child(self, child):
        self.insert_child(len(self.children), child)

    def delete_child(self, i):
        self.children[i].parent = None
        self.children[i].order = 0
        self._adjust_length(-self.children[i].length)
        self.children[i:i+1] = []
        for j in range(i,len(self.children)):
            self.children[j].order = j

    def detach(self):
        if self.parent:
            self.parent.delete_child(self.order)

    def delete_clean(self):
        "Cleans up childless ancestors"
        parent = self.parent
        if not parent:
            raise TreeDeleted()
        self.detach()
        if len(parent.children) == 0:
            parent.delete_clean()

    def bottomup(self):
        for child in self.children:
            for node in child.bottomup():
                yield node
        yield self

    # preterminal frontier
    def pret_frontier(self):
        if len(self.children) > 1 or (len(self.children) == 1 and not self.children[0].is_terminal()):
            l = []
            for child in self.children:
                l.extend(child.frontier())
            return l
        else:
            return [self]

    def frontier(self):
        if len(self.children) != 0:
            l = []
            for child in self.children:
                l.extend(child.frontier())
            return l
        else:
            return [self]

    def tags(self):
        return [n.label for n in self.pret_frontier()]

    def words(self):
        return [n.label for n in self.frontier()]

    def span(self):
        if self.parent is None:
            return (0,self.length)
        (i, j) = self.parent.span()
        for sister in self.parent.children[:self.order]:
            i += sister.length
        return (i, i+self.length)

    def is_dominated_by(self, node):
        return self is node or (self.parent != None and self.parent.is_dominated_by(node))
    def dominates(self, arg):
        if type(arg) is list:
            flag = 1
            for node in arg:
                flag = flag and node.is_dominated_by(self)
            return flag
        elif isinstance(arg, Node):
            return node.is_dominated_by(self)

    def traversal(self):
        yield self
        for child in self.children:
            for node in child.traversal():
                yield node

    # input: a list of nodes
    # output: lowest node that dominates them
    def cover(self,nodes):
        if len(nodes) == 1:
            return nodes[0]
        elif len(nodes) < 1:
            return None
        elif nodes[0].dominates(nodes[1]):
            return self.cover([nodes[0]] + nodes[2:])
        elif nodes[0].parent == None:
            return None
        else:
            return self.cover([nodes[0].parent] + nodes[1:])

    def fill_span_helper(self, lbarrier, rbarrier):
        if (lbarrier != None and lbarrier.is_dominated_by(self)) or (rbarrier != None and rbarrier.is_dominated_by(self)):
            return None
        if (self.parent != None):
            result = self.parent.fill_span_helper(lbarrier, rbarrier)
            if (result != None):
                return result
        return self

    @staticmethod
    def fill_span(frontier, i, j):
        if (i == j):
            return []
        lbarrier = rbarrier = None
        if i>0:
            lbarrier = frontier[i-1]
        if j<len(frontier):
            rbarrier = frontier[j]
        node = frontier[i].fill_span_helper(lbarrier, rbarrier)
        i += node.length
        result = [node]
        result.extend(Node.fill_span(frontier, i, j))
        return result

    def fill(self, i, j):
        """input: a span
        output: minimum set of nodes that exactly covers them"""
        return Node.fill_span(self.frontier(), i, j)

    def span_helper(self, i, s):
        # don't include terminals
        if len(self.children) == 0:
            return
        s.setdefault((i,i+self.length), []).append(self.label)
        for child in self.children:
            child.span_helper(i, s)
            i += child.length

    def spans(self):
        """return a hash which maps from spans to lists of labels"""
        s = {}
        self.span_helper(0, s)
        return s

def scan_tree(tokens, pos):
    try:
        if tokens[pos] == "(":
            if tokens[pos+1] == "(":
                label = ""
                pos += 1
            else:
                label = tokens[pos+1]
                pos += 2
            children = []
            (child, pos) = scan_tree(tokens, pos)
            while child != None:
                children.append(child)
                (child, pos) = scan_tree(tokens, pos)
            if tokens[pos] == ")":
                return (Node(label, children), pos+1)
            else:
                return (None, pos)
        elif tokens[pos] == ")":
            return (None, pos)
        else:
            label = tokens[pos]
            label = label.replace("-LRB-", "(")
            label = label.replace("-RRB-", ")")
            return (Node(label,[]), pos+1)
    except IndexError:
        return (None, pos)

tokenizer = re.compile(r"\(|\)|[^()\s]+")

def str_to_tree(s):
    tokens = tokenizer.findall(s)
    (tree, n) = scan_tree(tokens, 0)
    if n != len(tokens):
        return None
    return tree

class TreeParser(sgmllib.SGMLParser):
    def __init__(self):
        sgmllib.SGMLParser.__init__(self)
	self.root = self.node = Node(None)

    def unknown_starttag(self, tag, attrs):
        attrs = attrs_to_dict(attrs)
        if "label" in attrs:
            label = attrs["label"]
            del attrs["label"]
        else:
            label = tag
        node = Node(label)
        node.attrs = attrs
        self.node.append_child(node)
        self.node = node
        return None

    def unknown_endtag(self, tag):
        if len(self.node.children) == 0:
            self.node.append_child(Node("-NONE-"))
        self.node = self.node.parent

    def handle_data(self, s):
        for word in s.split():
            self.node.append_child(Node(word))

def attrs_to_str(d):
    if len(d) == 0:
        return ""
    l = [""]+["%s=%s" % (name, xml.sax.saxutils.quoteattr(value)) for (name, value) in d]
    return " ".join(l)

def attrs_to_dict(a):
    d = {}
    for (name, value) in a:
	if d.has_key(name.lower()):
	    raise ValueError, "duplicate attribute names"
	d[name.lower()] = value
    return d

def sgml_to_trees(s, label=None):
    p = TreeParser()
    p.feed(s)
    p.close()
    p.root.label = label
    p.root.attrs = dict()
    return p.root

if __name__ == "__main__":
    import sys
    for line in sys.stdin:
        t = str_to_tree(line)
        ts = str(t)
