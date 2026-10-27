"""CivicLens single-process local demonstration API. See README for security boundaries."""
import os,json,secrets,tempfile,logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI,HTTPException,UploadFile,File,Request,Depends,BackgroundTasks,Query,Header, Form
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select,func,or_
from sqlalchemy.orm.exc import StaleDataError
from dotenv import load_dotenv
from app.schemas import GrievanceRequest,UpdateRequest,DuplicateRequest,UnsolvableRequest
from app.classification import Classifier
from app.pipeline import Pipeline
from app.store import initialize,Grievance,Audit,Notification,Duplicate,public_record,audit,notify
from app.security import admin,is_admin,can_read,digest,Limiter
from app.routing import route
from app.duplicates import find_duplicates
from app.notifications import dispatch
from app import asr
ROOT=Path(__file__).resolve().parent
load_dotenv(ROOT/'.env')
TRANSITIONS={'Submitted':{'Assigned','Rejected'},'Assigned':{'In Progress','Rejected'},'In Progress':{'Resolved','Rejected'},'Resolved':{'Reopened'},'Reopened':{'Assigned','In Progress','Rejected'},'Rejected':{'Reopened'}}

def create_app(database_url=None):
    @asynccontextmanager
    async def lifespan(app):
        url=database_url or os.getenv('DATABASE_URL',f'sqlite:///{ROOT}/data/grievances.db')
        engine,Session=initialize(url);app.state.engine=engine;app.state.Session=Session
        app.state.model_error=None
        try:
            if os.getenv('MODEL_BACKEND','baseline')=='transformer':
                from app.transformer import TransformerClassifier
                clf=TransformerClassifier(ROOT/'models/transformer')
            else:clf=Classifier(os.getenv('MODEL_DIR',str(ROOT/'models')))
            app.state.pipeline=Pipeline(clf)
        except Exception:
            app.state.pipeline=None;app.state.model_error='Model unavailable. Run training with this environment; see README.'
        app.state.limiter=Limiter()
        yield
        engine.dispose()
    app=FastAPI(title='Multilingual Local Government Grievance Router',version='2.0.0',lifespan=lifespan)
    @app.middleware('http')
    async def harden(request,call_next):
        # Bound JSON bodies even when no Content-Length is supplied.
        if request.method in ('POST','PATCH'):
            body_limit=10*1024*1024+65536 if 'multipart/form-data' in request.headers.get('content-type','') else 32768
            total=0;parts=[]
            async for chunk in request.stream():
                total+=len(chunk)
                if total>body_limit:
                    from starlette.responses import JSONResponse
                    return JSONResponse({'detail':'Request body too large'},status_code=413)
                parts.append(chunk)
            request._body=b''.join(parts)
        response=await call_next(request)
        response.headers['Cache-Control']='no-store';response.headers['X-Content-Type-Options']='nosniff'
        return response
    def model():
        if not app.state.pipeline:raise HTTPException(503,app.state.model_error)
        return app.state.pipeline
    def get(s,id):
        g=s.get(Grievance,id)
        if not g:raise HTTPException(404,'Complaint not found')
        return g
    @app.get('/')
    def root():return {'service':'CivicLens','docs':'/docs'}
    @app.get('/health')
    def health():
        with app.state.Session() as s:s.execute(select(1))
        return {'status':'healthy' if app.state.pipeline else 'degraded','database':'ready','model_ready':bool(app.state.pipeline)}
    @app.get('/api/v1/locations/tamil-nadu')
    def tamil_nadu_locations():
        return json.loads((ROOT/'config'/'tamil_nadu_places.json').read_text())
    @app.get('/api/v1/system',dependencies=[Depends(admin)])
    def system():
        return {'model_backend':os.getenv('MODEL_BACKEND','baseline'),'model_error':app.state.model_error,
                'metrics':json.loads((ROOT/('models/transformer/metrics.json' if os.getenv('MODEL_BACKEND','baseline')=='transformer' else 'models/metrics.json')).read_text()) if (ROOT/('models/transformer/metrics.json' if os.getenv('MODEL_BACKEND','baseline')=='transformer' else 'models/metrics.json')).exists() else None,
                'asr_configured':bool(os.getenv('ASR_MODEL_PATH')),'sentence_model_configured':bool(os.getenv('SENTENCE_MODEL_PATH')),
                'optional_models_note':'Configuration does not prove a model can load or perform accurately.',
                'jurisdictions':json.loads((ROOT/'config/jurisdictions.json').read_text()),'email_enabled':os.getenv('EMAIL_ENABLED','false')=='true'}
    @app.post('/api/v1/predict')
    def predict(req:GrievanceRequest,request:Request):
        app.state.limiter.check(request)
        return model().run(req.text,req.source)
    @app.post('/api/v1/grievances',status_code=201)
    @app.post('/api/v1/grievances/analyze',status_code=201)
    def submit(req:GrievanceRequest,request:Request,background:BackgroundTasks):
        app.state.limiter.check(request)
        if not req.location.district or not req.location.place:
            raise HTTPException(422,'Select a Tamil Nadu district and place before submitting a complaint')
        prediction=model().run(req.text,req.source)
        with app.state.Session() as candidates_session:
            recent=[public_record(g) for g in candidates_session.scalars(select(Grievance).order_by(Grievance.timestamp.desc()).limit(1000))]
        duplicate_candidates=find_duplicates(req.text,req.location.model_dump(),recent)
        routing=route(req.location.model_dump(),prediction['departments'],req.text)
        prediction['routing']=routing
        if routing['review_required']:
            prediction['review_required']=True;prediction['warnings'].append(routing['reason'])
        token=secrets.token_urlsafe(32)
        with app.state.Session() as s:
            g=Grievance(id=prediction['id'],token_hash=digest(token),timestamp=prediction['timestamp'],original_text=req.text,
                        language=prediction['detected_language'],normalized_text=prediction['normalized_text'],prediction=json.dumps(prediction,ensure_ascii=False),
                        location=req.location.model_dump_json(),departments=json.dumps(prediction['departments']),urgency=prediction['urgency'],
                        status='Submitted',email=req.email if req.email_opt_in else None)
            s.add(g);s.flush();audit(s,g,'citizen','submitted',{'status':'Submitted'})
            audit(s,g,'system','duplicate-candidates',duplicate_candidates)
            notify(s,g);s.commit();result=public_record(g)
        background.add_task(dispatch,app.state.Session)
        # Citizen response never includes other citizens' complaints or duplicate matches.
        return {**result,'tracking_token':token}
    @app.post('/api/v1/grievances/analyze-audio')
    async def audio(request:Request,file:UploadFile=File(...),language:str|None=Form(default=None)):
        app.state.limiter.check(request)
        suffix=Path(file.filename or '').suffix.lower()
        if suffix not in ('.wav','.mp3'):raise HTTPException(415,'Upload WAV or MP3')
        path=None
        try:
            with tempfile.NamedTemporaryFile(delete=False,suffix=suffix) as f:
                path=f.name;total=0;header=b''
                while chunk:=await file.read(65536):
                    total+=len(chunk)
                    if total>10*1024*1024:raise HTTPException(413,'Maximum audio size is 10 MiB')
                    if not header:header=chunk[:16]
                    f.write(chunk)
            valid=(suffix=='.wav' and header.startswith(b'RIFF') and header[8:12]==b'WAVE') or (suffix=='.mp3' and (header.startswith(b'ID3') or len(header)>1 and header[0]==255 and header[1]&224==224))
            if not valid:raise HTTPException(422,'Invalid audio signature')
            if language not in (None, '', 'English', 'Hindi', 'Tamil'):
                raise HTTPException(422, 'Language must be English, Hindi, or Tamil')
            text,detected_language=await run_in_threadpool(asr.transcribe_audio,path,language or None)
            prediction=await run_in_threadpool(model().run,text,'voice')
            return {'transcript':text,'asr_language':detected_language,'selected_language':language or 'Auto-detect','prediction':prediction,'stored':False,'next_step':'Correct transcript then submit via POST /api/v1/grievances with source=voice'}
        except RuntimeError as e:raise HTTPException(503,str(e))
        except ValueError as e:raise HTTPException(422,str(e))
        finally:
            await file.close()
            if path:Path(path).unlink(missing_ok=True)
    @app.get('/api/v1/grievances',dependencies=[Depends(admin)])
    def listing(status:str|None=None,urgency:str|None=None,department:str|None=None,q:str=Query('',max_length=100),offset:int=Query(0,ge=0),limit:int=Query(25,ge=1,le=100)):
        filters=[]
        if status:filters.append(Grievance.status==status)
        if urgency:filters.append(Grievance.urgency==urgency)
        if department:filters.append(Grievance.departments.contains(json.dumps(department)))
        if q:filters.append(or_(Grievance.original_text.contains(q,autoescape=True),Grievance.id.contains(q,autoescape=True)))
        from sqlalchemy import case
        with app.state.Session() as s:
            total=s.scalar(select(func.count()).select_from(Grievance).where(*filters))
            rows=s.scalars(select(Grievance).where(*filters).order_by(case((Grievance.urgency=='Emergency',0),(Grievance.urgency=='Urgent',1),else_=2),Grievance.timestamp.desc()).offset(offset).limit(limit))
            return {'count':total,'offset':offset,'limit':limit,'items':[public_record(g) for g in rows]}
    @app.get('/api/v1/analytics',dependencies=[Depends(admin)])
    def analytics():
        from collections import Counter
        with app.state.Session() as s:
            rows=list(s.scalars(select(Grievance)))
            return {'total':len(rows),'departments':dict(Counter(d for g in rows for d in json.loads(g.departments))),
                    'urgency':dict(Counter(g.urgency for g in rows)),'status':dict(Counter(g.status for g in rows)),
                    'languages':dict(Counter(g.language for g in rows)),'review_required':sum(json.loads(g.prediction)['review_required'] for g in rows),
                    'solvability':{'solvable':sum(not g.is_unsolvable for g in rows),'unsolvable':sum(bool(g.is_unsolvable) for g in rows)}}
    @app.get('/api/v1/grievances/{id}')
    def detail(id:str,request:Request,x_tracking_token:str|None=Header(default=None)):
        with app.state.Session() as s:
            g=get(s,id);can_read(request,g);result=public_record(g)
            result['notifications']=[{'id':n.id,'timestamp':n.timestamp,'message':n.message,'delivery':n.delivery} for n in s.scalars(select(Notification).where(Notification.grievance_id==id).order_by(Notification.id))]
            if is_admin(request):result['audit']=[{'id':a.id,'timestamp':a.timestamp,'actor':a.actor,'kind':a.kind,'payload':json.loads(a.payload)} for a in s.scalars(select(Audit).where(Audit.grievance_id==id))]
            return result
    @app.patch('/api/v1/grievances/{id}')
    def update(id:str,req:UpdateRequest,background:BackgroundTasks,actor:str=Depends(admin)):
        with app.state.Session() as s:
            g=get(s,id)
            if req.expected_version!=g.version:raise HTTPException(409,'Record changed; refresh before editing')
            before=public_record(g)
            if req.status and req.status!=g.status and req.status not in TRANSITIONS[g.status]:raise HTTPException(409,'Invalid lifecycle transition')
            if req.assigned_department is not None:g.assigned_department=req.assigned_department
            if req.status in ('Assigned','In Progress') and not g.assigned_department:raise HTTPException(422,'Assign a department first')
            if req.status=='Resolved' and not (req.resolution or '').strip():raise HTTPException(422,'Resolution details required')
            if req.status:g.status=req.status
            if req.departments is not None:g.departments=json.dumps(req.departments)
            if req.urgency:g.urgency=req.urgency
            if req.resolution is not None:g.resolution=req.resolution
            if req.location is not None:g.location=req.location.model_dump_json()
            # Note-only feedback also advances the version.
            g.version+=1
            audit(s,g,actor,'feedback',{'before':{'departments':before['departments'],'urgency':before['urgency'],'status':before['status'],'location':before['location'],'assigned_department':before['assigned_department']},'changes':req.model_dump(exclude_none=True)})
            notify(s,g)
            try:s.commit()
            except StaleDataError:s.rollback();raise HTTPException(409,'Concurrent update; refresh')
            result=public_record(g)
        background.add_task(dispatch,app.state.Session)
        return result
    @app.post('/api/v1/grievances/{id}/unsolvable')
    def mark_unsolvable(id:str,req:UnsolvableRequest,actor:str=Depends(admin)):
        with app.state.Session() as s:
            g=get(s,id)
            if req.expected_version!=g.version:raise HTTPException(409,'Record changed; refresh before editing')
            before={'is_unsolvable':bool(g.is_unsolvable),'reason':g.unsolvable_reason,'status':g.status}
            g.is_unsolvable=True;g.unsolvable_reason=req.reason;g.unsolvable_by=actor
            from app.store import now
            g.unsolvable_at=now();g.version+=1
            audit(s,g,actor,'marked-unsolvable',{'before':before,'reason':req.reason,'status_preserved':g.status})
            try:s.commit()
            except StaleDataError:s.rollback();raise HTTPException(409,'Concurrent update; refresh')
            return public_record(g)
    @app.get('/api/v1/grievances/{id}/duplicates',dependencies=[Depends(admin)])
    def duplicates(id:str):
        with app.state.Session() as s:
            g=get(s,id);records=[public_record(r) for r in s.scalars(select(Grievance).where(Grievance.id!=id).order_by(Grievance.timestamp.desc()).limit(1000))]
            result=find_duplicates(g.original_text,json.loads(g.location),records)
            result['candidate_window']='Most recent 1000 other complaints'
            result['confirmed']=[{'first_id':d.first_id,'second_id':d.second_id,'note':d.note} for d in s.scalars(select(Duplicate).where(or_(Duplicate.first_id==id,Duplicate.second_id==id)))]
            return result
    @app.post('/api/v1/grievances/{id}/duplicates')
    def confirm_duplicate(id:str,req:DuplicateRequest,actor:str=Depends(admin)):
        if id==req.other_id:raise HTTPException(422,'Cannot link complaint to itself')
        with app.state.Session() as s:
            g=get(s,id);get(s,req.other_id);a,b=sorted([id,req.other_id])
            if not s.get(Duplicate,(a,b)):
                s.add(Duplicate(first_id=a,second_id=b,actor=actor,note=req.note));audit(s,g,actor,'duplicate-confirmed',req.model_dump());s.commit()
            return {'linked':[a,b],'originals_preserved':True}
    @app.get('/api/v1/feedback/export',dependencies=[Depends(admin)])
    def feedback_export():
        with app.state.Session() as s:
            return {'sensitive':True,'automatic_training':False,'items':[{'audit_id':a.id,'grievance_id':a.grievance_id,'timestamp':a.timestamp,'actor':a.actor,'original_prediction':json.loads(s.get(Grievance,a.grievance_id).prediction),'feedback':json.loads(a.payload)} for a in s.scalars(select(Audit).where(Audit.kind=='feedback'))]}
    @app.post('/api/v1/notifications/dispatch',dependencies=[Depends(admin)])
    def retry(background:BackgroundTasks):
        background.add_task(dispatch,app.state.Session)
        return {'queued':True,'note':'Dispatches pending outbox records only. Failed/sending records require operator review to avoid duplicate email.'}
    return app
app=create_app()
