from quantity_segmenter import *
from numerical_parser import *
from scorer import *
from eval import *
from constants import *
import argparse
from logger import *
from all_tree_generator import *
import pickle

# New pruner and ilp imports
from numset_pruner import NumsetPruner
from numset import Numset
from parsed_numsets import ParsedNumsets
from compatible_numsets import CompatibleNumsets
from ilp import ILPEquationGenerator

from utils_reasoner import *

total_hyp_count = 0.00
total_pruned_pairs = 0

all_extracted = []


class EntailmentReasoner():
    def __init__(self, ilp_file="/usr1/anaik/Numerical_Reasoner/awp_ilp_gold_equations",
                 extractor_file="/usr1/anaik/Numerical_Reasoner/extractor.pkl"):
        self.segmenter = Segmenter()
        self.num_parse = NumericalParser()
        self.pruner = NumsetPruner()
        self.scorer = Scorer()

        self.equation_generator = ILPEquationGenerator()

    def extract_parses(self, example, premise, hypothesis, extractor):
        '''
        :param example: NLI example
        '''

        # Extract all quantity mentions from a sentence
        quantity_mentions, noun_phrases = self.segmenter.segment(example['sentence1_syntax_parse'])
        if len(quantity_mentions) == 0:
            extractor["predicted_label"] = "neutral"
        extractor["premise_quantity_mentions"] = quantity_mentions
        extractor["premise_quantity_sets"] = self.num_parse.get_numsets(premise, example['sentence1_tokens'],
                                                                        example['sentence1_pos'],
                                                                        example['sentence1_syntax_parse'],
                                                                        example['sentence1_dep_parse'])

        '''Hypothesis'''
        # Extract all quantity mentions from a sentence
        quantity_mentions, noun_phrases = self.segmenter.segment(example['sentence2_syntax_parse'])
        if len(quantity_mentions) == 0:
            extractor["predicted_label"] = "neutral"
        extractor["hypothesis_quantity_mentions"] = quantity_mentions
        extractor["hypothesis_quantity_sets"] = self.num_parse.get_numsets(hypothesis, example['sentence2_tokens'],
                                                                           example['sentence2_pos'],
                                                                           example['sentence2_syntax_parse'],
                                                                           example['sentence2_dep_parse'])

    def prune_pairs(self, extractor):
        '''
        :param extractor: dictionary object consisting of premise and hypothesis, along with their numsets
        :return: prune compatible premise-hypothesis pairs
        '''

        extractor['ph_pairs'] = []

        # To convert data into new format
        # This portion can be removed once parser
        # starts using the new format
        parsed_numsets = ParsedNumsets()
        for numset in extractor["premise_quantity_sets"]:
            # numset = Numset(q['Value'], q['Units'], q['Entities'], q['Approximate'], q['Frequency'], q['Change'],
            #         q['Adjective'], q['Verb'], q['Location'], q['full mention'], q['Position'])
            parsed_numsets.add_numset(numset, "premise")
        for numset in extractor["hypothesis_quantity_sets"]:
            # numset = Numset(q['Value'], q['Units'], q['Entities'], q['Approximate'], q['Frequency'], q['Change'],
            #         q['Adjective'], q['Verb'], q['Location'], q['full mention'], q['Position'])
            parsed_numsets.add_numset(numset, "hypothesis")

        all_pairs = self.pruner.get_numset_pairs(parsed_numsets)  # pair generation
        pruned_pairs = self.pruner.prune_numset_pairs(all_pairs)  # pair pruning based on unit

        for pair in pruned_pairs:
            if len(pair.premise_numsets) == 1:
                # This is also data format conversion
                # Can be removed later
                premise_numset = pair.premise_numsets[0]
                hypothesis_numset = pair.hypothesis_numset
                extractor['ph_pairs'].append([premise_numset, hypothesis_numset])

        return pruned_pairs, None

    def generate_equations(self, sample):
        prem_q = sample['premise_quantity_sets']
        hyp_q = sample['hypothesis_quantity_sets']
        if 'ph_pairs' not in sample:
            return []
        ph_pairs = sample['ph_pairs']
        sample_equations = []

        for hyp_quantity in hyp_q:
            equation_data = {}
            if not hyp_quantity.value or len(hyp_quantity.value[1]) > 2:
                continue
            current_pq = []
            for pair in ph_pairs:
                if hyp_quantity.mention == pair[-1].mention:
                    current_pq += pair[:-1]
            prem_qlist = []
            prem_rlist = []
            for x in current_pq:
                if x not in prem_qlist and x.value and len(x.value[1]) == 1:
                    prem_qlist.append(x)
                if x not in prem_rlist and x.value and len(x.value[1]) == 2:
                    prem_rlist.append(x)

            equation_data['hypothesis_quantity'] = hyp_quantity
            equation_data['premise_quantities'] = prem_qlist + prem_rlist
            equation_data['trees'] = []

            ilp_hyp_quantity = hyp_quantity
            ilp_prem_quantities = []
            for premise_quantity in equation_data['premise_quantities']:
                ilp_prem_quantities.append(premise_quantity)

            max_equation_length = 10
            for length in range(3, max_equation_length, 2):
                if (length - 1) / 2 > len(prem_qlist + prem_rlist):
                    break
                self.equation_generator.create_ilp_model()
                self.equation_generator.add_ilp_vars(ilp_prem_quantities, ilp_hyp_quantity, length)
                self.equation_generator.add_ilp_constraints(length)
                self.equation_generator.add_ilp_objective(length)
                possible_trees = self.equation_generator.solve()
                for tree in possible_trees:
                    if self.equation_generator.is_valid_tree(tree):
                        post_tree = self.equation_generator.postprocess_tree(tree)
                        if post_tree not in equation_data['trees']:
                            equation_data['trees'].append(post_tree)
            sample_equations.append(equation_data)

        return sample_equations

    def shallow_logical_reasoner(self, each_ind, each_pair, pruned_pairs, extractor, equations):
        '''
        A lightweight reasoner that checks if a hypothesis is entailed, by determining
        if a justification can be constructed for each quantity present in the hypothesis
        from the premise.
        :param each_ind:
        :param each_pair:
        :param pruned_pairs:
        :param extractor:
        :return:
        '''
        predicted_label = "neutral"

        justified = []
        extractor["ilp_trees"] = []

        if len(pruned_pairs) > 0:

            hyp_q_sets = extractor["hypothesis_quantity_sets"]

            # Form possible candidate justifications for each quantity in hypothesis
            # where a hypothesis can be justified from a single premise quantity

            cand_just = []
            for each_hyp in hyp_q_sets:
                hyp_compat = [ph_pair[0] for ph_pair in extractor["ph_pairs"] if
                              ph_pair[1].mention == each_hyp.mention]
                cand_just.append((each_hyp, hyp_compat))

            # We will use this to check which hypothesis quantities have been justified
            justified = [False for hyp_ind in range(len(hyp_q_sets))]

            # Compares justifications for each hypothesis along all aspects of the numset
            # This is to correctly infer examples such as :
            # Two people were injured in the attack and
            # Two people perpetrated the attack
            # where quantities match but other aspects related to the quantity differ
            for ind, each_numset in enumerate(cand_just):

                # If numset is valid
                if len(each_numset[0].value) != 0:

                    hyp_set = each_numset[0]
                    poss_just = each_numset[1]

                    # Some numsets are not even unit compatible
                    if len(poss_just) > 0:

                        # For numsets that are unit compatible
                        for each_prem in poss_just:

                            if len(each_prem.value) == 0:
                                continue

                            hyp_value = hyp_set.value[1]
                            prem_value = each_prem.value[1]

                            attribute_similarity = self.scorer.get_sim_score((each_prem, hyp_set))

                            # Values may be a range or exact
                            # if value is not a range i.e values of both premise and hypothesis are exact
                            if len(hyp_value) == 1 and len(prem_value) == 1:

                                # If premise and hypothesis quantity match in most attributes
                                if attribute_similarity.index(max(attribute_similarity)) == 0 and hyp_value[0] == \
                                        prem_value[0]:
                                    justified[ind] = "ENTAILMENT"

                                # If premise and hypotthesis quantities match in value but not in other quantity aspects
                                elif attribute_similarity.index(max(attribute_similarity)) == 2 and hyp_value[0] == \
                                        prem_value[0]:
                                    justified[ind] = "CONTRADICTION"

                                # If premise and hypothesis quantities match in most apects but not value
                                elif attribute_similarity.index(max(attribute_similarity)) == 0 and hyp_value[0] != \
                                        prem_value[0]:
                                    justified[ind] = "CONTRADICTION"



                            # if both premise and hypothesis values are ranges
                            elif len(prem_value) == 2 and len(hyp_value) == 2:

                                if attribute_similarity.index(max(attribute_similarity)) == 0 and (
                                                prem_value[0] == hyp_value[0] and hyp_value[1] == prem_value[1]):
                                    justified[ind] = "ENTAILMENT"

                                elif attribute_similarity.index(max(attribute_similarity)) == 2 and (
                                                prem_value[0] == hyp_value[0] and hyp_value[1] == prem_value[1]):
                                    justified[ind] = "CONTRADICTION"
                                elif attribute_similarity.index(max(attribute_similarity)) == 0 and (
                                                prem_value[0] != hyp_value[0] or hyp_value[1] != prem_value[1]):
                                    justified[ind] = "CONTRADICTION"

                            # if premise is a value and hypothesis is a range
                            elif len(prem_value) == 1 and len(hyp_value) == 2:
                                if attribute_similarity.index(max(attribute_similarity)) == 0 and (
                                                hyp_value[0] < prem_value[0] and prem_value[0] < hyp_value[1]):
                                    justified[ind] = "ENTAILMENT"
                                elif attribute_similarity.index(max(attribute_similarity)) == 2 and (
                                                hyp_value[0] < prem_value[0] and prem_value[0] < hyp_value[1]):
                                    justified[ind] = "CONTRADICTION"
                                elif attribute_similarity.index(max(attribute_similarity)) == 0 and (
                                                prem_value[0] < hyp_value[0] or prem_value[0] >= hyp_value[1]):
                                    justified[ind] = "CONTRADICTION"

            # If the index passed is valid
            for ind in range(len(equations)):

                hyp_quant = equations[ind]['hypothesis_quantity']
                poss_just = equations[ind]['premise_quantities']
                trees = equations[ind]['trees']
                print(trees)

                eqn_data = {}
                eqn_data['premise_quantities'] = poss_just
                eqn_data['hypothesis_quantity'] = hyp_quant
                eqn_data['trees'] = trees

                extractor['ilp_trees'] = trees
                if len(trees) > 0:
                    justified[ind] = "ENTAILMENT"

            if justified.count("ENTAILMENT") == len(justified):
                predicted_label = "entailment"
            elif False in justified:
                predicted_label = "neutral"

            if "CONTRADICTION" in justified:
                predicted_label = "contradiction"

        extractor["hypothesis_justifications"] = justified
        return predicted_label

    def predict(self, dataset, LOG_FILE=None):
        '''
        Q-REAS predictions for each example in the dataset.
        :param dataset: dataset for Q-REAS predictions
        :param LOG_FILE: segmenter, parser, pruner and ILP output for each example in dataset
        :return: accuracy on dataset
        '''

        # If a log file has not been specified
        if not LOG_FILE:
            LOG_FILE = "error_analysi_" + dataset + ".txt"

        # Load data from constants.py
        dev_data = read_data(datasets[dataset]["data_path"])

        gold_labels = []
        predicted_labels = []

        # Open log file for writing
        f = open(LOG_FILE, "w")
        f.close()

        for each_ind, each_pair in enumerate(dev_data):

            n_classes = datasets[dataset]["classes"]
            gold_label = each_pair["gold_label"]
            premise = preprocess(each_pair['sentence1'])
            hypothesis = preprocess(each_pair['sentence2'])
            gold_labels.append(gold_label)

            # Parse into logical form
            extractor = {}
            extractor["input_pair"] = each_pair
            self.extract_parses(each_pair, premise, hypothesis, extractor)

            # Derive compatible numseta
            pruned_pairs, tags = self.prune_pairs(extractor)

            print("PRUNED PAIR LENGTH")
            print(len(extractor['ph_pairs']))

            # Generate ILP equations
            equations = self.generate_equations(extractor)

            # Apply shallow reasoner
            predicted_label = self.shallow_logical_reasoner(each_ind, each_pair, pruned_pairs, extractor, equations)

            # Log errors for analysis
            if not is_example_correct(n_classes, gold_label, predicted_label):
                log_example(LOG_FILE, premise, hypothesis, each_pair["gold_label"], extractor)

            predicted_labels.append(predicted_label)

        accuracy = evaluate_acc(gold_labels, predicted_labels, datasets[dataset]["classes"])
        print "ACCURACY : " + str(accuracy)

        return accuracy


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Quantitative Reasoning baseline')
    # parser.add_argument('--dataset', dest='dataset', type=str,
    #                     help='Dataset to train on')
    parser.add_argument('-mnli_dev', dest='mnli_dev', action='store_true',
                        help='Evaluate on multinli dev matched')
    parser.add_argument('-mnli_test', dest='mnli_test', action='store_true',
                        help='Evaluate on multinli test matched')
    parser.add_argument('-stresstest', dest='stresstest', action='store_true',
                        help='Evaluate on stress test')
    parser.add_argument('-rte', dest='rte', action='store_true',
                        help='Evaluate on rte')
    parser.add_argument('-awp', dest='awp', action='store_true',
                        help='Evaluate on awp')
    parser.add_argument('-mnli', dest='mnli', action='store_true',
                        help='Evaluate on mnli')
    parser.add_argument('-newsnli', dest='newsnli', action='store_true',
                        help='Evaluate on newsnli')
    parser.add_argument('-reddit', dest='reddit', action='store_true',
                        help='Evaluate on reddit')

    reasoner = EntailmentReasoner()

    args = parser.parse_args()

    '''Numerical Reasoning'''
    results_dict = {}

    '''Stress Test'''
    if args.stresstest:
        acc = reasoner.predict("stresstest")
        results_dict["Numerical Stress Test"] = round(acc * 100.0, 2)

    if args.mnli:
        acc = reasoner.predict("mnli_num")

    '''AWP'''
    if args.awp:
        acc = reasoner.predict("awp")
        results_dict["AWP"] = round(acc * 100.0, 2)

    '''RTE'''
    if args.rte:
        acc = reasoner.predict("rte")
        results_dict["RTE"] = round(acc * 100.0, 2)

    '''Reddit'''
    if args.reddit:
        acc = reasoner.predict("reddit")
        results_dict["Reddit"] = round(acc * 100.0, 2)

    '''QNLI'''
    if args.newsnli:
        acc = reasoner.predict("newsnli")
        results_dict["NewsNLI"] = round(acc * 100.0, 2)

    create_latex_table_row(results_dict, "NumReasoner", train_name="multinli")
