#!/usr/bin/env python
# coding: utf-8

# Installing dependencies. You might need to tweak the CMAKE_ARGS for the `llama-cpp-python` pip package.

# In[1]:


import random
random.seed(2202)

# GPU 
# This config has been tested on an v100. 32GB 
# For download the models

import os
os.environ['HF_HOME'] = './.hf/'

#!pip install --upgrade pip
#!pip install huggingface_hub


# Download an instruction-finetuned Llama3 model.

# In[2]:


import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from huggingface_hub import hf_hub_download, login

# safely copy your hf_token to this working directoy to login fo HF
with open('./hf_token', 'r') as file:
    hftoken = file.readlines()[0].strip()

login(token=hftoken, add_to_git_credential=True)
model_name = "meta-llama/Meta-Llama-3-8B-Instruct"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(device)

model = AutoModelForCausalLM.from_pretrained(model_name, trust_remote_code=True).to(device)
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)


# In[3]:


import pandas as pd

file_path = "questions-hi.tsv"
file_path = "more_hind_questions_extra.tsv"  #"leftover_hi.tsv"
records = pd.read_csv(file_path, sep='\t').to_dict(orient='records')

pd.read_csv(file_path, sep='\t')


# In[4]:

configs = [
    ('k50_p0.90_t0.1', dict(top_k=50, top_p=0.90, temperature=0.1)),
    ('k50_p0.95_t0.2', dict(top_k=50, top_p=0.95, temperature=0.2)),
    ('k75_p0.90_t0.2', dict(top_k=75, top_p=0.90, temperature=0.1)),
    ('k75_p0.95_t0.1', dict(top_k=75, top_p=0.95, temperature=0.1)),
    ('default', dict()),
]

random.shuffle(configs)

# In[ ]:


import tqdm
from transformers.utils import logging
import pathlib
import json
logging.set_verbosity_warning()

for shorthand, config in tqdm.tqdm(configs):
    output_file_path = f'outputs_lastover/hindi-{model_name.split("/")[1]}.{shorthand}.jsonl'
    anootation_file_path = f'outputs_lastover/hindi-{model_name.split("/")[1]}-annotation.{shorthand}.jsonl'
    if not pathlib.Path(anootation_file_path).is_file():
        new_records = []
        with open(output_file_path, 'w', encoding='utf-8') as file:
            for record in tqdm.tqdm(records):
                record = {**record}
                message = [
                            {"role": "user", "content": record['question']},
                        ]

                inputs = tokenizer.apply_chat_template(
                    message,
                    add_generation_prompt=True,
                    return_tensors="pt"
                ).to(model.device)

                terminators = [
                    tokenizer.eos_token_id,
                    tokenizer.convert_tokens_to_ids("<|eot_id|>"),
                    tokenizer.encode('\n')[-1],
                ]

                outputs = model.generate(
                    inputs,
                    max_new_tokens=512,
                    num_return_sequences=1,
                    eos_token_id=terminators,
                    pad_token_id=tokenizer.eos_token_id,
                    return_dict_in_generate=True,
                    output_logits=True,
                    do_sample=True,
                    **config
                )

        
                # response repeats the input in the begining
                response = outputs.sequences[0][inputs.shape[-1]:]
                response_text = tokenizer.decode(response, skip_special_tokens=True)
                
                #response_token_ids = outputs.sequences[0].to("cpu").tolist()[len(inputs.input_ids[0]):]
                response_token_ids = response.to("cpu").tolist()
                # response_embeddings = outputs.sequences[0].to("cpu").tolist()[len(inputs.input_ids[0]):]
                response_tokens = tokenizer.convert_ids_to_tokens(response_token_ids)
                #response_logits = [l.to("cpu").tolist() for l in outputs.logits]
                response_logits = [l.squeeze().to("cpu").tolist()[response_token_ids[idx]] for idx,l in enumerate(outputs.logits)]
                
                """print("\n\n")
                print(f"Q: {message}")
                print(f"A: {response_text}")
        
                print("input length", len(inputs.input_ids[0]))
                # print("sequence length", len(outputs.sequences[0]))
                print("response token length", len(response_tokens))
                print("response token ID length", len(response_token_ids))
                print("logits length", len(response_logits))
                # print("embedding length", len(response_embeddings))
                raise"""
        
        
                record['model_id'] = model_name
                record['lang'] = 'hi'
        
                record['output_text'] = response_text
                record['output_tokens'] = response_tokens
                record['output_logits'] = response_logits
                # record['output_embeddings'] = response_embeddings
        
                json.dump(record, file, ensure_ascii=False)
                file.write('\n')

                
                columns_to_extract = ['URL-hi', 'lang', 'question', 'model_id', 'output_text', 'output_tokens', 'title']
                extracted_data = {key: record[key] for key in columns_to_extract if key in record}
                new_records.append(extracted_data)
        
        
        output_data = []
        
        with open(anootation_file_path, 'w', encoding='utf-8') as file:
            for extracted_data in new_records:
                # extracted_data = {key: data[key] for key in columns_to_extract if key in data}
        
                json.dump(extracted_data, file, ensure_ascii=False)
                file.write('\n')
                
