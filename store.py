"""SQLAlchemy persistence with transactional schema migrations and optimistic locking."""
import json,os
from datetime import datetime,timezone
from pathlib import Path
from sqlalchemy import create_engine,Column,String,Integer,Text,ForeignKey,event,Boolean
from sqlalchemy.orm import DeclarativeBase,sessionmaker
class Base(DeclarativeBase):pass
class Grievance(Base):
    __tablename__='grievances'
    id=Column(String,primary_key=True)
    token_hash=Column(String,nullable=False)
    timestamp=Column(String,nullable=False)
    original_text=Column(Text,nullable=False)
    language=Column(String,nullable=False)
    normalized_text=Column(Text,nullable=False)
    prediction=Column(Text,nullable=False)
    location=Column(Text,nullable=False)
    departments=Column(Text,nullable=False)
    urgency=Column(String,nullable=False)
    status=Column(String,nullable=False,default='Submitted')
    assigned_department=Column(String)
    resolution=Column(Text)
    email=Column(String)
    version=Column(Integer,nullable=False,default=1)
    is_unsolvable=Column(Boolean,nullable=False,default=False)
    unsolvable_reason=Column(Text)
    unsolvable_by=Column(String)
    unsolvable_at=Column(String)
    __mapper_args__={'version_id_col':version}
class Audit(Base):
    __tablename__='audit_events'
    id=Column(Integer,primary_key=True)
    grievance_id=Column(String,ForeignKey('grievances.id'),nullable=False)
    timestamp=Column(String,nullable=False)
    actor=Column(String,nullable=False)
    kind=Column(String,nullable=False)
    payload=Column(Text,nullable=False)
class Notification(Base):
    __tablename__='notifications'
    id=Column(Integer,primary_key=True)
    grievance_id=Column(String,ForeignKey('grievances.id'),nullable=False)
    timestamp=Column(String,nullable=False)
    message=Column(Text,nullable=False)
    delivery=Column(String,nullable=False,default='pending')
    attempts=Column(Integer,nullable=False,default=0)
class Duplicate(Base):
    __tablename__='duplicates'
    first_id=Column(String,ForeignKey('grievances.id'),primary_key=True)
    second_id=Column(String,ForeignKey('grievances.id'),primary_key=True)
    actor=Column(String,nullable=False)
    note=Column(Text,nullable=False)
def now():return datetime.now(timezone.utc).isoformat()
def initialize(url):
    from sqlalchemy.engine import make_url
    parsed=make_url(url)
    if parsed.drivername.startswith('sqlite') and parsed.database and parsed.database!=':memory:':
        database_path=Path(parsed.database)
        database_path.parent.mkdir(parents=True,exist_ok=True)
        fd=os.open(database_path,os.O_WRONLY|os.O_CREAT,0o600);os.close(fd);os.chmod(database_path,0o600)
    engine=create_engine(url,connect_args={'check_same_thread':False,'timeout':30} if url.startswith('sqlite') else {})
    if url.startswith('sqlite'):
        @event.listens_for(engine,'connect')
        def pragmas(conn,_):
            cur=conn.cursor();cur.execute('PRAGMA foreign_keys=ON');cur.execute('PRAGMA journal_mode=WAL');cur.close()
    # Versioned SQL migration files run once; never silently drop/recreate tables.
    migrations=Path(__file__).resolve().parents[1]/'migrations'
    with engine.begin() as conn:
        conn.exec_driver_sql('CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY)')
        done={r[0] for r in conn.exec_driver_sql('SELECT version FROM schema_migrations')}
        migration_files=sorted(migrations.glob('*.sql'))
        available={int(file.name.split('_')[0]) for file in migration_files}
        if done and max(done)>max(available, default=0):raise RuntimeError('Database schema is newer than this application')
        for file in migration_files:
            v=int(file.name.split('_')[0])
            if v not in done:
                for sql in file.read_text().split(';'):
                    if sql.strip():conn.exec_driver_sql(sql)
                conn.exec_driver_sql('INSERT INTO schema_migrations (version) VALUES (?)',(v,))
    return engine,sessionmaker(engine,expire_on_commit=False)
def public_record(g):
    p=json.loads(g.prediction)
    from .routing import route
    current_routing=route(json.loads(g.location),json.loads(g.departments),g.original_text)
    return {**p,'location':json.loads(g.location),'departments':json.loads(g.departments),'urgency':g.urgency,
            'original_prediction':p,'current_routing':current_routing,'status':g.status,'assigned_department':g.assigned_department,
            'resolution':g.resolution,'version':g.version,'is_unsolvable':bool(g.is_unsolvable),
            'unsolvable_reason':g.unsolvable_reason,'unsolvable_by':g.unsolvable_by,'unsolvable_at':g.unsolvable_at}
def audit(s,g,actor,kind,payload):
    s.add(Audit(grievance_id=g.id,timestamp=now(),actor=actor,kind=kind,payload=json.dumps(payload,ensure_ascii=False)))
def notify(s,g):
    s.add(Notification(grievance_id=g.id,timestamp=now(),message=f'Complaint {g.id}: {g.status}',delivery='pending'))
