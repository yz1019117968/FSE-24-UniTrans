import re

import openai
import json
import jsonlines
from tqdm import tqdm
from cleaned_data.templates.examples_inp import example_cpp, valid_inputs_cpp, \
    example_java, valid_inputs_java, example_python, valid_inputs_python
from cleaned_data.templates.examples_trans import \
    example_code_java, example_code_cpp, example_code_python, \
    example_test_cases_java, example_test_cases_cpp, example_test_cases_python
from cleaned_data.templates.example_refine import python_refine_example2_1, python_refine_example2_2, \
    cpp_refine_example2_1, cpp_refine_example2_2, java_refine_example2_1, java_refine_example2_2
from tenacity import (
    retry,
    retry_if_exception_type,
    wait_random_exponential,
)  # for exponential backoff
import argparse

# 最少等待1秒，最多10秒
@retry(wait=wait_random_exponential(min=1, max=60), retry=retry_if_exception_type((openai.error.RateLimitError, openai.error.APIError)))
def collect_one(prompt, api_key, sample_num=20):
    openai.api_key = api_key
    ret = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=prompt,
        max_tokens=500,
        temperature=0.8,
        n=sample_num,
        top_p=0.95
    )

    samples = ret['choices']
    candidates = []
    for id, i in enumerate(samples):
        candi_lst = i['message']['content'].strip().split("\n")
        candi = ""
        for snippet in candi_lst:
            if snippet.endswith("END_OF_CASE"):
                break
            else:
                candi += snippet + "\n"
        candi = candi.strip()
        if candi != "":
            candidates.append(candi)
    return candidates
def prompt_trans(src_lang, dst_lang, item):
    return {"role": "user", "content": f"Given the {src_lang} code:\n{item}\nPlease translate the above {src_lang} code to {dst_lang} code, and use END_OF_CASE to finish your answer."}

def prompt_trans_one_shot(src_lang, dst_lang, item):
    example_dst_code = eval(f"example_code_{dst_lang}")
    example_src_code = eval(f"example_code_{src_lang}")
    content = f"Given {src_lang} code:\n{example_src_code}\nTranslate given {src_lang} code to {dst_lang} code, " \
              f"and use END_OF_CASE to finish your answer.\n{example_dst_code}\nEND_OF_CASE\n"
    target = f"Given {src_lang} code:\n{item}\nTranslate given {src_lang} code to {dst_lang} code, " \
              f"and use END_OF_CASE to finish your answer.\n"
    content = content + target
    return {"role": "user", "content": content}
def prompt_trans_w_case(src_lang, dst_lang, item, test_cases, test_case_num):
    example_dst_code = eval(f"example_code_{dst_lang}")
    example_src_code = eval(f"example_code_{src_lang}")
    example_test_cases = "\n".join(eval(f"example_test_cases_{dst_lang}")[: test_case_num])

    content = f"Given {src_lang} code:\n{example_src_code}\nGiven test cases:\n{example_test_cases}\n" \
              f"Translate given {src_lang} code to {dst_lang} code, and ensure the translated {dst_lang} code can pass all given test cases." \
              f"Use END_OF_CASE to finish your answer.\n{example_dst_code}\nEND_OF_CASE\n"
    target = f"Given {src_lang} code:\n{item}\nGiven test cases:\n{test_cases}\n" \
             f"Translate given {src_lang} code to {dst_lang} code, and ensure the translated {dst_lang} code can pass all given test cases." \
             f"Use END_OF_CASE to finish your answer.\n"
    content = content + target
    # print("TRANS W CASES:", content)
    return {"role": "user", "content": content}

def prompt_case(dst_lang, item):
    if dst_lang == "cpp":
        return {"role": "user", "content": f"{example_cpp}\n{valid_inputs_cpp}\n{item}\nplease generate ten groups of differentiated valid inputs for the above focal method of {dst_lang} language, in the format of [Input_1]\n[Input_2]\n...[Input_10]. Finally, use END_OF_CASE to finish your answer."}
    elif dst_lang == "java":
        return {"role": "user", "content": f"{example_java}\n{valid_inputs_java}\n{item}\nplease generate ten groups of differentiated valid inputs for the above focal method of {dst_lang} language, in the format of [Input_1]\n[Input_2]\n...[Input_10]. Finally, use END_OF_CASE to finish your answer."}
    elif dst_lang == "python":
        return {"role": "user", "content": f"{example_python}\n{valid_inputs_python}\n{item}\nplease generate ten groups of differentiated valid inputs for the above focal method of {dst_lang} language, in the format of [Input_1]\n[Input_2]\n...[Input_10]. Finally, use END_OF_CASE to finish your answer."}
    else:
        assert False, "unknown lang!"

def prompt_refine(dst_lang, org_sol, feedback):
    if dst_lang == "python":
        dst_lang_comm = "#"
    elif dst_lang == "java" or dst_lang == "cpp":
        dst_lang_comm = "//"
    else:
        assert False, "unknown lang!"

    if feedback['marked_code']:
        code = feedback['marked_code'].strip()
        content = f"Given buggy {dst_lang} code:\n{code}\n" \
                  f"Given test case:\n{feedback['case']}\n" \
                  f"Error message:{feedback['err_msg']}\n" \
                  f"Fix the buggy line (marked {dst_lang_comm}<Buggy Line>) in the buggy {dst_lang} code according to the given error message. " \
                  f"Use END_OF_CASE to finish your answer:\n"
        prompt = eval(f"{dst_lang}_refine_example2_1") + "\n" + content
    else:
        code = org_sol.strip()
        content = f"Given buggy {dst_lang} code:\n{code}\n" \
                  f"Given test case:\n{feedback['case']}\n" \
                  f"Error message:{feedback['err_msg']}\n" \
                  f"Fix the buggy {dst_lang} code according to the error message. Use END_OF_CASE to finish your answer:\n"
        prompt = eval(f"{dst_lang}_refine_example2_2") + "\n\n" + content
    # print("REFINE: ", prompt)
    return {"role": "user", "content": prompt}

def main(data_path, src_lang, dst_lang, obj, sample_num, api_key, out_path, test_case_num, feedback_file, org_sol_file, start):
    data = []
    sample_ids = []
    with open(data_path, encoding="utf-8") as fr:
        for line in fr.readlines():
            line = json.loads(line)
            data.append(line[src_lang])
            sample_ids.append(line['id'])

    if obj == TRANS_W_CASES:
        test_case_lst = {}
        with open(f"./cleaned_data/gpt3_5/test_cases/test_cases_{dst_lang}.jsonl", encoding="utf-8") as fr:
            for line in fr.readlines():
                line = json.loads(line)
                test_case_lst.update({line['id']: list(line['test_case'])[:test_case_num]})
    if obj == REFINE:
        test_case_lst = {}
        with open(f"./cleaned_data/gpt3_5/test_cases/test_cases_{dst_lang}.jsonl", encoding="utf-8") as fr:
            for line in fr.readlines():
                line = json.loads(line)
                test_case_lst.update({line['id']: list(line['test_case'])[:test_case_num]})
        feedbacks = {}
        with open(feedback_file, encoding="utf-8") as fr:
            for line in fr.readlines():
                line = json.loads(line)
                feedbacks.update({line['id']: line['feedbacks']})
        org_sols = {}
        with open(org_sol_file, encoding="utf-8") as fr:
            for line in fr.readlines():
                line = json.loads(line)
                org_sols.update({line['id']: line[dst_lang]})


    prefix = [{"role": "system", "content": "You are a professional developer proficient in java, python, and cpp.\n"}]
    count = 0
    for id, item in tqdm(zip(sample_ids, data), total=len(sample_ids)):
        count += 1
        if count < start:
            continue
        if obj == TRANS:
            target = [prompt_trans(src_lang, dst_lang, item)]
        elif obj == GEN_VAL_INP:
            target = [prompt_case(dst_lang, item)]
        elif obj == TRANS_ONE_SHOT:
            target = [prompt_trans_one_shot(src_lang, dst_lang, item)]
        elif obj == TRANS_W_CASES:
            test_cases = "\n".join(test_case_lst[id])
            if test_cases.strip() == "":
                target = [prompt_trans_one_shot(src_lang, dst_lang, item)]
            else:
                target = [prompt_trans_w_case(src_lang, dst_lang, item, test_cases, test_case_num)]
        elif obj == REFINE:
            flag = True
            feedback = feedbacks[id] if id in feedbacks else []
            err_fd = []
            for i in feedback:
                if i['err_type'] != "PASS":
                    flag = False
                    err_fd.append(i)
            if flag is True:
                with jsonlines.open(out_path, "a") as fw:
                    fw.write({"id": id, dst_lang: org_sols[id]})
                continue
            else:
                feedback0 = err_fd[0]
                if feedback0['err_type'] == "REDO":
                    test_cases = "\n".join(test_case_lst[id])
                    if test_cases.strip() == "":
                        target = [prompt_trans_one_shot(src_lang, dst_lang, item)]
                        # print("REDO W/O CASE: ", target)
                    else:
                        target = [prompt_trans_w_case(src_lang, dst_lang, item, test_cases, test_case_num)]
                        # print("REDO W CASES: ", prompt)
                else:
                    target = [prompt_refine(dst_lang, org_sols[id][0].strip(), feedback0)]
        else:
            assert False, "no such objective!"
        prompt = prefix + target
        with jsonlines.open(out_path, "a") as fw:
            fw.write({"id": id, dst_lang: collect_one(prompt, api_key, sample_num=sample_num)})


if __name__ == "__main__":
    GEN_VAL_INP = 0
    TRANS = 1
    TRANS_ONE_SHOT = 2
    TRANS_W_CASES = 3
    REFINE = 4

    parser = argparse.ArgumentParser()
    parser.add_argument("--apikey", type=str, help="enter your api key", default="")
    parser.add_argument("--src_lang", type=str, help="source language", default="java")
    parser.add_argument("--dst_lang", type=str, help="target language", default="python")
    parser.add_argument("--k", type=int, help="sampling number", default=10)
    parser.add_argument("--start", type=int, help="start index", default=1)
    parser.add_argument("--shots", type=int, help="one shot or not", default=1)
    parser.add_argument("--round", type=int, help="number of round", default=2)
    parser.add_argument("--test_case_num", type=int, help="num of test cases", default=3)
    parser.add_argument("--obj", type=int, help="select an objective - 0: gen_val_inp, 2: trans, 3: trans_w_cases, 4: refine", default=0)
    args = parser.parse_args()



    API_KEY = args.apikey
    src_lang = args.src_lang
    dst_lang = args.dst_lang
    obj = args.obj
    sample_num = args.k
    _round = args.round
    test_case_num = args.test_case_num  # todo only be activated when obj == TRANS_W_CASES
    test_file = f"./cleaned_data/testable_samples.jsonl"
    # 用于第N轮refine的feedbacks
    feedback_file = f"./cleaned_data/gpt3_5/feedbacks/testable_{src_lang}_{dst_lang}_w_{test_case_num}cases_{_round}round.jsonl"
    # 第N-1轮作为原始结果
    org_sol_file = f"./cleaned_data/gpt3_5/post_processed_w_{test_case_num}cases_{_round}round/testable_{src_lang}_{dst_lang}_w_{test_case_num}cases_{_round}round.jsonl"
    # todo not adapt for gen_val_inp yet
    # 第N轮refine输出
    out_path = f"./cleaned_data/gpt3_5/testable_{src_lang}_{dst_lang}_w_{test_case_num}cases_{_round}round.jsonl"
    # TODO: init: start=1, restart: start=stop_count+1
    main(test_file, src_lang, dst_lang, obj, sample_num, API_KEY, out_path, test_case_num, feedback_file, org_sol_file, start=1)


