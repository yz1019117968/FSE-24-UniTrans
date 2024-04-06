import os.path

from transformers import AutoModelForCausalLM, AutoTokenizer, LlamaTokenizer, LlamaForCausalLM, LlamaConfig, AutoConfig
from tqdm import tqdm
import jsonlines
import torch
import argparse
from dataset2 import CTDataset
from torch.utils.data import DataLoader
import time

def collect_one(model, tokenizer, input_ids, attention_mask, k, max_len):
    completions = []
    with torch.no_grad():
        sample_outputs = model.generate(input_ids=input_ids, attention_mask=attention_mask, max_length=max_len, do_sample=True,
                                    temperature=0.8, top_p=0.95, num_return_sequences=k)[:, input_ids.shape[1]:]
    for sample_output in sample_outputs:
        sample_i = tokenizer.decode(sample_output, skip_special_tokens=True)
        candi_lst = sample_i.strip().split("\n")
        candi = ""
        for snippet in candi_lst:
            if snippet.endswith("END_OF_CASE"):
                candi += snippet.split("END_OF_CASE")[0]+"\n"
                break
            else:
                candi += snippet + "\n"
        candi = candi.strip()
        completions.append(candi)
    return completions


def main(obj, dst_lang_comm, checkpoint, k, max_len, data_path, feedback_file, org_sol_file,
         src_lang, dst_lang, shots, test_case_num, out_path, start):
    test_set = CTDataset(obj, data_path, feedback_file, org_sol_file, checkpoint, src_lang,
                         dst_lang, dst_lang_comm, shots, test_case_num)
    dataloader = DataLoader(test_set, batch_size=1, shuffle=False, num_workers=0)
    if "codegen" in checkpoint:
        model = AutoModelForCausalLM.from_pretrained(checkpoint, device_map="auto", torch_dtype=torch.float16)
        tokenizer = AutoTokenizer.from_pretrained(checkpoint)
    elif "llama" in checkpoint:
        configuration = LlamaConfig()
        model = LlamaForCausalLM.from_pretrained(checkpoint, device_map="auto", torch_dtype=torch.float16, config=configuration)
        tokenizer = LlamaTokenizer.from_pretrained(checkpoint)
    else:
        assert False, "unknown model!"
    model.half()
    model.eval()
    count = 0
    st_time = time.time()
    for batch in tqdm(dataloader):
        count += 1
        if count < start:
            continue
        id = batch['id'][0]
        if list(batch.keys()) == ['id', 'org_sol']:
            code_solutions = [i[0] for i in batch['org_sol']]
        elif list(batch.keys()) == ['id', 'input_ids', 'attention_mask']:
            input_ids = batch['input_ids'][0].cuda()
            attention_mask = batch['attention_mask'][0].cuda()
            code_solutions = collect_one(model, tokenizer, input_ids, attention_mask, k, max_len)
        else:
            assert False, "key error!"
        with jsonlines.open(out_path, "a") as fw:
            fw.write({"id": id, dst_lang: code_solutions})
    ed_time = time.time()
    print(f"total time spent: {ed_time - st_time}s, {(ed_time - st_time)/len(test_set)}s/sample")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=str, help="model type", default="decapoda-research/llama-7b-hf")
    parser.add_argument("--src_lang", type=str, help="source language", default="java")
    parser.add_argument("--dst_lang", type=str, help="target language", default="python")
    parser.add_argument("--k", type=int, help="sampling number", default=10)
    parser.add_argument("--max_len", type=int, help="max length of the return value", default=600)
    parser.add_argument("--start", type=int, help="start index", default=1)
    parser.add_argument("--shots", type=int, help="one shot or not", default=1)
    parser.add_argument("--round", type=int, help="number of round", default=2)
    parser.add_argument("--test_case_num", type=int, help="num of test cases", default=3)
    parser.add_argument("--obj", type=int, help="select an objective - 0: gen_val_inp, 2: trans, 3: trans_w_cases, 4: refine", default=0)
    args = parser.parse_args()

    checkpoint = args.checkpoint
    k = args.k
    src_lang = args.src_lang
    dst_lang = args.dst_lang
    if dst_lang == "python":
        dst_lang_comm = "#"
    elif dst_lang == "java" or dst_lang == "cpp":
        dst_lang_comm = "//"
    else:
        assert False, "unknown lang!"
    model_folder = args.checkpoint.split("/")[1]
    data_path = "./cleaned_data/testable_samples.jsonl"
    feedback_file = None
    org_sol_file = None
    if args.obj == 0:
        print(">" * 15 + f"OBJECTIVE: Valid Inputs Generation for {dst_lang} Using {checkpoint}" + "<" * 15)
        out_path = f"./cleaned_data/{model_folder}/valid_inputs/valid_inputs_{dst_lang}.jsonl"
    elif args.obj == 2:
        print(">" * 15 + f"OBJECTIVE: Translation with {args.shots} Shot from {src_lang} to {dst_lang} Using {checkpoint}" + "<" * 15)
        out_path = f"./cleaned_data/{model_folder}/testable_{src_lang}_{dst_lang}_one_shot.jsonl"
    elif args.obj == 3:
        print(">" * 15 + f"OBJECTIVE: Translation with One Shot and {args.test_case_num} Test Cases from {src_lang} to {dst_lang} Using {checkpoint}" + "<" * 15)
        out_path = f"./cleaned_data/{model_folder}/testable_{src_lang}_{dst_lang}_w_cases.jsonl"
    elif args.obj == 4:
        print(">" * 15 + f"OBJECTIVE: Refine round {args.round} with One Shot from {src_lang} to {dst_lang} Using {checkpoint}" + "<" * 15)
        feedback_file = f"./cleaned_data/{model_folder}/feedbacks/testable_{src_lang}_{dst_lang}_w_{args.test_case_num}cases_{args.round}round.jsonl"
        if args.round == 1:
            org_sol_file = f"./cleaned_data/{model_folder}/post_processed_w_cases/testable_{src_lang}_{dst_lang}_w_cases.jsonl"
            out_path = f"./cleaned_data/{model_folder}/testable_{src_lang}_{dst_lang}_w_cases_r12.jsonl"
        elif args.round == 2:
            org_sol_file = f"./cleaned_data/{model_folder}/post_processed_w_cases_r12/testable_{src_lang}_{dst_lang}_w_cases_r12.jsonl"
            out_path = f"./cleaned_data/{model_folder}/testable_{src_lang}_{dst_lang}_w_cases_r2.jsonl"
        elif args.round == 3:
            org_sol_file = f"./cleaned_data/{model_folder}/post_processed_w_cases_r2/testable_{src_lang}_{dst_lang}_w_cases_r2.jsonl"
            out_path = f"./cleaned_data/{model_folder}/testable_{src_lang}_{dst_lang}_w_cases_r3.jsonl"
        else:
            assert False, "reach maximum repair round!"
    else:
        assert False, "unknown objective!"

    main(obj=args.obj, dst_lang_comm=dst_lang_comm, checkpoint=checkpoint, k=k, max_len=args.max_len,
         data_path=data_path, feedback_file=feedback_file, org_sol_file=org_sol_file, src_lang=src_lang, dst_lang=dst_lang,
         shots=args.shots, test_case_num=args.test_case_num, out_path=out_path, start=args.start)

