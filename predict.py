import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from app.classification import Classifier
from app.pipeline import Pipeline
r=Pipeline(Classifier()).run(" ".join(sys.argv[1:]))
for k in ["id","detected_language","english_text","departments","urgency","urgency_reason","recommended_action"]:print(f"{k}: {r[k]}")
