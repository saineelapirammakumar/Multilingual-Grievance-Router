"""Starts real servers with an isolated database; checks HTTP and all ten Streamlit views."""
import os,sys,tempfile,subprocess,time,json,secrets
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import requests
from streamlit.testing.v1 import AppTest

def main():
    out={};processes=[]
    with tempfile.TemporaryDirectory() as d:
        env=os.environ.copy();env.update({'DATABASE_URL':f'sqlite:///{d}/smoke.db','ADMIN_TOKEN':secrets.token_urlsafe(40),'EMAIL_ENABLED':'false','API_URL':'http://127.0.0.1:8765','STREAMLIT_BROWSER_GATHER_USAGE_STATS':'false'})
        logs=[]
        try:
            for name,cmd in [('backend',[sys.executable,'-m','uvicorn','backend:app','--host','127.0.0.1','--port','8765','--no-access-log']),('dashboard',[sys.executable,'-m','streamlit','run','dashboard.py','--server.address','127.0.0.1','--server.port','8509','--browser.gatherUsageStats','false'])]:
                f=open(Path(d)/(name+'.log'),'w');logs.append(f);processes.append(subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=f,stderr=f))
            for name,url in [('backend','http://127.0.0.1:8765/health'),('dashboard','http://127.0.0.1:8509/_stcore/health')]:
                deadline=time.monotonic()+30
                while True:
                    try:
                        r=requests.get(url,timeout=2)
                        if r.status_code==200:out[name+'_http_health']=True;break
                    except requests.RequestException:pass
                    if time.monotonic()>deadline:raise RuntimeError(name+' startup timed out')
                    time.sleep(.2)
            # Streamlit widget execution with a running backend, not just an import test.
            os.environ.update({k:env[k] for k in ['API_URL','ADMIN_TOKEN','EMAIL_ENABLED']})
            at=AppTest.from_file(str(ROOT/'dashboard.py'),default_timeout=15).run()
            assert not at.exception,at.exception
            # The updated UI starts on a welcome screen, so enter the citizen
            # workspace before looking for workspace-specific widgets.
            next(w for w in at.button if w.label == 'Continue as Citizen  →').click().run()
            assert not at.exception, at.exception
            views=list(next(w for w in at.radio if w.label=='Workspace').options);out['view_checks']={}
            for view in views:
                next(w for w in at.radio if w.label=='Workspace').set_value(view).run()
                assert not at.exception,(view,at.exception)
                out['view_checks'][view]='rendered without exception'
                if view=='Voice grievance upload':
                    next(w for w in at.radio if w.label=='Audio source').set_value('Record microphone').run()
                    assert not at.exception
                    out['microphone_widget_rendered']=True
            next(w for w in at.radio if w.label=='Workspace').set_value(views[0]).run()
            at.text_area[0].set_value('A live wire has fallen near the school')
            # Named labels avoid positional dependency on widget layout.
            next(w for w in at.button if w.label=='Submit grievance').click().run()
            assert not at.exception and len(at.success)>0
            out['dashboard_text_submission']=True
            next(w for w in at.radio if w.label=='Workspace').set_value(views[2]).run()
            next(w for w in at.button if w.label=='Load complaint').click().run()
            assert not at.exception and any(m.value=='Submitted' for m in at.metric)
            out['dashboard_tracking']=True
            auth={'Authorization':'Bearer '+env['ADMIN_TOKEN']}
            assert requests.get(env['API_URL']+'/api/v1/analytics',headers=auth,timeout=5).json()['total']==1
            out['live_database_analytics']=True
        finally:
            for proc in processes:
                proc.terminate()
                try:proc.wait(timeout=5)
                except subprocess.TimeoutExpired:proc.kill();proc.wait()
            for log in logs:log.close()
            out['server_logs']={p.name:p.read_text() for p in Path(d).glob('*.log')}
            (ROOT/'reports/smoke_results.json').write_text(json.dumps(out,indent=2))
    print(json.dumps({k:v for k,v in out.items() if k!='server_logs'},indent=2))
if __name__=='__main__':main()
