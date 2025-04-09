import pathlib
import pandas as pd
import tqdm

class FakeClassForEvalCalls:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class TextGenerationOutputDetails(FakeClassForEvalCalls):
    pass


class TextGenerationOutputToken(FakeClassForEvalCalls):
    pass


class TextGenerationOutputPrefillToken(FakeClassForEvalCalls):
    pass


for file in pathlib.Path('.').glob('**/*det*.txt'):
    print(file)
    with open(file, 'r') as istr:
        lines = list(map(str.strip, istr))
        questions = lines[0::3]
        details = list(map(eval, lines[1::3]))
        records = [{'question': question, 'output_tokens': [tok.kwargs['text'] for tok in  detail.kwargs['tokens']], 'output_logits': [tok.kwargs['logprob'] for tok in  detail.kwargs['tokens']], 'file': str(file)} for question, detail in zip(questions, details)]
    pd.DataFrame.from_records(records).to_json(file.with_suffix('.jsonl'), lines=True, orient='records')


