"""Executable frozen-encoder comparison; requires a separately downloaded local MuRIL snapshot."""
import sys,json,argparse,hashlib,random
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--encoder',required=True,help='Local google/muril-base-cased snapshot');parser.add_argument('--revision',required=True,help='Actual downloaded model commit SHA');args=parser.parse_args()
    import re
    if not re.fullmatch(r'[0-9a-f]{40}',args.revision):parser.error('Use the actual 40-character encoder commit SHA')
    import numpy as np,pandas as pd,joblib,torch
    from sklearn.linear_model import LogisticRegression
    from sklearn.multiclass import OneVsRestClassifier
    from app.transformer import Encoder,TransformerClassifier
    from app.translation import feature_text
    from app.evaluation import evaluate
    from app.schemas import DEPARTMENTS
    random.seed(42);np.random.seed(42);torch.manual_seed(42)
    from app.datasets import load_corpus
    tr,te,manifest=load_corpus()
    encoder=Encoder(args.encoder);x=encoder.encode(tr.text.map(feature_text).tolist())
    y=np.array([[int(d in ds.split('|')) for d in DEPARTMENTS] for ds in tr.departments])
    dept=OneVsRestClassifier(LogisticRegression(max_iter=2500,class_weight='balanced',random_state=42)).fit(x,y)
    urg=LogisticRegression(max_iter=2500,class_weight='balanced',random_state=42).fit(x,tr.urgency)
    out=ROOT/'models/transformer';out.mkdir(parents=True,exist_ok=True)
    # Keep large pretrained weights external; final ZIP contains only the fitted heads.
    joblib.dump(dept,out/'department.joblib');joblib.dump(urg,out/'urgency.joblib')
    config={'model_id':'google/muril-base-cased','revision':args.revision,'strategy':'frozen mean-pooled MuRIL + logistic heads; not end-to-end fine-tuning','labels':DEPARTMENTS,'seed':42,'split_manifest':manifest,'max_length':128,'calibrated':False}
    (out/'config.json').write_text(json.dumps(config,indent=2))
    metrics=evaluate(TransformerClassifier(out,encoder_path=args.encoder),te,DEPARTMENTS)
    metrics['dataset_manifest']=manifest
    (out/'metrics.json').write_text(json.dumps(metrics,indent=2));(ROOT/'reports/transformer_metrics.json').write_text(json.dumps(metrics,indent=2))
    print('Comparison complete. Review reports before explicitly setting MODEL_BACKEND=transformer. No automatic deployment.')
if __name__=='__main__':main()
