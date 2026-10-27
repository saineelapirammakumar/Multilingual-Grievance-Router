# CivicLens — Multilingual Local Government Grievance Router v3

An extension of the supplied FastAPI + Streamlit project. Local-first academic demonstration, with trainable TF-IDF/logistic models, multilingual civic normalization, SQLite tracking, auditable official review and optional local neural models. No paid API is required.

**Start here:** [Ubuntu setup](SETUP_UBUNTU.md) · [Windows/WSL setup](SETUP_WINDOWS_WSL.md) · [Verification](TEST_RESULTS.md) · [Limitations](KNOWN_LIMITATIONS.md).

## Delivery status

Text workflows, real WAV/MP3 transcription, multilingual sentence embeddings and frozen-MuRIL classification were executed in this revision. **58 pytest tests passed**, plus real neural API and live backend/dashboard smoke checks. See `TEST_RESULTS.md` for exact scope.

The default classifier remains TF-IDF + Logistic Regression: it outperformed frozen MuRIL on the inherited hold-out. Both use **195 training examples (65 inherited + 130 synthetic)** and the same **22 held-out inherited examples**. No independent real municipal evaluation dataset has been supplied. Actual results, model errors and provenance are in `docs/EVALUATION.md`.

Large neural weights are **not bundled**. Download the pinned snapshots once using `docs/OPTIONAL_MODELS.md`; baseline text processing runs without them. No paid service, government integration or automatic emergency dispatch is used.

## Quick start (Python 3.12)

From the extracted project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/init_local.py
python scripts/train.py
python -m pytest -q
uvicorn backend:app --host 127.0.0.1 --port 8000 --no-access-log
```

In another terminal, activate the same environment and run:

```bash
streamlit run dashboard.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false
```

Dashboard: http://localhost:8501 · API documentation: http://localhost:8000/docs

**Voice setup:** after baseline setup, run `bash scripts/setup_voice.sh` in Ubuntu/WSL to install the local English/Tamil/Hindi ASR runtime, download the pinned Whisper-tiny model, and configure `ASR_MODEL_PATH`. Model weights are not bundled in the ZIP. See `FRONTEND_AND_VOICE_UPDATE_GUIDE.md`.

`init_local.py` creates `.env` with a strong random official token without overwriting an existing file. Copy `ADMIN_TOKEN` from `.env` into the dashboard sidebar to use official views; keep it private. Citizen submission does not need this token. Each citizen receives a separate private tracking token, displayed once. Only its SHA-256 digest is stored.

## Included

- The original project archive in `docs/original_project.zip` and original training metrics in `reports/`.
- Compatible `backend.py`, `dashboard.py`, `app/`, `scripts/train.py` and `scripts/predict.py` entry points.
- `POST /api/v1/grievances/analyze` compatibility alias that stores a complaint and now returns HTTP 201 plus a tracking token.
- English, Tamil, Hindi, Hinglish and Tanglish script/lexicon handling; no forced full translation.
- Multi-label statistical routing, learned three-level urgency, explicit safety rules, coefficient evidence and review warnings.
- SQLite/SQLAlchemy, migrations, status transitions, optimistic locking, original predictions and private audit history.
- Location mappings, duplicate candidates and confirmed links, local notifications and optional SMTP outbox.
- Ten working Streamlit views, tests, real evaluation JSON, synthetic demo scenarios, Docker and CI configuration.
- Tested optional frozen MuRIL comparison, Sentence Transformer retrieval and faster-whisper integration; see `docs/OPTIONAL_MODELS.md`.

## Main commands

```bash
python scripts/predict.py "school ke paas live wire gir gaya hai"
python scripts/demo.py
python scripts/smoke_test.py
python scripts/compare_models.py
```

The demo script writes to a temporary database and never sends email. Demo examples are not an independent benchmark. The smoke test starts backend port 8765 and frontend port 8509, executes all ten views and submits/tracks a complaint. Keep those ports free.

## Official workflow

Submit → save ID/token → official loads record → assign department with audit note → In Progress → Resolved with resolution details. Reopened and Rejected are supported with transition validation. Version conflicts return 409; reload before applying edits again. Human corrections never overwrite the original prediction. Corrections can be exported privately for annotation; no automatic retraining or deployment occurs.

## Security and deployment boundary

Bind to localhost, keep `.env` and databases out of Git, use synthetic data for demonstrations, and protect local file access. The SQLite file is not encrypted. A shared official token is suitable only for this local single-administrator demo; no individual account management or department-specific roles are provided. See `docs/SECURITY.md` before changing the deployment boundary.

Run `docker compose up --build` after creating `.env` for optional container deployment. This path is supplied but unexecuted here. Baseline weights are included and tied to the pinned scikit-learn version; retrain after dependency changes. Load only trusted joblib files.

## Research integrity

Frozen inherited split: 65 train / 22 test, seed 42. A separate 130-row AI-authored synthetic CSV expands only training families, bringing training to 195 rows. Translation/paraphrase families stay together; test data is never fitted. No hyperparameter search uses the test set. The inherited civic lexicon was designed with knowledge of the supplied corpus, so this is not a fully blind external evaluation. The synthetic training set adds native Hindi; the inherited test set still has no native Hindi rows, so Hindi accuracy remains unmeasured. See `docs/DATASET_ANNOTATION_GUIDE.md` and `docs/EVALUATION.md`.

## Reproduce advanced checks

After installing optional dependencies and downloading pinned models:

```bash
python scripts/evaluate_optional.py --asr-path local_models/asr --sentence-path local_models/duplicates
python scripts/verify_neural_api.py --asr-path local_models/asr --sentence-path local_models/duplicates --muril-path local_models/classifier
```

These commands execute actual models, never mocks. Included MuRIL heads are small; set `MURIL_ENCODER_PATH` to the downloaded encoder before selecting `MODEL_BACKEND=transformer`. Keep baseline as the default unless a fresh evaluation supports changing it.


## Tamil Nadu locations and solvability review

Citizen text and voice submissions require a Tamil Nadu district and a dependent city/town/local-area selection. The district/place catalogue is stored in `config/tamil_nadu_places.json` and exposed through `GET /api/v1/locations/tamil-nadu`; submissions persist both fields in the existing JSON location record. The list provides common locations per district and can be extended in that configuration file.

Officials can use the Human feedback and reassignment view to mark a complaint **Unsolvable** with a required reason. The decision is stored independently of the lifecycle `status`, includes the official identifier and timestamp, advances the record version, and writes a `marked-unsolvable` audit event. `GET /api/v1/analytics` includes `solvability.solvable` and `solvability.unsolvable` counts. Database migration `002_location_unsolvable.sql` adds the persistent decision fields without replacing existing records.
