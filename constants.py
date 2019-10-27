from nltk.data import load
from nltk.tree import ParentedTree

tagset = load('help/tagsets/upenn_tagset.pickle').keys()

'''Paths and number of categories for evaluation datasets'''
datasets = {"mnli_num": {"data_path": "./multinli_0.9_quant_comb.jsonl", "classes": 3,
                         },

            "rte": {"data_path": "./ProcessedDatasets/RTE_Quant.jsonl",
                    "classes": 2,
                    },

            "stresstest": {"data_path": "./ProcessedDatasets/StressTest.jsonl",
                           "classes": 3,
                           },

            "awp": {"data_path": "./ProcessedDatasets/AWPNLI.jsonl", "classes": 2,
                    },

            "reddit": {"data_path": "./ProcessedDatasets/RedditNLI.jsonl",
                       "classes": 3,
                       },

            "newsnli": {"data_path": "./ProcessedDatasets/NewsNLI.jsonl",
                     "classes": 2,
                     }
            }
