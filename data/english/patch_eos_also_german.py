eos_tokens_dict = {
        'TheBloke/SauerkrautLM-7B-v1-GGUF': '</s>',
        'TheBloke/Mistral-7B-Instruct-v0.2-GGUF': '</s>',
}



def patch_logits_in_tokens(row):
        if 'pythia' in row['model_id'].lower():
                return row['model_output_logits'][:len(row['model_output_tokens'])]
        else:
                return row['model_output_logits']


def patch_eos_in_tokens(row):
        if row['model_id'] not in eos_tokens_dict:
                eos_token_str =  AutoTokenizer.from_pretrained(row['model_id']).eos_token
                eos_tokens_dict[row['model_id']] = eos_token_str
        if 'pythia' in row['model_id'].lower():
                return row['model_output_tokens']
        elif len(row['model_output_tokens']) == len(row['model_output_logits']):
                assert row['model_output_tokens'][-1] == eos_tokens_dict[row['model_id']], 'does not end in EOS!'
                return row['model_output_tokens']
        else:
                assert (len(row['model_output_tokens']) + 1) == len(row['model_output_logits']), f'unhandled case...? {row}'
                return row['model_output_tokens'] + [eos_tokens_dict[row['model_id']]]


(df_train.apply(patch_logits_in_tokens, axis=1).apply(len) ==  df_train.apply(patch_eos_in_tokens, axis=1).apply(len)).all()

