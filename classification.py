from pathlib import Path
import joblib
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
class Classifier:
    def __init__(self,model_dir=None):
        root=Path(model_dir or ROOT/'models')
        self.department=joblib.load(root/'department_model.joblib')
        self.urgency_model=joblib.load(root/'urgency_model.joblib')
        self.labels=joblib.load(root/'department_labels.joblib')
    def departments(self,text):
        q=self.department.predict_proba([text])[0]
        labels=[x for x,v in zip(self.labels,q) if v>=.5]
        # Retain the original application's top-label fallback, but only with recognized features.
        # Pipeline marks every below-threshold fallback as tentative and requiring review.
        if not labels and self.coverage(text)>0:labels=[self.labels[int(q.argmax())]]
        return labels,{x:float(v) for x,v in zip(self.labels,q)}
    def urgency(self,text):
        q=self.urgency_model.predict_proba([text])[0]
        return str(self.urgency_model.classes_[q.argmax()]),{str(x):float(v) for x,v in zip(self.urgency_model.classes_,q)}
    def evidence(self,text):
        def contributions(model,coefs):
            vec=model.named_steps['tfidf']; x=vec.transform([text]); names=vec.get_feature_names_out()
            result={}
            for label,coef in coefs:
                terms=[{'term':str(names[j]),'contribution':float(x[0,j]*coef[j])} for j in x.indices]
                result[label]=sorted(terms,key=lambda z:abs(z['contribution']),reverse=True)[:8]
            return result
        clf=self.department.named_steps['clf']; urg=self.urgency_model.named_steps['clf']
        return {'method':'TF-IDF × linear coefficient (logit contribution; not a causal explanation)',
                'departments':contributions(self.department,[(d,e.coef_[0]) for d,e in zip(self.labels,clf.estimators_)]),
                'urgency':contributions(self.urgency_model,list(zip(urg.classes_,urg.coef_)))}
    def coverage(self,text):
        return int(self.department.named_steps['tfidf'].transform([text]).nnz)
