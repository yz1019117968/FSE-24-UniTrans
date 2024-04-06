import json
import re
import jsonlines
import os
import ast
from tqdm import tqdm
import argparse


def extract_data(mode):
    with open(f"./evaluation_transcoder/transcoder_{mode}.cpp.detok", encoding="utf-8") as fr:
        text = fr.read().strip()
        cpp_lst = text.split("\n\n")

    with open(f"./evaluation_transcoder/transcoder_{mode}.java.detok", encoding="utf-8") as fr:
        text = fr.read().strip()
        java_lst = text.split("\n\n")

    with open(f"./evaluation_transcoder/transcoder_{mode}.python.detok", encoding="utf-8") as fr:
        text = fr.read().strip()
        python_lst = text.split("\n\n")

    def get_id_code(item):
        id_end, code_beg = re.search(r"\|", item).span()
        id = item[:id_end].strip()
        code = item[code_beg:].strip()
        return id, code

    all = []
    for cpp, java, py in zip(cpp_lst, java_lst, python_lst):
        cpp_id, cpp_code = get_id_code(cpp)
        java_id, java_code = get_id_code(java)
        py_id, py_code = get_id_code(py)

        assert cpp_id == java_id == py_id

        all.append({"id":cpp_id, "cpp": cpp_code, "java": java_code, "python": py_code})

    with jsonlines.open(f"./evaluation_transcoder/{mode}.jsonl", "w") as fw:
        fw.write_all(all)

def remove_comm(program):
    pattern = re.compile(r"\'\'\'.+?\'\'\'|\"\"\".+?\"\"\"", flags=re.DOTALL)
    program = re.sub(pattern, "\n", program)
    return re.sub("# .+?\n", "\n", program)

def post_process_python(model, file, suffix):
    all = []
    with open(f"./cleaned_data/{model}/{file}", encoding="utf-8") as fr:
        for item in fr.readlines():
            item = json.loads(item)
            # if item['id'] != "POSITIVE_ELEMENTS_EVEN_NEGATIVE_ODD_POSITIONS":
            #     continue
            sample_lst = item["python"]
            new_sample_lst = []
            for sample in sample_lst:
                # print(sample)
                # sample = remove_comm(sample)
                new_sample = ""
                # if "END_OF_CASE" not in sample:
                line_lst = [i for i in sample.strip().split("\n") if i.strip() != ""]
                # else:
                #     line_lst = []
                #     sample_lst = sample.strip()
                #     for i in sample_lst:
                #         if "END_OF_CASE" in i:
                #             i = i.split("END_OF_CASE")[0]
                #             line_lst.append(i)
                #             break
                #         elif i != "":
                #             line_lst.append(i)
                start = False
                for line in line_lst:
                    if not start:
                        if not line.strip().startswith("def") and not re.search(r"from .+? import .+?", line) and not line.strip().startswith("import"):
                            continue
                        elif line.strip().startswith("def"):
                            start = True
                            new_sample += line + "\n"
                        else:
                            new_sample += line + "\n"
                    elif not line.startswith(" "):
                        break
                    else:
                        new_sample += line + "\n"
                # if new_sample != "":
                # print("AFTER:\n", new_sample)
                # assert False
                new_sample_lst.append(new_sample)
            all.append({"id":item["id"], "python": new_sample_lst})
    with jsonlines.open(f"./cleaned_data/{model}/post_processed{suffix}/{file}", "w") as fw:
        fw.write_all(all)

def post_process_java(model, file, suffix):
    all = []
    with open(f"./cleaned_data/{model}/{file}", encoding="utf-8") as fr:
        for item in fr.readlines():
            item = json.loads(item)
            sample_lst = item["java"]
            new_sample_lst = []
            for sample in sample_lst:
                new_sample = ""
                # if "END_OF_CASE" not in sample:
                line_lst = [i for i in sample.strip().split("\n") if i.strip() != ""]
                # else:
                #     line_lst = []
                #     sample_lst = sample.split()
                #     for i in sample_lst:
                #         if "END_OF_CASE" in i:
                #             i = i.split("END_OF_CASE")[0]
                #             line_lst.append(i)
                #             break
                #         elif i != "":
                #             line_lst.append(i)
                start = False
                for line in line_lst:
                    if not start:
                        if not re.match("public|private|protected|import|static", line.strip()):
                            continue
                        elif re.match("public|private|protected|static", line.strip()):
                            start = True
                            new_sample += line + "\n"
                        else:
                            new_sample += line + "\n"
                    elif not line.startswith(" ") and line.strip() != "}":
                        break
                    else:
                        new_sample += line + "\n"
                # if new_sample != "":
                new_sample_lst.append(new_sample)
            all.append({"id": item["id"], "java": new_sample_lst})
    with jsonlines.open(f"./cleaned_data/{model}/post_processed{suffix}/{file}", "w") as fw:
        fw.write_all(all)

def post_process_cpp(model, file, suffix):
    all = []
    with open(f"./cleaned_data/{model}/{file}", encoding="utf-8") as fr:
        for item in fr.readlines():
            item = json.loads(item)
            id = item['id']
            # if id != "C_PROGRAM_FACTORIAL_NUMBER":
            #     continue
            sample_lst = item["cpp"]
            new_sample_lst = []
            for sample in sample_lst:
                new_sample = ""
                # if "END_OF_CASE" not in sample:
                line_lst = [i for i in sample.strip().split("\n") if i.strip() != ""]
                # else:
                #     line_lst = []
                #     sample_lst = sample.split()
                #     for i in sample_lst:
                #         if "END_OF_CASE" in i:
                #             i = i.split("END_OF_CASE")[0]
                #             line_lst.append(i)
                #             break
                #         elif i != "":
                #             line_lst.append(i)
                start = False
                for line in line_lst:
                    if not start:
                        if not re.match("#include", line.strip()) and not re.findall(r"\w+\s\w+\s?\(.+?\)", line.strip()):
                            continue
                        elif re.findall(r"\w+\s\w+\s?\(.+?\)", line.strip()):
                            start = True
                            new_sample += line + "\n"
                        else:
                            new_sample += line + "\n"
                    elif not line.startswith(" ") and line.strip() != "}":
                        break
                    else:
                        new_sample += line + "\n"
                # if new_sample != "":
                new_sample_lst.append(new_sample)
            all.append({"id": item["id"], "cpp": new_sample_lst})
    with jsonlines.open(f"./cleaned_data/{model}/post_processed{suffix}/{file}", "w") as fw:
        fw.write_all(all)

def locate_function_name_py(code):
    # Parse the code into an AST
    try:
        tree = ast.parse(code)
        # Traverse the AST and collect function names
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                return node.name
    except Exception as e:
        return None
def locate_function_name_java(code):
    pattern = re.compile(r"(public|private|protected)?\s?(static)?\s?(\w+|\w+\[\])\s(\w+)\s?\(\s?(\w+.*\w*)?\s?\)")
    method_info = pattern.findall(code)
    try:
        return method_info[0][3]
    except Exception as e:
        return None
def locate_function_name_cpp(code):
    pattern = re.compile(r"(\w+)\s(\w+)\s?\(\s?(\w+.*\w*)?\s?\)")
    method_info = pattern.findall(code)
    try:
        return method_info[0][1]
    except Exception as e:
        return None

def formulate_scripts(model, src_lang, dst_lang, file, suffix):
    # formulate a series of test scripts for evaluation preparation.
    count = 0
    script_lst = [i.split(".")[0] for i in os.listdir(f"./cleaned_data/transcoder_evaluation_gfg/{dst_lang}")]
    with open(f"./cleaned_data/{model}/post_processed{suffix}/{file}", encoding="utf-8") as fr:
        for line in tqdm(fr.readlines()):
            line = json.loads(line)
            sample_lst = line[dst_lang]
            sample_id = line['id']
            if sample_id in script_lst:
                # if sample_id != "POSITIVE_ELEMENTS_EVEN_NEGATIVE_ODD_POSITIONS":
                #     continue
                count += 1
                path = f"./cleaned_data/{model}/test_scripts{suffix}/{src_lang}_{dst_lang}/{sample_id}"
                if not os.path.exists(path):
                    os.makedirs(path)
                i = 0
                for sample in sample_lst:
                    script = ""
                    if dst_lang == "python":
                        func_name = locate_function_name_py(sample)
                        if not func_name:
                            func_name = "CANNOT_COMPILE"
                        with open(f"./cleaned_data/transcoder_evaluation_gfg/{dst_lang}/{sample_id}.py", encoding="utf-8") as fr:
                            for line in fr.readlines():
                                if line.strip() == "#TOFILL":
                                    script += sample
                                else:
                                    script += line
                        script = script.replace("f_filled", func_name)
                        # print(script)
                        # assert False
                        with open(f"{path}/sample_{i}.py", "w", encoding="utf-8") as fw:
                            fw.write(script)
                        i += 1
                    elif dst_lang == "java":
                        func_name = locate_function_name_java(sample)
                        if not func_name:
                            func_name = "CANNOT_COMPILE"
                        with open(f"./cleaned_data/transcoder_evaluation_gfg/{dst_lang}/{sample_id}.java", encoding="utf-8") as fr:
                            for line in fr.readlines():
                                if line.strip() == "//TOFILL":
                                    script += sample
                                else:
                                    script += line
                        script = script.replace("f_filled", func_name)
                        with open(f"{path}/sample_{i}.java", "w", encoding="utf-8") as fw:
                            fw.write(script)
                        i += 1
                    elif dst_lang == "cpp":
                        func_name = locate_function_name_cpp(sample)
                        if not func_name:
                            func_name = "CANNOT_COMPILE"
                        with open(f"./cleaned_data/transcoder_evaluation_gfg/{dst_lang}/{sample_id}.cpp", encoding="utf-8") as fr:
                            for line in fr.readlines():
                                if line.strip() == "//TOFILL":
                                    script += sample
                                else:
                                    script += line
                        script = script.replace("f_filled", func_name)
                        with open(f"{path}/sample_{i}.cpp", "w", encoding="utf-8") as fw:
                            fw.write(script)
                        i += 1
                    else:
                        assert False, "unknown lang!"
    print(f"testable num: {count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, help="model name", default="llama-7b-hf")
    parser.add_argument("--src_lang", type=str, help="source language", default="java")
    parser.add_argument("--dst_lang", type=str, help="target language", default="python")
    parser.add_argument("--suffix", type=int, help="append test case and repair round info", default="")
    args = parser.parse_args()

    model = args.model
    src_lang = args.src_lang
    dst_lang = args.dst_lang
    suffix = args.suffix
    raw_file = f"testable_{src_lang}_{dst_lang}{suffix}.jsonl"
    if dst_lang == "python":
        post_process_python(model, raw_file, suffix)
        formulate_scripts(model, src_lang=src_lang, dst_lang=dst_lang, file=raw_file, suffix=suffix)
    elif dst_lang == "java":
        post_process_java(model, raw_file, suffix)
        formulate_scripts(model, src_lang=src_lang, dst_lang=dst_lang, file=raw_file, suffix=suffix)
    elif dst_lang == "cpp":
        post_process_cpp(model, raw_file, suffix)
        formulate_scripts(model, src_lang=src_lang, dst_lang=dst_lang, file=raw_file, suffix=suffix)
    elif dst_lang == "c#":
        pass
    else:
        assert False, "unknown lang!"


