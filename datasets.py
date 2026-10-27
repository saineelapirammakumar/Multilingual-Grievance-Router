"""Shared leakage checks and training corpus for both model families."""
import json,hashlib
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load_corpus():
    manifest=json.loads((ROOT/'data/split_manifest.json').read_text())
    if sha(ROOT/'data/annotated.csv')!=manifest['dataset_sha256']:raise ValueError('Original dataset changed; review/version the manifest')
    original=pd.read_csv(ROOT/'data/annotated.csv');syn=pd.read_csv(ROOT/'data/synthetic_train.csv')
    train=original[original.row_id.isin(manifest['train_ids'])].copy();test=original[original.row_id.isin(manifest['test_ids'])].copy()
    if set(syn.group_id)&set(test.group_id):raise ValueError('Synthetic family overlaps held-out test')
    if not set(syn.group_id).issubset(set(train.group_id)):raise ValueError('Synthetic family not reviewed against original training groups')
    if set(syn.text.str.casefold())&set(test.text.str.casefold()):raise ValueError('Exact synthetic test leakage')
    if not (syn.synthetic_status=='synthetic').all() or not (syn.split=='train').all():raise ValueError('Synthetic provenance/split invalid')
    combined=pd.concat([train,syn],ignore_index=True)
    if combined.row_id.duplicated().any():raise ValueError('Duplicate row IDs')
    manifest={**manifest,'synthetic_sha256':sha(ROOT/'data/synthetic_train.csv'),'training_rows':len(combined),'synthetic_rows':len(syn),
              'test_sha256':hashlib.sha256(test[['row_id','text','departments','urgency','language']].to_csv(index=False).encode()).hexdigest(),
              'evaluation_origin':'inherited demonstration holdout; not independent human evaluation'}
    return combined,test,manifest
