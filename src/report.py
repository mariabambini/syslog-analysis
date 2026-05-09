import json
import os
from datetime import datetime
from config import OUTPUT_REPORTS

def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def save_json(results: dict[str, list[dict]], templates: dict[int, str] | None = None):
    payload = {
        "generated_at": datetime.now().isoformat(),
        "templates": {str(k): v for k, v in (templates or {}).items()},
        "anomalies_by_file": results,
    }
    path = os.path.join(OUTPUT_REPORTS, f"anomalies_{_timestamp()}.json")
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"Relatório JSON salvo em: {path}")
    return path


def print_summary(results: dict[str, list[dict]], templates: dict[int, str] | None = None):
    templates = templates or {}
    total_anomalies = sum(len(v) for v in results.values())

    print(f"\n{'═'*60}")
    print(f"  Relatório de anomalias — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'═'*60}")
    print(f"  Total de anomalias detectadas: {total_anomalies}")
    print(f"{'─'*60}")

    for fname, anomalies in results.items():
        print(f"\n  Arquivo: {fname}  ({len(anomalies)} anomalias)")
        if not anomalies:
            print("    ✓ Nenhuma anomalia encontrada.")
            continue

        for a in anomalies[:20]: # mostra no máximo 20 por arquivo
            tmpl = templates.get(a["event_id"], "?")
            print(f"[pos {a['position']:6d}] event_id={a['event_id']:4d} template='{tmpl}'")

        if len(anomalies) > 20:
            print(f"    ... e mais {len(anomalies) - 20} anomalias (ver JSON completo)")

    print(f"\n{'═'*60}\n")
