from datetime import datetime,timezone
import uuid,time
from .language_id import detect_language
from .translation import normalize,feature_text
from .urgency import safety_details,action
class Pipeline:
    def __init__(self,classifier):self.classifier=classifier
    def run(self,text,source='web'):
        start=time.perf_counter()
        if not text.strip():raise ValueError('Grievance cannot be empty')
        l=detect_language(text); norm=normalize(text); features=feature_text(text)
        ds,dq=self.classifier.departments(features); learned,uq=self.classifier.urgency(features)
        urgency,rules,negation=safety_details(norm,learned)
        warnings=[]
        if ds and max(dq.values())<.5:warnings.append('Tentative top-label fallback: no department reached the 0.5 threshold.')
        if not ds or max(dq.values())<.65:warnings.append('Department prediction is uncertain; official review required.')
        if max(uq.values())<.60:warnings.append('Urgency prediction is uncertain.')
        if self.classifier.coverage(features)<3:warnings.append('Limited recognized vocabulary or incomplete complaint.')
        if negation:warnings.append('Possible negation or historical context; safety rule needs human verification.')
        if l['language'] in ('Mixed','Unknown'):warnings.append('Ambiguous language.')
        if rules and urgency == 'Urgent':
            warnings.append('Safety-related urgency signal detected; verify priority during official review.')
        if urgency=='Emergency':warnings.append('Emergency triage requires immediate human confirmation.')
        return dict(id=str(uuid.uuid4()),timestamp=datetime.now(timezone.utc).isoformat(),source=source,
                    original_text=text,normalized_text=norm,english_text=norm,detected_language=l['language'],
                    language_confidence=None,language_metadata=l,script=l['script'],code_mixed=l['code_mixed'],
                    translation_engine='lexicon enrichment; not full translation',departments=ds,department_scores=dq,
                    urgency=urgency,learned_urgency=learned,urgency_scores=uq,safety_rules=rules,
                    urgency_reason='safety-rule' if rules else 'classifier',recommended_action=action(urgency),
                    score_type='uncalibrated model probabilities; not reliable confidence estimates',
                    explanations=self.classifier.evidence(features),review_required=bool(warnings),warnings=warnings,
                    inference_ms=(time.perf_counter()-start)*1000)
