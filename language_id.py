"""Transparent script/lexicon fallback; no invented probability estimates."""
import re
TAMIL=set('thanni tanni thanneer varala varalai kuz hai kuzhai kuppai saalai irukku aagala aaguthu aagudhu pakkam pakkathula mela vizhundhu vizhundhuduchu sakkadai pannala romba naala la'.split())
HINDI=set('paani pani nahi nahin raha rahi gali kachra bijli taar sadak naali ganda gir gaya gayi hai bahut teen din uthaya ke paas kharab'.split())
def detect_language(text):
    tokens=set(re.findall(r'[a-z]+',text.lower()))
    ta=bool(re.search(r'[\u0B80-\u0BFF]',text)); hi=bool(re.search(r'[\u0900-\u097F]',text))
    latin=bool(tokens); t=tokens&TAMIL; h=tokens&HINDI
    if ta and hi: language='Mixed'; script='mixed'
    elif ta: language='Tamil'; script='Tamil'
    elif hi: language='Hindi'; script='Devanagari'
    elif t and h: language='Mixed'; script='Latin'
    elif t: language='Tanglish'; script='Latin'
    elif h: language='Hinglish'; script='Latin'
    elif latin: language='English'; script='Latin'
    else: language='Unknown'; script='unknown'
    return dict(language=language,confidence=None,script=script,code_mixed=(ta or hi) and latin or bool(t or h),
                method='script-and-civic-lexicon-heuristic',evidence=sorted(t|h),warning='Heuristic label; English is a Latin-script fallback, not verified language identification.')
