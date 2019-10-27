'''Creates latex table row to log experiment results'''

def create_latex_table_row(results_dict, model_name, train_name = "multinli"):
    f = open("./results/"+model_name+"_"+train_name+"_results.txt", "w")
    latex_string = model_name+"  & "

    if "Numerical Stress Test" in results_dict:
        latex_string +=str(results_dict["Numerical Stress Test"])+"\% &"
    else:
        latex_string+=" & "

    if "RTE" in results_dict:
        latex_string +=str(results_dict["RTE"])+"\% &"
    else:
        latex_string+=" & "

    if "AWP" in results_dict:
        latex_string +=str(results_dict["AWP"])+"\% &"
    else:
        latex_string+=" & "


    if "QuantNLI" in results_dict:
        latex_string +=str(results_dict["QuantNLI"])+"\% \\\\ \hline"
    else:
        latex_string+=" \\\\ \hline "
    f.write(latex_string)
    f.close()




