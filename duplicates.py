"""Local cosine retrieval with a labeled lexical fallback; never automatically merge."""
import os,re,time
from functools import lru_cache
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .translation import normalize
@lru_cache(maxsize=2)
def load_encoder(path):
    import torch
    torch.set_num_threads(2)
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(path,device='cpu',local_files_only=True)
def score_candidates(text,candidates):
    start=time.perf_counter();mode='lexical-normalized-tfidf-fallback';warning='Lexical fallback is not a validated cross-language semantic model.'
    if not candidates:return np.zeros(0),mode,warning,0.0
    texts=[text]+list(candidates);path=os.getenv('SENTENCE_MODEL_PATH','')
    try:
        if not path:raise RuntimeError('No local sentence model configured')
        emb=load_encoder(path).encode(texts,normalize_embeddings=True,show_progress_bar=False)
        sims=emb[1:]@emb[0];mode='multilingual-sentence-transformer';warning=None
    except (ImportError,OSError,RuntimeError,ValueError):
        try:
            canonical=[re.sub(r'\b(leaking|leaks|leakage)\b','leak',normalize(t)) for t in texts]
            vectors=TfidfVectorizer(ngram_range=(1,1),stop_words='english').fit_transform(canonical)
            sims=cosine_similarity(vectors[0],vectors[1:])[0]
        except ValueError:sims=np.zeros(len(candidates))
    return sims,mode,warning,(time.perf_counter()-start)*1000

def find_duplicates(text,location,records,threshold=None):
    threshold=float(os.getenv('DUPLICATE_THRESHOLD','0.65')) if threshold is None else threshold
    if not 0<=threshold<=1:raise ValueError('Duplicate threshold must be 0..1')
    sims,mode,warning,elapsed=score_candidates(text,[r['original_text'] for r in records]);matches=[]
    for r,score in zip(records,sims):
        if score>=threshold:
            loc=r['location'];same=all(location.get(k) and location.get(k)==loc.get(k) for k in ('municipality','ward','area'))
            matches.append(dict(id=r['id'],similarity=float(score),location=loc,same_location=bool(same),original_text=r['original_text']))
    return dict(mode=mode,warning=warning,threshold=threshold,inference_ms=elapsed,items=sorted(matches,key=lambda x:x['similarity'],reverse=True)[:10])
