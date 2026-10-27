import json
from fastapi.testclient import TestClient
from backend import create_app
from app.store import initialize
from sqlalchemy import text

def test_migration_idempotent(tmp_path):
    url=f'sqlite:///{tmp_path}/db.sqlite'
    for _ in range(2):
        e,s=initialize(url)
        with e.connect() as c:assert c.execute(text('SELECT COUNT(*) FROM schema_migrations')).scalar()==2
        e.dispose()

def test_restart_persistence_including_unsolvable_decision(tmp_path,monkeypatch):
    monkeypatch.setenv('EMAIL_ENABLED','false');monkeypatch.setenv('ADMIN_TOKEN','test-token-'+'x'*40);url=f'sqlite:///{tmp_path}/db.sqlite'
    auth={'Authorization':'Bearer '+'test-token-'+'x'*40}
    with TestClient(create_app(url)) as c:
        r=c.post('/api/v1/grievances',json={'text':'Water pipe leak','location':{'district':'Chennai','place':'Adyar'}}).json()
        assert r['id']
        flagged=c.post(f"/api/v1/grievances/{r['id']}/unsolvable",headers=auth,json={'expected_version':r['version'],'reason':'Outside municipal authority'})
        assert flagged.status_code==200,flagged.text
    with TestClient(create_app(url)) as c:
        detail=c.get('/api/v1/grievances/'+r['id'],headers={'X-Tracking-Token':r['tracking_token']}).json()
        assert detail['original_text']=='Water pipe leak'
        assert detail['is_unsolvable'] is True and detail['unsolvable_reason']=='Outside municipal authority'
        assert detail['status']=='Submitted'

def test_missing_model_degradation(tmp_path,monkeypatch):
    monkeypatch.setenv('MODEL_DIR',str(tmp_path/'absent'))
    with TestClient(create_app(f'sqlite:///{tmp_path}/db.sqlite')) as c:
        assert c.get('/health').json()['status']=='degraded'
        assert c.post('/api/v1/grievances',json={'text':'Water leak','location':{'district':'Chennai','place':'Adyar'}}).status_code==503

def test_initializer_preserves_existing_secret(tmp_path):
    from scripts.init_local import initialize
    assert initialize(tmp_path)
    original=(tmp_path/'.env').read_text()
    assert len(next(x for x in original.splitlines() if x.startswith('ADMIN_TOKEN=')).split('=',1)[1])>=32
    assert not initialize(tmp_path) and (tmp_path/'.env').read_text()==original
