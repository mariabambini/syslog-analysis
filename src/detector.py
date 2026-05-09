import logging
import os

from parser     import LogParser
from classifier import DeepLogClassifier
from config     import DATA_PARSED, DEEPLOG_TOP_K, DEEPLOG_WINDOW_SIZE

logger = logging.getLogger(__name__)


def load_event_ids_from_parsed(name: str) -> list[int]:
    path = os.path.join(DATA_PARSED, name)
    with open(path) as f:
        return [int(line.strip()) for line in f if line.strip()]


def flatten_sequences(sequences: dict[str, list[int]]) -> list[int]:
    flat = []
    for ids in sequences.values():
        flat.extend(ids)
    return flat


class AnomalyDetector:
    def __init__(self):
        self.parser: LogParser | None = None
        self.classifier: DeepLogClassifier | None = None

    def run_parser(self, log_dir: str) -> dict[str, list[int]]:
        logger.info("Parsing em execução...")
        self.parser = LogParser()
        sequences   = self.parser.parse_directory(log_dir)
        self.parser.save_results(sequences)
        self.parser.print_templates()
        return sequences

    def run_training(self, sequences: dict[str, list[int]]):
        logger.info("Treinando DeepLog...")
        event_ids    = flatten_sequences(sequences)
        num_classes  = max(event_ids) + 1

        self.classifier = DeepLogClassifier(num_classes)
        self.classifier.train(event_ids)

    def run_detection(self, sequences: dict[str, list[int]]) -> dict[str, list[dict]]:
        logger.info("Detectando anomalias...")

        if self.classifier is None:
            raise RuntimeError("Rode run_training() antes de run_detection().")

        results = {}
        for fname, ids in sequences.items():
            logger.info(f"Analisando: {fname}")
            anomalies = self.classifier.predict_anomalies(ids)
            results[fname] = anomalies

            pct = len(anomalies) / max(1, len(ids) - DEEPLOG_WINDOW_SIZE) * 100
            logger.info(f"{len(anomalies)} anomalias em {len(ids)} eventos ({pct:.1f}%)")

        return results

    def full_pipeline(self, log_dir: str) -> dict[str, list[dict]]:
        sequences = self.run_parser(log_dir)
        self.run_training(sequences)
        return self.run_detection(sequences)

    def detect_only(self, log_dir: str, num_classes: int) -> dict[str, list[dict]]:
        logger.info("Parsing e detedção com modelo pré-treinado")
        sequences = self.run_parser(log_dir)

        self.classifier = DeepLogClassifier(num_classes)
        self.classifier.load()

        return self.run_detection(sequences)
