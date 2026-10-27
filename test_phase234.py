import json
from pathlib import Path
import pytest
from app.datasets import load_corpus
from app.schemas import DEPARTMENTS
from app.pipeline import Pipeline
from app.classification import Classifier
ROOT=Path(__file__).resolve().parents[1]

def test_synthetic_provenance_and_holdout_separation():
    train,test,manifest=load_corpus();syn=train[train.synthetic_status=='synthetic']
    assert len(train)==195 and len(test)==22 and len(syn)==130
    assert syn.language.value_counts().to_dict()=={x:26 for x in ['English','Hindi','Tamil','Hinglish','Tanglish']}
    assert not set(train.group_id)&set(test.group_id)
    assert not set(syn.text)&set(test.text)
    assert set(syn.provenance)=={'ai_authored_synthetic'}
    assert all(set(d.split('|'))<=set(DEPARTMENTS) for d in syn.departments)
    assert set(syn.urgency)=={'Routine','Urgent','Emergency'}

@pytest.mark.parametrize('text',[
 'The STREETLIGHT is broken!!!',
 'पुस्तकालय के बाहर की स्ट्रीट लाइट खराब है।',
 'பொது கழிப்பறை அழுக்காக உள்ளது',
 'school pakkam water pipe leak aaguthu',
 'bijli ka taar neeche latak raha hai',
 '🙂🙂', 'zzzz qqqq', 'water\u200b pipe leak',
 'The live wire was repaired yesterday; there is no longer a danger.'
])
def test_multilingual_edge_contract(text):
    r=Pipeline(Classifier()).run(text)
    assert r['original_text']==text and r['urgency'] in ['Routine','Urgent','Emergency']
    assert all(0<=score<=1 for score in r['department_scores'].values())
    assert set(r['departments'])<=set(DEPARTMENTS)
    assert r['language_confidence'] is None
    if 'yesterday' in text:assert any('historical' in w for w in r['warnings'])

def test_char_feature_explanations_match_fitted_features():
    clf=Classifier();r=clf.evidence('streetlight broken')
    assert 'word__' in ' '.join(t['term'] for values in r['departments'].values() for t in values)
    assert clf.department.named_steps['tfidf'].get_params()['char__analyzer']=='char_wb'

def test_optional_comparison_uses_same_data():
    path=ROOT/'reports/transformer_metrics.json'
    if not path.exists():pytest.skip('Optional comparison has not run')
    a=json.loads((ROOT/'reports/baseline_grouped_metrics.json').read_text());b=json.loads(path.read_text())
    assert a['test_ids']==b['test_ids'] and a['dataset_manifest']==b['dataset_manifest']
    assert 'department_exact_match_accuracy' in a and 'department_exact_match_accuracy' in b

def test_word_error_distance():
    from scripts.evaluate_optional import distance,clean
    assert distance(['water','pipe'],['water','leak'])==1
    assert clean('WATER, pipe!')=='water pipe'
