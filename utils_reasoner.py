import jsonlines


def preprocess(text):
    text = text.lower()
    text = text.replace("-", " - ")
    return text


def read_data(filename):
    ''' Reads a jsonl file
    :param filename: file to be read
    :return: list of NLI samples
    '''

    dev_data = []

    with jsonlines.open(filename) as reader:
        for obj in reader:
            dev_data.append(obj)

    assert len(dev_data) > 0

    return dev_data


def log_example(LOG_FILE, premise, hypothesis, gold_label, extractor):
    f = open(LOG_FILE, "a")

    f.write("-----\n")
    f.write("PREMISE : " + str(premise.encode('ascii', 'ignore')) + "\n")
    f.write("HYPOTHESIS : " + str(hypothesis.encode('ascii', 'ignore')) + "\n")

    f.write("-----\n")
    f.write("PREMISE QUANTITIY MENTIONS:\n")
    f.write(str(extractor["premise_quantity_mentions"]) + "\n\n\n")
    f.write("HYPOTHESIS QUANTITIY MENTIONS:\n")
    f.write(str(extractor["hypothesis_quantity_mentions"]) + "\n\n\n")

    f.write("-----\n")
    f.write("PREMISE QUANTITY SETS:\n")
    f.write(str(extractor["premise_quantity_sets"]) + "\n\n\n")
    f.write("HYPOTHESIS QUANTITIY SETS:\n")
    f.write(str(extractor["hypothesis_quantity_sets"]) + "\n")

    f.write("-----\n")
    f.write("PRUNED PAIRS:\n")
    f.write(str(len(extractor['ph_pairs'])) + "\n")
    for each_pair in extractor['ph_pairs']:
        f.write(str(each_pair) + "\n")

    f.write("-----\n")
    f.write("ILP TREES:\n")
    f.write(str(extractor["ilp_trees"]) + "\n\n\n")

    f.write("-----\n")
    f.write("JUSTIFICATIONS:\n")
    f.write(str(extractor["hypothesis_justifications"]) + "\n\n\n")

    f.write("-----\n")
    f.write("GOLD LABEL:\n")
    f.write(str(gold_label) + "\n\n\n")

    f.write("============================\n\n\n\n\n")

    f.close()


def is_example_correct(n_classes, gold_label, predicted_label):
    return (n_classes == 3 and gold_label == predicted_label) or (n_classes == 2 and (
        (gold_label == "entailment" and gold_label == predicted_label) or (
            gold_label != "entailment" and predicted_label != "entailment")))
