import json
import re
import jsonlines
from process_valid_inputs import locate_function_name_java
import argparse

def process_py_feed_backs(feedback_file, output_file, sample_file):
    sample_dict = {}
    with open(sample_file, encoding="utf-8") as fr:
        for line in fr.readlines():
            line = json.loads(line)
            if len(line['python']) < 1:
                sample_dict.update({line['id']: "NONE"})
            else:
                sample_dict.update({line['id']:line['python'][0]})
    pattern_line_no = re.compile(r", line (\d+)")
    new_feedback_lst = []
    with open(feedback_file, encoding="utf-8") as fr:
        for line in fr.readlines():
            line = json.loads(line)
            id = line['id']
            print(id)
            # if id != "CALCULATE_ANGLE_HOUR_HAND_MINUTE_HAND":
            #     continue
            code = sample_dict[id]
            pattern_comm = re.compile(r"#<Buggy Line>")
            code = pattern_comm.sub("", code)
            item_lst = line['feedbacks']
            new_item_lst = []
            for idx, item in enumerate(item_lst):
                code_lines = code.split("\n")
                if item[1] == "OK":
                    new_item_lst.append({"idx":idx,"case":item[0],"err_type":"PASS","err_msg":None,"err_line":None,"err_line_no":None, "marked_code":None})
                elif item[1] == "":
                    new_item_lst.append({"idx": idx, "case": item[0], "err_type": "REDO", "err_msg": None, "err_line": None,"err_line_no": None, "marked_code":None})
                else:
                    if "Logic Error" in item[1]:
                        print("Logic Error")
                        err_msg = item[1].split("\n")[1]
                        print("err_msg", err_msg)
                        new_item_lst.append({"idx": idx, "case": item[0], "err_type": "Logic Error", "err_msg": err_msg, "err_line": None,"err_line_no": None, "marked_code":None})
                    elif "Compilation Error" in item[1]:
                        print("compilation error")
                        err_lst = [line for line in item[1].split("\n") if re.sub(r"\s*~*\^+~*", "", line) != ""]
                        err_line = err_lst[-2].strip()
                        err_msg = err_lst[-1].strip()
                        err_line_no = int(pattern_line_no.findall(err_lst[-3])[0]) - 13
                        if err_line_no >= len(code_lines):
                            new_item_lst.append({"idx": idx, "case": item[0], "err_type": "Compilation Error", "err_msg": err_msg,"err_line": err_line, "err_line_no": None,"marked_code": None})
                        else:
                            code_lines[err_line_no] += " #<Buggy Line>"
                            new_item_lst.append({"idx": idx, "case": item[0], "err_type": "Compilation Error", "err_msg": err_msg,"err_line": err_line, "err_line_no": err_line_no,"marked_code": "\n".join(code_lines)})
                        print("ERR LINE:", err_line)
                        print("err_msg", err_msg)
                        print("marked_code", "\n".join(code_lines))
                        # new_item_lst.append({"idx": idx, "case": item[0], "err_type": "Compilation Error", "err_msg": err_msg,"err_line": err_line, "err_line_no": err_line_no, "marked_code":"\n".join(code_lines)})
                    elif "Runtime Error" in item[1]:
                        print("runtime error")
                        err_lst = [line for line in item[1].split("\n") if re.sub(r"\s*~*\^+~*", "", line) != ""]
                        err_line = err_lst[-2].strip()
                        err_msg = err_lst[-1].strip()
                        err_line_no = int(pattern_line_no.findall(err_lst[-3])[0]) - 13
                        if err_line_no >= len(code_lines):
                            new_item_lst.append({"idx": idx, "case": item[0], "err_type": "Runtime Error", "err_msg": err_msg,"err_line": err_line, "err_line_no": None,"marked_code": None})
                        else:
                            code_lines[err_line_no] += " #<Buggy Line>"
                            new_item_lst.append({"idx": idx, "case": item[0], "err_type": "Runtime Error", "err_msg": err_msg,"err_line": err_line, "err_line_no": err_line_no,"marked_code": "\n".join(code_lines)})
                        print("ERR LINE:", err_line)
                        print("err_msg", err_msg)
                        print("marked_code", "\n".join(code_lines))

            new_feedback_lst.append({"id":id, "feedbacks":new_item_lst})
    with jsonlines.open(output_file, "w") as fw:
        fw.write_all(new_feedback_lst)

def process_ja_feed_backs(feedback_file, output_file, sample_file):
    # 取出被评估的样本
    sample_dict = {}
    with open(sample_file, encoding="utf-8") as fr:
        for line in fr.readlines():
            line = json.loads(line)
            sample_dict.update({line['id']: line['java'][0]})
    new_feedback_lst = []
    with open(feedback_file, encoding="utf-8") as fr:
        for line in fr.readlines():
            line = json.loads(line)
            id = line['id']
            print(id)
            code = sample_dict[id]
            pattern_comm = re.compile(r"//<Buggy Line>")
            code = pattern_comm.sub("", code)
            func_name, _, _ = locate_function_name_java(code)
            item_lst = line['feedbacks']
            new_item_lst = []
            for idx, item in enumerate(item_lst):
                code_lines = code.split("\n")
                if item[1] == "OK":
                    new_item_lst.append({"idx":idx,"case":item[0],"err_type":"PASS","err_msg":None,"err_line":None,"err_line_no":None, "marked_code":None})
                elif item[1] == "":
                    new_item_lst.append({"idx": idx, "case": item[0], "err_type": "REDO", "err_msg": None, "err_line": None,"err_line_no": None, "marked_code":None})
                else:
                    if "Compilation Error" in item[1]:
                        print("COMPILE:")
                        pattern = re.compile(r"tmp\.java:(\d+): error: (.+)")
                        flag = False
                        for line in item[1].split("\n"):
                            if pattern.findall(line) != []:
                                err_msg = pattern.findall(line)[0][1]
                                err_line_no = int(pattern.findall(line)[0][0]) - 7
                                flag = True
                                continue
                            if flag is True:
                                err_line = line.strip()
                                break
                        if err_line_no >= len(code_lines):
                            new_item_lst.append({"idx": idx, "case": item[0], "err_type": "Compilation Error", "err_msg": err_msg,"err_line": err_line, "err_line_no": None, "marked_code": None})
                        else:
                            code_lines[err_line_no] += " //<Buggy Line>"
                            new_item_lst.append({"idx": idx, "case": item[0], "err_type": "Compilation Error", "err_msg": err_msg,"err_line": err_line, "err_line_no": err_line_no,"marked_code": "\n".join(code_lines)})
                        print("ERR LINE:", err_line)
                        print("marked_code", "\n".join(code_lines))
                        print("err_msg: ", err_msg)
                    elif "Runtime Error" in item[1]:
                        print("RUNTIME: ")
                        ret_lst = item[1].split("\n")
                        err_msg = ret_lst[1].strip()
                        pattern = re.compile(r"\."+func_name+r"\(tmp\.java:(\d+)\)")
                        find_ret = pattern.findall(item[1])
                        err_line_no = int(find_ret[0]) - 7
                        if err_line_no >= len(code_lines):
                            new_item_lst.append({"idx": idx, "case": item[0], "err_type": "Compilation Error", "err_msg": err_msg,"err_line": None, "err_line_no": None, "marked_code": None})
                            print("err_msg: ", err_msg)
                        else:
                            code_lines[err_line_no] += " //<Buggy Line>"
                            new_item_lst.append({"idx": idx, "case": item[0], "err_type": "Compilation Error", "err_msg": err_msg,"err_line": code_lines[err_line_no].strip(), "err_line_no": err_line_no,"marked_code": "\n".join(code_lines)})
                            print("ERR LINE:", code_lines[err_line_no])
                            print("marked_code", "\n".join(code_lines))
                            print("err_msg: ", err_msg)
                    elif "Logic Error" in item[1]:
                        err_msg = item[1].split("\n")[1]
                        new_item_lst.append({"idx": idx, "case": item[0], "err_type": "Logic Error", "err_msg": err_msg,
                                             "err_line": None, "err_line_no": None, "marked_code": None})
                        print("LOGIC: ", err_msg)
            new_feedback_lst.append({"id": id, "feedbacks": new_item_lst})
    with jsonlines.open(output_file, "w") as fw:
        fw.write_all(new_feedback_lst)

def process_cp_feed_backs(feedback_file, output_file, sample_file):
    # 取出被评估的样本
    sample_dict = {}
    with open(sample_file, encoding="utf-8") as fr:
        for line in fr.readlines():
            line = json.loads(line)
            sample_dict.update({line['id']: line['cpp'][0]})
    new_feedback_lst = []
    with open(feedback_file, encoding="utf-8") as fr:
        for line in fr.readlines():
            line = json.loads(line)
            id = line['id']
            print(id)
            code = sample_dict[id]
            pattern_comm = re.compile(r"//<Buggy Line>")
            code = pattern_comm.sub("", code)
            item_lst = line['feedbacks']
            new_item_lst = []
            for idx, item in enumerate(item_lst):
                code_lines = code.split("\n")
                if item[1] == "OK":
                    new_item_lst.append({"idx": idx, "case": item[0], "err_type": "PASS", "err_msg": None, "err_line": None,"err_line_no": None, "marked_code": None})
                elif item[1] == "":
                    new_item_lst.append({"idx": idx, "case": item[0], "err_type": "REDO", "err_msg": None, "err_line": None,"err_line_no": None, "marked_code": None})
                else:
                    if "Compilation Error" in item[1]:
                        print("COMPILE:")
                        # print(item[1])
                        fd_lst = item[1].split("\n")
                        flag = False
                        for fd_i in fd_lst:
                            if "error" in fd_i:
                                err_msg = "error:" + fd_i.split("error:")[1]
                                flag = True
                            elif flag:
                                pattern = re.compile(r"(\d+)\s\|\s(.*)")
                                err_line = pattern.findall(fd_i)[0][1]
                                err_line_no = int(pattern.findall(fd_i)[0][0]) - 19
                                break
                        if err_line_no >= len(code_lines):
                            new_item_lst.append({"idx": idx, "case": item[0], "err_type": "Compilation Error", "err_msg": err_msg,"err_line": err_line, "err_line_no": None,"marked_code": None})
                        else:
                            code_lines[err_line_no] += " //<Buggy Line>"
                            new_item_lst.append({"idx": idx, "case": item[0], "err_type": "Compilation Error", "err_msg": err_msg,"err_line": err_line, "err_line_no": err_line_no,"marked_code": "\n".join(code_lines)})
                        print("ERR LINE:", err_line)
                        print("marked_code", "\n".join(code_lines))
                        print("err_msg: ", err_msg)
                    elif "Runtime Error" in item[1]:
                        # print("RUNTIME: ", item[1])
                        pattern = re.compile(r">\s+(\d+):\s?(.+)\n")
                        err_lines = []
                        for i in pattern.findall(item[1]):
                            if i[1].strip() in code:
                                err_lines.append(i)
                        if len(err_lines) > 0:
                            err_line = err_lines[-1][1].strip()
                            err_line_no = int(err_lines[-1][0]) - 19
                        else:
                            err_line = None
                            err_line_no = None
                        msg_head = item[1].split("Stack trace (most recent call last):")[0].replace("Runtime Error:", "").strip()
                        flag = False
                        err_msg = []
                        if "stack smashing detected" in msg_head or "double free or corruption (out)" in msg_head:
                            err_msg = ",".join(msg_head.split("\n"))
                        elif "throwing an instance of" in msg_head:
                            for line in msg_head.split("\n"):
                                if "throwing an instance of" in line:
                                    err_msg.append(line)
                                    flag = True
                                elif flag:
                                    err_msg.append(line)
                            err_msg = ",".join(err_msg)
                        else:
                            err_msg = item[1].split("\n")[-1]
                        if err_line_no is None or err_line_no >= len(code_lines):
                            new_item_lst.append({"idx": idx, "case": item[0], "err_type": "Compilation Error", "err_msg": err_msg,"err_line": err_line, "err_line_no": None,"marked_code": None})
                        else:
                            code_lines[err_line_no] += " //<Buggy Line>"
                            new_item_lst.append({"idx": idx, "case": item[0], "err_type": "Compilation Error", "err_msg": err_msg,"err_line": err_line, "err_line_no": err_line_no,"marked_code": "\n".join(code_lines)})
                        print("ERR LINE:", err_line, err_line_no)
                        print("marked_code", "\n".join(code_lines))
                        print("err_msg: ", err_msg)
                    elif "Logic Error" in item[1]:
                        pattern = re.compile(r"Expected Output:.*?,Actual Output:.*?,Expected output and actual output are not equal!")
                        err_msg = pattern.findall(item[1])[0]
                        new_item_lst.append({"idx": idx, "case": item[0], "err_type": "Logic Error", "err_msg": err_msg,
                                             "err_line": None, "err_line_no": None, "marked_code": None})
                        print("LOGIC: ", err_msg)
            new_feedback_lst.append({"id": id, "feedbacks": new_item_lst})
    with jsonlines.open(output_file, "w") as fw:
        fw.write_all(new_feedback_lst)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--src_lang", type=str, help="source language", default="java")
    parser.add_argument("--dst_lang", type=str, help="target language", default="python")
    parser.add_argument("--round", type=int, help="number of round", default=1)
    parser.add_argument("--test_case_num", type=int, help="num of test cases", default=3)
    args = parser.parse_args()

    src_lang = args.src_lang
    dst_lang = args.dst_lang
    model = args.model
    round = args.round
    test_case_num = args.test_case_num
    feedback_file = f"./cleaned_data/{model}/feedbacks/raw/testable_{src_lang}_{dst_lang}_w_{test_case_num}cases_{round}round_raw.jsonl"
    output_file = f"./cleaned_data/{model}/feedbacks/testable_{src_lang}_{dst_lang}_w_{test_case_num}cases_{round}round.jsonl"
    # todo
    sample_file = f"./cleaned_data/{model}/post_processed_w_{test_case_num}cases/testable_{src_lang}_{dst_lang}_w_{test_case_num}cases.jsonl"
    if dst_lang == "python":
        process_py_feed_backs(feedback_file, output_file, sample_file)
    elif dst_lang == "java":
        process_ja_feed_backs(feedback_file, output_file, sample_file)
    elif dst_lang == "cpp":
        process_cp_feed_backs(feedback_file, output_file, sample_file)
