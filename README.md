# EQUATE


This repository contains the EQUATE dataset, and the Q-REAS symbolic reasoning baseline[[1]](https://arxiv.org/abs/1901.03735).

## EQUATE

EQUATE (Evaluating Quantitative Understanding Aptitude in Textual Entailment) is a new framework for evaluating quantitative reasoning ability in textual entailment.
EQUATE consists of five NLI test sets featuring quantities. Three of these tests for quantitative reasoning feature language from real-world sources
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

Q-Reas has five stages:
1. Quantity mentions are extracted and
parsed into semantic representations called NUMSETS
2. Compatible NUMSETS are identified
3. Compatible numsets are composed to form plausible equation trees
4. Justifications are constructed for each quantity in the hypothesis
5. Justifications are analyzed to determine entailment labels

<p float="left">
  <img src="https://github.com/AbhilashaRavichander/EQUATE/edit/master/models.pdf" width="100" />
</p>

### How to Run Q-Reas

#### Running on EQUATE

python global_reasoner.py -DATASET_NAME (rte, newsnli, reddit, awp, stresstest)


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
