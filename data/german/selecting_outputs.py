import json

# language="chinese" #TODO modify language
# model_names = ["Baichuan2-13B-Chat", "chatglm3-6b", "internlm2-chat-7b", "Qwen1.5-14B-Chat"] #TODO modify model names
# file_paths = [f"{language}-{model_id}-annotation.jsonl" for model_id in model_names]


language="german" #TODO modify language
model_names = ['bloom-6b4-clp-german-oasst-v0.1-annotation.k50_p0.90_t0.1',
               'bloom-6b4-clp-german-oasst-v0.1-annotation.k75_p0.95_t0.1',
               'occiglot-7b-de-en-instruct-annotation.k50_p0.90_t0.1',
               'occiglot-7b-de-en-instruct-annotation.k75_p0.95_t0.1',
               'sauerkraut-annotation.k50_p0.90_t0.1',
               'sauerkraut-annotation.k75_p0.95_t0.1']



selection_num = {f"{idx}": model_id for idx, model_id in enumerate(model_names)}
print(selection_num)

all_records_dict = {f"{model_id}": [] for model_id in model_names}


for model_id in model_names:
    with open(f"{language}-{model_id}.jsonl", 'r', encoding='utf-8') as file:
        for line in file:
            item = json.loads(line)
            all_records_dict[model_id].append(item)

with open(f'{language}_selected_outputs.jsonl', 'w', encoding='utf-8') as output_file:

    for i in range(len(all_records_dict[model_id])):
        print("*"*89)
        print("Input Question:", all_records_dict[model_id][i]["question"])
        for idx, m in enumerate(model_names):
            print(f"###{idx}###: ", all_records_dict[m][i]["output_text"], "\n")
        
        selection_index = input("Enter the index of the selected output text for this item: ")
        selected_model = selection_num[selection_index]

        output_file.write(json.dumps(all_records_dict[selected_model][i], ensure_ascii=False) + '\n')
