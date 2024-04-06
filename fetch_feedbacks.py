import json
import os
import re
from process_transcoder import locate_function_name_py
import signal
from process_valid_inputs import TimeoutHandler, run_cmd, locate_params_py, \
    refine_code_py, locate_function_name_java, refine_code_ja, has_array, \
    locate_function_name_cpp, refine_code_cpp
from tqdm import tqdm
import jsonlines
import argparse



def fetch_exe_ret_py(target_file, out_file, test_case_file, test_case_num, timeout):
    eval_ids = os.listdir(f"./cleaned_data/transcoder_evaluation_gfg/python")
    test_case_pool = {}
    with open(test_case_file, encoding="utf-8") as fr:
        for line in fr.readlines():
            line = json.loads(line)
            test_case_pool.update({line['id']:line['test_case']})
    correct = 0
    count = 0
    with open(target_file, encoding="utf-8") as fr:
        for line in tqdm(fr.readlines()):
            line = json.loads(line)
            id = line['id']
            if f"{id}.py" not in eval_ids:
                continue
            # if id != "LONGEST_COMMON_SUBSEQUENCE_WITH_AT_MOST_K_CHANGES_ALLOWED":
            #     continue
            count += 1
            # 默认第一个
            if len(line['python']) < 1:
                code = "NONE"
            else:
                code = line['python'][0]
            func_name = locate_function_name_py(code)
            var_lst = locate_params_py(code)
            code = refine_code_py(code)
            test_cases = test_case_pool[id][:test_case_num]
            cases_errs = []
            sub_correct = 0
            # skip samples without testcases
            if test_cases != [] and func_name == None:
                with jsonlines.open(out_file, "a") as fw:
                    fw.write({"id": id, "feedbacks": [(i, "") for i in test_cases]})
                continue
            elif test_cases == [] and func_name != None:
                with jsonlines.open(out_file, "a") as fw:
                    fw.write({"id": id, "feedbacks": [("", "OK") for _ in range(test_case_num)]})
                correct += 1
                continue
            elif test_cases == [] and func_name == None:
                with jsonlines.open(out_file, "a") as fw:
                    fw.write({"id": id, "feedbacks": [("", "") for _ in range(test_case_num)]})
                continue

            for case_id, pair in enumerate(test_cases):
                if "Outputs (void):\n" not in pair:
                    pattern = re.compile(r"Inputs:\n(.+)\nOutputs:\n(.+)", flags=re.S)
                    out = pattern.findall(pair)
                    if out == []:
                        print(id)
                        assert False
                    inputs, outputs = out[0]
                    param_lst = inputs.split("\n")
                    param_lst1 = [i.split("=")[1] for i in param_lst if i != "" and "=" in i]
                    case = ",".join(param_lst)
                    case1 = param_lst1[0]
                    script = ""
                    with open("./cleaned_data/test_case_gen_scripts/unit_test.py", encoding="utf-8") as fr:
                        for line in fr.readlines():
                            if "# TO_FILL_FUNC" in line:
                                script += code + "\n"
                            elif "# ACT_OUT" in line:
                                if len(param_lst) <= 1:
                                    script += line.replace("# ACT_OUT", f"act_out = {func_name}({case1})")
                                else:
                                    param_lines = ""
                                    for param in param_lst:
                                        param_lines += line.replace("# ACT_OUT", f"{param}") + "\n"
                                    script += param_lines + line.replace("# ACT_OUT", f"act_out = {func_name}({case})")
                            elif "# EXP_OUT" in line:
                                if outputs.strip() == 'inf' or outputs.strip() == '-inf':
                                    outputs = f"float(\'{outputs.strip()}\')"
                                script += line.replace("# EXP_OUT", f"exp_out = {outputs}")
                            else:
                                script += line
                else:
                    pattern = re.compile(r"Inputs:\n(.+)\nOutputs \(void\):\n", flags=re.S)
                    out = pattern.findall(pair)
                    inputs = out[0]
                    if out == []:
                        print(id)
                        assert False
                    param_lst = inputs.split("\n")
                    param_lst1 = [i.split("=")[1] for i in param_lst if i != "" and "=" in i]
                    case = ",".join(param_lst)
                    case1 = param_lst1[0]
                    script = ""
                    with open("./cleaned_data/test_case_gen_scripts/unit_test.py", encoding="utf-8") as fr:
                        for line in fr.readlines():
                            if "# TO_FILL_FUNC" in line:
                                script += code + "\n"
                            elif "# ACT_OUT" in line:
                                if len(param_lst) <= 1:
                                    script += line.replace("# ACT_OUT", f"act_out = {func_name}({case1})")
                                else:
                                    param_lines = ""
                                    for param in param_lst:
                                        param_lines += line.replace("# ACT_OUT", f"{param}") + "\n"
                                    script += param_lines + line.replace("# ACT_OUT", f"act_out = {func_name}({case})")
                            elif "# EXP_OUT" in line:
                                script += line.replace("# EXP_OUT", f"exp_out = None")
                            else:
                                script += line
                with open("./cleaned_data/test_case_gen_scripts/tmp_scripts/tmp.py", "w") as fw:
                    fw.write(script)
                # print(script)
                # assert False
                signal.signal(signal.SIGALRM, TimeoutHandler)
                signal.alarm(timeout)
                try:
                    result = run_cmd(f"python ./cleaned_data/test_case_gen_scripts/tmp_scripts/tmp.py")
                    signal.alarm(0)
                except Exception as ret:
                    cases_errs.append((pair, "Timeout Error"))
                    signal.alarm(0)
                    print("timeout error")
                    continue
                # print("result: ", result)
                # assert False
                if result[0] == "" and result[1] != "":
                    cases_errs.append((pair, f"Compilation Error:\n{result[1]}"))
                    print("compilation error")
                elif "Runtime Error:\n" in result[0]:
                    cases_errs.append((pair, f"Runtime Error:\n{result[0]}"))
                    print("runtime error")
                elif "OK" not in result[0].split("\n"):
                    err_msg = result[0].replace("\n", ",")
                    cases_errs.append((pair, f"Logic Error:\n{err_msg}"))
                    print("logic error")
                else:
                    sub_correct += 1
                    cases_errs.append((pair, "OK"))
            if sub_correct == len(test_cases):
                correct += 1
            # assert False
            with jsonlines.open(out_file, "a") as fw:
                fw.write({"id":id, "feedbacks": cases_errs})
    print(f"pass rate: {correct / count}, {correct}, {count}")

def return_var_lst_ja(param_lst):
    pattern_pa1 = re.compile(r"\w+\s(\w+)")
    pattern_pa2 = re.compile(r"\w+\s?\[\s?\]\s(\w+)")
    var_lst = []
    for i in param_lst:
        if len(pattern_pa1.findall(i)) > 0:
            var_lst.append(pattern_pa1.findall(i)[0])
        elif len(pattern_pa2.findall(i)) > 0:
            var_lst.append(pattern_pa2.findall(i)[0])
    return var_lst

def fetch_exe_ret_ja(target_file, out_file, test_case_file, test_case_num, timeout):
    eval_ids = os.listdir(f"./cleaned_data/transcoder_evaluation_gfg/java")
    test_case_pool = {}
    with open(test_case_file, encoding="utf-8") as fr:
        for line in fr.readlines():
            line = json.loads(line)
            test_case_pool.update({line['id']:line['test_case']})
    correct = 0
    count = 0
    with open(target_file, encoding="utf-8") as fr:
        for line in tqdm(fr.readlines()):
            line = json.loads(line)
            id = line['id']
            if f"{id}.java" not in eval_ids:
                continue
            # if id != "FIND_THREE_ELEMENT_FROM_DIFFERENT_THREE_ARRAYS_SUCH_THAT_THAT_A_B_C_K_1":
            #     continue
            count += 1
            # 默认第一个
            if len(line['java']) < 1:
                code = "NONE"
            else:
                code = line['java'][0]
            func_name, act_return_type, act_var_lst = locate_function_name_java(code)
            code = refine_code_ja(code)
            test_cases = test_case_pool[id][:test_case_num]
            cases_errs = []
            sub_correct = 0
            # skip samples
            if test_cases != [] and func_name == None:
                with jsonlines.open(out_file, "a") as fw:
                    fw.write({"id": id, "feedbacks": [(i, "") for i in test_cases]})
                continue
            elif test_cases == [] and func_name != None:
                with jsonlines.open(out_file, "a") as fw:
                    fw.write({"id": id, "feedbacks": [("", "OK") for _ in range(test_case_num)]})
                correct += 1
                continue
            elif test_cases == [] and func_name == None:
                with jsonlines.open(out_file, "a") as fw:
                    fw.write({"id": id, "feedbacks": [("", "") for _ in range(test_case_num)]})
                continue

            for pair in test_cases:
                if "Outputs (void):\n" not in pair:
                    exp_return_type = re.findall(f"Outputs \((.*)\):\n", pair)[0]
                    pattern = re.compile(r"Inputs:\n(.+)\nOutputs \(.*\):\n(.+)", flags=re.S)
                    out = pattern.findall(pair)
                    if out == []:
                        print(id)
                        assert False
                    inputs, outputs = out[0]
                    param_lst = inputs.split("\n")
                    case = ",".join(act_var_lst)
                    script = ""
                    with open("./cleaned_data/test_case_gen_scripts/unit_test.java", encoding="utf-8") as fr:
                        for line in fr.readlines():
                            if "// TO_FILL_FUNC" in line: # done
                                script += code + "\n"
                            elif "// ACT_OUT" in line:
                                if len(param_lst) <= 1: # done
                                    param_lst_one = [i for i in param_lst if i != "" and "=" in i][0]
                                    head = param_lst_one.split("=")[0]
                                    var = head.strip().split()[-1]
                                    param_lines = line.replace("// ACT_OUT", f"{param_lst_one}") + "\n"
                                    script += param_lines + line.replace("// ACT_OUT", f"{act_return_type} act_out = {func_name}({var});")
                                else:
                                    param_lines = ""
                                    for param in param_lst:
                                        param_lines += line.replace("// ACT_OUT", f"{param}") + "\n"
                                    script += param_lines + line.replace("// ACT_OUT", f"{act_return_type} act_out = {func_name}({case});")
                            elif "// EXP_OUT" in line:
                                script += line.replace("// EXP_OUT", f"{exp_return_type} exp_out = {outputs};") # done
                            elif "// COMPARE" in line:
                                if has_array(exp_return_type):
                                    # todo signal
                                    print("AN ARRAY APPEAR!!!")
                                    single_return_type = exp_return_type.replace("[", "").replace("]", "").strip()
                                    line0 = line.replace("// COMPARE", f"String act_out_str = \"{{\";\nfor({single_return_type} single_value: act_output){{\nact_out_str += single_value + \",\";\n}}\n"
                                                                       f"act_out_str = act_out_str.substring(0,act_out_str.length()-1)) + \"}}\";")
                                    line1 = line.replace("// COMPARE", f"if(Arrays.equals(act_out, exp_out)) System.out.println(\"OK\");\n")
                                    line2 = line.replace("// COMPARE", f"else {{\nSystem.out.print(\"Expected Output:{outputs}\\nActual Output:\" + act_out_str + \"\\nExpected output and actual output are not equal!\");}}")
                                    script += line0 + line1 + line2
                                elif exp_return_type == "String":
                                    line1 = line.replace("// COMPARE", f"if(act_out.equals(exp_out)) System.out.println(\"OK\");\n")
                                    line2 = line.replace("// COMPARE", f"else {{\nSystem.out.print(\"Expected Output:\" + {outputs} + \"\\nActual Output:\" + act_out + \"\\nExpected output and actual output are not equal!\");}}")
                                    script += line1 + line2
                                elif exp_return_type in ['float', 'double']:
                                    line1 = line.replace("// COMPARE",
                                                         f"if(Math.abs(act_out-exp_out)<1e-3) System.out.println(\"OK\");\n")
                                    line2 = line.replace("// COMPARE",
                                                         f"else {{\nSystem.out.print(\"Expected Output:\");\nSystem.out.print({outputs});"
                                                         f"\nSystem.out.print(\"\\nActual Output:\");\nSystem.out.print(act_out);"
                                                         f"\nSystem.out.print(\"\\nExpected output and actual output are not equal!\");}}")
                                    script += line1 + line2
                                else:
                                    line1 = line.replace("// COMPARE", f"if(act_out == exp_out) System.out.println(\"OK\");\n")
                                    line2 = line.replace("// COMPARE", f"else {{\nSystem.out.print(\"Expected Output:{outputs}\\nActual Output:\");\nSystem.out.print(act_out);\nSystem.out.print(\"\\nExpected output and actual output are not equal!\");}}")
                                    script += line1 + line2
                            else:
                                script += line
                else:
                    pattern = re.compile(r"Inputs:\n(.+)\nOutputs \(void\):\n", flags=re.S)
                    out = pattern.findall(pair)
                    inputs = out[0]
                    if out == []:
                        print(id)
                        assert False
                    param_lst = inputs.split("\n")
                    case = ",".join(act_var_lst)
                    script = ""
                    with open("./cleaned_data/test_case_gen_scripts/unit_test.java", encoding="utf-8") as fr:
                        for line in fr.readlines():
                            if "// TO_FILL_FUNC" in line:
                                script += code + "\n"
                            elif "// ACT_OUT" in line:
                                if len(param_lst) <= 1:
                                    param_lst_one = [i for i in param_lst if i != "" and "=" in i][0]
                                    head = param_lst_one.split("=")[0]
                                    var = head.strip().split()[-1]
                                    param_lines = line.replace("// ACT_OUT", f"{param_lst_one}") + "\n"
                                    script += param_lines + line.replace("// ACT_OUT", f"{func_name}({var});")
                                else:
                                    param_lines = ""
                                    for param in param_lst:
                                        param_lines += line.replace("// ACT_OUT", f"{param}") + "\n"
                                    script += param_lines + line.replace("// ACT_OUT", f"{func_name}({case});")
                            elif "// COMPARE" in line:
                                script += line.replace("// COMPARE", f"System.out.println(\"OK\");")
                            else:
                                script += line
                # print(script)
                # assert False
                with open("./cleaned_data/test_case_gen_scripts/tmp_scripts/tmp.java", "w") as fw:
                    fw.write(script)
                # print(script)
                # assert False
                signal.signal(signal.SIGALRM, TimeoutHandler)
                signal.alarm(timeout)
                try:
                    result = run_cmd(f"java ./cleaned_data/test_case_gen_scripts/tmp_scripts/tmp.java")
                    signal.alarm(0)
                except Exception as ret:
                    cases_errs.append((pair, f"Timeout Error"))
                    signal.alarm(0)
                    print("timeout error")
                    continue
                # print("result: ", result)
                # assert False
                if result[0] == "" and result[1] != "":
                    cases_errs.append((pair, f"Compilation Error:\n{result[1]}"))
                    print("compilation error")
                elif "Runtime Error:" == result[0]:
                    cases_errs.append((pair, f"Runtime Error:\n{result[1]}"))
                    print("runtime error")
                elif "OK" not in result[0].split("\n"):
                    err_msg = result[0].replace("\n", ",")
                    cases_errs.append((pair, f"Logic Error:\n{err_msg}"))
                    print("logic error")
                else:
                    sub_correct += 1
                    cases_errs.append((pair, result[0]))
            if sub_correct == len(test_cases):
                correct += 1
            with jsonlines.open(out_file, "a") as fw:
                fw.write({"id": id, "feedbacks": cases_errs})
    print(f"pass rate: {correct / count}, {correct}, {count}")

def fetch_exe_ret_cp(target_file, out_file, test_case_file, test_case_num, timeout=5):
    eval_ids = os.listdir(f"./cleaned_data/transcoder_evaluation_gfg/cpp")
    test_case_pool = {}
    with open(test_case_file, encoding="utf-8") as fr:
        for line in fr.readlines():
            line = json.loads(line)
            test_case_pool.update({line['id']: line['test_case']})
    correct = 0
    count = 0
    with open(target_file, encoding="utf-8") as fr:
        for line in tqdm(fr.readlines()):
            line = json.loads(line)
            id = line['id']
            if f"{id}.cpp" not in eval_ids:
                continue
            # if id != "AREA_OF_THE_CIRCLE_THAT_HAS_A_SQUARE_AND_A_CIRCLE_INSCRIBED_IN_IT":
            #     continue
            count += 1
            # 默认第一个
            if len(line['cpp']) < 1:
                code = "NONE"
            else:
                code = line['cpp'][0]
            func_name, act_return_type, act_var_lst = locate_function_name_cpp(code)
            code = refine_code_cpp(code)
            test_cases = test_case_pool[id][:test_case_num]
            cases_errs = []
            sub_correct = 0
            # skip cases
            if test_cases != [] and func_name == None:
                with jsonlines.open(out_file, "a") as fw:
                    fw.write({"id": id, "feedbacks": [(i, "") for i in test_cases]})
                continue
            elif test_cases == [] and func_name != None:
                with jsonlines.open(out_file, "a") as fw:
                    fw.write({"id": id, "feedbacks": [("", "OK") for _ in range(test_case_num)]})
                correct += 1
                continue
            elif test_cases == [] and func_name == None:
                with jsonlines.open(out_file, "a") as fw:
                    fw.write({"id": id, "feedbacks": [("", "") for _ in range(test_case_num)]})
                continue

            for pair in test_cases:
                if "Outputs (void):\n" not in pair:
                    exp_return_type = re.findall(f"Outputs \((.*)\):\n", pair)[0]
                    pattern = re.compile(r"Inputs:\n(.+)\nOutputs \(.*\):\n(.+)", flags=re.S)
                    out = pattern.findall(pair)
                    if out == []:
                        print(id)
                        assert False
                    inputs, outputs = out[0]
                    param_lst = inputs.split("\n")
                    # exp_var_lst = return_var_lst_ja(param_lst)
                    # param_lst1 = [i.split("=")[1] for i in param_lst if i != "" and "=" in i]
                    # case1 = param_lst1[0].strip().rstrip(";")
                    case = ",".join(act_var_lst)
                    script = ""
                    with open("./cleaned_data/test_case_gen_scripts/backward_test.cc", encoding="utf-8") as fr:
                        for line in fr.readlines():
                            if "// TO_FILL_FUNC" in line:
                                script += code + "\n" #done
                            elif "// ACT_OUT" in line:
                                if len(param_lst) <= 1:
                                    param_lst_one = [i for i in param_lst if i != "" and "=" in i][0]
                                    head = param_lst_one.split("=")[0]
                                    var = head.replace("[", "").replace("]", "").strip().split()[-1]
                                    param_lines = line.replace("// ACT_OUT", f"{param_lst_one}") + "\n"
                                    script += param_lines + line.replace("// ACT_OUT",
                                                                         f"{act_return_type} act_out = {func_name}({var});")

                                    # script += line.replace("// ACT_OUT", f"{act_return_type} act_out = {func_name}({case1});") #done
                                else:
                                    param_lines = ""
                                    for param in param_lst:
                                        param_lines += line.replace("// ACT_OUT", f"{param}") + "\n"
                                    script += param_lines + line.replace("// ACT_OUT",
                                                                         f"{act_return_type} act_out = {func_name}({case});") #done
                            elif "// EXP_OUT" in line:
                                # if outputs.strip() == 'inf' or outputs.strip() == '-inf':
                                #     outputs = f"float(\'{outputs.strip()}\')"
                                script += line.replace("// EXP_OUT", f"{exp_return_type} exp_out = {outputs};") # done
                            elif "// COMPARE" in line:
                                if has_array(exp_return_type):
                                    # todo signal
                                    print("AN ARRAY APPEAR!!!")
                                    assert False
                                    # single_return_type = exp_return_type.replace("[", "").replace("]", "").strip()
                                    # line0 = line.replace("// COMPARE",
                                    #                      f"String act_out_str = \"{{\";\nwhile(*output){{\nact_out_str += *output + \",\";\\n output++;}}\n}}\n"
                                    #                      f"act_out_str = act_out_str.substr(0, strlen(act_out_str)-1)) + \"}}\";")
                                    # line1 = line.replace("// COMPARE",
                                    #                      f"if(Arrays.equals(act_out, exp_out)) System.out.println(\"OK\");\n")
                                    # line2 = line.replace("// COMPARE",
                                    #                      f"else {{\nSystem.out.print(\"Expected Output:{outputs}\\nActual Output:\" + act_out_str + \"\\nExpected output and actual output are not equal!\");}}")
                                    # script += line0 + line1 + line2
                                elif exp_return_type == "string":
                                    line1 = line.replace("// COMPARE",
                                                         f"if(act_out.compare(exp_out) == 0) cout << \"OK\";\n") #done
                                    line2 = line.replace("// COMPARE",
                                                         f"else {{\ncout << \"Expected Output:\" << {outputs} << \"\\nActual Output:\" << act_out << \"\\nExpected output and actual output are not equal!\";}}") #done
                                    script += line1 + line2
                                elif exp_return_type in ['float', 'double']:
                                    line1 = line.replace("// COMPARE",
                                                         f"if(abs(act_out - exp_out)<1e-3) cout << \"OK\";\n")  # done
                                    line2 = line.replace("// COMPARE",
                                                         f"else {{\ncout << \"Expected Output:{outputs}\\nActual Output:\";\ncout << act_out;\ncout << \"\\nExpected output and actual output are not equal!\";}}")  # done
                                    script += line1 + line2
                                else:
                                    line1 = line.replace("// COMPARE",
                                                         f"if(act_out == exp_out) cout << \"OK\";\n") #done
                                    line2 = line.replace("// COMPARE",
                                                         f"else {{\ncout << \"Expected Output:{outputs}\\nActual Output:\";\ncout << act_out;\ncout << \"\\nExpected output and actual output are not equal!\";}}") #done
                                    script += line1 + line2
                            else:
                                script += line
                else:
                    pattern = re.compile(r"Inputs:\n(.+)\nOutputs \(void\):\n", flags=re.S)
                    out = pattern.findall(pair)
                    inputs = out[0]
                    if out == []:
                        print(id)
                        assert False
                    param_lst = inputs.split("\n")
                    # param_lst1 = [i.split("=")[1] for i in param_lst if i != "" and "=" in i]
                    # case1 = param_lst1[0].strip().rstrip(";")
                    case = ",".join(act_var_lst)
                    script = ""
                    with open("./cleaned_data/test_case_gen_scripts/backward_test.cc", encoding="utf-8") as fr:
                        for line in fr.readlines():
                            if "// TO_FILL_FUNC" in line:
                                script += code + "\n"
                            elif "// ACT_OUT" in line:
                                if len(param_lst) <= 1:
                                    param_lst_one = [i for i in param_lst if i != "" and "=" in i][0]
                                    head = param_lst_one.split("=")[0]
                                    var = head.replace("[", "").replace("]", "").strip().split()[-1]
                                    param_lines = line.replace("// ACT_OUT", f"{param_lst_one}") + "\n"
                                    script += param_lines + line.replace("// ACT_OUT", f"{func_name}({var});")
                                    # script += line.replace("// ACT_OUT", f"{func_name}({case1});") #done
                                else:
                                    param_lines = ""
                                    for param in param_lst:
                                        param_lines += line.replace("// ACT_OUT", f"{param}") + "\n"
                                    script += param_lines + line.replace("// ACT_OUT", f"{func_name}({case});") #done
                            elif "// COMPARE" in line:
                                script += line.replace("// COMPARE", f"cout << \"OK\";") #done
                            else:
                                script += line

                with open("./cleaned_data/test_case_gen_scripts/tmp_scripts/backtrace/example/backward_test.cc", "w") as fw:
                    fw.write(script)
                # print(script)
                # assert False
                signal.signal(signal.SIGALRM, TimeoutHandler)
                signal.alarm(timeout)
                try:
                    result = run_cmd(f"cd ./cleaned_data/test_case_gen_scripts/tmp_scripts/backtrace"
                                     f"&& make && ./tmp_bt")
                    signal.alarm(0)
                except Exception as ret:
                    cases_errs.append((pair, f"Timeout Error"))
                    signal.alarm(0)
                    print("timeout error")
                    continue
                # print(result)
                if "make done" not in result[0] and result[1] != "":
                    cases_errs.append((pair, f"Compilation Error:\n{result[1]}"))
                    print("compilation error")
                elif "make done" in result[0] and result[0].split("\n")[-1] == "OK":
                    sub_correct += 1
                    cases_errs.append((pair, "OK"))
                elif "make done" in result[0] and result[0].split("\n")[-1] != "OK" and result[0].strip().split("\n")[-1] == "Expected output and actual output are not equal!":
                    err_msg = result[0].replace("\n", ",")
                    cases_errs.append((pair, f"Logic Error:\n{err_msg}"))
                    print("logic error")
                else:
                    cases_errs.append((pair, f"Runtime Error:\n{result[1]}"))
                    print("runtime error")
            if sub_correct == len(test_cases):
                correct += 1
            with jsonlines.open(out_file, "a") as fw:
                fw.write({"id": id, "feedbacks": cases_errs})
    print(f"pass rate: {correct / count}, {correct}, {count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, help="model name", default="llama-7b-hf")
    parser.add_argument("--start", type=int, help="start point", default=1)
    parser.add_argument("--src_lang", type=str, help="source language", default="python")
    parser.add_argument("--dst_lang", type=str, help="target language", default="java")
    parser.add_argument("--test_case_num", type=int, help="num of test cases", default=3)
    parser.add_argument("--round", type=int, help="number of round", default=2)
    args = parser.parse_args()

    model = args.model
    src_lang = args.src_lang
    dst_lang = args.dst_lang
    test_case_num = args.test_case_num
    refine_round = args.round
    target_file = f"./cleaned_data/{model}/post_processed/testable_{src_lang}_{dst_lang}_w_{test_case_num}cases_{refine_round}round.jsonl"
    out_file = f"./cleaned_data/{model}/feedbacks/raw/testable_{src_lang}_{dst_lang}_w_{test_case_num}cases_{refine_round}round_raw.jsonl"
    test_case_file = f"./cleaned_data/{model}/test_cases/test_cases_{dst_lang}.jsonl"
    if dst_lang == "python":
        fetch_exe_ret_py(target_file, out_file, test_case_file, test_case_num, timeout=10)
    elif dst_lang == "java":
        fetch_exe_ret_ja(target_file, out_file, test_case_file, test_case_num, timeout=10)
    elif dst_lang == "cpp":
        fetch_exe_ret_cp(target_file, out_file, test_case_file, test_case_num, timeout=10)
