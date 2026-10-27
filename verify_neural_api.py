"""Real optional-model integration checks; run explicitly after downloading models."""
import argparse,os,sys,tempfile,json,wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from fastapi.testclient import TestClient
from backend import create_app

def main():
    p=argparse.ArgumentParser();p.add_argument('--asr-path',required=True);p.add_argument('--sentence-path',required=True);p.add_argument('--muril-path',required=True);a=p.parse_args()
    os.environ.update(ASR_MODEL_PATH=str(Path(a.asr_path).resolve()),SENTENCE_MODEL_PATH=str(Path(a.sentence_path).resolve()),MURIL_ENCODER_PATH=str(Path(a.muril_path).resolve()),ADMIN_TOKEN='local-neural-test-'+'x'*40,EMAIL_ENABLED='false',MODEL_BACKEND='baseline')
    checks={};auth={'Authorization':'Bearer '+os.environ['ADMIN_TOKEN']}
    with tempfile.TemporaryDirectory() as d:
        with TestClient(create_app(f'sqlite:///{d}/neural.db')) as c:
            for file in ['civic_wire.wav','civic_water.mp3']:
                with (ROOT/'data/audio_samples'/file).open('rb') as stream:
                    response=c.post('/api/v1/grievances/analyze-audio',files={'file':(file,stream,'audio/wav' if file.endswith('wav') else 'audio/mpeg')})
                assert response.status_code==200,response.text
                checks[file]={'status':response.status_code,'transcript':response.json()['transcript']}
                stored=c.post('/api/v1/grievances',json={'text':response.json()['transcript'],'source':'voice'});assert stored.status_code==201
            silent=Path(d)/'silence.wav'
            with wave.open(str(silent),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000);w.writeframes(b'\0'*16000*2*3)
            with silent.open('rb') as f:r=c.post('/api/v1/grievances/analyze-audio',files={'file':('silence.wav',f,'audio/wav')})
            assert r.status_code==422,r.text;checks['real_silence_rejected']=True
            long=Path(d)/'long.wav'
            with wave.open(str(long),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000);w.writeframes(b'\0'*16000*2*121)
            with long.open('rb') as f:r=c.post('/api/v1/grievances/analyze-audio',files={'file':('long.wav',f,'audio/wav')})
            assert r.status_code==422,r.text;checks['over_duration_rejected']=True
            x=c.post('/api/v1/grievances',json={'text':'The streetlight outside the library is broken'}).json()
            y=c.post('/api/v1/grievances',json={'text':'पुस्तकालय के बाहर की स्ट्रीट लाइट खराब है'}).json()
            result=c.get('/api/v1/grievances/'+y['id']+'/duplicates',headers=auth).json()
            assert result['mode']=='multilingual-sentence-transformer';checks['real_neural_retrieval']=result
        os.environ['MODEL_BACKEND']='transformer'
        with TestClient(create_app(f'sqlite:///{d}/transformer.db')) as c:
            assert c.get('/health').json()['model_ready']
            r=c.post('/api/v1/grievances',json={'text':'The street light is broken'});assert r.status_code==201,r.text
            assert 'Leave-one-word' in r.json()['explanations']['method'];checks['muril_submission_and_explanations']=True
    (ROOT/'reports/neural_api_results.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2));print('Real neural API checks passed')
if __name__=='__main__':main()
