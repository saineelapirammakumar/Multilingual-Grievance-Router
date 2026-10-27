import re
RULES={
 'live_wire':r'\blive\s+(?:electric(?:al)?\s+)?(?:wire|cable)\b',
 'fallen_electric_wire':r'\b(?:electric(?:al)?\s+wire|power\s+(?:cable|line)|electricity.*wire)\b.{0,60}\b(?:fell|fallen|falling|down|broken)\b',
 'wire_sparks':r'\b(?:wire|cable|transformer)\b.{0,60}\b(?:spark\w*|fire|burn\w*)\b|\b(?:fire|spark\w*)\b.{0,40}\btransformer\b',
 'low_power_line':r'\b(?:power line|electricity.*wire|electric.*cable)\b.{0,60}\b(?:hanging|low)\b',
 'open_manhole':r'\bopen manhole\b',
 'sewage_in_home':r'\b(?:sewage|flood water)\b.{0,60}\b(?:house\w*|home\w*)\b',
 'blocked_ambulance':r'\bambulance route\b.{0,30}\bblocked\b|\bblocking ambulance route\b',
 'accident_with_injury':r'\baccident\b.{0,100}\b(?:injur\w*|hurt|bleed\w*)\b|\b(?:injur\w*|hurt|bleed\w*)\b.{0,100}\baccident\b',
 'immediate_danger_help':r'\b(?:accident|injur\w*|danger)\b.{0,80}\b(?:immediate|now)\b.{0,40}\bhelp\b|\b(?:immediate|now)\b.{0,40}\bhelp\b.{0,80}\b(?:accident|injur\w*|danger)\b'}
URGENT={'unsafe_access':r'\b(?:night|dark)\b.{0,100}\b(?:safe|safely|cannot go|cannot walk|people)\b|\b(?:safe|safely)\b.{0,100}\b(?:night|dark)\b', 'water_shortage':r'\bno water\b|\bwater\b.{0,20}\bnot coming\b', 'active_leak':r'\bleak\w*\b|\boverflow\w*\b'}
def safety_details(text,learned):
    s=text.lower()
    fired=[k for k,v in RULES.items() if re.search(v,s)]
    caution=bool(re.search(r'\b(no longer|not live|not sparking|repaired|resolved|yesterday)\b',s))
    if fired:return 'Emergency',fired,caution
    urgent=[k for k,v in URGENT.items() if re.search(v,s)]
    return ('Urgent' if urgent and learned=='Routine' else learned),urgent,caution

def apply_safety(text,learned):
    u,r,_=safety_details(text,learned)
    return u,'safety-rule' if r else 'classifier'
def action(u):
    return {'Emergency':'Immediate human safety review. This application does not dispatch emergency services.', 'Urgent':'Prioritize for departmental review.', 'Routine':'Review in the normal departmental queue.'}[u]
