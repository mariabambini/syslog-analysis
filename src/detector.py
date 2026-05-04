"""
detector.py
───────────
Orquestra o pipeline completo:
  parse → treino → detecção de anomalias
"""

import logging
import os

from parser     import LogParser
from classifier import DeepLogClassifier
from config     import DATA_PARSED, DEEPLOG_TOP_K, DEEPLOG_WINDOW_SIZE

logger = logging.getLogger(__name__)


def load_event_ids_from_parsed(name: str) -> list[int]:
    """Lê um arquivo .eventids já gerado pelo parser."""
    path = os.path.join(DATA_PARSED, name)
    with open(path) as f:
        return [int(line.strip()) for line in f if line.strip()]


def flatten_sequences(sequences: dict[str, list[int]]) -> list[int]:
    """Concatena todas as sequências num único vetor para treino."""
    flat = []
    for ids in sequences.values():
        flat.extend(ids)
    return flat


class AnomalyDetector:
    def __init__(self):
        self.parser: LogParser | None = None
        self.classifier: DeepLogClassifier | None = None

    # ── Fase 1: parse ──────────────────────────────────────────────────────

    def run_parser(self, log_dir: str) -> dict[str, list[int]]:
        logger.info("=== FASE 1: Parse com Drain3 ===")
        self.parser = LogParser()
        sequences   = self.parser.parse_directory(log_dir)
        self.parser.save_results(sequences)
        self.parser.print_templates()
        return sequences

    # ── Fase 2: treino ─────────────────────────────────────────────────────

    def run_training(self, sequences: dict[str, list[int]]):
        logger.info("=== FASE 2: Treino do DeepLog ===")
        event_ids    = flatten_sequences(sequences)
        num_classes  = max(event_ids) + 1   # IDs são contínuos a partir de 0

        self.classifier = DeepLogClassifier(num_classes)
        self.classifier.train(event_ids)

    # ── Fase 3: detecção ───────────────────────────────────────────────────

    def run_detection(self, sequences: dict[str, list[int]]) -> dict[str, list[dict]]:
        logger.info("=== FASE 3: Detecção de Anomalias ===")

        if self.classifier is None:
            raise RuntimeError("Rode run_training() antes de run_detection().")

        results = {}
        for fname, ids in sequences.items():
            logger.info(f"Analisando: {fname}")
            anomalies = self.classifier.predict_anomalies(ids)
            results[fname] = anomalies

            pct = len(anomalies) / max(1, len(ids) - DEEPLOG_WINDOW_SIZE) * 100
            logger.info(f"  {len(anomalies)} anomalias em {len(ids)} eventos ({pct:.1f}%)")

        return results

    # ── Pipeline completo ──────────────────────────────────────────────────

    def full_pipeline(self, log_dir: str) -> dict[str, list[dict]]:
        sequences = self.run_parser(log_dir)
        self.run_training(sequences)
        return self.run_detection(sequences)

    # ── Carregar modelo existente + detectar ───────────────────────────────

    def detect_only(self, log_dir: str, num_classes: int) -> dict[str, list[dict]]:
        """Usa modelo já treinado para detectar em novos logs."""
        logger.info("=== Parse + Detecção (modelo pré-treinado) ===")
        sequences = self.run_parser(log_dir)

        self.classifier = DeepLogClassifier(num_classes)
        self.classifier.load()

        return self.run_detection(sequences)
