import pickle
from collections import deque

class TreeGenerator:

    def __init__(self):#, premise, hypothesis, prem_q, hyp_q, ph_pairs):
        # self.premise = premise
        # self.hypothesis = hypothesis
        # self.prem_q = prem_q
        # self.hyp_q = hyp_q
        # self.ph_pairs = ph_pairs

        self.weight = 10 #can be fiddled with
        self.operators = ['+', '-', '*', '/', '=', '<='] #<= indicates subset relation for now. We need to add more subset operations

    def get_types(self, pq, hq):
        types = []
        for quantity in pq:
            types += quantity['Units']
        types += hq['Units']
        type_list = list(set(types))
        return type_list

    def generate_trees(self, hq, pqlist, length):
        #-1 stands for hypothesis quantity, premise quantities are represented by their index in the list, operators are strings
        trees = []
        tree_tails = [[-1, '=']]   #[-1, '<=']] - FIX LATER FOR RANGES
        if length == 3:   #Postfix expressions ph= or ph<=
            for tail in tree_tails:
                for num, pq in enumerate(pqlist):
                    trees.append([num] + tail)
        elif length == 5:    #Postfix expressions ppoh= or ppoh<=
            for tail in tree_tails:
                for operator in self.operators[:-2]:
                    for num2, q2 in enumerate(pqlist):
                        for num1, q1 in enumerate(pqlist):
                            if num1 == num2:
                                continue
                            trees.append([num1, num2, operator] + tail)
        elif length == 7:    #Postfix expressions ppopoh=, ppopoh<=, pppooh=, pppooh<=
            for tail in tree_tails:
                for operator in self.operators[:-2]:
                    #ppopoh= or ppopoh<=
                    for num3, q3 in enumerate(pqlist):
                        for operator2 in self.operators[:-2]:
                            for num2, q2 in enumerate(pqlist):
                                for num1, q1 in enumerate(pqlist):
                                    if num1 == num2 or num2 == num3 or num3 == num1:
                                        continue
                                    trees.append([num1, num2, operator2, num3, operator] + tail)
                    #pppooh= or pppooh<=
                    for operator2 in self.operators[:-2]:
                        for num3, q3 in enumerate(pqlist):
                            for num2, q2 in enumerate(pqlist):
                                for num1, q1 in enumerate(pqlist):
                                    if num1 == num2 or num2 == num3 or num3 == num1:
                                        continue
                                    trees.append([num1, num2, num3, operator2, operator] + tail)
        elif length == 9:    #Postfix expression ppoppooh= or ppoppooh<=
            for tail in tree_tails:
                for operator in self.operators[:-2]:
                    for operator2 in self.operators[:-2]:
                        for num4, q4 in enumerate(pqlist):
                            for num3, q3 in enumerate(pqlist):
                                for operator3 in self.operators[:-2]:
                                    for num2, q2 in enumerate(pqlist):
                                        for num1, q1 in enumerate(pqlist):
                                            if num1 == num2 or num2 == num3 or num3 == num4 or num2 == num4 or num1 == num4 or num1 == num3:
                                                continue
                                            trees.append([num1, num2, operator3, num3, num4, operator3, operator] + tail)
        return trees

    def create_valued_postfix(self, postfix, hq, pqlist):
        mod_postfix = []
        for index in postfix:
            if isinstance(index, int) and index > -1:
                mod_postfix.append(pqlist[index]['Value'][1][0]) ##FIX FOR RANGES
            elif index == -1:
                mod_postfix.append(hq['Value'][1][0])
            else:
                mod_postfix.append(index)
        return mod_postfix

    def solve_postfix(self, expression):
        stack = deque()
        for element in expression:
            if element not in self.operators:
                stack.append(element)
            else:
                roperand = stack.pop()
                loperand = stack.pop()
                if element == '+':
                    if loperand == 0 or roperand == 0:
                        return False
                    stack.append(loperand+roperand)
                elif element == '-':
                    if roperand == 0:
                        return False
                    stack.append(loperand-roperand)
                elif element == '*':
                    if loperand == 1 or roperand == 1:
                        return False
                    stack.append(loperand*roperand)
                elif element == '/':
                    if roperand == 1 or roperand == 0:
                        return False
                    stack.append(loperand/roperand)
                elif element == '=':
                    if loperand == roperand:
                        return True
                    else:
                        return False
                else:
                    if loperand <= roperand:  ##FIX LATER FOR RANGES
                        return True
        return False

    def is_valid_tree(self, postfix, hq, pqlist):
        mod_postfix = self.create_valued_postfix(postfix, hq, pqlist)
        #print mod_postfix
        return self.solve_postfix(mod_postfix)

if __name__ == '__main__':
    #Main can be removed later, only used for testing
    data = pickle.load(open('extractor.pkl', 'rb'))
    for sample_num, sample in enumerate(data):
        print 'Processing '+str(sample_num)+'...'
        premise = sample['input_pair']['sentence1']
        hypothesis = sample['input_pair']['sentence2']
        prem_q = sample['premise_quantity_sets']
        hyp_q = sample['hypothesis_quantity_sets']
        if 'ph_pairs' not in sample:
            continue
        ph_pairs = sample['ph_pairs']
        complete_equation_data = []
        tree_generator = TreeGenerator(premise, hypothesis, prem_q, hyp_q, ph_pairs)
        #Go through all hypothesis quantities to get justification for each
        for q in tree_generator.hyp_q:
            equation_data = {}
            if not q['Value'] or len(q['Value'][1]) > 1:
                continue
            current_pq = []
            for pair in tree_generator.ph_pairs:
                if q == pair[-1]:
                    for x in pair[:-1]:
                        if x['Value'] and len(x['Value'][1]) == 1:  ##FIX FOR RANGES
                            current_pq += pair[:-1]
            prem_qlist = []
            for x in current_pq:
                if x not in prem_qlist:
                    prem_qlist.append(x)

            #Start populating equation-related data (hypothesis quantity/ all associated premise-related quantities) 
            equation_data['hypothesis_quantity'] = q
            equation_data['premise_quantities'] = prem_qlist

            #For exhaustive generation, we restrict ourselves to trees of depth 3. Possible equation lengths are 3,5,7 and 9
            equation_data['trees'] = []
            for length in range(3,10,2):
                possible_trees = tree_generator.generate_trees(q, prem_qlist, length)
                valid_trees = []
                for tree in possible_trees:
                    if tree_generator.is_valid_tree(tree, q, prem_qlist):
                        equation_data['trees'].append(tree)
            complete_equation_data.append(equation_data)
        sample['all_equation_data'] = complete_equation_data
        #print complete_equation_data
        #raw_input()
    pickle.dump(data, open('exhaustive_equations.pkl', 'wb'))

