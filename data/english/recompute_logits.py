import os
import random
import json
import torch
import tqdm
import pathlib
import pandas as pd

from transformers import AutoModelForCausalLM, AutoTokenizer

# USAGE: 
# You 1st NEED TO INSTALL llamma_cpp:
#   Install in PUHTI:
#       module load pytorch/2.4 gcc/13 cuda
#       pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu122
#   Run in PUHTI:
    srun  -p gpu --nodes=1 --gres=gpu:v100:2,nvme:10 --mem=256G -A project_2005099 --time=01:30:00 --pty $BASH
    module load pytorch/2.4 gcc/13 cuda 
    export HF_HOME='./hf/'
    cd /scratch/project_2005099/members/mickusti/mu-shroom
    python3 recompute_logits_english.py
       python3 recompute_logits.py


#just in case, twice again:
os.environ['HF_HOME'] = './.hf/'
os.putenv('HF_HOME','./hf/'); os.system('bash')

def apply_model_specific_templtate(mname, ans, tokenizer):
    if 'Pythia' in mname:
        prompt = f'<human>: {ans.question}\n<bot>:'
        prompt_len = tokenizer(prompt, return_tensors="pt")['input_ids'].size(-1)
        sentence = prompt + ans.output_text + tokenizer.eos_token
        inputs = tokenizer(sentence, return_tensors="pt").to(device)
    elif 'falcon' in mname:
        # messages = [{"role": "user", "content": ans.question},]
        # prompt = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_dict=False, return_tensors='pt',).to(device)
        # prompt_len = prompt.size(-1)

        # As done during generation:
        prompt = ans.question + '\n'
        prompt_len = tokenizer(prompt, return_tensors="pt")['input_ids'].size(-1)
        sentence = prompt + ans.output_text + tokenizer.eos_token
        inputs = tokenizer(sentence, return_tensors="pt").to(device)
    elif 'TheBloke' in mname:
        prompt = f"[INST] {ans.question} [/INST]"
        # Encode the prompt (tokenize it)
        tokens = tokenizer(bytes(prompt, encoding="utf-8"))
        prompt_len = len(tokens)
        sentence = prompt + ans.output_text
        inputs = tokenizer(bytes(sentence, encoding="utf-8"))

    return prompt_len, inputs


def get_logits(df):
    model_name =  set(df.model_id).pop()
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(model_name, trust_remote_code=True).to(device)

    all_logits = {} # df.output_logits
    for idx,ans in tqdm.tqdm(df.iterrows(), desc=model_name):
        # inputs will contain the prompt. Will compute all together and then strip the unecessary bits
        prompt_len, inputs = apply_model_specific_templtate(model_name, ans, tokenizer)

        with torch.no_grad():  
            outputs = model(**inputs)

        response_token_ids = inputs['input_ids'].to("cpu").tolist()[0]

        output_logits = outputs.logits.squeeze().to('cpu')
        response_logits = [logit.tolist()[response_token_ids[idx]] for idx,logit in enumerate(output_logits)]
        response_token_ids = response_token_ids[prompt_len:]
        response_logits = response_logits[prompt_len:]
        
        all_logits[idx] = response_logits
    
    #for idx, values in all_logits.items():
    #    df.loc[idx, 'output_logits'] = list(values)
    df.output_logits = all_logits
    # clean cuda
    model = None
    tokenizer = None
    del model
    del tokenizer
    torch.cuda.empty_cache()
    return df

def get_logits_llamacpp(df):
    from huggingface_hub import hf_hub_download
    
    #model_name =  set(df.model_id).pop()
    model_name = "TheBloke/Mistral-7B-Instruct-v0.2-GGUF"
    model_basename = "mistral-7b-instruct-v0.2.Q6_K.gguf"
    model_path = hf_hub_download(repo_id=model_name, filename=model_basename)

    # This config has been tested on an RTX 3080 (VRAM of 16GB).
    # you might need to tweak with respect to your hardware.
    from llama_cpp import Llama
    lcpp_llm = Llama(
        model_path=model_path,
        n_threads=4, # CPU cores
        n_batch=8192, # Should be between 1 and n_ctx, consider the amount of VRAM in your GPU.
        n_gpu_layers=400, # Change this value based on your model and your GPU VRAM pool.
        n_ctx=8192, # Context window
        logits_all=True
    )
    all_logits = {} # df.output_logits
    all_outtexts = {idx:''.join(ans.tokens) for idx,ans in df.iterrows()}
    df.output_text = all_outtexts

    for idx, ans in tqdm.tqdm(df.iterrows(), desc=model_basename):
        prompt_len, inputs = apply_model_specific_templtate(model_name, ans, lcpp_llm.tokenize)
        inputs.append(lcpp_llm.token_eos())


        lcpp_llm.eval(inputs) # fills the np array Llama._scores with the logits
        output_logits = lcpp_llm._scores.copy()
        lcpp_llm.reset() # nukes the contents of Llama._scores and replaces it with a fresh new array
 
        response_logits = [logit.tolist()[inputs[idx]] for idx,logit in enumerate(output_logits)]
        response_token_ids = inputs[prompt_len:]
        response_logits = inputs[prompt_len:]
        
        all_logits[idx] = response_logits
        all_outtexts[idx] = ''.join(ans.tokens)

        
    df.output_logits = all_logits

    lcpp_llm = None
    del lcpp_llm
    torch.cuda.empty_cache()
    return df

def main():
    infile2fix = 'english-selection.jsonl'
    outfile = 'english_ready_for_anotation_fixed.tsv'

    finalanswers = pd.read_json(infile2fix, lines=True)
    # put finalanswers in the right format to save later on 
    finalanswers['output_logits'] = None
    finalanswers = finalanswers.rename(columns={'en-url': 'url-localized'})
    finalanswers['Primary Wikipedia URL'] = None
    finalanswers['url-idx'] = None
    finalanswers = finalanswers.rename(columns={'model_file_name': 'config_info'})


    finalanswers['tmp'] = None
    fillwith = {}
    for idx,row in old.iterrows():
        if isinstance(row.output_tokens,list):
            fillwith[idx] = row.output_tokens
        else:
            fillwith[idx] = row.tokens

    finalanswers.tmp = fillwith
    finalanswers.output_tokens = finalanswers.tmp


    finalanswers[finalanswers.output_text.isna()].tokens

    # NaN's are for mistral (llama_cpp)
    finalanswers.model_id = finalanswers.model_id.fillna('TheBloke/Mistral-7B-Instruct-v0.2-GGUF')
    modelnames = set(finalanswers.model_id.dropna())

    for mname in modelnames:
        df = finalanswers[finalanswers.model_id == mname]
        if mname == 'TheBloke/Mistral-7B-Instruct-v0.2-GGUF':
            df = get_logits_llamacpp(df) 
        else:
            df = get_logits(df)
        for idx,row in df.iterrows(): 
            finalanswers.loc[idx] = row



    finalanswers = finalanswers[finaldfcols]      

    finalanswers.to_csv(outfile, sep='\t', index=False)
    print(f"Dumped corrected output file in {outfile}")
    #import ipdb; ipdb.set_trace()


global device, finaldfcols
device='cuda' if torch.cuda.is_available() else 'cpu'
finaldfcols = ['url-idx', 'Primary Wikipedia URL', 'title', 
               'url-localized', 'question', 'model_id', 'config_info', 
               'lang', 'output_text', 'output_tokens', 'output_logits']


if __name__ == '__main__':
    main()
