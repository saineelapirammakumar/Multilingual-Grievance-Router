import time
import numpy as np
from sklearn.metrics import precision_recall_fscore_support,hamming_loss,classification_report,confusion_matrix,multilabel_confusion_matrix,accuracy_score
from .translation import feature_text,normalize
from .urgency import safety_details
URGENCIES=['Routine','Urgent','Emergency']
def evaluate(clf,test,labels):
    y=np.array([[int(d in ds.split('|')) for d in labels] for ds in test.departments]);pred=[];learned=[];safe=[];latency=[]
    for text in test.text:
        start=time.perf_counter();ds,_=clf.departments(feature_text(text));u,_=clf.urgency(feature_text(text))
        pred.append([int(d in ds) for d in labels]);learned.append(u);safe.append(safety_details(normalize(text),u)[0]);latency.append((time.perf_counter()-start)*1000)
    pred=np.asarray(pred)
    def subset(indices):
        ix=np.asarray(indices);out={'support':int(len(ix))}
        for avg in ['micro','macro']:
            p,r,f,_=precision_recall_fscore_support(y[ix],pred[ix],average=avg,zero_division=0)
            out.update({f'department_{avg}_precision':float(p),f'department_{avg}_recall':float(r),f'department_{avg}_f1':float(f)})
        out['department_exact_match_accuracy']=float(accuracy_score(y[ix],pred[ix]))
        out['department_hamming_loss']=float(hamming_loss(y[ix],pred[ix]))
        gold=test.urgency.to_numpy()[ix]
        for name,values in [('learned',learned),('with_safety_rules',safe)]:
            vals=np.asarray(values)[ix];report=classification_report(gold,vals,labels=URGENCIES,output_dict=True,zero_division=0)
            out[name]={'urgency_report':report,'confusion_matrix':confusion_matrix(gold,vals,labels=URGENCIES).tolist(),
                       'emergency_recall':report['Emergency']['recall'] if report['Emergency']['support'] else None}
        return out
    result=subset(np.arange(len(test)))
    from .language_id import detect_language
    detected=[detect_language(t)['language'] for t in test.text]
    result['language_identification_report']=classification_report(test.language,detected,output_dict=True,zero_division=0)
    result['department_policy']='threshold 0.5; tentative top-label fallback with recognized vocabulary; human review below 0.65'
    result['missing_language_evaluations']=[lang for lang in ['English','Hindi','Tamil','Hinglish','Tanglish'] if lang not in set(test.language)]
    result.update({'language_wise':{lang:subset(np.flatnonzero(test.language.to_numpy()==lang)) for lang in sorted(test.language.unique())},
                   'department_confusion_matrices':dict(zip(labels,multilabel_confusion_matrix(y,pred).tolist())),
                   'urgency_label_order':URGENCIES,'inference_latency_ms':{'mean':float(np.mean(latency)),'p95':float(np.percentile(latency,95)),
                   'scope':'department + urgency + rules; excludes database, ASR, explanations and embedding retrieval'},
                   'test_ids':test.row_id.tolist(),'warning':'Small supplied demo dataset; not real-world accuracy. Absent language/classes cannot be evaluated.'})
    return result
