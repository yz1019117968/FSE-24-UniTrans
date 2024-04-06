import json
import os
import re
import ast
from tqdm import tqdm
import signal
import argparse
import jsonlines
import numpy as np

def TimeoutHandler(signum, frame):
    raise Exception("timeout")

def evaluate_scripts(model, src_lang, dst_lang, k, suffix, timeout=5):
    script_file_path = f"./cleaned_data/{model}/test_scripts{suffix}/{src_lang}_{dst_lang}"
    testable_file_lst = os.listdir(script_file_path)
    print("num: ", len(testable_file_lst))
    log_details = []
    all_log = []
    all_pass_rate_log = []
    for file in tqdm(testable_file_lst):
        sample_lst = os.listdir(f"{script_file_path}/{file}")
        topk = min(len(sample_lst), k)
        log_lst = []
        log_pass_rate_lst = []
        for id in range(topk):
            signal.signal(signal.SIGALRM, TimeoutHandler)
            signal.alarm(timeout)
            try:
                if dst_lang == "python":
                    result = os.popen(f"python {script_file_path}/{file}/sample_{id}.py")
                    # 此时打开的a是一个对象，如果直接打印的话是对象内存地址
                elif dst_lang == "java":
                    result = os.popen(f"java --module-path $PATH_TO_FX --add-modules javafx.controls {script_file_path}/{file}/sample_{id}.java")
                elif dst_lang == "cpp":
                    os.system(f"g++ {script_file_path}/{file}/sample_{id}.cpp -o {script_file_path}/{file}/sample_{id}")
                    result = os.popen(f"{script_file_path}/{file}/sample_{id}")
                else:
                    assert False, "unknown dst_lang!"
                log = result.read()
                # 要用read（）方法读取后才是文本对象
                log_ret = re.findall(r"#Results:\s?\d+,\s?\d+\n?", log)
                if len(log_ret) > 0:
                    act, tal = log_ret[0].replace("#Results:", "").split(",")
                    # PASS@K
                    if int(act.strip()) == int(tal.strip()):
                        log_lst.append(True)
                    else:
                        log_lst.append(False)
                    # PASS RATE
                    log_pass_rate_lst.append(int(act.strip()) / int(tal.strip()))
                else:
                    log_lst.append(False)
                    log_pass_rate_lst.append(0)
                signal.alarm(0)
            except Exception as ret:
                print("EXCEPTION:", ret)
                log_lst.append(False)
                log_pass_rate_lst.append(0)
                signal.alarm(0)
                continue
        log_details.append({"id": file, "ret": log_lst, "rate": log_pass_rate_lst})
        if True in log_lst:
            # exist at least one true candidate
            all_log.append(True)
        else:
            all_log.append(False)
        all_pass_rate_log.append(np.max(log_pass_rate_lst))
    print(f"computational acc: {all_log.count(True) / len(all_log)}, Correct_num: {all_log.count(True)}, Total: {len(all_log)}")
    print(f"AVG PASS RATE: {np.mean(all_pass_rate_log)}")
    with jsonlines.open(f"./log_details_{model}_{src_lang}_{dst_lang}{suffix}.jsonl", "w") as fw:
        fw.write_all(log_details)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--src_lang", type=str, help="source language", default="python")
    parser.add_argument("--dst_lang", type=str, help="target language", default="java")
    parser.add_argument("--k", type=int, help="pass@k", default=1)
    parser.add_argument("--timeout", type=int, help="timeout", default=1)
    parser.add_argument("--model", type=str, help="select an llm", default="gpt3_5")
    parser.add_argument("--suffix", type=str, help="suffix of experiments", default="_zero_shot")
    args = parser.parse_args()
    model = args.model
    src_lang = args.src_lang
    dst_lang = args.dst_lang
    evaluate_scripts(model, src_lang, dst_lang, k=args.k, suffix=args.suffix, timeout=args.timeout)
