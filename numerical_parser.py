from pycorenlp import StanfordCoreNLP
import pickle
from word2number import w2n
import re
import re
from quantity_segmenter import *
from nltk.data import load
from nltk.tree import ParentedTree
from constants import *
from utils_segmenter import *
from utils_parser import *
from numset import Numset


class NumericalParser():
    def __init__(self):
        self.nlp = StanfordCoreNLP('http://localhost:9000')
        self.segmenter = Segmenter()

    def extract_value(self, quantity_mention, syntax_parse):
        '''Extracts the value of a given quanity mention. Normalizes value to float'''

        word_value = []
        non_adj = False

        inc_keywords = ["increasing", "rising", "decreasing", "falling", "rose from", "increas", "fell from"]

        for ind, each_unit in enumerate(quantity_mention):

            if ind > 0 and quantity_mention[ind - 1] == "CD":
                if len(word_value) > 0:
                    if word_value[-1][0] != ind - 1:
                        non_adj = True

                word_value.append((ind, each_unit))

        # Remove , from everything
        preprocess_wv = [x[1].replace(",", "") for x in word_value]
        final_value = []

        # Handles explicit specification of a range
        if ("to" in quantity_mention or "between" in quantity_mention) and len(word_value) == 2 and len(
                set(inc_keywords).intersection(set(quantity_mention))) == 0:
            first_val = word_value[0][1]
            second_val = word_value[1][1]

            if first_val.replace('.', '', 1).isdigit():
                first_val = float(first_val)
            elif first_val.isalpha():
                try:
                    first_val = w2n.word_to_num(preprocess_number(first_val))
                except Exception as e:
                    return []

            if second_val.replace('.', '', 1).isdigit():
                second_val = float(second_val)
            elif second_val.isalpha():
                try:
                    second_val = w2n.word_to_num(preprocess_number(second_val))
                except Exception as e:
                    return []
            final_value = [word_value[0][0], [first_val, second_val]]
            return final_value

        quant_to_number = {"million": 1000000, "m": 1000000, "mn": 1000000, "billion": 1000000000, "b": 1000000000,
                           "hundred": 100,
                           "thousand": 1000}

        # five million
        if len(preprocess_wv) > 2:
            if preprocess_wv[-1] in quant_to_number.keys():
                base = " ".join(preprocess_wv[:-1:])
                try:
                    base = w2n.word_to_num(preprocess_number(base))
                    val_cand = base * quant_to_number[preprocess_wv[-1]]
                    final_value = [word_value[0][0], [val_cand]]
                except Exception as e:
                    pass


            else:
                try:
                    float_quants = [w2n.word_to_num(preprocess_number(word)) for word in preprocess_wv]

                    for ind, each_num in enumerate(float_quants):
                        if float_quants[ind] < 10:
                            float_quants[ind] = each_num * 10 ** (len(float_quants) - ind - 1)

                    val_cand = 0
                    for each_num in float_quants:
                        val_cand += each_num
                    final_value = [word_value[0][0], [val_cand]]
                except Exception as e:
                    print e




        elif len(preprocess_wv) == 2:
            '''Takes care of two hundred'''
            if preprocess_wv[1] in quant_to_number:
                try:
                    if preprocess_wv[0].replace('.', '', 1).isdigit():
                        final_value = [word_value[0][0],
                                       [float(preprocess_wv[0]) * quant_to_number[preprocess_wv[1]]]]
                    else:
                        final_value = [word_value[0][0], [
                            w2n.word_to_num(preprocess_number(preprocess_wv[0])) * quant_to_number[preprocess_wv[1]]]]
                except Exception as e:
                    print e
            else:
                if "/" in preprocess_wv[0]:
                    return []
                try:
                    msd = float(w2n.word_to_num(preprocess_number(preprocess_wv[0])))
                    if msd < 10:
                        # TODO:
                        pass
                    else:
                        try:
                            if preprocess_wv[0].replace('.', '', 1).isdigit():
                                final_value = [word_value[0][0], [msd + float(preprocess_wv[1])]]
                            else:
                                final_value = [word_value[0][0],
                                               [msd + float(w2n.word_to_num(preprocess_number(preprocess_wv[1])))]]
                        except Exception as e:
                            print e
                except Exception as e:
                    print e

        # TODO: handle ratios
        # quarter half 20/20
        val_candidate = 0
        # Single word values
        if len(preprocess_wv) == 1:
            value_quant = preprocess_wv[0]
            if value_quant.replace('.', '', 1).isdigit():
                preprocess_wv[0] = float(preprocess_wv[0])
            elif value_quant.isalpha():
                if "I" not in preprocess_wv[0]:
                    try:
                        preprocess_wv[0] = float(w2n.word_to_num(preprocess_number(preprocess_wv[0])))
                    except Exception as e:
                        print e
            else:
                if "m" in value_quant:
                    number = re.findall("\d+", value_quant)[0]
                    try:
                        preprocess_wv[0] = float(number[0]) * quant_to_number["m"]
                    except Exception as e:
                        print e

                if "b" in value_quant:
                    number = re.findall("\d+", value_quant)

                    preprocess_wv[0] = float(number[0]) * quant_to_number["b"]
            final_value = [word_value[0][0], [preprocess_wv[0]]]

        # Is it a range
        less_range_kw = ["less than", "lesser than", "below", "under", "lesser", "lower than", "fewer",
                         "not as many as", "up to"]
        more_range_kw = ["greater than", "more than", "exceeding", "beyond", "over", "in excess of", "at least"]

        # TODO : Handle multiple range specifiers





        for kw in less_range_kw:
            if kw in strip_parse(quantity_mention):
                if len(final_value) == 0:
                    final_value = preprocess_wv
                point_val = final_value[1]
                final_value = [final_value[0], [float("-inf"), point_val[0]]]
                break
        for kw in more_range_kw:
            if kw in strip_parse(quantity_mention):
                if len(final_value) == 0:
                    final_value = preprocess_wv
                point_val = final_value[1]
                final_value = [final_value[0], [point_val[0], float("inf")]]

        # If there are two quantity mentions in 1 noun phrase: usually a change : represent change


        return final_value

    def extract_units(self, quantity_mention, syntax_parse):
        word_value = []
        non_adj = False

        for ind, each_unit in enumerate(quantity_mention):

            if ind > 0 and quantity_mention[ind - 1] == "CD":
                if len(word_value) > 0:
                    if word_value[-1][0] != ind - 1:
                        non_adj = True
                word_value.append(each_unit)

        unit_candidates = []
        for each_sentence in syntax_parse:
            dep_parse = each_sentence
            for each_word in dep_parse:
                if each_word['dependentGloss'] in word_value:
                    if each_word['dep'] == 'nummod' or each_word['dep'] == 'nmod':
                        unit_candidates.append(each_word['governorGloss'])

        if len(unit_candidates) == 0:
            if "$" in quantity_mention:
                unit_candidates = ["$"]

        if len(unit_candidates) == 1:
            if "percent" in unit_candidates[0]:
                unit_candidates[0] = "%"

            if "dollar" in unit_candidates[0] or "USD" in unit_candidates[0]:
                unit_candidates[0] = "$"

            if "rupees" in unit_candidates[0]:
                unit_candidates[0] = "Rs."

        return unit_candidates

    def extract_entities(self, quantity_mention, syntax_parse):

        # TODO : Consider units to be noun phrases, birds vs migratory birds
        # TODO: Consider nearest noun in case of parser failure
        word_value = []
        non_adj = False

        for ind, each_unit in enumerate(quantity_mention):

            if ind > 0 and quantity_mention[ind - 1] == "CD":
                if len(word_value) > 0:
                    if word_value[-1][0] != ind - 1:
                        non_adj = True
                word_value.append(each_unit)

        '''Extract unit candidates'''
        unit_candidates = []
        for each_sentence in syntax_parse:
            dep_parse = each_sentence
            for each_word in dep_parse:
                if each_word['dependentGloss'] in word_value:
                    if each_word['dep'] == 'nummod' or each_word['dep'] == 'nmod':
                        unit_candidates.append(each_word['governorGloss'])

        entity_candidates = []
        '''Entity candidates are in nmod relationships with unit candidates'''
        for each_sentence in syntax_parse:
            dep_parse = each_sentence
            for each_word in dep_parse:
                if each_word['dependentGloss'] in unit_candidates:
                    if each_word['dep'] == 'nmod':
                        entity_candidates.append(each_word['governorGloss'])

        return entity_candidates

    def extract_approx(self, quantity_mention, syntax_parse):

        # TODO : Handle nearly seperately, nearly is always less than
        # TODO :  Handle noun phrases denoting approximate
        # TODO: include words about specific values


        approx_gazeteer = ["roughly", "approximately", "about", "nearly", "roundabout", "around", "circa", "almost",
                           "approaching", "pushing"]

        mwe_gazeteer = ["more or less", "in the neighborhood of", "in the region of", "on the order of",
                        "something like", "give or take (a few)", "near to", "close to", "in the ballpark of"]

        word_value = []
        approx = False

        for ind, each_unit in enumerate(quantity_mention):

            if ind > 0 and quantity_mention[ind - 1] == "CD":
                if len(word_value) > 0:
                    if word_value[-1][0] != ind - 1:
                        non_adj = True
                word_value.append(each_unit)

        unit_candidates = []
        for each_sentence in syntax_parse:
            dep_parse = each_sentence
            for each_word in dep_parse:
                if each_word['dependentGloss'] in word_value:
                    if each_word['dep'] == 'advmod' and each_word['governorGloss'] in approx_gazeteer:
                        approx = True

        return approx

    def extract_location(self, quantity_mention, syntax_parse, units, entities, noun_phrases):
        location = ""

        for each_sentence in syntax_parse:
            parse = each_sentence
            parse = parse.replace("\n", " ")
            parse = parse.replace("(", " ( ")
            parse = parse.replace(")", " ) ")
            parse = " ".join(str(parse.encode('ascii', 'ignore')).split())

            q_mention = " ".join(quantity_mention)
            if q_mention in parse:

                start_ind = parse.index(q_mention)

                span = start_ind + len(" ".join(quantity_mention)) + 3
                if span + 1 < len(parse):
                    next_parse = parse[span:]

                    all_parts = next_parse.split()

                    if all_parts[1] == 'PP':
                        if all_parts[3] == "IN":
                            if all_parts[7] == "NP":
                                if all_parts[11] == "DT":
                                    '''we are looking for a (PP (IN ) (NP (DT ) (NP )) structure'''
                                    if all_parts[15] == "NN":
                                        '''extract this noun phrase'''
                                        location = all_parts[16]

        return location

    def extract_verb(self, quantity_mention, tokens, pos, syntax_parse, entity, unit):
        word_value = []
        verbs = []
        non_adj = False

        for i, each_sentence in enumerate(pos):
            for j, each_token in enumerate(each_sentence):
                if each_token.startswith('V'):
                    verbs.append(tokens[i][j])

        for ind, each_unit in enumerate(quantity_mention):

            if ind > 0 and quantity_mention[ind - 1] == "CD":
                if len(word_value) > 0:
                    if word_value[-1][0] != ind - 1:
                        non_adj = True
                word_value.append(each_unit)

        verb_candidates = []
        for each_sentence in syntax_parse:
            dep_parse = each_sentence
            for each_word in dep_parse:
                if (each_word['dependentGloss'] in entity or each_word['dependentGloss'] in unit or each_word[
                    'dependentGloss'] in word_value) and each_word[
                    'governorGloss'] in verbs:
                    if each_word['dep'].startswith('dobj') or each_word['dep'].startswith('nsubj'):
                        verb_candidates.append(each_word['governorGloss'])

        return verb_candidates

    def extract_adj(self, quantity_mention, tokens, pos, syntax_parse, entity):
        word_value = []
        adjectives = []
        non_adj = False

        for i, each_sentence in enumerate(pos):
            for j, each_token in enumerate(each_sentence):
                if each_token.startswith('J'):
                    adjectives.append(tokens[i][j])

        for ind, each_unit in enumerate(quantity_mention):

            if ind > 0 and quantity_mention[ind - 1] == "CD":
                if len(word_value) > 0:
                    if word_value[-1][0] != ind - 1:
                        non_adj = True
                word_value.append(each_unit)

        adj_candidates = []
        for each_sentence in syntax_parse:
            dep_parse = each_sentence
            for each_word in dep_parse:
                if (each_word['dependentGloss'] in entity or each_word['dependentGloss'] in word_value) and each_word[
                    'governorGloss'] in adjectives:
                    if each_word['dep'].startswith('amod'):
                        adj_candidates.append(each_word['governorGloss'])

        return adj_candidates

    def extract_frequency(self, quantity_mention, tokens, unit, entity):
        frequency = ""

        freq_word_list = ["per", "every"]

        if len(quantity_mention) == 8:  # has both a value and a unit
            value = str(quantity_mention[2])
            unit = quantity_mention[6]

            sentence_tokens = []
            for each_ind in range(len(tokens)):
                sentence_tokens += [x.lower() for x in tokens[each_ind]]

            value_index = sentence_tokens.index(value)
            if value_index + 2 < len(sentence_tokens):
                freq_word = sentence_tokens[value_index + 2]
                if freq_word in freq_word_list:
                    frequency = freq_word + " " + sentence_tokens[value_index + 2]
                    # return frequency

        return frequency

    def extract_change(self, quantity_mention, tokens, pos, syntax_parse, unit, entity):
        inc_keywords = ["increasing", "rising", "rose"]
        dec_keywords = ["decreasing", "falling", "fell", "drop"]

        verbs = []
        non_adj = False

        inc_dec = [False, False]

        for i, each_sentence in enumerate(pos):
            for j, each_token in enumerate(each_sentence):
                if each_token.startswith('V'):
                    verbs.append(tokens[i][j])

        adj_candidates = []
        for each_sentence in syntax_parse:
            dep_parse = each_sentence
            for each_word in dep_parse:
                if (each_word['dependentGloss'] in entity or each_word['dependentGloss'] in unit) and each_word[
                    'governorGloss'] in verbs:
                    if each_word['dep'].startswith('nmod') or each_word['dep'].startswith('conj'):
                        if each_word['governorGloss'] in inc_keywords:
                            inc_dec[0] = True
                        if each_word['governorGloss'] in dec_keywords:
                            inc_dec[1] = False

        return inc_dec

    def logic_parse(self, quantity_mention, tokens, pos, syntax_parse, dep_parse, noun_phrases, text):
        '''

        :param quantity_mention: each quantity phrase
        :param syntax_parse: all Stanford parser annotations
        :return: A Quantity Set Parse consisting of the following fields-
        1) Value: A range of values representing the value mentioned in this quantity phrase
        2) Unit: The Unit or quantity associated with this quantity phrase
        3) Entity: An Entity associated with the value AND unit (Eg- (Donations ENTITY) worth (500 million VALUE) ($
        UNIT)
        4) Exact/Approximate : Determine if a value is exact or approximate. If approximate, what is considered as +=
        depending on value and units
        5) Location : In A Container (eg - 5 students IN bus)
        6) Action/Verb : Governing Verb for this quantity phrase
        7) Adjective : Adjective, if any, to describe the quantity
        8) Change : Is this quantity in a state of flux, i.e is it increasing or decreasing
        9) Frequency: Does this quantity have a multiplier

        Necessary assumption : Each quantity mention has only one value of each field
        '''

        qset = {}
        qset["Position"] = -1
        text_qmention = " ".join(quantity_mention)
        match_obj = re.search("[a-z0-9]+", text_qmention)
        if match_obj is not None:
            search_term = match_obj.group()
            if search_term in text:
                qset["Position"] = text.index(search_term)
        qset["Value"] = self.extract_value(quantity_mention, syntax_parse)
        qset["Units"] = self.extract_units(quantity_mention, dep_parse)
        qset["Entities"] = self.extract_entities(quantity_mention, dep_parse)
        qset["Approximate"] = self.extract_approx(quantity_mention, dep_parse)
        qset["Location"] = self.extract_location(quantity_mention, syntax_parse, qset["Units"], qset["Entities"],
                                                 noun_phrases)

        qset["full mention"] = quantity_mention
        qset["Verb"] = self.extract_verb(quantity_mention, tokens, pos, dep_parse, qset["Entities"], qset["Units"])
        qset["Adjective"] = self.extract_adj(quantity_mention, tokens, pos, dep_parse, qset["Entities"])
        qset["Frequency"] = self.extract_frequency(quantity_mention, tokens, qset["Entities"], qset["Units"])
        qset["Change"] = self.extract_change(quantity_mention, tokens, pos, dep_parse, qset["Entities"], qset["Units"])

        numset = Numset(qset["Value"])
        numset.set_dict(qset)

        return numset

    def get_numsets(self, text, tokens, pos, syntax_parse, dep_parse):
        # Extract all quantity mentions from a sentence
        quantity_mentions, noun_phrases = self.segmenter.segment(syntax_parse)
        print quantity_mentions

        numsets = []
        for each_mention in quantity_mentions:
            numsets.append(self.logic_parse(each_mention, tokens, pos, syntax_parse, dep_parse, noun_phrases, text))

        return numsets


if __name__ == "__main__":
    import pickle

    num_parse = NumericalParser()

    rte_expanded = pickle.load(
        open('./mnli_train_numerical.pkl', "rb"))

    all_qsets = []

    for each_ind, each_pair in enumerate(rte_expanded):

        try:
            extractor = {}
            extractor["input_pair"] = each_pair

            print "-----------"
            print each_ind

            premise = each_pair['sentence1']
            hypothesis = each_pair['sentence2']

            '''Premise'''
            # Extract all quantity mentions from a sentence
            quantity_mentions, syntax_parse_output, noun_phrases = num_parse.segmenter(premise)
            extractor["premise_quantity_mentions"] = quantity_mentions
            extractor["premise_syntax_parse"] = syntax_parse_output
            extractor["premise_quantity_sets"] = num_parse.get_numsets(premise)

            '''Hypothesis'''
            # Extract all quantity mentions from a sentence
            quantity_mentions, syntax_parse_output, noun_phrases = num_parse.segmenter(hypothesis)
            extractor["hypothesis_quantity_mentions"] = quantity_mentions
            extractor["hypothesis_syntax_parse"] = syntax_parse_output
            extractor["hypothesis_quantity_sets"] = num_parse.get_numsets(hypothesis)

            all_qsets.append(extractor)
            if each_ind % 1000 == 0:
                pickle.dump(all_qsets, open("./multinli_qsets.pkl", "wb"))
        except Exception as e:
            print e
