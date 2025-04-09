import sys
import torch

from argparse import ArgumentParser
from logging import warning

from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline


DTYPE_MAP = {
    'fp32': torch.float32,
    'fp16': torch.float16,
    'bf16': torch.bfloat16,
}

DMAP_CHOICES = ['auto', 'sequential']

def argparser():
    ap = ArgumentParser()
    ap.add_argument('--max_prompts', default=10, type=int)
    ap.add_argument('--min_new_tokens', default=10, type=int)
    ap.add_argument('--max_new_tokens', default=100, type=int)
    ap.add_argument('--temperature', default=1.0, type=float)
    ap.add_argument('--num_return_sequences', default=1, type=int)
    ap.add_argument('--memory-usage', action='store_true')
    ap.add_argument('--show-devices', action='store_true')
    ap.add_argument('--dtype', choices=DTYPE_MAP.keys(), default='bf16')
    ap.add_argument('--device-map', choices=DMAP_CHOICES, default='auto')
    ap.add_argument('--trust-remote-code', default=None, action='store_true')
    ap.add_argument('--transformers_cache',type=str, default="/scratch/project_462000444/cache")
    ap.add_argument('--model', type=str)
    ap.add_argument('--prompts_file', type=str)
    ap.add_argument('--tokenizer', type=str)
    ap.add_argument('--top_k', type=int)
    return ap


def report_memory_usage(message, out=sys.stderr):
    print(f'max memory allocation {message}:', file=out)
    total = 0
    for i in range(torch.cuda.device_count()):
        mem = torch.cuda.max_memory_allocated(i)
        print(f'  cuda:{i}: {mem/2**30:.1f}G', file=out)
        total += mem
    print(f'  TOTAL: {total/2**30:.1f}G', file=out)


def generate(prompts, tokenizer, model, args):
    eos_token_id = tokenizer.eos_token_id
    pipe = pipeline(
            'text-generation',
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=1024,
            min_new_tokens=10,
            temperature=args.temperature,
            do_sample=True,
            eos_token_id=[eos_token_id],
            repetition_penalty=1.1,
            top_k = args.top_k,
            output_logis=True,
            # skip_special_tokens=True
        )
    for i, prompt in enumerate(prompts):
        prompt = prompt.rstrip('\n')
        messages = [{"role": "user", "content": prompt}]
        formatted_prompt = tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)
        generated = pipe(formatted_prompt)
        for g in generated:
            print("-"*10, "PROMPT", i+1, "-"*10)
            print(prompt)
            print("--"*20)
            text = g['generated_text']
            # print("RAW RESPONSE:", text)
            # print("--"*20)
            text = text.replace(formatted_prompt, '', 1)
            print("RESPONSE:")
            print(text)
            print(generated.keys())

def load_model(args):
    print("Loading model:", args.model)
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        device_map=args.device_map,
        torch_dtype=DTYPE_MAP[args.dtype],
        trust_remote_code=args.trust_remote_code,
        cache_dir=args.transformers_cache
    )
    print("Done loading!")
    return model


def check_devices(model, args):
    if args.show_devices:
        print(f'devices:', file=sys.stderr)
    for name, module in model.named_modules():
        for param_name, param in module.named_parameters(recurse=False):
            if args.show_devices:
                print(f'  {name}.{param_name}:{param.device}', file=sys.stderr)
            elif param.device.type != 'cuda':
                warning(f'{name}.{param_name} on device {param.device}')


def main(argv):
    args = argparser().parse_args(argv[1:])
    if args.tokenizer is None:
        args.tokenizer = args.model
    tokenizer = AutoTokenizer.from_pretrained(args.tokenizer)
    model = load_model(args)
    # if args.memory_usage:
    report_memory_usage('after model load')
    prompts = open(args.prompts_file).readlines()
    print("prompts:", len(prompts))
    generate(prompts, tokenizer, model, args)

    if args.memory_usage:
        report_memory_usage('after generation')


if __name__ == '__main__':
    sys.exit(main(sys.argv))
