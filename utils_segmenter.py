from constants import *
from collections import deque


class Node():
    def __init__(self, value=None):
        self.value = value
        self.children = []

    def __eq__(self, other):
        """Overrides the default implementation
        For our purposes, at the node level, we consider a node equal to another if they share the same value
        and their children share the same value"""
        if isinstance(other, Node):
            is_equal = self.value == other.value and len(self.children) == len(other.children)
            if is_equal:
                for child_ind in range(len(self.children)):
                    if self.children[child_ind].value != other.children[child_ind].value:
                        return False
                return is_equal
        return False

    def __ne__(self, other):
        """Overrides the default implementation (unnecessary in Python 3)"""
        return not self.__eq__(other)

    def set_value(self, value):
        self.value = value

    def set_child_at_index(self, child, index=-1):
        if index == -1:
            self.children.append(child)
        else:
            self.children[index] = child

    def get_value(self):
        return self.value

    def get_child_at_index(self, index=-1):
        assert abs(index) < len(self.children)
        return self.children[index]

    def get_children(self):
        return self.children


class Tree():
    def __init__(self, root):
        '''
        Initialize tree with root
        @param root: root is an object of type Node, representing root of the binary tree
        '''
        self.root = root

    def __eq__(self, other):
        """Overrides the default implementation
        For our purposes, at the node level, we consider a node equal to another if they share the same value
        and their children share the same value"""
        if isinstance(other, Tree):
            return self.get_prefix_traversal(self.root) == self.get_prefix_traversal(other.root)
        return False

    def __ne__(self, other):
        """Overrides the default implementation (unnecessary in Python 3)"""
        return not self.__eq__(other)

    def get_prefix_traversal(self, start_node=None):
        '''
        Get prefix traversal of tree
        :param start_node: node in the tree, which is root of the subtree we
        would like a prefix traversal for
        :return: prefix traversal
        '''

        if start_node == None:
            return []

        def is_pos_tag(node):
            children = node.get_children()
            return len(children) == 1 and children[0] and len(children[0].get_children()) == 0

        # If we reach a POS tag we follow the same format as
        # the Stanford parser prefix
        if is_pos_tag(start_node):
            prefix_traversal = ["(", start_node.value, start_node.get_children()[0].value, ")"]
            return prefix_traversal

        prefix_traversal = ["(", start_node.value]

        for each_child in start_node.get_children():
            prefix_traversal += self.get_prefix_traversal(each_child)

        prefix_traversal.append(")")
        return prefix_traversal

    def get_ancestors(self, query_node, current_node, path=[]):
        '''
        Get all ancestors along the path from root to a query node
        :param query_node: Node object whose ancestors we want
        '''

        if current_node == None:
            return []

        # If we reach our query node
        if current_node == query_node:
            return [current_node]

        found_query = False
        for each_child in current_node.get_children():
            path_to_leaf = self.get_ancestors(query_node, each_child, path)

            if len(path_to_leaf) > 0:
                found_query = True
                path = path_to_leaf
                path.append(current_node)
                return path

        if not found_query:
            return []

    def get_nodes_with_value(self, query_value, start_node, path=[]):
        '''
        Get all nodes with a particular value
        :param query_node: Node object whose ancestors we want
        '''
        nodes_with_value = []

        def visit_all_nodes(query_value, current_node):

            if current_node == None:
                return

            # If we reach our query node
            if current_node.value == query_value:
                nodes_with_value.append(current_node)

            for each_child in current_node.get_children():
                visit_all_nodes(query_value, each_child)

        visit_all_nodes(query_value, start_node)
        return nodes_with_value


def get_subtree(parts, start_index):
    '''
    get_subtree returns the end_index in the parse prefix expression corresponding to a given subtree
    :param parts: prefix expression of constituency parse of the sentence in the form of a list
    :param start_index: start of the subtree
    :return: end_index: end of the subtree in the prefix expression
    '''

    # This is invalid
    if parts[start_index] != '(':
        return -1

    # Create a deque to use it as a stack.
    stack = deque()

    for element_index in range(start_index, len(parts)):

        # Pop a starting bracket
        # for every closing bracket
        if parts[element_index] == ')':
            stack.popleft()

        # Push all starting brackets
        elif parts[element_index] == '(':
            stack.append(parts[element_index])

        # If stack becomes empty
        if not stack:
            end_index = element_index
            return end_index

    return -1


def get_tree(parts, start_index):
    '''
    Returns tree structure
    :param parts:
    :param start_index:
    :return:
    '''

    if start_index >= len(parts):
        return Node(None)

    # Current Node in prefix expression becomes value of the node
    value_index = start_index + 1  # TAG after opening brace
    value = parts[value_index]
    node = Node(value)

    subtree_start = value_index + 1
    while parts[subtree_start] == "(":
        subtree_end = get_subtree(parts, subtree_start)
        if subtree_end - subtree_start == 3:
            pos_tag = parts[subtree_start + 1]
            word = parts[subtree_end - 1]

            child_node = Node(pos_tag)
            word_node = Node(word)

            child_node.set_child_at_index(word_node, -1)
            node.set_child_at_index(child_node, -1)
        else:
            node.set_child_at_index(get_tree(parts, subtree_start), -1)
        subtree_start = subtree_end + 1

    return node


def construct_parse(parse):
    '''
    Converts prefix expression of parse to an expression tree
    :param parse: constituency parse of the sentence in prefix
    :return: expression tree of constituency parse of the sentence
    '''
    parse = parse.replace("(", " ( ")
    parse = parse.replace(")", " ) ")
    parts = parse.split()
    start_index = 0

    root = get_tree(parts, start_index)
    parse_tree = Tree(root)

    return parse_tree


def strip_parse(parse):
    parse = " ".join(parse)
    parse = parse.replace("(", " ")
    parse = parse.replace(")", " ")
    for each_postag in tagset:
        parse = parse.replace(each_postag, "")
    parse = " ".join(parse.split())
    return parse
