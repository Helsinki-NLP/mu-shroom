import random
random.seed(2202)

# GPU 
# This config has been tested on an v100. 32GB 
# For download the models

import os
os.environ['HF_HOME'] = '/scratch/project_2005099/members/mickusti/cerberus/hf/'

#!pip install --upgrade pip
#!pip install huggingface_hub


# Download an instruction-finetuned Llama3 model.

# In[2]:


import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BatchEncoding
from huggingface_hub import hf_hub_download, login

# safely copy your hf_token to this working directoy to login fo HF
with open('./hf_token', 'r') as file:
    hftoken = file.readlines()[0].strip()

login(token=hftoken, add_to_git_credential=True)
#model_name = "nickmalhotra/ProjectIndus" #
model_name = "meta-llama/Meta-Llama-3-8B-Instruct"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(device)

model = AutoModelForCausalLM.from_pretrained(model_name, trust_remote_code=True).to(device)
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)


import tqdm
from transformers.utils import logging
import pathlib
import json
logging.set_verbosity_warning()

#config = ('k50_p0.95_t0.2', 
config = dict(top_k=50, top_p=0.90, temperature=0.1) #dict(top_k=50, top_p=0.95, temperature=0.2) #)

import pandas as pd
df =  pd.read_csv('cleaned_50_with_logits.tsv', sep='\t')
index=38
record ={'question':df.question.values[index],
         'ans':df.output_text.values[index],
         'tokens': df.output_tokens.values[index]}
import ast
record['tokens'] = ast.literal_eval(record['tokens'])
print(record)

# ================= iteration 1 ==============================================
"""message = [ {"role": "user", "content": record['question']},]

prompt = tokenizer.apply_chat_template(
                    message,
                    tokenize=True,
                    add_generation_prompt=True,
                    return_tensors="pt",
                    return_dict=False
                ).to(model.device)

prompt_len = prompt.size(-1)

answer = torch.tensor(tokenizer.convert_tokens_to_ids(record['tokens'])).to(device)

inputs={'input_ids': torch.cat((prompt,answer.unsqueeze(0) ), dim=1)}

terminators = [
                    tokenizer.eos_token_id,
                    tokenizer.convert_tokens_to_ids("<|eot_id|>"),
                    tokenizer.encode('\n')[-1],
                ]

with torch.no_grad():
	outputs = model(**inputs)
"""
# ============================================================================

# =================== iteration 2 ============================================
prompt = record['question'] + '\n'
prompt_tokens = tokenizer.tokenize(prompt)
prompt_len = len(prompt_tokens) #tokenizer(prompt, return_tensors="pt")['input_ids'].size(-1)
all_tokens = prompt_tokens + record['tokens']
if tokenizer.eos_token is not None and all_tokens[-1] != tokenizer.eos_token:
     all_tokens.append(tokenizer.eos_token)
# sentence = prompt + ans.output_text + tokenizer.eos_token
data = {'input_ids' : [tokenizer.convert_tokens_to_ids(all_tokens)], 'attention_mask': [[1] * len(all_tokens)], }
inputs = BatchEncoding(data, tensor_type='pt').to(device)

with torch.no_grad():
        outputs = model(**inputs)

# ============================================================================

response_token_ids = inputs['input_ids'].to("cpu").tolist()[0]

output_logits = outputs.logits.squeeze().to('cpu')
response_logits = [logit.tolist()[response_token_ids[idx]] for idx,logit in enumerate(output_logits)]
response_token_ids = response_token_ids[prompt_len:]
response_logits = response_logits[prompt_len:]

#print(outputs)

#response = outputs.sequences[0][inputs.shape[-1]:]
#response_text = tokenizer.decode(response, skip_special_tokens=True)

#response_token_ids = outputs.sequences[0].to("cpu").tolist()[len(inputs.input_ids[0]):]
#response_token_ids = response.to("cpu").tolist()
# response_embeddings = outputs.sequences[0].to("cpu").tolist()[len(inputs.input_ids[0]):]
#response_tokens = tokenizer.convert_ids_to_tokens(response_token_ids)
#response_logits = [l.to("cpu").tolist() for l in outputs.logits]
#response_logits = [l.squeeze().to("cpu").tolist()[response_token_ids[idx]] for idx,l in enumerate(outputs.logits)]

print("\n\n")
#print(f"Q: {message}")
#print(f"A: {response_text}")
print("input: ", inputs)
# print("sequence length", len(outputs.sequences[0]))
#print("response token length", len(response_tokens))
print("response token ID length", len(response_token_ids))
print("logits length", len(response_logits))
print("logits", response_logits)

#"""
