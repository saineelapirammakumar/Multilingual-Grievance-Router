import json
from pathlib import Path
import pandas as pd
import pytest
from app.language_id import detect_language
from app.translation import normalize,feature_text
from app.urgency import safety_details
from app.classification import Classifier
from app.pipeline import Pipeline
from app.routing import route
from app.duplicates import find_duplicates
@pytest.mark.parametrize('text,label',[('road near school','English'),('தண்ணீர் வரவில்லை','Tamil'),('पानी नहीं आ रहा','Hindi'),('street la water varala','Tanglish'),('paani nahi aa raha','Hinglish')])
def test_language(text,label):assert detect_language(text)['language']==label and detect_language(text)['confidence'] is None

def test_normalizer_boundaries():
    assert normalize('painting road')=='painting road'
    assert 'water' in normalize('PAANI nahi aa raha')
    assert 'தண்ணீர்' in feature_text('தண்ணீர் வரவில்லை')

def test_safety_and_negation_warning():
    u,r,c=safety_details('live wire was repaired yesterday','Routine');assert u=='Emergency' and r and c
    assert safety_details('live wire near school','Routine')[0]=='Emergency'
    assert safety_details('no water coming','Routine')[0]=='Urgent'

def test_uncertainty_and_evidence():
    p=Pipeline(Classifier());r=p.run('zzzz qqqq');assert r['review_required'] and not r['departments']
    r=p.run('water pipe leaking');assert r['explanations']['departments'] and r['inference_ms']>0

def test_routing_ambiguity():
    r=route({},['Roads'],'Near School Road and Lake Colony');assert r['review_required'] and len(r['suggestions'])==2
    assert route({'municipality':'Demo Municipality','ward':'1','area':'School Road'},['Roads'])['demonstration_only']

def test_cross_language_duplicate_fallback(monkeypatch):
    monkeypatch.delenv('SENTENCE_MODEL_PATH',raising=False)
    records=[{'id':'a','original_text':'Water pipe leak near school','location':{}}]
    r=find_duplicates('School pakkam water pipe leak aaguthu',{},records,threshold=.2)
    assert r['items'][0]['id']=='a' and r['warning'] and r['mode']=='lexical-normalized-tfidf-fallback'

def test_split_no_leakage():
    root=Path(__file__).resolve().parents[1];df=pd.read_csv(root/'data/annotated.csv')
    train=df[df.split=='train'];test=df[df.split=='test']
    assert not set(train.group_id)&set(test.group_id)
    assert not set(train.text)&set(test.text)
    assert len(train)+len(test)==87

def test_tentative_fallback_is_labeled():
    r=Pipeline(Classifier()).run('street la water varala')
    assert r['departments'] and r['review_required']
    if max(r['department_scores'].values())<.5:assert any('Tentative' in s for s in r['warnings'])


def test_tanglish_urgency_regression_examples():
    pipeline = Pipeline(Classifier())
    routine = pipeline.run("Enga area la street light work aagala. Please repair it when possible.")
    urgent = pipeline.run("Enga area la street light work aagala. Innaiku night romba dark ah irukku, people road la safe ah poga mudiyala.")
    emergency = pipeline.run("Street light work aagala. Ippo road la accident nadanthirukku, people injured ah irukanga. Immediate help venum.")
    assert routine["urgency"] != "Emergency"
    assert urgent["urgency"] in ("Urgent", "Emergency")
    assert emergency["urgency"] == "Emergency"
    assert "accident_with_injury" in emergency["safety_rules"]


def test_initializer_template_exists_and_preserves_secret(tmp_path):
    from scripts.init_local import initialize
    assert initialize(tmp_path)
    env = (tmp_path / ".env").read_text()
    assert len(next(line for line in env.splitlines() if line.startswith("ADMIN_TOKEN=")).split("=",1)[1]) >= 32
    assert initialize(tmp_path) is False
    assert (tmp_path / ".env").read_text() == env


def test_tanglish_unsafe_access_requires_review():
    result = Pipeline(Classifier()).run(
        "Enga area la street light work aagala. Innaiku night romba dark ah irukku, people road la safe ah poga mudiyala."
    )
    assert result["urgency"] in ("Urgent", "Emergency")
    assert result["review_required"]
    assert any("Safety-related" in warning or "Emergency triage" in warning for warning in result["warnings"])
