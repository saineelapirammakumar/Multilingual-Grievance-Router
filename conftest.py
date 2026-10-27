import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pytest
from fastapi.testclient import TestClient
from backend import create_app
@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setenv('ADMIN_TOKEN','test-token-'+'x'*40);monkeypatch.setenv('EMAIL_ENABLED','false');monkeypatch.setenv('RATE_LIMIT_PER_MINUTE','1000');monkeypatch.delenv('ASR_MODEL_PATH',raising=False);monkeypatch.delenv('SENTENCE_MODEL_PATH',raising=False);monkeypatch.setenv('MODEL_BACKEND','baseline')
    with TestClient(create_app(f'sqlite:///{tmp_path}/test.db')) as c:yield c
@pytest.fixture
def auth():return {'Authorization':'Bearer '+'test-token-'+'x'*40}
