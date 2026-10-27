import io,wave
from backend import asr

def wav():
    buf=io.BytesIO()
    with wave.open(buf,'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000);w.writeframes(b'\x00'*3200)
    return buf.getvalue()
def test_invalid_type(client):assert client.post('/api/v1/grievances/analyze-audio',files={'file':('x.txt',b'test','text/plain')}).status_code==415

def test_invalid_signature(client):assert client.post('/api/v1/grievances/analyze-audio',files={'file':('x.wav',b'not audio','audio/wav')}).status_code==422

def test_missing_asr_is_explicit(client):
    r=client.post('/api/v1/grievances/analyze-audio',files={'file':('x.wav',wav(),'audio/wav')});assert r.status_code==503

def test_size_limit(client):
    r=client.post('/api/v1/grievances/analyze-audio',files={'file':('x.mp3',b'ID3'+b'0'*(10*1024*1024),'audio/mpeg')});assert r.status_code==413

def test_asr_contract_correction_and_submit(client,monkeypatch,auth):
    # Contract mock only: this does NOT establish real recognition accuracy.
    monkeypatch.setattr(asr,'transcribe_audio',lambda path, language=None:('water pipe leaking','en'))
    r=client.post('/api/v1/grievances/analyze-audio',files={'file':('x.wav',wav(),'audio/wav')}).json()
    assert r['transcript']=='water pipe leaking' and not r['stored']
    assert client.get('/api/v1/grievances',headers=auth).json()['count']==0
    assert client.post('/api/v1/grievances',json={'text':r['transcript']+' at school','source':'voice','location':{'district':'Chennai','place':'Adyar'}}).status_code==201


def test_language_hint_is_passed_to_asr(client,monkeypatch):
    seen={}
    def fake(path,language=None):
        seen['language']=language
        return 'தண்ணீர் குழாய் கசிகிறது','ta'
    monkeypatch.setattr(asr,'transcribe_audio',fake)
    r=client.post('/api/v1/grievances/analyze-audio',files={'file':('x.wav',wav(),'audio/wav')},data={'language':'Tamil'})
    assert r.status_code==200
    assert seen['language']=='Tamil'
    assert r.json()['selected_language']=='Tamil'
    assert r.json()['asr_language']=='ta'

def test_silence_contract(client,monkeypatch):
    def silent(path, language=None):raise ValueError('No speech detected')
    monkeypatch.setattr(asr,'transcribe_audio',silent)
    assert client.post('/api/v1/grievances/analyze-audio',files={'file':('x.wav',wav(),'audio/wav')}).status_code==422
