"""Evaluate a separately collected human-labeled CSV without modifying training data."""
import argparse,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import pandas as pd
from app.datasets import load_corpus,sha
from app.classification import Classifier
from app.evaluation import evaluate
from app.schemas import DEPARTMENTS

def main():
    p=argparse.ArgumentParser();p.add_argument('--csv',required=True);p.add_argument('--model',choices=['baseline','muril'],default='baseline');p.add_argument('--encoder');p.add_argument('--output',required=True);a=p.parse_args()
    test=pd.read_csv(a.csv);required={'row_id','text','departments','urgency','language','group_id','provenance','synthetic_status'}
    if not required.issubset(test.columns) or test.empty:raise ValueError('Nonempty CSV with the documented independent evaluation schema required')
    if not (test.provenance=='independent_human').all() or not (test.synthetic_status=='real').all():raise ValueError('Independent evaluation requires declared independently collected human-labeled real examples; do not relabel synthetic data')
    train,old,manifest=load_corpus()
    if set(test.group_id)&set(train.group_id) or set(test.text.str.casefold())&set(train.text.str.casefold()):raise ValueError('Evaluation overlap with training detected')
    if test.row_id.duplicated().any() or test[list(required)].isna().any().any():raise ValueError('Duplicate IDs or missing fields')
    if any(not set(x.split('|'))<=set(DEPARTMENTS) for x in test.departments):raise ValueError('Unknown department')
    if a.model=='muril':
        from app.transformer import TransformerClassifier
        clf=TransformerClassifier(ROOT/'models/transformer',encoder_path=a.encoder)
    else:clf=Classifier()
    report=evaluate(clf,test,DEPARTMENTS);report['evaluation_file_sha256']=sha(a.csv);report['dataset_manifest']=manifest
    report['warning']='Declared independent human data; provenance requires external verification. Automated overlap checks cannot detect every paraphrase.'
    Path(a.output).write_text(json.dumps(report,ensure_ascii=False,indent=2));print('Saved measured evaluation:',a.output)
if __name__=='__main__':main()
