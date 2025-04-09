import bs4

from . import models

def annots_to_json_spans(selected, text, hf_model_name):
    selected = selected.replace('\r\n', '\n')
    soup = bs4.BeautifulSoup(selected, 'html.parser')
    start = 0
    spans = []
    for child in soup.children:
        end = start + len(child.text)
        if type(child) is bs4.element.Tag:
            spans.append(f'{start}:{end}')
        start = end
    return ';'.join(spans)
    
def get_profile(user):
    profile = (
        models
        .Profile
        .objects
        .get(annotator__username=user.username)
    )
    return profile
