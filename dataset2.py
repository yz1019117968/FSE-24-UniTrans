from torch.utils.data import Dataset
import os
import json
from transformers import AutoTokenizer, LlamaTokenizer
from cleaned_data.templates.examples_trans import \
    example_code_java, example_code_cpp, example_code_python, \
    example_test_cases_java, example_test_cases_cpp, example_test_cases_python
from cleaned_data.templates.examples_inp import example_cpp, valid_inputs_cpp, \
    example_java, valid_inputs_java, example_python, valid_inputs_python
import torch
import re
from cleaned_data.templates.example_refine import python_refine_example2_1, python_refine_example2_2, \
    cpp_refine_example2_1, cpp_refine_example2_2, java_refine_example2_1, java_refine_example2_2
class CTDataset(Dataset):
    def __init__(self, obj, path, feedback_file, org_sol_file, checkpoint, src_lang, dst_lang, dst_lang_comm, shots, test_case_num):
        self.path = path
        root_path = os.getcwd()
        self.data = []
        self.src_lang = src_lang
        self.dst_lang = dst_lang
        self.dst_lang_comm = dst_lang_comm
        self.shots = shots
        self.obj = obj
        self.test_case_num = test_case_num
        model_folder = checkpoint.split("/")[1]
        if "codegen" in checkpoint:
            self.tokenizer = AutoTokenizer.from_pretrained(checkpoint)
        elif "llama" in checkpoint:
            self.tokenizer = LlamaTokenizer.from_pretrained(checkpoint)
        with open(os.path.join(root_path, path), encoding="utf-8") as fr:
            for line in fr.readlines():
                self.data.append(json.loads(line))

        if obj == 3:
            # trans with cases
            self.test_case_lst = {}
            with open(f"./cleaned_data/{model_folder}/test_cases/test_cases_{dst_lang}.jsonl", encoding="utf-8") as fr:
                for line in fr.readlines():
                    line = json.loads(line)
                    self.test_case_lst.update({line['id']: list(line['test_case'])[:test_case_num]})
        elif obj == 4:
            # refine
            self.test_case_lst = {}
            with open(f"./cleaned_data/{model_folder}/test_cases/test_cases_{dst_lang}.jsonl", encoding="utf-8") as fr:
                for line in fr.readlines():
                    line = json.loads(line)
                    self.test_case_lst.update({line['id']: list(line['test_case'])[:test_case_num]})
            self.feedbacks = {}
            with open(feedback_file, encoding="utf-8") as fr:
                for line in fr.readlines():
                    line = json.loads(line)
                    self.feedbacks.update({line['id']: line['feedbacks']})
            self.org_sols = {}
            with open(org_sol_file, encoding="utf-8") as fr:
                for line in fr.readlines():
                    line = json.loads(line)
                    self.org_sols.update({line['id']: line[dst_lang]})
        else:
            assert False, "unknown objective!"

    def prompt_trans(self, src_lang, dst_lang, code, shots):
        if shots == 1:
            example_dst_code = eval(f"example_code_{dst_lang}")
            example_src_code = eval(f"example_code_{src_lang}")
            example = f"Given {src_lang} code:\n{example_src_code}\nTranslate given {src_lang} code to {dst_lang} code, " \
                           f"and use END_OF_CASE to finish your answer.\n{self.dst_lang_comm}{self.dst_lang} code\n{example_dst_code}\nEND_OF_CASE\n"
        elif shots == 0:
            example = ""
        else:
            assert False, "shot number cannot exceed one!"
        prompt = example + f"Given the {self.src_lang} code:\n{code}\nTranslate given {self.src_lang} code to {self.dst_lang} code, " \
                                f"and use END_OF_CASE to finish your answer.\n{self.dst_lang_comm}{self.dst_lang} code\n"
        return prompt

    def prompt_case(self, dst_lang, code):
        example_dst_code = eval(f"example_{dst_lang}")
        example_val_inps = eval(f"valid_inputs_{dst_lang}")
        prompt = f"{example_dst_code}\n{example_val_inps}\n{code}\nplease generate ten groups of differentiated valid inputs for the above focal method of {dst_lang} language, " \
                 f"in the format of [Input_1]\\n[Input_2]\\n...[Input_10]. Finally, use END_OF_CASE to finish your answer."
        return prompt

    def prompt_trans_w_case(self, src_lang, dst_lang, code, test_cases, test_case_num):
        example_src_code = eval(f"example_code_{src_lang}")
        example_dst_code = eval(f"example_code_{dst_lang}")
        example_test_cases = "\n".join(eval(f"example_test_cases_{dst_lang}")[: test_case_num])
        content = f"Given {src_lang} code:\n{example_src_code}\nGiven test cases:\n{example_test_cases}\n" \
                  f"Translate given {src_lang} code to {dst_lang} code, and ensure the translated {dst_lang} code can pass all given test cases." \
                  f"Use END_OF_CASE to finish your answer.\n{self.dst_lang_comm}{self.dst_lang} code\n{example_dst_code}\nEND_OF_CASE\n"
        target = f"Given {src_lang} code:\n{code}\nGiven test cases:\n{test_cases}\n" \
                 f"Translate given {src_lang} code to {dst_lang} code, and ensure the translated {dst_lang} code can pass all given test cases." \
                 f"Use END_OF_CASE to finish your answer.\n{self.dst_lang_comm}{self.dst_lang} code\n"
        prompt = content + target
        return prompt

    def prompt_refine(self, dst_lang, dst_lang_comm, org_sol, feedback):
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
        return prompt

    def __getitem__(self, idx):
        item = self.data[idx]
        task_id = item['id']
        if self.obj == 2:
            src_code = item[self.src_lang]
            prompt = self.prompt_trans(self.src_lang, self.dst_lang, src_code, self.shots)
        elif self.obj == 0:
            dst_code = item[self.dst_lang]
            prompt = self.prompt_case(self.dst_lang, dst_code)
        elif self.obj == 3:
            # trans with cases
            src_code = item[self.src_lang]
            test_cases = "\n".join(self.test_case_lst[task_id])
            if test_cases.strip() == "":
                prompt = self.prompt_trans(self.src_lang, self.dst_lang, src_code, self.shots)
            else:
                prompt = self.prompt_trans_w_case(self.src_lang, self.dst_lang, src_code, test_cases, self.test_case_num)
        elif self.obj == 4:
            # refine
            flag = True
            feedback = self.feedbacks[task_id] if task_id in self.feedbacks else []
            # print("feedback: ", feedback)
            err_fd = []
            for i in feedback:
                if i['err_type'] != "PASS":
                    flag = False
                    err_fd.append(i)
            if flag is True:
                return {
                    "id": task_id,
                    "org_sol": self.org_sols[task_id]
                }
            else:
                feedback0 = err_fd[0]
                if feedback0['err_type'] == "REDO":
                    src_code = item[self.src_lang]
                    test_cases = "\n".join(self.test_case_lst[task_id])
                    if test_cases.strip() == "":
                        prompt = self.prompt_trans(self.src_lang, self.dst_lang, src_code, self.shots)
                        # print("REDO W/O CASE: ", prompt)
                    else:
                        prompt = self.prompt_trans_w_case(self.src_lang, self.dst_lang, src_code, test_cases,self.test_case_num)
                        # print("REDO W CASES: ", prompt)
                else:
                    prompt = self.prompt_refine(self.dst_lang, self.dst_lang_comm, self.org_sols[task_id][0].strip(), feedback0)
                    # print("REPAIR: ", prompt)
        else:
            assert False, "unknown objective!"
        inputs = self.tokenizer(prompt, return_tensors="pt")
        input_ids = inputs['input_ids']
        attention_mask = inputs['attention_mask']
        return {
            "id": task_id,
            "input_ids": input_ids,
            "attention_mask": attention_mask
        }

    def __len__(self):
        return len(self.data)









