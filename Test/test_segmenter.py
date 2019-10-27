import unittest
import pytest
from utils_parser import *
from utils_segmenter import *
from QuantitySegmenter import *
import re


class TestSegmenter(unittest.TestCase):
    """
    Very simple unit tests, just to ensure all segmenter modules
    are providing the expected functionality
    """

    #



    def test_prefix_traversal(self):
        """
        Test that the tree is constructed correctly.
        """
        prefix_expression = "(ROOT \n(S \n(PP (IN during) \n(NP \n(NP \n(NP (NN reinsdorf) (POS 's)) \n(CD 24) (NNS " \
                            "seasons)) \n(PP (IN as)  \n(NP (NN chairman))))) \n(, ,) \n(NP (PRP he)) \n(VP (VBD " \
                            "excelled))))"
        expression_tree = construct_parse(prefix_expression)
        prefix_traversal = " ".join(expression_tree.get_prefix_traversal(expression_tree.root))

        gold_traversal = prefix_expression.replace("\n", "").replace("(", " ( ").replace(")", " ) ").strip()

        assert gold_traversal.replace(" ", "") == prefix_traversal.replace(" ", "")

    def test_get_ancestors(self):
        """
        Test that the get ancestors functionality returns the correct ancestor chain
        """
        prefix_expression = "(ROOT \n(S \n(PP (IN during) \n(NP \n(NP \n(NP (NN reinsdorf) (POS 's)) \n(CD 24) (NNS " \
                            "seasons)) \n(PP (IN as)  \n(NP (NN chairman))))) \n(, ,) \n(NP (PRP he)) \n(VP (VBD " \
                            "excelled))))"
        expression_tree = construct_parse(prefix_expression)
        path = expression_tree.get_ancestors(Node("chairman"), expression_tree.root)
        path_values = [node.value for node in path]
        assert path_values == ['chairman', 'NN', 'NP', 'PP', 'NP', 'PP', 'S', 'ROOT']

    def test_get_nodes_with_value(self):
        """
        Test that the get ancestors functionality returns the correct ancestor chain
        """
        prefix_expression = "(ROOT \n(S \n(PP (IN during) \n(NP \n(NP \n(NP (NN reinsdorf) (POS 's)) \n(CD 24) (NNS " \
                            "seasons)) \n(PP (IN as)  \n(NP (NN chairman))))) \n(, ,) \n(NP (PRP he)) \n(VP (VBD " \
                            "excelled))))"
        expression_tree = construct_parse(prefix_expression)
        path_PP = expression_tree.get_nodes_with_value("PP", expression_tree.root)
        path_NP = expression_tree.get_nodes_with_value("NP", expression_tree.root)
        assert len(path_PP) == prefix_expression.count("(PP") and len(path_NP) == prefix_expression.count("(NP")

    def test_empty_parse(self):
        """
        The simplest possible test, just ensuring there aren't syntax errors.
        """
        prefix_expression = ""
        expression_tree = construct_parse(prefix_expression)
        print(expression_tree.root.value)
        assert expression_tree.root.value == None

    def test_segmenter(self):
        self.segmenter = Segmenter()
        text = "during X 's 29 seasons as chairman of the chicago bulls , the team captured the title seven times , " \
               "including in 2000 "
        quantity_phrases, output, noun_phrases = self.segmenter.segment(text)
        assert len(quantity_phrases) == 3
