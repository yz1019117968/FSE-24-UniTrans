import json
import re
import argparse






def remove_comm_py(program):
    pattern = re.compile(r"\'\'\'.+?\'\'\'|\"\"\".+?\"\"\"", flags=re.DOTALL)
    program = re.sub(pattern, "\n", program)
    return re.sub("#\s*.+?\n", "\n", program)

def remove_comm_ja(program):
    pattern = re.compile(r"/\*.+?\*/", flags=re.DOTALL)
    program = re.sub(pattern, "\n", program)
    return re.sub("//\s*.+?\n", "\n", program)

def process_py(code):
    code = remove_comm_py(code)
    cd_lst = code.split("\n")
    new_cd_lst = []
    start = False
    for line in cd_lst:
        if start is False:
            if re.search(r"from .+? import .+?", line) or line.strip().startswith("import"):
                continue
            elif line.strip().startswith("def"):
                start = True
                new_cd_lst.append(line)
        else:
            new_cd_lst.append(line)
    return "\n".join(new_cd_lst)

def process_ja(code):
    code = remove_comm_ja(code)
    cd_lst = code.split("\n")
    new_cd_lst = []
    start = False
    for line in cd_lst:
        if start is False:
            if line.strip().startswith("import"):
                continue
            elif re.match("public|private|protected|static", line.strip()):
                start = True
                if line.startswith("public"):
                    new_cd_lst.append(line[6:].strip())
                else:
                    new_cd_lst.append(line)
        else:
            new_cd_lst.append(line)
    return "\n".join(new_cd_lst)

def process_cpp(code):
    code = remove_comm_ja(code)
    cd_lst = code.split("\n")
    new_cd_lst = []
    start = False
    for line in cd_lst:
        if start is False:
            if line.strip().startswith("#include"):
                continue
            elif re.findall(r"\w+\s\w+\s?\(.+?\)", line.strip()):
                start = True
                new_cd_lst.append(line)
        else:
            new_cd_lst.append(line)
    return "\n".join(new_cd_lst)

def evaluation_em():
    gold_lst = {}
    with open(gold_file_path, encoding="utf-8") as fr:
        for line in fr.readlines():
            line = json.loads(line)
            gold_lst.update({line["id"]: line[dst_lang]})
    correct = 0
    total = 0
    with open(file_path, encoding="utf-8") as fr:
        for line in fr.readlines():
            line = json.loads(line)
            id = line['id']
            gold = gold_lst[id]
            if len(line[dst_lang]) > 0:
                ret = line[dst_lang][0].strip()
                if dst_lang == "python":
                    ret1 = process_py(ret)
                elif dst_lang == "java":
                    ret1 = process_ja(ret)
                    if gold.startswith("public"):
                        gold = gold[6:].strip()
                elif dst_lang == "cpp":
                    ret1 = process_cpp(ret)
                if re.sub("\s", "", ret1) == re.sub("\s", "", gold):
                    correct += 1
            total += 1
    print("EM: ", correct / total)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, help="select an llm", default="gpt3_5")
    parser.add_argument("--src_lang", type=str, help="source language", default="python")
    parser.add_argument("--dst_lang", type=str, help="target language", default="java")
    parser.add_argument("--suffix", type=str, help="suffix of experiments", default="_zero_shot")
    args = parser.parse_args()
    model = args.model
    src_lang = args.src_lang
    dst_lang = args.dst_lang
    suffix = args.suffix
    file_path = f"./cleaned_data/{model}/post_processed{suffix}/testable_{src_lang}_{dst_lang}{suffix}.jsonl"
    gold_file_path = f"./cleaned_data/testable_samples.jsonl"


