from nltk.data import load
from nltk.tree import ParentedTree
from constants import *
from utils_segmenter import *
from pycorenlp import StanfordCoreNLP
import pickle
from word2number import w2n


class Segmenter():
    """
    Inputs:
        args:
            sentence : sentence to extract quantity mentions from
            parse : constituency parse of sentence
    Outputs:
        quantity mentions : list of noun phrases containing quantities from parse
    """

    def __init__(self):
        pass
        # self.nlp = StanfordCoreNLP('http://localhost:9000')

    def segment(self, parse):
        '''Extracts and returns all quantity mentions in a text.
        Quantity mentions are defined as least ancestor noun phrases containing quantities.
        @param text: Sentence (typically) that we want to extract quantity mentions from
        @returns quantity_mentions: List of quantity mentions found in sentence'''

        noun_phrases, quantity_phrases = [], []
        for each_parse_sentence in parse:
            parse_tree = construct_parse(each_parse_sentence)
            quantities = parse_tree.get_nodes_with_value("CD", parse_tree.root)
            ancestor_chains = [parse_tree.get_ancestors(quantity, parse_tree.root) for quantity in quantities]

            for each_chain in ancestor_chains:
                chain_values = [node.value for node in each_chain]
                lca_index = -1

                # Finds least common noun phrase
                if "NP" in chain_values:
                    lca_index = chain_values.index("NP")

                # FInds least common NP-TMP phrase
                if "NP-TMP" in chain_values:
                    tmp_index = chain_values.index("NP-TMP")
                    if lca_index == -1 or tmp_index < lca_index:
                        lca_index = tmp_index

                # Extracts first noun phrase node in each ancestor chain
                if lca_index != -1:
                    noun_phrases.append(each_chain[lca_index])

            quantity_phrases += [parse_tree.get_prefix_traversal(noun_node) for noun_node in noun_phrases]

        return quantity_phrases, noun_phrases
