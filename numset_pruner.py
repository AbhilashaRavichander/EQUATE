import pickle
import itertools
import io
import numpy as np

from nltk.corpus import wordnet as wn
from collections import deque
from compatible_numsets import CompatibleNumsets


class NumsetPruner:
    def __init__(self):
        # Read in lists of jobs and nationalities from wikipedia
        self.jobs = []
        self.nationalities = []

        job_file = open('jobs.txt', 'r')
        nationalities_file = open('nationalities.txt', 'r')

        for line in job_file:
            self.jobs.append(line.strip().lower())

        for line in nationalities_file:
            self.nationalities.append(line.strip().lower())

    def get_numset_pairs(self, parsed_numsets):
        # INPUT: ParsedNumsets object (contains lists of
        # premise and hypothesis numsets)
        # TASK: Generate all possible pairs and triples
        # from premise and hypothesis numset lists
        # OUTPUT: List of all numset pairs/ triples
        hypothesis_numsets = parsed_numsets.hypothesis_numsets
        premise_numsets = parsed_numsets.premise_numsets
        all_pairs = []

        # Generate all (p, h) pairs
        for n1 in premise_numsets:
            for n2 in hypothesis_numsets:
                all_pairs.append([n1, n2])

        # Generate all (p, p, h) pairs
        # Use permutations here to generate (p, p) pairs
        # since certain operations like subtraction and
        # divison are non-commutative
        premise_numset_pairs = list(itertools.permutations(premise_numsets, 2))
        for pair in premise_numset_pairs:
            for n in hypothesis_numsets:
                all_pairs.append([pair[0], pair[1], n])
        return all_pairs

    def get_all_hypernyms(self, target):
        # INPUT: Synset for a word
        # TASK: Return all possible hypernyms using BFS
        # OUTPUT: List of hypernyms
        hypernyms = []
        to_process = deque()

        # Get all hypernyms of current synset
        # Also store them in a queue
        for syn in target.hypernyms():
            hypernyms.append(syn)
            to_process.append(syn)

        # While queue is not empty, continue extracting
        # hypernyms for each synset in the queue
        while len(to_process) != 0:
            current = to_process.popleft()
            for syn in current.hypernyms():
                hypernyms.append(syn)
                to_process.append(syn)

        return hypernyms

    def synonym_match(self, syn1, syn2):
        # INPUT: Two wordnet synsets
        # TASK: Evaluate synonym match between them
        # OUTPUT: True if both have same synonym set, False otherwise
        syn1_synonyms = set([x.lower() for x in syn1.lemma_names()])
        syn2_synonyms = set([x.lower() for x in syn2.lemma_names()])
        if syn1_synonyms == syn2_synonyms:
            return True, syn1_synonyms, syn2_synonyms
        return False, syn1_synonyms, syn2_synonyms

    def hypernym_match(self, syn1, syn2):
        # INPUT: Two wordnet synsets
        # TASK: Check whether one is a hypernym of the other
        # OUTPUT: True is one is a hypernym, False otherwise
        syn1_hypernyms = self.get_all_hypernyms(syn1)
        syn2_hypernyms = self.get_all_hypernyms(syn2)
        if syn1 in syn2_hypernyms or syn2 in syn1_hypernyms:
            return True
        return False

    def job_list_check(self, syn1_synonyms, syn2_synonyms):
        # INPUT: All synonyms of two wordnet synsets
        # TASK: Check if one is a job title and the other
        # corresponds to people/ person/ worker
        # OUTPUT: True if this holds, False otherwise
        for job in self.jobs:
            if job in syn1_synonyms:
                if "person" in syn2_synonyms or "people" in syn2_synonyms or "worker" in syn2_synonyms:
                    return True
            if job in syn2_synonyms:
                if "person" in syn1_synonyms or "people" in syn1_synonyms or "worker" in syn1_synonyms:
                    return True
        return False

    def nationality_list_check(self, syn1_synonyms, syn2_synonyms):
        # INPUT: All synonyms of two wordnet synsets
        # TASK: Check if one is nationality and the
        # other corresponds to people/ person/ citizen
        # OUTPUT: True if this holds, False otherwise
        for nationality in self.nationalities:
            if nationality in syn1_synonyms:
                if "person" in syn2_synonyms or "people" in syn2_synonyms or "citizen" in syn2_synonyms:
                    return True
            if nationality in syn2_synonyms:
                if "person" in syn1_synonyms or "people" in syn1_synonyms or "citizen" in syn1_synonyms:
                    return True
        return False

    def unit_compatibility(self, unit1, unit2):
        # INPUT: Units for two quantities
        # TASK: Check whether units are compatible
        # OUTPUT: True if they are, False otherwise

        # If there is any lexical overlap between units
        # consider them compatible
        if len(set(unit1.split()).intersection(set(unit2.split()))) > 0:
            return True

        # Extract wordnet synsets corresponding to units
        # Since Lesk does not work well, we just choose
        # the most common synset if multiple are returned
        unit1_syn = wn.synsets(unit1)
        unit2_syn = wn.synsets(unit2)
        # If wordnet synsets for either are not available
        # and they have no lexical overlap, we make the
        # conservative assumption that they do not match.
        # This step is high precision/ low recall
        if not unit1_syn or not unit2_syn:
            return False
        unit1_syn = unit1_syn[0]
        unit2_syn = unit2_syn[0]

        # Check synonym compatibility
        synonym_match, unit1_synonyms, unit2_synonyms = self.synonym_match(unit1_syn, unit2_syn)
        if synonym_match:
            return True

        # Check hypernym compatibility
        hypernym_match = self.hypernym_match(unit1_syn, unit2_syn)
        if hypernym_match:
            return True

        # Check job-based matching
        job_match = self.job_list_check(unit1_synonyms, unit2_synonyms)
        if job_match:
            return True

        # Check nationality-based matching
        nationality_match = self.nationality_list_check(unit1_synonyms, unit2_synonyms)
        if nationality_match:
            return True

        return False

    def entity_compatibility(self, entity1, entity2, unit1, unit2):
        # INPUT: Entities and units for two quantities
        # TASK: Check whether the entities are compatible
        # OUTPUT: True if they are, False otherwise

        # Exact string match as well as entity containment in unit,
        # both lead to entities being marked as compatible
        if entity1 in unit2 or entity2 in unit1 or entity1 == entity2:
            return True

        # If entities have some lexical overlap
        # consider them compatible
        if len(set(entity1.split()).intersection(set(entity2.split()))) > 0:
            return True

        # Get wordnet synsets for entities
        entity1_syn = wn.synsets(entity1)
        entity2_syn = wn.synsets(entity2)

        # As before, return False in cases where no synsets are found
        # and pick most common synset in cases with multiple synsets
        if not entity1_syn or not entity2_syn:
            return False
        entity1_syn = entity1_syn[0]
        entity2_syn = entity2_syn[0]

        # Check synonym compatibility
        synonym_match, entity1_synonyms, entity2_synonyms = self.synonym_match(entity1_syn, entity2_syn)
        if synonym_match:
            return True

        # Check hypernym compatibility
        hypernym_match = self.hypernym_match(entity1_syn, entity2_syn)
        if hypernym_match:
            return True

        # Check job-based matching
        job_match = self.job_list_check(entity1_synonyms, entity2_synonyms)
        if job_match:
            return True

        # Check nationality-based matching
        nationality_match = self.nationality_list_check(entity1_synonyms, entity2_synonyms)
        if nationality_match:
            return True

        return False

    def check_pair_compatibility(self, pair):
        # INPUT: Pair of numsets
        # TASK: Check whether the numsets are compatible
        # based on units and entities
        # OUTPUT: True if they are, False otherwise
        numset1, numset2 = pair

        # We again take a conservative approach,
        # assuming that quantites without units
        # are not compatible

        # CHANGE THIS BACK IF ACCURACY DROPS
        if numset1.unit is None or numset2.unit is None or not numset1.unit or not numset2.unit:
            return True

        unit1 = numset1.unit[0]
        unit2 = numset2.unit[0]

        # If both quantities have entities,
        # decide their compatibility based on
        # entity compatibility
        if len(numset1.entity) > 1 and len(numset2.entity) > 1:

            entity1 = numset1.entity[0]
            entity2 = numset2.entity[0]
            if self.entity_compatibility(entity1, entity2, unit1, unit2):
                return True

        # Otherwise, decide based on unit compatibility
        if unit1 == unit2:
            return True
        elif self.unit_compatibility(unit1, unit2):
            return True

        return False

    def check_triple_compatibility(self, triple):
        # INPUT: Triple of numsets
        # TASK: Decide compatibility based on units/ entities
        # OUTPUT: True if they are, False otherwise
        numset1, numset2, numset3 = triple

        # As per conservative approach, predict False
        # for numsets missings units

        # CHANGE THIS BACK IF ACCURACY DROPS
        if numset1.unit is None or numset2.unit is None or numset3.unit is None or not numset1.unit or not \
                numset2.unit or not numset3.unit:
            return True

        unit1 = numset1.unit[0]
        unit2 = numset2.unit[0]
        unit3 = numset3.unit[0]
        # Check compatibility for addition/ subtraction
        # This implies that both premise numsets should 
        # be compatible with the hypothesis numset
        if unit1 == unit3 and unit2 == unit3:
            return True
        elif self.unit_compatibility(unit1, unit3) and self.unit_compatibility(unit2, unit3):
            return True
        # Check compatibility for multiplication/ division
        # This implies that both premise numsets should
        # be compatible with the hypothesis numset
        elif unit1 == unit3 or unit2 == unit3:
            return True
        elif self.unit_compatibility(unit1, unit3) or self.unit_compatibility(unit2, unit3):
            return True

        return False

    def prune_numset_pairs(self, pairs):
        # INPUT: All possible pairs and triples of numsets
        # TASK: Remove all incompatible pairs and triples
        # OUTPUT: List of compatible pairs and triples
        pruned_pairs = []
        for num, pair in enumerate(pairs):
            compatible = False
            # Check compatibility for (p, h) pairs
            if len(pair) == 2:
                compatible = self.check_pair_compatibility(pair)
            # Check compatibility for (p, p, h) triples
            elif len(pair) == 3:
                compatible = self.check_triple_compatibility(pair)
            if compatible:
                # Overwrite premise numset units to
                # match hypothesis numset units, just
                # to make it easier for ILP
                if len(pair) == 2:
                    pair[0].unit = pair[1].unit
                if len(pair) == 3:
                    pair[0].unit = pair[2].unit
                    pair[1].unit = pair[2].unit
                pruned_pairs.append(CompatibleNumsets(pair))
        return pruned_pairs
