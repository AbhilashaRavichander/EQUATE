'''
Data structure which holds compatible pairs or triples of numsets
Compatible pairs/ triples are constructed by the numset pruner
'''

class CompatibleNumsets:

    def __init__(self, args):
        
        # Since compatible numsets can be either pairs or triples,
        # each pair can have one or two premise numsets
        # The last numset returned by the pruner is always
        # the hypothesis numset

        self.hypothesis_numset = args[-1]
        self.premise_numsets = args[:-1]
