# EQUATE


This repository contains the EQUATE dataset, and the Q-REAS symbolic reasoning baseline[[1]](https://arxiv.org/abs/1901.03735).

## EQUATE

EQUATE (Evaluating Quantitative Understanding Aptitude in Textual Entailment) is a new framework for evaluating quantitative reasoning ability in textual entailment.
EQUATE consists of five NLI test sets featuring quantities. You can download EQUATE [here](https://github.com/AbhilashaRavichander/EQUATE/tree/master/ProcessedDatasets). Three of these tests for quantitative reasoning feature language from real-world sources
such as news articles and social media (RTE, NewsNLI Reddit), and two are controlled synthetic tests, evaluating model ability
to reason with quantifiers and perform simple arithmetic (AWP, Stress Test).


| Test Set        | Source  | Size | Classes  | Phenomena |
| ------------- |:-------------:| :-----:|:-------------:| :-----:|
| RTE-Quant     | RTE2-RTE4 | 166 | 2 | Arithmetic, Ranges, Quantifiers |
| NewsNLI   |  CNN | 968 | 2 | Ordinals, Quantifiers, Arithmetic, Approximation, Magnitude, Ratios, Verbal |
| RedditNLI  | Reddit | 250 | 3 | Range, Arithmetic, Approximation, Verbal  |
| StressTest     | AQuA-RAT | 7500 | 3 | Quantifiers |
| AWPNLI     | Arithmetic Word Problems | 722 | 2 | Arithmetic |


Models reporting performance on any NLI dataset can additionally evaluate on the EQUATE benchmark,
to demonstrate competence at quantitative reasoning.

## Q-Reas

We also provide a baseline quantitative reasoner Q-Reas. Q-Reas manipulates quantity representations symbolically to make entailment decisions.
We hope this provides a framework for the development of hybrid neuro-symbolic architectures to combine the strengths of symbolic reasoners and
neural models.

Q-Reas has five modules:
1. Quantity Segmenter: Extracts quantity mentions
2. Quantity Parser: Parses mentions into semantic representations called NUMSETS
3. Quantity Pruner: Identifies compatible NUMSET pairs
4. ILP Equation Generator: Composes compatible NUMSETS to form plausible equation trees
5. Global Reasoner: Constructs justifications for each quantity in the hypothesis,
analyzes them to determine entailment labels

![Qreas](qreas.jpeg?raw=true)




### How to Run Q-Reas

#### Running Q-Reas on EQUATE

To run Q-Reas on EQUATE, you will need to run the following command:
python global_reasoner.py -DATASET_NAME (rte, newsnli, reddit, awp, stresstest)

Q-Reas consists of the following components:
1. Quantity Segmenter: quantity_segmenter.py (uses utils_segmenter.py)
2. Quantity Parser: numerical_parser.py (uses utils_parser.py)
3. Quantity Pruner: numset_pruner.py
4. ILP Equation Generator: ilp.py
5. Global Reasoner: global_reasoner.py (uses utils_reasoner.py, scorer.py, eval.py)

and utilizes the following data structures:
1. numset.py: Defines semantic representation for a quantity
2. parsed_numsets.py: Stores extracted NUMSETS for a premise-hypothesis pair
3. compatible_numsets.py: Stores compatible pairs of NUMSETS

## References

Please cite [[1]](https://arxiv.org/abs/1901.03735) if our work influences your research.

### EQUATE: A Benchmark Evaluation Framework for Quantitative Reasoning in Natural Language Inference (CoNLL 2019)

[1] A. Ravichander*, A. Naik*, C. Rose, E. Hovy [*EQUATE: A Benchmark Evaluation Framework for Quantitative Reasoning in Natural Language Inference*](https://arxiv.org/abs/1901.03735)

```
@article{ravichander2019equate,
  title={EQUATE: A Benchmark Evaluation Framework for Quantitative Reasoning in Natural Language Inference},
  author={Ravichander, Abhilasha and Naik, Aakanksha and Rose, Carolyn and Hovy, Eduard},
  journal={arXiv preprint arXiv:1901.03735},
  year={2019}
}
