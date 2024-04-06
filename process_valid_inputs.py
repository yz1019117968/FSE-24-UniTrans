


import json
import re
from process_transcoder import locate_function_name_py
import os
from tqdm import tqdm
import jsonlines
import signal
import subprocess
from cleaned_data.templates.examples_inp import example_cpp, valid_inputs_cpp, \
    example_java, valid_inputs_java, example_python, valid_inputs_python
import argparse

def TimeoutHandler(signum, frame):
    raise Exception("timeout")

def locate_params_py(code):
    pattern = re.compile(r"def \w+\s?\(\s?(\w+.*)\s?\)\s?:")
    params = pattern.findall(code)
    if params != []:
        return [i.strip() for i in params[0].split(",")]
    else:
        return None
def refine_code_py(code):
    pattern = re.compile(r"print\s?\(\s?.*?\s?\)\n", flags=re.S)
    code = pattern.sub("pass\n", code)
    return code

def post_process_py(model, keep_all, timeout=5, start=1):
    # script_lst = os.listdir("./cleaned_data/transcoder_evaluation_gfg/python")
    count = 0
    with open(f"./cleaned_data/{model}/valid_inputs/valid_inputs_python.jsonl", encoding="utf-8") as fr:
        for line in tqdm(fr.readlines()):
            count += 1
            if count < start:
                continue
            line = json.loads(line)
            id = line['id']
            # todo del
            # if id != "ANALYSIS_OF_ALGORITHMS_SET_2_ASYMPTOTIC_ANALYSIS":
            #     continue
            item = line['python']
            item_case_lst = []
            for item_i in item:
                if model != "gpt3_5":
                    # item_i = item_i.replace(example_python, "").replace(valid_inputs_python, "")
                    item_i = item_i.split("END_OF_CASE\n")[1]
                    found = re.findall(r"Input_\d+:.+", item_i, flags=re.S)
                    if len(found) != 0:
                        item_i = found[0]
                    else:
                        item_i = ""
                        print("NO CASES! ", id)
                case_lst = [i.strip() for i in re.split(r"Input_\d+:", item_i) if i != ""]
                for case in case_lst:
                    param_lst = case.split("\n")
                    param_lst1 = [pa.split("=")[1].strip() for pa in param_lst if pa != "" and "=" in pa] # value
                    param_lst2 = [pa for pa in param_lst if pa != "" and "=" in pa] # var = value
                    case_save = "\n".join(param_lst2) # var = value
                    if param_lst2 != []:
                        case_new1 = param_lst1[0] # for single inp
                        case_new2 = ",".join(param_lst2) # for multi-inp
                        with open("./cleaned_data/testable_samples.jsonl", encoding="utf-8") as fr:
                            for line_code in fr.readlines():
                                line_code = json.loads(line_code)
                                if line_code['id'] == id:
                                    code = line_code['python']
                                    break
                        func_name = locate_function_name_py(code)
                        var_name = locate_params_py(code)
                        code = refine_code_py(code)
                        if func_name is None:
                            print(id)
                            print(code)
                        code1 = "\n".join([i for i in code.split("\n") if i.strip() != "return"])

                        script = ""
                        with open("./cleaned_data/test_case_gen_scripts/gen_case.py", encoding="utf-8") as fr:
                            for line_script in fr.readlines():
                                if line_script.strip() == "# TO_FILL_FUNC":
                                    script += code + "\n"
                                elif line_script.strip() == "# TO_FILL_EXEC":
                                    if "return" in code1:
                                        if len(param_lst2) <= 1:
                                            script += line_script.replace("# TO_FILL_EXEC", f"print(repr({func_name}({case_new1})))") + "\n"
                                        else:
                                            param_lines = ""
                                            for param in param_lst2:
                                                param_lines += line_script.replace("# TO_FILL_EXEC", f"{param}") + "\n"
                                            script += param_lines + line_script.replace("# TO_FILL_EXEC", f"print(repr({func_name}({case_new2})))") + "\n"
                                    else:
                                        if len(param_lst2) <= 1:
                                            script += line_script.replace("# TO_FILL_EXEC", f"{func_name}({case_new1})") + "\n"
                                        else:
                                            param_lines = ""
                                            for param in param_lst2:
                                                param_lines += line_script.replace("# TO_FILL_EXEC", f"{param}") + "\n"
                                            script += param_lines + line_script.replace("# TO_FILL_EXEC", f"{func_name}({case_new2})") + "\n"
                                else:
                                    script += line_script
                        with open(f"./cleaned_data/test_case_gen_scripts/tmp_scripts/tmp.py", "w") as fw:
                            fw.write(script)
                        # print(script)
                        signal.signal(signal.SIGALRM, TimeoutHandler)
                        signal.alarm(timeout)
                        try:
                            result = run_cmd(f"python ./cleaned_data/test_case_gen_scripts/tmp_scripts/tmp.py")
                            signal.alarm(0)
                        except Exception as ret:
                            print("IGNORE THIS CASE - EXCEPTION:", ret)
                            signal.alarm(0)
                            if keep_all:
                                item_case_lst.append("FAILED")
                            continue
                        # print("result: ", result)
                        # assert False
                        if result[0] == "" and result[1] != "":
                            print("compilation error")
                            # compilation error
                            if keep_all:
                                item_case_lst.append("FAILED")
                            continue
                        elif result[0] == "exception":
                            print("runtime error")
                            # runtime error
                            if keep_all:
                                item_case_lst.append("FAILED")
                            continue
                        result = result[0]
                        case_save_var_lst = []
                        case_save_var_pa = re.compile(r"(\w+) = .+?", flags=re.S)
                        for i in case_save.split("\n"):
                            if i != "":
                                found = case_save_var_pa.findall(i)
                                if len(found) != 0:
                                    tmp_var = found[0]
                                else:
                                    continue
                                if tmp_var != "" and tmp_var in var_name:
                                    case_save_var_lst.append(i)
                        if len(case_save_var_lst) != len(var_name):
                            if keep_all:
                                item_case_lst.append("FAILED")
                            continue
                        case_save = "\n".join(case_save_var_lst)
                        if "return" not in code1:
                            item_case_lst.append(f"Inputs:\n{case_save}\nOutputs (void):\nVoid function does not have output.")
                        elif len(param_lst2) <= 1:
                            item_case_lst.append(f"Inputs:\n{var_name[0]}={case_new1}\nOutputs:\n{result}")
                        else:
                            item_case_lst.append(f"Inputs:\n{case_save}\nOutputs:\n{result}")
            if keep_all:
                with jsonlines.open(f"./cleaned_data/{model}/test_cases/test_cases_python_keep_all.jsonl", "a") as fw:
                    fw.write({"id": id, "test_case": item_case_lst})
            else:
                with jsonlines.open(f"./cleaned_data/{model}/test_cases/test_cases_python.jsonl", "a") as fw:
                    fw.write({"id": id, "test_case": list(set(item_case_lst))})

def locate_function_name_java(code):
    pattern = re.compile(r"(public|private|protected)?\s?(static)?\s?(\w+|\w+\[\])\s(\w+)\s?\(\s?(\w+.*\w*)?\s?\)")
    method_info = pattern.findall(code)
    try:
        pattern_pa1 = re.compile(r"\w+\s(\w+)")
        pattern_pa2 = re.compile(r"\w+\s?[\[\s?\]]+\s(\w+)")
        var_lst = []
        for i in method_info[0][-1].split(","):
            if len(pattern_pa1.findall(i)) > 0:
                var_lst.append(pattern_pa1.findall(i)[0])
            elif len(pattern_pa2.findall(i)) > 0:
                var_lst.append(pattern_pa2.findall(i)[0])
        return method_info[0][3], method_info[0][2], var_lst
    except Exception as e:
        return None, None, None

def locate_function_name_cpp(code):
    code4func = re.sub(r"//.+?\n", "", code)
    pattern = re.compile(r"([\w\s\*]+)\s(\w+)\s?\(\s?(\w+.*\w*)?\s?\)")
    method_info = pattern.findall(code4func)
    try:
        var_lst = []
        # int a, const std::vector<std::vector<double>>& m, vector<vector<int>> mat
        pattern_pa1 = re.compile(r"\w+\s(\w+)$")
        # int * xp; int & xp;
        pattern_pa2 = re.compile(r"\w+\s?[\*\&]{1}\s?(\w+)")
        # int arr [ ]
        pattern_pa3 = re.compile(r"\w+\s?(\w+)\s?\[\s?\]")
        # print("VARS: ", method_info[0][-1].split(","))
        for i in method_info[0][-1].split(","):
            # for-> unsigned int/long.. var;
            i = i.replace("unsigned", "").strip()
            if len(pattern_pa2.findall(i)) > 0:
                var_lst.append(pattern_pa2.findall(i)[0])
            elif len(pattern_pa3.findall(i)) > 0:
                var_lst.append(pattern_pa3.findall(i)[0])
            elif len(pattern_pa1.findall(i)) > 0:
                var_lst.append(pattern_pa1.findall(i)[0])
        # print("var_lst: ", var_lst)
        return method_info[0][1], method_info[0][0], var_lst
    except Exception as e:
        return None, None, None

def return_func_name(id, lang):
    with open("./cleaned_data/testable_samples.jsonl", encoding="utf-8") as fr:
        for line_code in fr.readlines():
            line_code = json.loads(line_code)
            if line_code['id'] == id:
                code = line_code[lang]
                break
    if lang == "java":
        func_name, return_type, var_lst = locate_function_name_java(code)
    elif lang == "cpp":
        func_name, return_type, var_lst = locate_function_name_cpp(code)
    else:
        assert False, "unknown lang!"
    if func_name is None:
        print(id)
        print(code)
    if lang == "java":
        code = refine_code_ja(code)
    elif lang == "cpp":
        code = refine_code_cpp(code)
    else:
        assert False, "unknown lang!"
    return func_name, code, return_type, var_lst

def has_array(return_type):
    pattern = re.compile(r"(\[\s?\])")
    pattern1 = re.compile(r"(\w+\s?\*)")
    if len(pattern.findall(return_type)) == 0 and len(pattern1.findall(return_type)) == 0:
        return False
    else:
        return True

def refine_code_ja(code):
    # 非贪婪方式， 包括换行符
    pattern = re.compile(r"System\s?\.\s?out\s?\.\s?print[ln]*\s?\(\s?.*?\s?\)\s?;\n", flags=re.S)
    code = pattern.sub(";\n", code)
    return code
def refine_code_cpp(code):
    pattern = re.compile(r"cout\s?<<\s?.*?;\n", flags=re.S)
    pattern1 = re.compile(r"printf\s?\(.*?\);\n", flags=re.S)
    code = pattern.sub(";\n", code)
    code = pattern1.sub(";\n", code)
    return code

def run_cmd(cmd):
    result = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf8")
    return result.stdout.read().strip(), result.stderr.read().strip()

# todo java/cpp not done
def post_process_ja(model, keep_all, timeout=5, start=1):
    # script_lst = os.listdir("./cleaned_data/transcoder_evaluation_gfg/java")
    count = 0
    with open(f"./cleaned_data/{model}/valid_inputs/valid_inputs_java.jsonl", encoding="utf-8") as fr:
        for line in tqdm(fr.readlines()):
            count += 1
            if count < start:
                continue
            line = json.loads(line)
            id = line['id']
            # todo del
            # if id != "LOWER_CASE_UPPER_CASE_INTERESTING_FACT":
            #     continue
            item = line['java']
            func_name, code, return_type, var_lst = return_func_name(id, "java")
            item_case_lst = []
            for item_i in item:
                # todo deal with llm
                if model != "gpt3_5":
                    # item_i = item_i.replace(example_java, "").replace(valid_inputs_java, "")
                    # print(item_i)
                    # assert False
                    item_i = item_i.split("END_OF_CASE\n")[1]
                    found = re.findall(r"Input_\d+:.+", item_i, flags=re.S)
                    if len(found) != 0:
                        item_i = found[0]
                    else:
                        item_i = ""
                        print("NO CASES! ", id)
                case_lst = [i.strip() for i in re.split(r"Input_\d+:", item_i) if i != ""]
                for case in case_lst:
                    case_save = ""
                    param_lst = case.split("\n")
                    for pa in param_lst:
                        if pa != "" and pa.count("=") == 1:
                            head, tail = pa.split("=")
                            value = tail.strip().strip(";")
                            var = head.strip().split()[-1]
                            tp = "".join(head.strip().split()[:-1])
                            case_save += f"{tp} {var} = {value};\n"
                    if return_type == "void":
                        script_case = "try {\n" + case_save + func_name + "(" + ",".join(var_lst) + ");\n}catch(Exception e){System.out.println(\"exception\");}\n"
                    elif has_array(return_type):
                        params = ",".join(var_lst)
                        single_return_type = return_type.replace("[", "").replace("]","").strip()
                        script_case = f"try {{\n{case_save}{return_type} output = {func_name}({params});\n" \
              f"for({single_return_type} single_value: output){{\nSystem.out.println(single_value);\n}}\n"\
              + "}catch(Exception e){System.out.println(\"exception\");}\n"
                    else:
                        script_case = "try {\n" + case_save + "System.out.println(" + func_name + "(" + ",".join(var_lst) + "));\n}catch(Exception e){System.out.println(\"exception\");}\n"
                    script = ""
                    with open("./cleaned_data/test_case_gen_scripts/gen_case.java", encoding="utf-8") as fr:
                        for line_script in fr.readlines():
                            if line_script.strip() == "//TO_FILL_FUNC":
                                script += code + "\n"
                            elif line_script.strip() == "//TO_FILL_EXEC":
                                script += line_script.replace("//TO_FILL_EXEC", script_case) + "\n"
                            else:
                                script += line_script
                    with open(f"./cleaned_data/test_case_gen_scripts/tmp_scripts/tmp.java", "w") as fw:
                        fw.write(script)
                    # print(script)
                    signal.signal(signal.SIGALRM, TimeoutHandler)
                    signal.alarm(timeout)
                    try:
                        result = run_cmd(f"java ./cleaned_data/test_case_gen_scripts/tmp_scripts/tmp.java")
                        signal.alarm(0)
                    except Exception as ret:
                        print("IGNORE THIS CASE - EXCEPTION:", ret)
                        signal.alarm(0)
                        if keep_all:
                            item_case_lst.append("FAILED")
                        continue

                    if result[0] == "" and result[1] != "":
                        print("compilation error")
                        # compilation error
                        if keep_all:
                            item_case_lst.append("FAILED")
                        continue
                    elif result[0] == "exception":
                        print("runtime error")
                        # runtime error
                        if keep_all:
                            item_case_lst.append("FAILED")
                        continue
                    # print(result)
                    case_save_var_lst = []
                    case_save_var_pa = re.compile(r"(\w+) = .+?;", flags=re.S)
                    for i in case_save.split("\n"):
                        if i != "":
                            found = case_save_var_pa.findall(i)
                            if len(found) != 0:
                                tmp_var = found[0]
                            else:
                                continue
                            if tmp_var != "" and tmp_var in var_lst:
                                case_save_var_lst.append(i)
                    if len(case_save_var_lst) != len(var_lst):
                        if keep_all:
                            item_case_lst.append("FAILED")
                        continue
                    case_save = "\n".join(case_save_var_lst)
                    result = result[0]
                    if return_type == "void":
                        item_case_lst.append(f"Inputs:\n{case_save}\nOutputs (void):\nVoid function does not have output.")
                    elif has_array(return_type):
                        if "char" in return_type:
                            result = ",".join([f"\'{i}\'" for i in result.strip().split()])
                        elif "String" in return_type:
                            result = ",".join([f"\"{i}\"" for i in result.strip().split()])
                        else:
                            result = ",".join(result.strip().split())
                        item_case_lst.append(f"Inputs:\n{case_save}\nOutputs ({return_type}):\n{{{result}}}")
                    else:
                        if return_type == 'char':
                            item_case_lst.append(f"Inputs:\n{case_save}\nOutputs ({return_type}):\n\'{result}\'")
                        elif return_type == 'String':
                            item_case_lst.append(f"Inputs:\n{case_save}\nOutputs ({return_type}):\n\"{result}\"")
                        elif return_type == 'long':
                            item_case_lst.append(f"Inputs:\n{case_save}\nOutputs ({return_type}):\n{result}L")
                        elif return_type == 'float':
                            item_case_lst.append(f"Inputs:\n{case_save}\nOutputs ({return_type}):\n{result}F")
                        else:
                            item_case_lst.append(f"Inputs:\n{case_save}\nOutputs ({return_type}):\n{result}")

            if keep_all:
                with jsonlines.open(f"./cleaned_data/{model}/test_cases/test_cases_java_keep_all.jsonl", "a") as fw:
                    fw.write({"id": id, "test_case": item_case_lst})
            else:
                with jsonlines.open(f"./cleaned_data/{model}/test_cases/test_cases_java.jsonl", "a") as fw:
                    fw.write({"id": id, "test_case": list(set(item_case_lst))})


def post_process_cp(model, keep_all, timeout=5, start=1):
    # script_lst = os.listdir("./cleaned_data/transcoder_evaluation_gfg/cpp")
    count = 0
    # todo del
    # err_id_lst = []
    # with open("./cout_ids.txt", encoding="utf-8") as fr:
    #     for line in fr.readlines():
    #         if line.strip() != "":
    #             err_id_lst.append(line.strip())
    with open(f"./cleaned_data/{model}/valid_inputs/valid_inputs_cpp.jsonl", encoding="utf-8") as fr:
        for line in tqdm(fr.readlines()):
            count += 1
            if count < start:
                continue
            line = json.loads(line)
            id = line['id']
            # todo del
            # if id != "MAXIMUM_POSSIBLE_DIFFERENCE_TWO_SUBSETS_ARRAY_1":
            #     continue
            item = line['cpp']
            func_name, code, return_type, var_lst = return_func_name(id, "cpp")
            item_case_lst = []
            for item_i in item:
                # todo deal with llm
                if model != "gpt3_5":
                    # item_i = item_i.replace(example_cpp, "").replace(valid_inputs_cpp, "")
                    item_i = item_i.split("END_OF_CASE\n")[1]
                    found = re.findall(r"Input_\d+:.+", item_i, flags=re.S)
                    if len(found) != 0:
                        item_i = found[0]
                    else:
                        item_i = ""
                        print("NO CASES! ", id)
                case_lst = [i.strip() for i in re.split(r"Input_\d+:", item_i) if i != ""]
                for case in case_lst:
                    case_save = ""
                    var_tmp = []
                    param_lst = case.split("\n")
                    # print("param_lst: ", param_lst)
                    for pa in param_lst:
                        if pa != "" and pa.count("=") == 1:
                            head, tail = pa.split("=")
                            value = tail.strip().strip(";")
                            var = head.strip().split()[-1]
                            tp = "".join(head.strip().split()[:-1])
                            case_save += f"{tp} {var} = {value};\n"
                            var_tmp.append(var)
                    if len(var_tmp) == 1:
                        var_lst = var_tmp
                    if return_type == "void":
                        script_case = "try {\n" + case_save + func_name + "(" + ",".join(var_lst) + ");\n}catch(...){cout << \"exception\";}\n"
                    elif has_array(return_type):
                        params = ",".join(var_lst)
                        NEW_LINE = "\'\\n\'"
                        script_case = f"try {{\n{case_save}{return_type} output = {func_name}({params});\n" \
                                      f"while(*output){{\ncout << *output << {NEW_LINE};\noutput++;}}\n" \
                                      + "}catch(...){cout <<\"exception\";}\n"
                    else:
                        script_case = "try {\n" + case_save + "cout <<" + func_name + "(" + ",".join(var_lst) + ");\n}catch(...){cout <<\"exception\";}\n"
                    # print(f"{case_save}{func_name}(" + ",".join(var_lst) + ");")
                    script = ""
                    with open("./cleaned_data/test_case_gen_scripts/gen_case.cpp", encoding="utf-8") as fr:
                        for line_script in fr.readlines():
                            if line_script.strip() == "//TO_FILL_FUNC":
                                script += code + "\n"
                            elif line_script.strip() == "//TO_FILL_EXEC":
                                script += line_script.replace("//TO_FILL_EXEC", script_case) + "\n"
                            else:
                                script += line_script
                    with open(f"./cleaned_data/test_case_gen_scripts/tmp_scripts/tmp.cpp", "w") as fw:
                        fw.write(script)
                    # print(script)
                    signal.signal(signal.SIGALRM, TimeoutHandler)
                    signal.alarm(timeout)
                    try:
                        result = run_cmd(f"g++ ./cleaned_data/test_case_gen_scripts/tmp_scripts/tmp.cpp -o "
                                         f"./cleaned_data/test_case_gen_scripts/tmp_scripts/tmp && ./cleaned_data/test_case_gen_scripts/tmp_scripts/tmp")
                        signal.alarm(0)
                    except Exception as ret:
                        print("IGNORE THIS CASE - EXCEPTION:", ret)
                        signal.alarm(0)
                        if keep_all:
                            item_case_lst.append("FAILED")
                        continue

                    if result[0] == "" and result[1] != "":
                        print("compilation error")
                        # compilation error
                        if keep_all:
                            item_case_lst.append("FAILED")
                        continue
                    elif result[0] == "exception":
                        print("runtime error")
                        # runtime error
                        if keep_all:
                            item_case_lst.append("FAILED")
                        continue
                    # print(result)
                    # assert False
                    result = result[0]
                    case_save_var_lst = []
                    case_save_var_pa = re.compile(r"(\w+)[\[\s\]]* = .+?;", flags=re.S)
                    for i in case_save.split("\n"):
                        if i != "":
                            found = case_save_var_pa.findall(i)
                            if len(found) != 0:
                                tmp_var = found[0]
                            else:
                                continue
                            if tmp_var != "" and tmp_var in var_lst:
                                case_save_var_lst.append(i)
                    if len(case_save_var_lst) != len(var_lst):
                        if keep_all:
                            item_case_lst.append("FAILED")
                        continue
                    case_save = "\n".join(case_save_var_lst)
                    if return_type == "void":
                        item_case_lst.append(
                            f"Inputs:\n{case_save}\nOutputs (void):\nVoid function does not have output.")
                    elif has_array(return_type):
                        if "char" in return_type:
                            result = ",".join([f"\'{i}\'" for i in result.strip().split()])
                        elif "string" in return_type:
                            result = ",".join([f"\"{i}\"" for i in result.strip().split()])
                        else:
                            result = ",".join(result.strip().split())
                        item_case_lst.append(f"Inputs:\n{case_save}\nOutputs ({return_type}):\n{{{result}}}")
                    else:
                        if return_type == 'char':
                            item_case_lst.append(f"Inputs:\n{case_save}\nOutputs ({return_type}):\n\'{result}\'")
                        elif return_type == 'string':
                            item_case_lst.append(f"Inputs:\n{case_save}\nOutputs ({return_type}):\n\"{result}\"")
                        else:
                            item_case_lst.append(f"Inputs:\n{case_save}\nOutputs ({return_type}):\n{result}")

            if keep_all:
                with jsonlines.open(f"./cleaned_data/{model}/test_cases/test_cases_cpp_keep_all.jsonl", "a") as fw:
                    fw.write({"id": id, "test_case": item_case_lst})
            else:
                with jsonlines.open(f"./cleaned_data/{model}/test_cases/test_cases_cpp.jsonl", "a") as fw:
                    fw.write({"id": id, "test_case": list(set(item_case_lst))})

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, help="model name", default="llama-7b-hf")
    parser.add_argument("--start", type=int, help="start point", default=1)
    parser.add_argument("--dst_lang", type=str, help="target language", default="python")
    parser.add_argument("--keep_all", type=bool, help="keep all correct/incorrect cases", default=False)
    args = parser.parse_args()
    if args.dst_lang == "python":
        post_process_py(model=args.model, start=args.start, keep_all=args.keep_all)
    elif args.dst_lang == "java":
        post_process_ja(model=args.model, start=args.start, keep_all=args.keep_all)
    elif args.dst_lang == "cpp":
        post_process_cp(model=args.model, start=args.start, keep_all=args.keep_all)
    else:
        print("unknown lang!")


