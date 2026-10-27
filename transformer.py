"""Optional frozen MuRIL encoder + learned logistic heads. CPU compatible, slower than TF-IDF."""
import json,os
from pathlib import Path
import joblib,numpy as np
class Encoder:
    def __init__(self,path):
        import torch
        from transformers import AutoTokenizer,AutoModel
        self.torch=torch;torch.set_num_threads(2)
        self.tokenizer=AutoTokenizer.from_pretrained(path,local_files_only=True,trust_remote_code=False,use_fast=False)
        self.model=AutoModel.from_pretrained(path,local_files_only=True,trust_remote_code=False).eval().to('cpu')
    def encode(self,texts):
        arrays=[]
        for i in range(0,len(texts),4):
            batch=self.tokenizer(texts[i:i+4],return_tensors='pt',padding=True,truncation=True,max_length=128)
            with self.torch.inference_mode():
                hidden=self.model(**batch).last_hidden_state;mask=batch['attention_mask'].unsqueeze(-1)
                mean=(hidden*mask).sum(1)/mask.sum(1).clamp(min=1)
            arrays.append(mean.cpu().numpy())
        return np.concatenate(arrays)
class TransformerClassifier:
    def __init__(self,path,encoder_path=None):
        path=Path(path);self.encoder=Encoder(encoder_path or os.getenv('MURIL_ENCODER_PATH',str(path/'encoder')))
        self.department=joblib.load(path/'department.joblib');self.urgency_model=joblib.load(path/'urgency.joblib')
        self.labels=json.loads((path/'config.json').read_text())['labels'];self._text=None;self._embedding=None
    def departments(self,text):
        q=self.department.predict_proba(self.encoder.encode([text]))[0]
        labels=[d for d,s in zip(self.labels,q) if s>=.5]
        if not labels and text.strip():labels=[self.labels[int(q.argmax())]]
        return labels,dict(zip(self.labels,map(float,q)))
    def urgency(self,text):
        q=self.urgency_model.predict_proba(self.encoder.encode([text]))[0]
        return str(self.urgency_model.classes_[q.argmax()]),dict(zip(map(str,self.urgency_model.classes_),map(float,q)))
    def coverage(self,text):return len(text.split())
    def evidence(self,text):
        # Actual perturbation sensitivity, never attention-as-causation. Bounded for CPU use.
        words=text.split();n=min(12,len(words));variants=[text]+[' '.join(words[:i]+words[i+1:]) for i in range(n)]
        x=self.encoder.encode(variants);dp=self.department.predict_proba(x);up=self.urgency_model.predict_proba(x)
        return {'method':'Leave-one-word-out probability change; local sensitivity, not causal evidence. First 12 words only; input truncated at 128 tokens.',
                'departments':{d:[{'term':words[i],'contribution':float(dp[0,j]-dp[i+1,j])} for i in range(n)] for j,d in enumerate(self.labels)},
                'urgency':{str(d):[{'term':words[i],'contribution':float(up[0,j]-up[i+1,j])} for i in range(n)] for j,d in enumerate(self.urgency_model.classes_)}}
