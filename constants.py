from nltk.data import load
from nltk.tree import ParentedTree

tagset = load('help/tagsets/upenn_tagset.pickle').keys()

'''Paths and number of categories for evaluation datasets'''
datasets = {"mnli_num": {"data_path": "./multinli_0.9_quant_comb.jsonl", "classes": 3,
                         },

            "rte": {"data_path": "/usr0/home/anaik/EQUATE/RefactoredCode/ProcessedDatasets/RTE_Quant.jsonl",
                    "classes": 2,
                    },

            "stresstest": {"data_path": "/usr0/home/anaik/EQUATE/RefactoredCode/ProcessedDatasets/StressTest.jsonl",
                           "classes": 3,
                           },

            "awp": {"data_path": "/usr0/home/anaik/EQUATE/RefactoredCode/ProcessedDatasets/AWPNLI.jsonl", "classes": 2,
                    },

            "reddit": {"data_path": "/usr0/home/anaik/EQUATE/RefactoredCode/ProcessedDatasets/RedditNLI.jsonl",
                       "classes": 3,
                       },

            "qnli": {"data_path": "/usr0/home/anaik/EQUATE/RefactoredCode/ProcessedDatasets/NewsNLI.jsonl",
                     "classes": 2,
                     }
            }
