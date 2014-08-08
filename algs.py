#!/usr/bin/python
# useful generic algorithms

# 7/28/10: sort entries of a dictionary  by key (from http://code.activestate.com/recipes/52306-to-sort-a-dictionary/)
def sortDict(dict):
    """
    Given a dictionary with sortable keys, return
    list of (key, value) tuples.
    
    dict (dictionary) - the input dictionary

    For just the values, do sortDictValues
    """
    keys = dict.keys()
    keys.sort()
    return map (lambda x: (x, dict[x]), keys)

def sortDictValues(dict):
    """
    Given a dictionary with sortable keys, return
    list of (value).
    
    dict (dictionary) - the input dictionary

    For (key, value) pairs, do sortDict
    """
    keys = dict.keys()
    keys.sort()
    return map (dict.get, keys)




