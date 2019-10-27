import pickle
from gurobipy import *
import copy
from collections import deque


class ILPEquationGenerator:
    def __init__(self):
        self.weight = 10  # Using setting described by original authors
        self.operators = ['+', '-', '*', '/', 'u', 'i', 'd', '=', '<=']
        self.num_solutions = 50  # Increase to get more trees

    def create_ilp_model(self):
        # Give all compatible premise numsets for a hypothesis numset
        # Ranges should follow single valued numsets
        self.model = Model('TreeGen')
        self.model.setParam(GRB.Param.Threads, 10)  # Increase to make solving faster
        self.model.setParam(GRB.Param.PoolSearchMode, 2)  # Retrieves top 2 solutions
        self.model.setParam(GRB.Param.PoolSolutions, self.num_solutions)  # Increase to get more solutions

    def get_types(self, premise_numsets, hypothesis_numset):
        types = []
        for quantity in premise_numsets:
            types += quantity.unit
        types += hypothesis_numset.unit
        type_list = list(set(types))
        self.type_list = type_list

    def add_ilp_vars(self, premise_numsets, hypothesis_numset, length):
        self.get_types(premise_numsets, hypothesis_numset)
        self.symbol_list = copy.deepcopy(premise_numsets)
        found = -1000
        for index, quantity in enumerate(premise_numsets):
            if len(quantity.value[1]) == 2:
                self.separator = index  # Indicates split point between single values and ranges
                found = index
                break
        if found == -1000:
            self.separator = len(premise_numsets)
        self.symbol_list.append(hypothesis_numset)  # We do this to include hyp quantity in generated equation tree
        self.symbol_list += self.operators
        indices = range(length)
        self.xvars = self.model.addVars(indices, lb=0, ub=len(self.symbol_list) - 1, vtype='I', name='x')
        self.cvars = self.model.addVars(indices, vtype='B', name='c')
        self.ovars = self.model.addVars(indices, vtype='B', name='o')
        self.rvars = self.model.addVars(indices, vtype='B', name='r')
        self.dvars = self.model.addVars(indices, lb=0, vtype='I', name='d')
        self.tvars = self.model.addVars(indices, lb=0, ub=len(self.type_list) - 1, vtype='I', name='t')

        # these are variables to keep track of operand 1 for each operator
        self.op1idxvars = self.model.addVars(indices, lb=0, ub=length - 2, vtype='I', name='op1idx')
        self.op1xvars = self.model.addVars(indices, lb=0, ub=len(self.symbol_list) - 1, vtype='I', name='op1x')
        self.op1cvars = self.model.addVars(indices, vtype='B', name='op1c')
        self.op1ovars = self.model.addVars(indices, vtype='B', name='op1o')
        self.op1tvars = self.model.addVars(indices, lb=0, ub=len(self.type_list) - 1, vtype='I', name='op1t')
        self.op1rvars = self.model.addVars(indices, vtype='B', name='op1r')

        # these are extra logical variables to keep track of conditions for operand access/ type consistency because
        # gurobi is dumb
        self.deqvars = self.model.addVars(indices, indices, vtype='B', name='deq')
        self.dgtvars = self.model.addVars(indices, indices, vtype='B', name='dgt')
        self.dltvars = self.model.addVars(indices, indices, vtype='B', name='dlt')
        self.opjeqvars = self.model.addVars(indices, indices, vtype='B', name='opjeq')
        self.opjgtvars = self.model.addVars(indices, indices, vtype='B', name='opjgt')
        self.opjltvars = self.model.addVars(indices, indices, vtype='B', name='opjlt')
        self.xjvars = self.model.addVars(indices, range(len(self.symbol_list)), vtype='B', name='xj')
        self.top1teqvars = self.model.addVars(indices, indices, lb=0, vtype='B', name='top1teq')
        self.top1tgtvars = self.model.addVars(indices, indices, lb=0, vtype='B', name='top1tgt')
        self.top1tltvars = self.model.addVars(indices, indices, lb=0, vtype='B', name='top1tlt')
        self.tteqvars = self.model.addVars(indices, indices, lb=0, vtype='B', name='tteq')
        self.ttgtvars = self.model.addVars(indices, indices, lb=0, vtype='B', name='ttgt')
        self.ttltvars = self.model.addVars(indices, indices, lb=0, vtype='B', name='ttlt')
        self.model.update()

    def add_ilp_constraints(self, length):
        # Definitional constraints - all constraints are hard
        # Range restriction for constant variables
        for i in range(length):
            self.model.addConstr(
                (self.cvars[i] == 1) >> (self.xvars[i] <= (len(self.symbol_list) - len(self.operators) - 1)),
                name='crange_' + str(i))
        for i in range(length):
            self.model.addConstr(
                (self.rvars[i] == 1) >> (self.xvars[i] <= (len(self.symbol_list) - len(self.operators) - 1)),
                name='rrange_' + str(i))

        for i in range(length):
            self.model.addConstr(
                (self.ovars[i] == 1) >> (self.xvars[i] >= (len(self.symbol_list) - len(self.operators))),
                name='orange_' + str(i))
        # Constant/Operator uniqueness constraint
        for i in range(length):
            self.model.addConstr((self.cvars[i] + self.ovars[i] + self.rvars[i]) == 1, name='counique_' + str(i))

        # Stack depth constraints (initial depth & depth update)
        self.model.addConstr(self.dvars[0] == 0, name='depth_init')
        for i in range(1, length):
            self.model.addConstr((self.dvars[i - 1] - (2 * self.ovars[i]) + 1) == self.dvars[i], name='sd_' + str(i))

        # First two elements must be operands
        self.model.addConstr((self.cvars[0] + self.rvars[0]) == 1)
        self.model.addConstr((self.cvars[1] + self.rvars[1]) == 1)

        # Last operator has to be = or <=
        self.model.addConstr(self.xvars[length - 1] >= (len(self.symbol_list) - 2), name='lastop')

        # Last quantity has to be hypothesis quantity
        self.model.addConstr(self.xvars[length - 2] == (len(self.symbol_list) - len(self.operators) - 1), name='lastq')

        # Set range/ constant for hypothesis quantity
        if len(self.symbol_list[len(self.symbol_list) - len(self.operators) - 1].value[1]) == 1:
            self.model.addConstr(self.cvars[length - 2] == 1, name='hyp_con')
        else:
            self.model.addConstr(self.rvars[length - 2] == 1, name='hyp_range')

        # All other quantities cannot be hypothesis quantities, plus take care of range/non-range things
        for i in range(length - 2):
            if self.separator > 0:
                self.model.addConstr((self.cvars[i] == 1) >> (self.xvars[i] <= (self.separator - 1)),
                                     name='nohypc_' + str(i))
            else:
                self.model.addConstr(self.cvars[i] == 0)  # if self.separator=0 then that means there are no constants
            if self.separator < (len(self.symbol_list) - len(self.operators) - 1):  # some ranges exist
                self.model.addConstr((self.rvars[i] == 1) >> (self.xvars[i] >= self.separator),
                                     name='nohypr1_' + str(i))
                self.model.addConstr(
                    (self.rvars[i] == 1) >> (self.xvars[i] <= (len(self.symbol_list) - len(self.operators) - 2)),
                    name='nohypr2_' + str(i))
            else:
                self.model.addConstr(self.rvars[i] == 0)

        # All other operators cannot be = or <=
        for i in range(length - 2):
            self.model.addConstr((self.ovars[i] == 1) >> (self.xvars[i] <= (len(self.symbol_list) - 3)),
                                 name='noeq_' + str(i))

        # Use a premise quantity at most once in a tree
        for j in range(len(self.symbol_list) - len(self.operators)):
            constraint = LinExpr()
            for i in range(length):
                constraint.addTerms(1, self.xjvars[i, j])
            self.model.addConstr(constraint, GRB.LESS_EQUAL, 1, name='premuse_' + str(j))

        # Stack depth and operand 1 equality constraints
        for i in range(length):
            for j in range(length):
                self.model.addConstr((self.deqvars[i, j] == 1) >> (self.dvars[i] == self.dvars[j]),
                                     name='sde1_' + str(i) + '_' + str(j))
                self.model.addConstr((self.dgtvars[i, j] == 1) >> (self.dvars[i] >= (self.dvars[j] + 1)),
                                     name='sde2_' + str(i) + '_' + str(j))
                self.model.addConstr((self.dltvars[i, j] == 1) >> (self.dvars[i] <= (self.dvars[j] - 1)),
                                     name='sde3_' + str(i) + '_' + str(j))
                self.model.addConstr((self.deqvars[i, j] + self.dgtvars[i, j] + self.dltvars[i, j]) == 1,
                                     name='sde4_' + str(i) + '_' + str(j))
                self.model.addConstr((self.opjeqvars[i, j] == 1) >> (self.op1idxvars[i] == j),
                                     name='opj1_' + str(i) + '_' + str(j))
                self.model.addConstr((self.opjgtvars[i, j] == 1) >> (self.op1idxvars[i] >= (j + 1)),
                                     name='opj2_' + str(i) + '_' + str(j))
                self.model.addConstr((self.opjltvars[i, j] == 1) >> (self.op1idxvars[i] <= (j - 1)),
                                     name='opj3_' + str(i) + '_' + str(j))
                self.model.addConstr((self.opjeqvars[i, j] + self.opjltvars[i, j] + self.opjgtvars[i, j]) == 1,
                                     name='opj4_' + str(i) + '_' + str(j))

        # Operand 1 initialization constraints
        self.model.addConstr(self.op1idxvars[0] == 0, name='op10')
        self.model.addConstr(self.op1idxvars[1] == 0, name='op11')

        # Operand access constraints
        for i in range(2, length):
            self.model.addConstr(self.op1idxvars[i] <= i - 2, name='opa1_' + str(i))  # second operator is always i-1,
            # first operator must be an index before that
            self.model.addConstr(self.op1idxvars[i] <= ((length - 1) * self.ovars[i]), name='op12_' + str(i))  # if
            # not-operator, left operand is irrelevant (==0)
            for j in range(i - 1):
                self.model.addConstr(
                    (self.ovars[i] == 1) >> (self.deqvars[(i, j)] <= (self.opjeqvars[(i, j)] + self.opjgtvars[i, j])),
                    name='doo1_' + str(i) + '_' + str(j))
                self.model.addConstr((self.ovars[i] == 1) >> (
                (self.dgtvars[i, j] + self.dltvars[i, j]) <= (self.opjgtvars[i, j] + self.opjltvars[i, j])),
                                     name='doo2_' + str(i) + '_' + str(j))

        # Constraints to maintain meta-information for operand 1
        for i in range(length):
            for j in range(length):
                self.model.addConstr((self.opjeqvars[i, j] == 1) >> (self.op1xvars[i] == self.xvars[j]),
                                     name='opx_' + str(i) + '_' + str(j))
                self.model.addConstr((self.opjeqvars[i, j] == 1) >> (self.op1xvars[i] == self.xvars[j]),
                                     name='opx_' + str(i) + '_' + str(j))
                self.model.addConstr((self.opjeqvars[i, j] == 1) >> (self.op1cvars[i] == self.cvars[j]),
                                     name='opc_' + str(i) + '_' + str(j))
                self.model.addConstr((self.opjeqvars[i, j] == 1) >> (self.op1ovars[i] == self.ovars[j]),
                                     name='opv_' + str(i) + '_' + str(j))
                self.model.addConstr((self.opjeqvars[i, j] == 1) >> (self.op1tvars[i] == self.tvars[j]),
                                     name='opt_' + str(i) + '_' + str(j))
                self.model.addConstr((self.opjeqvars[i, j] == 1) >> (self.op1rvars[i] == self.rvars[j]),
                                     name='opr_' + str(i) + '_' + str(j))

        # Syntactic validity constraints for postfix expression trees - all constraints are hard
        # Stack validity
        self.model.addConstr(self.dvars[length - 1] == 0, name='depth_end')

        # Type consistency constraints - all constraints are hard
        # Constraints to store indicators for x-assignments
        for i in range(length):
            constraint = LinExpr()
            for j in range(len(self.symbol_list)):
                self.model.addConstr((self.xjvars[i, j] == 1) >> (self.xvars[i] == j),
                                     name='xassign_' + str(i) + '_' + str(j))
                constraint.addTerms(1, self.xjvars[i, j])
            self.model.addConstr(constraint, GRB.EQUAL, 1, name='xrow_' + str(i))

        for i in range(length):
            for j in range(len(self.symbol_list) - len(self.operators)):
                if self.symbol_list[j].unit:
                    k = self.type_list.index(self.symbol_list[j].unit[0])
                    self.model.addConstr((self.xjvars[i, j] == 1) >> (self.tvars[i] == k),
                                         name='typeassign_' + str(i) + '_' + str(j))

        # These constraints just correctly assign values to the type equality variables
        for i in range(length):
            for j in range(length):
                self.model.addConstr((self.top1teqvars[i, j] == 1) >> (self.tvars[i] == self.op1tvars[j]),
                                     name='top1_' + str(i) + '_' + str(j))
                self.model.addConstr((self.top1tgtvars[i, j] == 1) >> (self.tvars[i] >= (self.op1tvars[j] + 1)),
                                     name='top2_' + str(i) + '_' + str(j))
                self.model.addConstr((self.top1tltvars[i, j] == 1) >> (self.tvars[i] <= (self.op1tvars[j] - 1)),
                                     name='top3_' + str(i) + '_' + str(j))
                self.model.addConstr((self.top1teqvars[i, j] + self.top1tgtvars[i, j] + self.top1tltvars[i, j]) == 1,
                                     name='top4_' + str(i) + '_' + str(j))
                self.model.addConstr((self.tteqvars[i, j] == 1) >> (self.tvars[i] == self.tvars[j]),
                                     name='top5_' + str(i) + '_' + str(j))
                self.model.addConstr((self.ttgtvars[i, j] == 1) >> (self.tvars[i] >= (self.tvars[j] + 1)),
                                     name='top6_' + str(i) + '_' + str(j))
                self.model.addConstr((self.ttltvars[i, j] == 1) >> (self.tvars[i] <= (self.tvars[j] - 1)),
                                     name='top7_' + str(i) + '_' + str(j))
                self.model.addConstr((self.tteqvars[i, j] + self.ttgtvars[i, j] + self.ttltvars[i, j]) == 1,
                                     name='top8_' + str(i) + '_' + str(j))

        # Constant/range semantics for operators
        # for i in range(2, length):
        #    model.addConstr((self.xjvars[i, self.symbol_list.index('+')] == 1) >> (self.cvars[i] == self.cvars[
        # i-1]), name='crsem1_'+str(i))
        #    model.addConstr((self.xjvars[i, self.symbol_list.index('-')] == 1) >> (self.cvars[i] == self.cvars[
        # i-1]), name='crsem2_'+str(i))
        #    model.addConstr((self.xjvars[i, self.symbol_list.index('*')] == 1) >> (self.cvars[i] == self.cvars[
        # i-1]), name='crsem3_'+str(i))
        #    model.addConstr((self.xjvars[i, self.symbol_list.index('/')] == 1) >> (self.cvars[i] == self.cvars[
        # i-1]), name='crsem4_'+str(i))
        #    model.addConstr((self.xjvars[i, self.symbol_list.index('=')] == 1) >> (self.cvars[i] == self.cvars[
        # i-1]), name='crsem5_'+str(i))
        #    model.addConstr((self.xjvars[i, self.symbol_list.index('u')] == 1) >> (self.cvars[i] == self.cvars[
        # i-1]), name='crsem6_'+str(i))
        #    model.addConstr((self.xjvars[i, self.symbol_list.index('i')] == 1) >> (self.cvars[i] == self.cvars[
        # i-1]), name='crsem7_'+str(i))
        #    model.addConstr((self.xjvars[i, self.symbol_list.index('d')] == 1) >> (self.cvars[i] == self.cvars[
        # i-1]), name='crsem8_'+str(i))
        #    model.addConstr((self.xjvars[i, self.symbol_list.index('<=')] == 1) >> (self.cvars[i] == self.cvars[
        # i-1]), name='crsem9_'+str(i))

        # Type semantics for operators
        for i in range(2, length):
            self.model.addConstr(
                (self.xjvars[i, self.symbol_list.index('+')] == 1) >> (self.tvars[i - 1] == self.op1tvars[i]),
                name='tsem1_' + str(i))
            self.model.addConstr(
                (self.xjvars[i, self.symbol_list.index('-')] == 1) >> (self.tvars[i - 1] == self.op1tvars[i]),
                name='tsem2_' + str(i))
            self.model.addConstr(
                (self.xjvars[i, self.symbol_list.index('=')] == 1) >> (self.tvars[i - 1] == self.op1tvars[i]),
                name='tsem3_' + str(i))
            self.model.addConstr(
                (self.xjvars[i, self.symbol_list.index('+')] == 1) >> (self.tvars[i] == self.tvars[i - 1]),
                name='tsem4_' + str(i))
            self.model.addConstr(
                (self.xjvars[i, self.symbol_list.index('-')] == 1) >> (self.tvars[i] == self.tvars[i - 1]),
                name='tsem5_' + str(i))
            self.model.addConstr(
                (self.xjvars[i, self.symbol_list.index('=')] == 1) >> (self.tvars[i] == self.tvars[i - 1]),
                name='tsem6_' + str(i))
            self.model.addConstr(
                (self.xjvars[i, self.symbol_list.index('/')] == 1) >> (self.tvars[i] == self.op1tvars[i]),
                name='tsem7_' + str(i))
            self.model.addConstr((self.xjvars[i, self.symbol_list.index('*')] == 1) >> (
            (self.top1tgtvars[i - 1, i] + self.top1tltvars[i - 1, i]) == 1), name='tsem8_' + str(i))
            self.model.addConstr((self.xjvars[i, self.symbol_list.index('/')] == 1) >> (
            (self.top1tgtvars[i - 1, i] + self.top1tltvars[i - 1, i]) == 1), name='tsem9_' + str(i))
            self.model.addConstr((self.xjvars[i, self.symbol_list.index('*')] == 1) >> (
            (self.tteqvars[i, i - 1] + self.top1teqvars[i, i]) == 1), name='tsem10_' + str(i))
            # adding range operators
            self.model.addConstr(
                (self.xjvars[i, self.symbol_list.index('u')] == 1) >> (self.tvars[i - 1] == self.op1tvars[i]),
                name='tsem11_' + str(i))
            self.model.addConstr(
                (self.xjvars[i, self.symbol_list.index('i')] == 1) >> (self.tvars[i - 1] == self.op1tvars[i]),
                name='tsem12_' + str(i))
            self.model.addConstr(
                (self.xjvars[i, self.symbol_list.index('d')] == 1) >> (self.tvars[i - 1] == self.op1tvars[i]),
                name='tsem13_' + str(i))
            self.model.addConstr(
                (self.xjvars[i, self.symbol_list.index('<=')] == 1) >> (self.tvars[i - 1] == self.op1tvars[i]),
                name='tsem14_' + str(i))
            self.model.addConstr(
                (self.xjvars[i, self.symbol_list.index('u')] == 1) >> (self.tvars[i] == self.tvars[i - 1]),
                name='tsem15_' + str(i))
            self.model.addConstr(
                (self.xjvars[i, self.symbol_list.index('i')] == 1) >> (self.tvars[i] == self.tvars[i - 1]),
                name='tsem16_' + str(i))
            self.model.addConstr(
                (self.xjvars[i, self.symbol_list.index('d')] == 1) >> (self.tvars[i] == self.tvars[i - 1]),
                name='tsem17_' + str(i))
            self.model.addConstr(
                (self.xjvars[i, self.symbol_list.index('<=')] == 1) >> (self.tvars[i] == self.tvars[i - 1]),
                name='tsem18_' + str(i))

        # adding operator-operand consistency to handle range operation validity
        for i in range(2, length):
            if self.separator == 0:  # no constants
                self.model.addConstr((self.xjvars[i, self.symbol_list.index('+')] + self.xjvars[
                    i, self.symbol_list.index('-')] + self.symbol_list.index('*') + self.xjvars[
                                          i, self.symbol_list.index('/')]) == 0, name='nocon')
            elif self.separator == (len(self.symbol_list) - len(self.operators) - 1):  # no ranges
                self.model.addConstr((self.xjvars[i, self.symbol_list.index('u')] + self.xjvars[
                    i, self.symbol_list.index('i')] + self.xjvars[i, self.symbol_list.index('d')]) == 0, name='norange')
            else:
                self.model.addConstr((self.xjvars[i, self.symbol_list.index('+')] == 1) >> (self.cvars[i - 1] == 1),
                                     name='opcon1_' + str(i))
                self.model.addConstr((self.xjvars[i, self.symbol_list.index('+')] == 1) >> (self.op1cvars[i] == 1),
                                     name='opcon2_' + str(i))
                self.model.addConstr((self.xjvars[i, self.symbol_list.index('-')] == 1) >> (self.cvars[i - 1] == 1),
                                     name='opcon3_' + str(i))
                self.model.addConstr((self.xjvars[i, self.symbol_list.index('-')] == 1) >> (self.op1cvars[i] == 1),
                                     name='opcon4_' + str(i))
                self.model.addConstr((self.xjvars[i, self.symbol_list.index('*')] == 1) >> (self.cvars[i - 1] == 1),
                                     name='opcon5_' + str(i))
                self.model.addConstr((self.xjvars[i, self.symbol_list.index('*')] == 1) >> (self.op1cvars[i] == 1),
                                     name='opcon6_' + str(i))
                self.model.addConstr((self.xjvars[i, self.symbol_list.index('/')] == 1) >> (self.cvars[i - 1] == 1),
                                     name='opcon7_' + str(i))
                self.model.addConstr((self.xjvars[i, self.symbol_list.index('/')] == 1) >> (self.op1cvars[i] == 1),
                                     name='opcon8_' + str(i))
                self.model.addConstr((self.xjvars[i, self.symbol_list.index('=')] == 1) >> (self.cvars[i - 1] == 1),
                                     name='opcon9_' + str(i))
                self.model.addConstr((self.xjvars[i, self.symbol_list.index('=')] == 1) >> (self.op1cvars[i] == 1),
                                     name='opcon10_' + str(i))
                self.model.addConstr((self.xjvars[i, self.symbol_list.index('u')] == 1) >> (self.rvars[i - 1] == 1),
                                     name='opcon11_' + str(i))
                self.model.addConstr((self.xjvars[i, self.symbol_list.index('u')] == 1) >> (self.op1rvars[i] == 1),
                                     name='opcon12_' + str(i))
                self.model.addConstr((self.xjvars[i, self.symbol_list.index('i')] == 1) >> (self.rvars[i - 1] == 1),
                                     name='opcon13_' + str(i))
                self.model.addConstr((self.xjvars[i, self.symbol_list.index('i')] == 1) >> (self.op1rvars[i] == 1),
                                     name='opcon14_' + str(i))
                self.model.addConstr((self.xjvars[i, self.symbol_list.index('d')] == 1) >> (self.rvars[i - 1] == 1),
                                     name='opcon15_' + str(i))
                self.model.addConstr((self.xjvars[i, self.symbol_list.index('d')] == 1) >> (self.op1rvars[i] == 1),
                                     name='opcon16_' + str(i))

                # self.model.addConstr((self.xjvars[i, self.symbol_list.index('<=')] == 1) >> (self.rvars[i-1] == 1),
                #  name='opcon17_'+str(i))
        self.model.update()

    def add_ilp_objective(self, length):
        self.model.setObjective(0.0)
        self.model.update()

    def solve(self):
        try:
            self.model.optimize()
            solutions = []
            for k in range(self.num_solutions):
                current = []
                self.model.setParam('SolutionNumber', k)
                for i in range(len(self.xvars)):
                    current.append(self.xvars[i].Xn)
                if current not in solutions:
                    solutions.append(current)
            return solutions
        except Exception as e:
            print e
            return []

    def create_valued_postfix(self, postfix):
        mod_postfix = []
        for index in postfix:
            index = int(index)
            if index < (len(self.symbol_list) - len(
                    self.operators)):  ##Need to have this because ILP does not restrict range<=num
                if len(self.symbol_list[index].value[1]) == 1:
                    mod_postfix.append(self.symbol_list[index].value[1][0])
                else:
                    mod_postfix.append(self.symbol_list[index].value[1])
            else:
                mod_postfix.append(self.symbol_list[index])
        return mod_postfix

    def is_subset(self, range1, range2):
        if not range1 or not range2:
            return False
        if not isinstance(range1, list):
            if not isinstance(range2, list):
                return False
            if range1 >= range2[0] and range1 <= range2[1]:
                return True
            else:
                return False
        if not isinstance(range2, list):
            return False
        start1, end1 = range1
        start2, end2 = range2
        if start2 <= start1 and end2 >= end1:
            return True
        return False

    def is_equal(self, range1, range2):
        if not range1 or not range2:
            return False
        if not isinstance(range1, list) or not isinstance(range2, list):
            return False
        start1, end1 = range1
        start2, end2 = range2
        if start1 == start2 and end1 == end2:
            return True
        return False

    def get_union(self, range1, range2):
        if not isinstance(range1, list):
            if not isinstance(range2, list):
                if range1 == range2:
                    return range1
                elif abs(range2 - range1) == 1:
                    return [min(range1, range2), max(range1, range2)]
                else:
                    return []
            else:
                if range1 >= range2[0] - 1 and range1 <= range2[1] + 1:
                    return [min(range1, range2[0]), max(range1, range2[1])]
                else:
                    return []
        if not isinstance(range2, list):
            if range2 >= range1[0] - 1 and range2 <= range1[2] + 1:
                return [min(range2, range1[0]), max(range2, range1[1])]
            else:
                return []
        start1, end1 = range1 if range1[0] < range2[0] else range2  # left range
        start2, end2 = range2 if range1[0] < range2[0] else range1  # right range
        if end1 < start2:  # disjoint
            return []
        if end1 >= start2:  # overlapping ranges, subsets filtered out previously
            return [start1, end2]
        return []

    def get_intersection(self, range1, range2):
        if not isinstance(range1, list):
            if not isinstance(range2, list):
                if range1 == range2:
                    return range1
                else:
                    return []
            else:
                if range1 >= range2[0] and range1 <= range2[1]:
                    return range1
                else:
                    return []
        if not isinstance(range2, list):
            if range2 >= range1[0] and range2 <= range1[1]:
                return range2
            else:
                return []
        start1, end1 = range1 if range1[0] < range2[0] else range2  # left range
        start2, end2 = range2 if range1[0] < range2[0] else range1  # right range
        if end1 < start2:  # disjoint
            return []
        if end1 == start2:  # touching ranges return a single number
            return end1
        if end1 > start2:  # overlapping ranges, subsets filtered out previously
            return [start2, end1]
        return []

    def get_difference(self, range1, range2):
        if not isinstance(range1, list):
            if not isinstance(range2, list):
                if range1 != range2:
                    return range1
                else:
                    return []
            else:
                if range1 >= range2[0] and range1 <= range2[1]:
                    return []
                else:
                    return range1
        if not isinstance(range2, list):
            if range2 >= range1[0] and range2 <= range1[1]:
                return range1
            else:
                return []
        start1, end1 = range1 if range1[0] < range2[0] else range2  # left range
        start2, end2 = range2 if range1[0] < range2[0] else range2  # right range
        if end1 < start2:  # disjoint
            return range1
        if end1 == start2:  # touching ranges, we need an if condition because set difference is not symmetric
            if end1 == range1[1]:
                return [range1[0], range1[1] - 1]
            else:
                return [range1[0] + 1, range1[1]]
        if end1 > start2:  # overlapping ranges, subsets filtered out, set difference is not symmetric
            if end1 == range1[1]:
                return [range1[0], start2 - 1]
            else:
                return [end1 + 1, range2[1]]
        return []

    def solve_postfix(self, expression):
        stack = deque()
        for element in expression:
            if element not in self.operators:
                stack.append(element)
            else:
                roperand = stack.pop()
                loperand = stack.pop()
                if not isinstance(loperand, int) and not isinstance(loperand, float) and not isinstance(loperand, list):
                    return False
                if not isinstance(roperand, int) and not isinstance(roperand, float) and not isinstance(roperand, list):
                    return False
                if element == '+':
                    if loperand == 0 or roperand == 0:
                        return False
                    stack.append(loperand + roperand)
                elif element == '-':
                    if roperand == 0:
                        return False
                    stack.append(loperand - roperand)
                elif element == '*':
                    if loperand == 1 or roperand == 1:
                        return False
                    stack.append(loperand * roperand)
                elif element == '/':
                    if roperand == 1 or roperand == 0:
                        return False
                    stack.append(loperand / roperand)
                elif element == '=':
                    if len(stack) > 0:
                        return False
                    if loperand == roperand:
                        return True
                    else:
                        return False
                elif element == 'u':
                    # set union
                    if self.is_equal(loperand, roperand):
                        stack.append(loperand)
                    elif self.is_subset(loperand, roperand):
                        stack.append(roperand)
                    elif self.is_subset(roperand, loperand):
                        stack.append(loperand)
                    else:
                        stack.append(self.get_union(loperand, roperand))
                elif element == 'i':
                    # set intersection
                    if self.is_equal(loperand, roperand):
                        stack.append(loperand)
                    elif self.is_subset(loperand, roperand):
                        stack.append(loperand)
                    elif self.is_subset(roperand, loperand):
                        stack.append(roperand)
                    else:
                        stack.append(self.get_intersection(loperand, roperand))
                elif element == 'd':
                    # set difference
                    if self.is_equal(loperand, roperand):
                        stack.append([])
                    elif self.is_subset(loperand, roperand):
                        stack.append([])
                    elif self.is_subset(roperand, loperand):
                        if roperand[0] == loperand[0]:
                            stack.append([roperand[1], loperand[1]])
                        elif roperand[1] == loperand[1]:
                            stack.append([loperand[0], roperand[0]])
                        else:
                            stack.append([])
                    else:
                        stack.append(self.get_difference(loperand, roperand))
                elif element == '<=':
                    # subset
                    if len(stack) > 0:
                        return False
                    if not isinstance(roperand, list):
                        if isinstance(loperand, list):
                            return False
                        else:
                            if loperand == roperand:
                                return True
                            else:
                                return False
                    if not isinstance(loperand, list) and isinstance(roperand, list):  # number vs set comparison
                        if loperand >= roperand[0] and loperand <= roperand[1]:
                            return True
                        else:
                            return False
                    if self.is_equal(loperand, roperand):
                        return True
                    elif self.is_subset(loperand, roperand):
                        return True
                    else:
                        return False
                elif loperand <= roperand:
                    return True
                else:
                    return False
        return False

    def is_valid_tree(self, postfix):
        mod_postfix = self.create_valued_postfix(postfix)
        return self.solve_postfix(mod_postfix)

    def postprocess_tree(self, tree):
        tree[-2] = -1
        for num, index in enumerate(tree):
            if index >= (len(self.symbol_list) - len(self.operators)):
                tree[num] = self.symbol_list[int(index)]
            else:
                tree[num] = int(index)
        return tree


if __name__ == '__main__':
    # Main can be removed later, only used for ILP testing
    data = pickle.load(open(sys.argv[1], 'rb'))
    flag = sys.argv[3]
    # data = [{'input_pair': {'sentence1': 'My father gave me 30 dimes', 'sentence2': 'I received 30 dimes from my
    # father'}, 'premise_quantity_sets': [{'Value': [5, [30.0]], 'Units': ['dimes']}], 'hypothesis_quantity_sets': [{
    # 'Value': [3, [30.0]], 'Units': ['dimes']}], 'ph_pairs': [[{'Value': [5, [30.0]], 'Units': ['dimes']},
    # {'Value': [3, [30.0]], 'Units': ['dimes']}]]}] #, {}, {}]
    # data += [{'input_pair': {'sentence1': 'My father gave me 30 dimes and my mother gave me 50 dimes', 'sentence2':
    #  'I received 30 dimes from my father'}, 'premise_quantity_sets': [{'Value': [5, [30.0]], 'Units': ['dimes']},
    # {'Value': [12, [50.0]], 'Units': 'dimes'}], 'hypothesis_quantity_sets': [{'Value': [3, [20.0]],
    # 'Units': ['dimes']}], 'ph_pairs': [[{'Value': [5, [20.0]], 'Units': ['dimes']}, {'Value': [3, [20.0]],
    # 'Units': ['dimes']}], [{'Value': [12, [50.0]], 'Units': ['dimes']}, {'Value': [3, [30.0]], 'Units': [
    # 'dimes']}], [{'Value': [5, [30.0]], 'Units': ['dimes']}, {'Value': [12, [50.0]], 'Units': ['dimes']},
    # {'Value': [3, [20.0]], 'Units': ['dimes']}]]}]
    # data = [{'input_pair': {'sentence1': 'blah', 'sentence2': 'blah', 'label': 'blah'}, 'premise_quantity_sets':[{
    # 'Value': [0, [30.0]], 'Units': ['dimes']}, {'Value': [0, [30.0, 50.0]], 'Units': ['dimes']}, {'Value': [0,
    # [50.0, 80.0]], 'Units': ['dimes']}], 'hypothesis_quantity_sets':[{'Value': [0, [30.0]], 'Units': ['dimes']},
    # {'Value': [0, [30.0, 80.0]], 'Units': ['dimes']}], 'ph_pairs': [[{'Value': [0, [30.0]], 'Units': ['dimes']},
    # {'Value': [0, [30.0]], 'Units': ['dimes']}], [{'Value': [0, [30.0, 50.0]], 'Units': ['dimes']}, {'Value': [0,
    # [30.0]], 'Units': ['dimes']}], [{'Value': [0, [30.0]], 'Units': ['dimes']}, {'Value': [0, [30.0, 50.0]],
    # 'Units': ['dimes']}, {'Value': [0, [30.0, 80.0]], 'Units': ['dimes']}], [{'Value': [0, [30.0, 50.0]],
    # 'Units': ['dimes']}, {'Value': [0, [50.0, 80.0]], 'Units': ['dimes']}, {'Value': [0, [30.0, 80.0]], 'Units': ['dimes']}]]}]
    for snum, sample in enumerate(data):
        prem_q = sample['premise_quantity_sets']
        hyp_q = sample['hypothesis_quantity_sets']
        if 'ph_pairs' not in sample:
            continue
        ph_pairs = sample['ph_pairs']
        tree_generator = TreeGenerator(premise, hypothesis, prem_q, hyp_q, ph_pairs)

        # Go through all hypothesis quantities to get justification for each
        complete_equation_data = []
        for q in tree_generator.hyp_q:
            equation_data = {}
            if not q['Value'] or len(q['Value'][1]) > 2:
                continue
            current_pq = []
            for pair in tree_generator.ph_pairs:
                if q == pair[-1]:
                    current_pq += pair[:-1]
            prem_qlist = []
            prem_rlist = []
            for x in current_pq:
                if x not in prem_qlist and x['Value'] and len(x['Value'][1]) == 1:
                    prem_qlist.append(x)
                if x not in prem_rlist and x['Value'] and len(x['Value'][1]) == 2:
                    prem_rlist.append(x)
            print prem_qlist
            print prem_rlist
            equation_data['hypothesis_quantity'] = q
            equation_data['premise_quantities'] = prem_qlist + prem_rlist
            equation_data['trees'] = []

            max_equation_length = 10  # We restrict ourselves to trees of depth 2
            for length in range(3, max_equation_length, 2):
                # Check whether we have enough premise quantities to make equations of this length
                if (length - 1) / 2 > len(prem_qlist + prem_rlist):
                    break
                model = tree_generator.init_ilp_model()
                tree_generator.add_ilp_vars(model, q, prem_qlist + prem_rlist, length)
                tree_generator.add_ilp_constraints(model, length)
                tree_generator.add_ilp_objective(model, length)
                possible_trees = tree_generator.solve(model)
                for tree in possible_trees:
                    if flag == 'train':
                        if tree_generator.is_valid_tree(tree, q, prem_qlist + prem_rlist):
                            post_tree = tree_generator.postprocess_tree(tree)
                            if post_tree not in equation_data['trees']:
                                equation_data['trees'].append(post_tree)
                    else:
                        equation_data['trees'].append(tree_generator.postprocess_tree(tree))
            complete_equation_data.append(equation_data)
        sample['all_equation_data'] = complete_equation_data
    pickle.dump(data, open(sys.argv[2], 'wb'))
