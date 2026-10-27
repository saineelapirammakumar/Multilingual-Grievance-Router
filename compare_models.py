"""Report only executed comparable evaluations; never invent missing transformer metrics."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    baseline=json.loads((ROOT/'reports/baseline_grouped_metrics.json').read_text())
    path=ROOT/'reports/transformer_metrics.json'
    if not path.exists():
        print('Only baseline evaluated. Transformer metrics unavailable; run optional training first.')
        print(json.dumps({k:baseline[k] for k in ['department_micro_f1','department_macro_f1','department_hamming_loss','inference_latency_ms']},indent=2));return
    transformer=json.loads(path.read_text())
    if baseline['test_ids']!=transformer['test_ids'] or baseline.get('dataset_manifest')!=transformer.get('dataset_manifest'):raise ValueError('Test partitions differ: cannot compare')
    print('| Model | Exact match | Micro-F1 | Macro-F1 | Macro precision | Macro recall | Urgency accuracy | Mean latency (ms) |')
    print('|---|---:|---:|---:|---:|---:|---:|---:|')
    for name,m in [('TF-IDF + LR',baseline),('Frozen MuRIL + LR',transformer)]:
        print(f"| {name} | {m['department_exact_match_accuracy']:.4f} | {m['department_micro_f1']:.4f} | {m['department_macro_f1']:.4f} | {m['department_macro_precision']:.4f} | {m['department_macro_recall']:.4f} | {m['learned']['urgency_report']['accuracy']:.4f} | {m['inference_latency_ms']['mean']:.2f} |")
if __name__=='__main__':main()
