import json,os,re
from pathlib import Path
DEFAULT=Path(__file__).resolve().parents[1]/'config/jurisdictions.json'
def route(location,departments,text=''):
    config=json.loads(Path(os.getenv('JURISDICTION_FILE',str(DEFAULT))).read_text())
    loc=dict(location);suggestions=[]
    for municipality,wards in config['municipalities'].items():
        for ward,details in wards.items():
            for area in details['areas']:
                if re.search(r'(?<!\w)'+re.escape(area)+r'(?!\w)',text,re.I):suggestions.append(dict(municipality=municipality,ward=ward,area=area))
    data=config['municipalities'].get(loc.get('municipality'),{}).get(loc.get('ward'))
    valid=bool(data and loc.get('area') in data['areas'] and departments and all(d in data['departments'] for d in departments))
    return dict(location=loc,review_required=not valid,suggestions=suggestions,
                candidates=[dict(department=d,municipality=loc.get('municipality'),ward=loc.get('ward')) for d in departments] if valid else [],
                demonstration_only=config.get('demonstration_only',True),reason='Configured jurisdiction matched' if valid else 'Missing, unknown, or ambiguous location/department; human routing required')
