import json
import pytest
from app.store import Grievance,Notification
LOC={'district':'Chennai','place':'Adyar','municipality':'Demo Municipality','ward':'1','area':'School Road'}
def submit(c,text='Water pipe leaking near school',**extra):
    r=c.post('/api/v1/grievances',json={'text':text,'location':LOC,**extra});assert r.status_code==201,r.text;return r.json()
def test_private_submission_and_listing(client,auth):
    r=submit(client);url='/api/v1/grievances/'+r['id']
    assert len(r['id'])==36
    assert client.get(url).status_code==404
    assert client.get(url,headers={'X-Tracking-Token':'wrong'}).status_code==404
    read=client.get(url,headers={'X-Tracking-Token':r['tracking_token']}).json()
    assert read['notifications'][0]['delivery']=='local'
    assert 'tracking_token' not in read and 'audit' not in read
    assert client.get('/api/v1/grievances').status_code==401
    assert client.get('/api/v1/grievances',headers=auth).json()['count']==1
    with client.app.state.Session() as s:
        g=s.get(Grievance,r['id']);assert g.token_hash!=r['tracking_token'];assert not g.email

def test_full_lifecycle_and_original_prediction(client,auth):
    r=submit(client);original=r['original_prediction'];url='/api/v1/grievances/'+r['id']
    for status in ['Assigned','In Progress','Resolved','Reopened','Assigned','Rejected']:
        payload={'expected_version':r['version'],'status':status,'assigned_department':'Water Supply','departments':['Water Supply'],'urgency':'Routine','note':'Reviewed by official','resolution':'Pipe repaired' if status=='Resolved' else None}
        response=client.patch(url,json=payload,headers=auth);assert response.status_code==200,response.text;r=response.json()
        assert r['original_prediction']==original and r['status']==status
    assert client.get(url,headers=auth).json()['audit'][-1]['kind']=='feedback'
    exported=client.get('/api/v1/feedback/export',headers=auth).json();assert len(exported['items'])==6

def test_invalid_updates_and_version_conflict(client,auth):
    r=submit(client);url='/api/v1/grievances/'+r['id'];base={'expected_version':1,'note':'Reviewed'}
    assert client.patch(url,json={**base,'status':'Resolved','resolution':'done'},headers=auth).status_code==409
    assert client.patch(url,json={**base,'status':'Assigned'},headers=auth).status_code==422
    assert client.patch(url,json=base).status_code==401
    assert client.patch(url,json={**base,'departments':['Made Up']},headers=auth).status_code==422
    assert client.patch(url,json=base,headers=auth).status_code==200
    assert client.patch(url,json=base,headers=auth).status_code==409

@pytest.mark.parametrize('payload',[{'text':'  '},{'text':'x'*5001},{'text':'water','location':{'latitude':95}},{'text':'water','location':{'latitude':10}},{'text':'water','email':'a\r\nb@x.com'},{'text':'water','source':'invalid'}])
def test_input_validation(client,payload):assert client.post('/api/v1/grievances',json=payload).status_code==422

def test_oversized_json(client):assert client.post('/api/v1/grievances',content='{"text":"'+'x'*33000+'"}',headers={'Content-Type':'application/json'}).status_code==413

def test_search_pagination_analytics(client,auth):
    submit(client);submit(client,'Live wire near school')
    result=client.get('/api/v1/grievances',headers=auth,params={'limit':1}).json();assert result['count']==2 and len(result['items'])==1
    assert result['items'][0]['urgency']=='Emergency'
    assert client.get('/api/v1/grievances',headers=auth,params={'q':'unfindable'}).json()['count']==0
    assert client.get('/api/v1/analytics',headers=auth).json()['total']==2
    assert client.get('/api/v1/analytics').status_code==401

def test_duplicate_review_preserves_originals(client,auth):
    a=submit(client);b=submit(client)
    url='/api/v1/grievances/'+a['id']+'/duplicates'
    assert client.get(url).status_code==401
    possible=client.get(url,headers=auth).json();assert possible['items'][0]['id']==b['id'];assert possible['items'][0]['similarity']>.99
    r=client.post(url,headers=auth,json={'other_id':b['id'],'note':'Same issue confirmed'});assert r.status_code==200
    assert client.get('/api/v1/grievances',headers=auth).json()['count']==2
    assert client.post(url,headers=auth,json={'other_id':a['id'],'note':'self'}).status_code==422

def test_location_correction_and_privacy(client,auth):
    a=submit(client,location={'district':'Chennai','place':'Adyar'});assert a['routing']['review_required']
    b=submit(client);assert 'possible_duplicates' not in b
    url='/api/v1/grievances/'+a['id']
    r=client.patch(url,headers=auth,json={'expected_version':1,'location':LOC,'note':'Verified address'});assert r.status_code==200 and r.json()['location']=={**LOC,'latitude':None,'longitude':None}

def test_rate_limit(client,monkeypatch):
    monkeypatch.setenv('RATE_LIMIT_PER_MINUTE','1');submit(client)
    assert client.post('/api/v1/predict',json={'text':'pipe leaking'}).status_code==429

def test_health_and_system(client,auth):
    assert client.get('/health').json()['model_ready']
    assert client.get('/api/v1/system').status_code==401
    assert client.get('/api/v1/system',headers=auth).json()['asr_configured'] is False

def test_no_admin_default(client,monkeypatch):
    monkeypatch.delenv('ADMIN_TOKEN');assert client.get('/api/v1/grievances').status_code==503

def test_outbox_retry_idempotent(client,auth):
    submit(client)
    for _ in range(2):assert client.post('/api/v1/notifications/dispatch',headers=auth).status_code==200
    with client.app.state.Session() as s:
        n=s.query(Notification).one();assert n.attempts==1 and n.delivery=='local'

def test_duplicate_candidates_audited_privately(client,auth):
    a=submit(client);b=submit(client)
    detail=client.get('/api/v1/grievances/'+b['id'],headers=auth).json()
    evidence=next(x for x in detail['audit'] if x['kind']=='duplicate-candidates')
    assert evidence['payload']['items'][0]['id']==a['id']
    citizen=client.get('/api/v1/grievances/'+b['id'],headers={'X-Tracking-Token':b['tracking_token']}).json()
    assert a['id'] not in json.dumps(citizen)

def test_tamil_nadu_locations_endpoint(client):
    data=client.get('/api/v1/locations/tamil-nadu').json()
    assert len(data)==38
    assert 'Tumakuru' not in data
    assert 'Chennai' in data and 'Adyar' in data['Chennai']

def test_submission_requires_valid_district_and_place(client):
    assert client.post('/api/v1/grievances',json={'text':'Water pipe leaking','location':LOC|{'district':'','place':''}}).status_code==422
    assert client.post('/api/v1/grievances',json={'text':'Water pipe leaking','location':LOC|{'district':'Chennai','place':'Pollachi'}}).status_code==422

def test_unsolvable_flag_is_official_audited_and_does_not_change_status(client,auth):
    r=submit(client)
    url=f"/api/v1/grievances/{r['id']}/unsolvable"
    assert client.post(url,json={'expected_version':r['version'],'reason':'Cannot be resolved'}).status_code==401
    assert client.post(url,headers=auth,json={'expected_version':r['version'],'reason':'No'}).status_code==422
    flagged=client.post(url,headers=auth,json={'expected_version':r['version'],'reason':'Outside municipal authority'} )
    assert flagged.status_code==200,flagged.text
    data=flagged.json()
    assert data['is_unsolvable'] is True
    assert data['unsolvable_reason']=='Outside municipal authority'
    assert data['status']=='Submitted'
    detail=client.get(f"/api/v1/grievances/{r['id']}",headers=auth).json()
    assert any(e['kind']=='marked-unsolvable' for e in detail['audit'])
    analytics=client.get('/api/v1/analytics',headers=auth).json()
    assert analytics['solvability']=={'solvable':0,'unsolvable':1}
    assert client.post(url,headers=auth,json={'expected_version':r['version'],'reason':'Another reason'}).status_code==409
