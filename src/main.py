"""
main.py
───────
Entry point CLI.

Modos:
  train     → parse + treino (sem detecção)
  detect    → parse + detecção com modelo já treinado
  full      → parse + treino + detecção (padrão)
  parse     → só parse (gera event IDs)

Uso:
  python main.py full   --logs data/raw
  python main.py train  --logs data/raw
  python main.py detect --logs data/raw --classes 50
  python main.py parse  --logs data/raw
"""

import argparse
import logging
import sys
import os

# garante que src/ está no path
sys.path.insert(0, os.path.dirname(__file__))

from detector import AnomalyDetector
from report   import save_json, print_summary
from config   import DATA_RAW


def setup_logging(verbose: bool):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def main():
    parser = argparse.ArgumentParser(
        description="DeepLog + Drain3 — Detecção de Anomalias em Logs"
    )
    parser.add_argument("mode", choices=["full", "train", "detect", "parse"],
                        nargs="?", default="full",
                        help="Modo de execução (padrão: full)")
    parser.add_argument("--logs",    default=DATA_RAW,
                        help=f"Diretório com logs .log (padrão: {DATA_RAW})")
    parser.add_argument("--classes", type=int, default=None,
                        help="Número de classes (necessário para modo detect)")
    parser.add_argument("--verbose", action="store_true",
                        help="Log detalhado")
    args = parser.parse_args()

    setup_logging(args.verbose)
    logger = logging.getLogger("main")

    if not os.path.isdir(args.logs):
        logger.error(f"Diretório não encontrado: {args.logs}")
        sys.exit(1)

    detector = AnomalyDetector()

    # ── parse only ────────────────────────────────────────────────────────
    if args.mode == "parse":
        sequences = detector.run_parser(args.logs)
        print(f"\nArquivos processados: {len(sequences)}")
        for fname, ids in sequences.items():
            print(f"  {fname}: {len(ids)} eventos")
        return

    # ── train only ────────────────────────────────────────────────────────
    if args.mode == "train":
        sequences = detector.run_parser(args.logs)
        detector.run_training(sequences)
        print("\nTreino concluído. Modelo salvo em output/models/deeplog.pt")
        return

    # ── detect only (modelo pré-treinado) ────────────────────────────────
    if args.mode == "detect":
        if args.classes is None:
            logger.error("Informe --classes N para o modo detect.")
            sys.exit(1)
        results = detector.detect_only(args.logs, args.classes)
        templates = detector.parser.templates if detector.parser else {}
        print_summary(results, templates)
        save_json(results, templates)
        return

    # ── full pipeline ─────────────────────────────────────────────────────
    results   = detector.full_pipeline(args.logs)
    templates = detector.parser.templates if detector.parser else {}
    print_summary(results, templates)
    save_json(results, templates)


if __name__ == "__main__":
    main()
