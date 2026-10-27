"""Create a private local configuration without overwriting existing secrets."""
import os,secrets
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def initialize(directory):
    target=Path(directory)/'.env';template=(ROOT/'.env.example').read_text()
    content=template.replace('ADMIN_TOKEN=\n','ADMIN_TOKEN='+secrets.token_urlsafe(40)+'\n',1)
    try:
        fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    except FileExistsError:return False
    with os.fdopen(fd,'w') as f:f.write(content)
    return True
if __name__=='__main__':
    print('Created private .env. Read ADMIN_TOKEN locally for the official sidebar.' if initialize(ROOT) else '.env already exists; left unchanged.')
