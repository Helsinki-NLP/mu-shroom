### How to: test the annotation interface for yourself:

The annotation interface is coded with Django, which has a very extensive documentation (cf [here](https://docs.djangoproject.com/en/5.0/)). I didn't do anything too fancy, so reading through their tutorial section should help you parse out the code.
Below is a crash-course on how to turn the interface on.

Step 1. install requirements (make a virtual environment, then install the contents of requirements.txt):

```sh
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
```

Step 2., create the SQLITE database (where annotations will be stored):

```sh
cd mu-shroom-annot-interface
python3 manage.py migrate
```

Step 3. populate the database with datapoints to annotate. For CN, you can currently do as follows:
- open a shell:
```sh
# assuming you are in the mu-shroom-annot-interface directory
python3 manage.py shell
```
- copy paste the contents of `utils/feed_cn.py` in the shell
- close the shell (with CTRL+D)

Step 4. run the website:
```sh
# assuming you are in the mu-shroom-annot-interface directory
python3 manage.py runserver
```

Then open [the local annotation page](http://127.0.0.1/annotation)


### Some useful shell commands:

```python 
# human readable report
pd.DataFrame.from_records(Profile.objects.filter(language='XX').annotate(n_datapoint=Count('annotation')).values('annotator__username', 'annotator__email', 'n_datapoint'))
```
Sometimes when an annotator clicks too quickly, they can submit the same form twice, which creates a duplicate annotation.
```python
# delete dupes
for d_id, a_id in {k:v for k, v in Counter(Annotation.objects.filter(datapoint__language='XX').values_list('datapoint_id', 'annotator_id')).items()  if v > 1 }.keys():
    Annotation.objects.filter(id__in=Annotation.objects.filter(datapoint_id=d_id, annotator_id=a_id)[1:].values_list('id', flat=True)).delete()
```
