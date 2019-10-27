from nltk.corpus import wordnet as wn


class Scorer():
    def __init__(self):
        pass

    def get_sim_score(self, pair):
        score = pair[0].is_equal(pair[1])
        neg_score = pair[0].is_unequal(pair[1])

        path_score = 0

        if len(pair[0].verb) > 1 and len(pair[1].verb) > 1:
            premise_verb = pair[0].verb[0]
            hyp_verb = pair[1].verb[0]

            poss_prem_syn = wn.synsets(premise_verb)
            poss_hyp_syn = wn.synsets(hyp_verb)
            if len(poss_prem_syn) > 0 and len(poss_hyp_syn) > 0:
                prem_syn = poss_prem_syn[0]
                hyp_syn = poss_hyp_syn[0]
                path_score = prem_syn.wup_similarity(hyp_syn)
        if path_score:
            return [path_score + score, 0, 1 - path_score + neg_score]
        return [score, 0, 1 - score]
