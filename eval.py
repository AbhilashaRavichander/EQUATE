'''Evaluation Framework'''

LABEL_MAP = {0: "entailment", 2: "neutral", 1: "contradiction"}


def evaluate_acc(dev_data, predicted_dev_labels, cat=2, write=True):
    '''Collapse if your model has entailment neutral and contradiction, but your data is entailment YES/NO. If not
    just compare.'''

    correct, total = 0, 0

    if write:
        f = open("./example_predictions_qreas.txt", "w")
    for each_ind, each_label in enumerate(dev_data):
        # Collapse neutral and contradiction
        if cat == 2:

            if not ((dev_data[each_ind] == "entailment" and predicted_dev_labels[each_ind] != "entailment")
                    or (dev_data[each_ind] != "entailment" and predicted_dev_labels[each_ind] == "entailment")):
                correct += 1

            if write:
                actual_pred = ""
                if dev_data[each_ind] == "entailment":
                    actual_pred += "YES,"
                else:
                    actual_pred += "NO,"

                if predicted_dev_labels[each_ind] == "entailment":
                    actual_pred += "YES\n"
                else:
                    actual_pred += "NO\n"

                f.write(actual_pred)


        elif cat == 3:

            if dev_data[each_ind] == predicted_dev_labels[each_ind]:
                correct += 1
            f.write(dev_data[each_ind] + "," + predicted_dev_labels[each_ind] + "\n")

        total += 1
    return (correct * 1.0) / total
