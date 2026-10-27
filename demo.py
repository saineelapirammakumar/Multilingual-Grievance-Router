"""Reproducible expectations with honest failure reporting; isolated temporary database."""
import sys,json,csv,os,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from fastapi.testclient import TestClient
from backend import create_app

def main():
    os.environ['ADMIN_TOKEN']='demo-only-'+('x'*40);os.environ['EMAIL_ENABLED']='false';os.environ['RATE_LIMIT_PER_MINUTE']='1000'
    auth={'Authorization':'Bearer '+os.environ['ADMIN_TOKEN']};results=[]
    with tempfile.TemporaryDirectory() as directory, TestClient(create_app(f'sqlite:///{directory}/demo.db')) as c:
        for row in csv.DictReader((ROOT/'data/demonstrations.csv').open()):
            r=c.post('/api/v1/grievances',json={'text':row['text'],'location':{}})
            data=r.json();checks={'stored':r.status_code==201}
            if row['expected_departments']:checks['departments']=set(row['expected_departments'].split('|')).issubset(data['departments'])
            if row['expected_urgency']:checks['urgency']=data['urgency']==row['expected_urgency']
            if row['expected_language']:checks['language']=data['detected_language']==row['expected_language']
            if row['scenario']=='low_confidence':checks['review_required']=data['review_required']
            if row['scenario']=='ambiguous_location':checks['location_review']=data['routing']['review_required'] and len(data['routing']['suggestions'])==2
            if row['scenario']=='semantic_pair':
                base=c.post('/api/v1/grievances',json={'text':'Water pipe leaking near school.'}).json()
                dup=c.get('/api/v1/grievances/'+data['id']+'/duplicates',headers=auth).json()
                checks['duplicate_at_default_threshold']=any(x['id']==base['id'] for x in dup['items'])
            results.append({'scenario':row['scenario'],'expected':row,'actual':{k:data[k] for k in ['departments','urgency','detected_language','review_required']},'checks':checks,'passed':all(checks.values())})
        url='/api/v1/grievances/'+data['id'];states=[]
        for state in ['Assigned','In Progress','Resolved']:
            response=c.patch(url,headers=auth,json={'expected_version':data['version'],'status':state,'assigned_department':'Roads','resolution':'Repair verified' if state=='Resolved' else None,'note':'Demonstration lifecycle'})
            states.append(response.status_code);data=response.json()
        results.append({'scenario':'complete_workflow','http_codes':states,'passed':states==[200,200,200] and data['status']=='Resolved'})
    report={'kind':'synthetic functional demonstrations; not held-out evaluation','passed':sum(r['passed'] for r in results),'total':len(results),'results':results}
    (ROOT/'reports/demo_results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
