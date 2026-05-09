import argparse
import logging
import sys
import os
from datetime import time as dtime

# garante que src/ está no path
sys.path.insert(0, os.path.dirname(__file__))

from detector      import AnomalyDetector
from report        import save_json, print_summary
from time_detector import TimeAnomalyDetector
from config        import DATA_RAW, OUTPUT_REPORTS


def setup_logging(verbose: bool):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def parse_time(s: str) -> dtime:
    """Converte string 'HH:MM' em datetime.time."""
    try:
        h, m = s.split(":")
        return dtime(int(h), int(m))
    except Exception:
        raise argparse.ArgumentTypeError(f"Formato inválido: '{s}'. Use HH:MM")


def run_time_check(log_dir: str, start: dtime, end: dtime):
    """Executa a verificação de horário e imprime/salva o relatório."""
    td = TimeAnomalyDetector(allowed_start=start, allowed_end=end)
    anomalies = td.scan_directory(log_dir)
    td.print_report(anomalies)
    if anomalies:
        td.save_json(anomalies, OUTPUT_REPORTS)


def main():
    parser = argparse.ArgumentParser(
        description="DeepLog + Drain3 — Detecção de Anomalias em Logs"
    )
    parser.add_argument("mode",
                        choices=["full", "train", "detect", "parse", "timescan"],
                        nargs="?", default="full",
                        help="Modo de execução (padrão: full)")
    parser.add_argument("--logs",    default=DATA_RAW,
                        help=f"Diretório com logs .log (padrão: {DATA_RAW})")
    parser.add_argument("--classes", type=int, default=None,
                        help="Número de classes (necessário para modo detect)")
    parser.add_argument("--start",   default="07:30",
                        help="Início do horário permitido (padrão: 07:30)")
    parser.add_argument("--end",     default="23:00",
                        help="Fim do horário permitido (padrão: 23:00)")
    parser.add_argument("--no-time-check", action="store_true",
                        help="Desativa a verificação de horário no modo full")
    parser.add_argument("--verbose", action="store_true",
                        help="Log detalhado")
    args = parser.parse_args()

    setup_logging(args.verbose)
    logger = logging.getLogger("main")

    if not os.path.isdir(args.logs):
        logger.error(f"Diretório não encontrado: {args.logs}")
        sys.exit(1)

    allowed_start = parse_time(args.start)
    allowed_end   = parse_time(args.end)

    if args.mode == "timescan":
        run_time_check(args.logs, allowed_start, allowed_end)
        return

    if args.mode == "parse":
        detector  = AnomalyDetector()
        sequences = detector.run_parser(args.logs)
        print(f"\nArquivos processados: {len(sequences)}")
        for fname, ids in sequences.items():
            print(f"  {fname}: {len(ids)} eventos")
        return

    if args.mode == "train":
        detector  = AnomalyDetector()
        sequences = detector.run_parser(args.logs)
        detector.run_training(sequences)
        print("\nTreino concluído. Modelo salvo em output/models/deeplog.pt")
        return

    if args.mode == "detect":
        if args.classes is None:
            logger.error("Informe --classes N para o modo detect.")
            sys.exit(1)
        detector  = AnomalyDetector()
        results   = detector.detect_only(args.logs, args.classes)
        templates = detector.parser.templates if detector.parser else {}
        print_summary(results, templates)
        save_json(results, templates)

        if not args.no_time_check:
            print("\n── Verificação de Horário ──")
            run_time_check(args.logs, allowed_start, allowed_end)
        return

    detector  = AnomalyDetector()
    results   = detector.full_pipeline(args.logs)
    templates = detector.parser.templates if detector.parser else {}
    print_summary(results, templates)
    save_json(results, templates)

    if not args.no_time_check:
        print("\n── Verificação de Horário ──")
        run_time_check(args.logs, allowed_start, allowed_end)


if __name__ == "__main__":
    main()
