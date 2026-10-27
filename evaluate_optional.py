"""Measured optional-model diagnostics. Synthetic fixtures are never independent benchmarks."""
import sys,os,json,time,re,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from sklearn.metrics import accuracy_score,precision_recall_fscore_support,confusion_matrix

def distance(a,b):
    row=list(range(len(b)+1))
    for i,x in enumerate(a,1):
        new=[i]
        for j,y in enumerate(b,1):new.append(min(new[-1]+1,row[j]+1,row[j-1]+(x!=y)))
        row=new
    return row[-1]
def clean(text):return ' '.join(re.findall(r'\w+',text.casefold(),flags=re.UNICODE))
def speech():
    from app.asr import transcribe_audio,get_model
    if not os.getenv('ASR_MODEL_PATH'):return {'status':'not_run','reason':'ASR_MODEL_PATH is not configured'}
    start=time.perf_counter()
    try:get_model(os.environ['ASR_MODEL_PATH'])
    except Exception as e:return {'status':'failed','reason':str(e)}
    load_ms=(time.perf_counter()-start)*1000;items=[];word_errors=char_errors=words=chars=0
    for sample in json.loads((ROOT/'data/audio_samples/manifest.json').read_text()):
        start=time.perf_counter();transcript,lang=transcribe_audio(str(ROOT/'data/audio_samples'/sample['file']));elapsed=(time.perf_counter()-start)*1000
        ref=clean(sample['reference']);hyp=clean(transcript);we=distance(ref.split(),hyp.split());ce=distance(ref,hyp)
        words+=len(ref.split());chars+=len(ref);word_errors+=we;char_errors+=ce
        items.append({**sample,'transcript':transcript,'asr_language':lang,'word_error_rate':we/len(ref.split()),'character_error_rate':ce/len(ref),'inference_ms':elapsed})
    return {'status':'executed','model_load_ms':load_ms,'micro_wer':word_errors/words,'micro_cer':char_errors/chars,'items':items,'warning':'Three English functional fixtures only, two synthetic and one familiar public upstream sample. Not independent ASR accuracy; Hindi/Tamil/code-mixed speech unmeasured.'}
def semantic():
    from app.duplicates import score_candidates,load_encoder
    pairs=json.loads((ROOT/'data/semantic_pairs.json').read_text());path=os.getenv('SENTENCE_MODEL_PATH');results={}
    for mode in ['fallback','neural']:
        if mode=='neural' and not path:results[mode]={'status':'not_run'};continue
        if mode=='fallback':os.environ.pop('SENTENCE_MODEL_PATH',None)
        else:os.environ['SENTENCE_MODEL_PATH']=path
        model_load_ms=0
        if mode=='neural':
            start=time.perf_counter()
            try:load_encoder(path)
            except Exception as e:results[mode]={'status':'failed','reason':str(e)};continue
            model_load_ms=(time.perf_counter()-start)*1000
        items=[]
        for pair in pairs:
            scores,actual,warning,ms=score_candidates(pair['a'],[pair['b']]);score=float(scores[0])
            if mode=='neural' and actual!='multilingual-sentence-transformer':raise RuntimeError('Neural evaluation unexpectedly fell back')
            items.append({**pair,'similarity':score,'predicted_duplicate':int(score>=.65),'inference_ms':ms})
        gold=[x['label'] for x in items];pred=[x['predicted_duplicate'] for x in items];precision,recall,f1,_=precision_recall_fscore_support(gold,pred,average='binary',zero_division=0)
        results[mode]={'status':'executed','threshold':.65,'accuracy':accuracy_score(gold,pred),'precision':precision,'recall':recall,'f1':f1,'confusion_matrix':confusion_matrix(gold,pred,labels=[0,1]).tolist(),'model_load_ms':model_load_ms,'mean_inference_ms':float(np.mean([x['inference_ms'] for x in items])),'items':items}
    if path:os.environ['SENTENCE_MODEL_PATH']=path
    return {'kind':'AI-authored synthetic diagnostic pairs; no threshold tuning and no independent quality claim','results':results}
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--asr-path');parser.add_argument('--sentence-path');args=parser.parse_args()
    if args.asr_path:os.environ['ASR_MODEL_PATH']=args.asr_path
    if args.sentence_path:os.environ['SENTENCE_MODEL_PATH']=args.sentence_path
    report={'speech':speech(),'semantic':semantic()}
    (ROOT/'reports/optional_evaluation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({k:v.get('status',v.get('kind')) for k,v in report.items()},indent=2))
if __name__=='__main__':main()
