def merge_annots(annotations):
    selected = [set() for _ in annotations]
    for idx, a in enumerate(annotations):
        for span in (
            range(*map(int, span.split(':')))
            for span in a.json_highlighted_spans.split(';')
        ):
            selected[idx] |= set(span)
    min_idx = min(min(slct) for slct in selected)
    max_idx = max(max(slct) for slct in selected)
    current_weight = -1
    spans = []
    end = -1
    in_span = False
    for idx in range(min_idx, max_idx + 2):
         new_weight = sum(1 for slct in selected if idx in slct)
         if new_weight != current_weight:
             if in_span:
                 spans[-1]['end'] = idx
             if new_weight != 0:
                 spans.append({
                    'start': idx, 
                    'prob': new_weight / len(annotations),
                 })
                 in_span = True
             else:
                 in_span = False
             current_weight = new_weight
    return spans


def to_dict(datapoint):
    dict_rep = {
        'id': datapoint.id,
        'lang': datapoint.language,
        'model_input': datapoint.model_input,
        'model_output_text': datapoint.model_output,
        'model_id': datapoint.hf_model_name,
        'soft_labels': merge_annots(datapoint.annotation_set.all()),
    }
    hard_labels = [] 
    prev_end = -1
    for start, end in (
        (lbl['start'], lbl['end']) 
        for lbl in dict_rep['soft_labels']
        if lbl['prob'] > 0.5
    ):
        if start == prev_end:
            hard_labels[-1][-1] = end
        else:
            hard_labels.append([start, end])
        prev_end = end
    dict_rep['hard_labels'] = hard_labels
    return dict_rep
