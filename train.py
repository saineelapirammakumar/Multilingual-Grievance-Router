"""Train only the frozen training partition; never fit on the held-out test partition."""
import sys,json,hashlib,platform
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import pandas as pd,joblib,sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline,FeatureUnion
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import MultiLabelBinarizer
from app.translation import feature_text
from app.classification import Classifier
from app.evaluation import evaluate
from app.schemas import DEPARTMENTS

def main():
    if not (ROOT/'data/annotated.csv').exists():
        from prepare_data import main as prepare
        prepare()
    from app.datasets import load_corpus
    tr,te,manifest=load_corpus()
    mlb=MultiLabelBinarizer(classes=DEPARTMENTS);y=mlb.fit_transform(tr.departments.str.split('|'))
    def vectorizer():
        return FeatureUnion([('word',TfidfVectorizer(ngram_range=(1,2),sublinear_tf=True)),
                             ('char',TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),sublinear_tf=True,min_df=2))],
                            transformer_weights={'word':1.0,'char':0.6})
    dept=Pipeline([('tfidf',vectorizer()),('clf',OneVsRestClassifier(LogisticRegression(max_iter=2500,class_weight='balanced',random_state=42)))])
    urg=Pipeline([('tfidf',vectorizer()),('clf',LogisticRegression(max_iter=2500,class_weight='balanced',random_state=42))])
    x=tr.text.map(feature_text);dept.fit(x,y);urg.fit(x,tr.urgency)
    root=ROOT/'models';root.mkdir(exist_ok=True)
    joblib.dump(dept,root/'department_model.joblib');joblib.dump(urg,root/'urgency_model.joblib');joblib.dump(DEPARTMENTS,root/'department_labels.joblib')
    metrics=evaluate(Classifier(),te,DEPARTMENTS)
    metrics['dataset_manifest']=manifest
    config={'model':'word-char-tfidf-logistic-v3','seed':42,'sklearn':sklearn.__version__,'python':platform.python_version(),
            'dataset_manifest':manifest,'dataset_sha256':manifest['dataset_sha256'],'synthetic_rows':manifest['synthetic_rows'],'train_rows':len(tr),'test_rows':len(te),'threshold':.5,
            'calibration':'not calibrated','deployment':'original train + 130 synthetic train only','hyperparameters':{'word_ngrams':[1,2],'char_ngrams':[3,5],'char_weight':0.6,'class_weight':'balanced','max_iter':2500}}
    config['model_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.glob('*.joblib')}
    (root/'model_config.json').write_text(json.dumps(config,indent=2));(root/'metrics.json').write_text(json.dumps(metrics,indent=2));(ROOT/'reports/baseline_grouped_metrics.json').write_text(json.dumps(metrics,indent=2));print(json.dumps(metrics,indent=2))
if __name__=='__main__':main()
