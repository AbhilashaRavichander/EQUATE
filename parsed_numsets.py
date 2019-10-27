class ParsedNumsets:

    def __init__(self):
        self.premise_numsets = []
        self.hypothesis_numsets = []

    def add_numset(self, numset, source):
        if source == "premise":
            self.premise_numsets.append(numset)
        elif source == "hypothesis":
            self.hypothesis_numsets.append(numset)
