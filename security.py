import hashlib,hmac,os,time,threading
from collections import defaultdict,deque
from fastapi import HTTPException,Request,Depends
from fastapi.security import HTTPBearer
bearer=HTTPBearer(auto_error=False)

def digest(token):return hashlib.sha256(token.encode()).hexdigest()
def admin(request:Request,credential=Depends(bearer)):
    expected=os.getenv('ADMIN_TOKEN','')
    supplied=request.headers.get('Authorization','').removeprefix('Bearer ')
    if len(expected)<32:raise HTTPException(503,'Configure ADMIN_TOKEN with at least 32 characters')
    if not supplied or not hmac.compare_digest(supplied,expected):raise HTTPException(401,'Valid official bearer token required')
    return 'local-official'
def is_admin(request):
    expected=os.getenv('ADMIN_TOKEN','');got=request.headers.get('Authorization','').removeprefix('Bearer ')
    return len(expected)>=32 and bool(got) and hmac.compare_digest(got,expected)
def can_read(request,g):
    if is_admin(request):return
    token=request.headers.get('X-Tracking-Token','')
    if not token or not hmac.compare_digest(digest(token),g.token_hash):raise HTTPException(404,'Complaint not found or tracking token invalid')
class Limiter:
    def __init__(self):self.calls=defaultdict(deque);self.lock=threading.Lock()
    def check(self,request):
        key=request.client.host if request.client else 'local';now=time.monotonic()
        with self.lock:
            for k in list(self.calls):
                if not self.calls[k] or self.calls[k][-1]<now-60:del self.calls[k]
            q=self.calls[key]
            while q and q[0]<now-60:q.popleft()
            if len(q)>=int(os.getenv('RATE_LIMIT_PER_MINUTE','30')):raise HTTPException(429,'Too many requests; retry later')
            q.append(now)
