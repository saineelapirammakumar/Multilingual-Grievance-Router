"""Explicit local download using recorded upstream revisions. Never invoked by the API."""
import argparse,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def download(kind,output,revision=None):
    from huggingface_hub import snapshot_download
    spec=json.loads((ROOT/'config/model_revisions.json').read_text())[kind]
    revision=revision or spec['revision']
    if not re.fullmatch(r'[0-9a-f]{40}',revision):raise ValueError('Use a full reviewed commit SHA')
    patterns=['*.json','*.txt','*.model','README.md','LICENSE*','1_Pooling/*','2_Normalize/*']
    patterns+=['model.bin'] if kind=='asr' else ['model.safetensors'] if kind=='duplicates' else ['pytorch_model.bin']
    path=snapshot_download(repo_id=spec['repo_id'],revision=revision,local_dir=output,allow_patterns=patterns,max_workers=2)
    (Path(path)/'download_provenance.json').write_text(json.dumps({'repo_id':spec['repo_id'],'revision':revision},indent=2))
    return path
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('kind',choices=['asr','duplicates','classifier']);p.add_argument('--revision');p.add_argument('--output',required=True);a=p.parse_args()
    print(download(a.kind,a.output,a.revision))
