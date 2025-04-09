import re
import requests
import random
import time
import pandas as pd
from time import sleep
from bs4 import BeautifulSoup as bs


stime = time.time()
searchlangs = ['fr', 'ar', 'hi', 'it']
languages = ['en','fi', 'sv', 'zh', 'fr', 'es','ar', 'hi', 'it']

found_entries = pd.DataFrame(columns=['url','title','langs'])

def update_df(soup, found_entries, languages=languages):
        languages.sort()
        if isinstance(soup,dict):
            new_row = pd.DataFrame(soup)
        else:
            new_row = pd.DataFrame({
                    'title': [soup.find('h1').text],
                    'url':   [soup.find('link', rel='canonical')['href']],
                    'langs': [','.join(languages)],
                    })

        print('Found multiparallel entry: ', new_row.url)      

        found_entries = pd.concat((found_entries,new_row), ignore_index=True)
        found_entries.to_csv('multiparallel_wiki_entries_ThisRun.tsv',sep='\t', header=True, index=False)

        return found_entries

iters = 0
while found_entries.shape[0] < 251:
    langchoice = random.choice(searchlangs)
    if langchoice == 'it':
        pass
    else:
        url=f'https://{langchoice}.wikipedia.org/wiki/Special:Random'
        response = requests.get(url)
        soup = bs(response.content, 'html.parser')
        
        parallel_langs = soup.find(attrs={'id':"p-lang-btn"}).find_all('a', lang=re.compile(r"|".join(languages)))
        fulllangslist = [langchoice]+[x['lang'] for x in parallel_langs]
        fulllangslist = [x for x in fulllangslist if len(x)==2]
        fulllangslist.sort()
        langslist = [x for x in fulllangslist if x in searchlangs]
        if (len(langslist) == 4) or (len(fulllangslist) >= 7):
            found_entries = update_df(soup, found_entries, fulllangslist)
        #elif len(parallel_langs) >= 2:  
        #    langslist = [x['lang'] for x in parallel_langs]
        #    found_entries = update_df(soup, found_entries, langslist)
        iters += 1
        if iters%10 == 0:
            print(iters,'iterations so far w/ ', found_entries.shape[0],'entries found (',int(time.time()-stime),'sec)')
        sleep(3)

#new_row = {'url':['https://en.wikipedia.org/wiki/David_F._Sandberg'],
#           'tile':['David F. Sandberg'],
#           'langs': [','.join(languages)] }

print(found_entries)
found_entries.to_csv('multiparallel_wiki_entries_hindi.tsv',sep='\t', mode='a', header=False, index=False)

#found_entries = update_df(new_row, found_entries)

