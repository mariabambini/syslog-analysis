from dataclasses import dataclass


@dataclass
class DetectionMetrics:
    tp: int = 0 # anomalias reais detectadas
    fp: int = 0 # normais classificadas como anomalia
    tn: int = 0 # normais classificadas como normais
    fn: int = 0 # anomalias reais não detectadas

    @property
    def precision(self) -> float:
        return self.tp / (self.tp + self.fp) if (self.tp + self.fp) else 0.0

    @property
    def recall(self) -> float:
        return self.tp / (self.tp + self.fn) if (self.tp + self.fn) else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) else 0.0

    @property
    def accuracy(self) -> float:
        total = self.tp + self.fp + self.tn + self.fn
        return (self.tp + self.tn) / total if total else 0.0

    def __str__(self):
        return (
            f"Precision: {self.precision:.4f} | "
            f"Recall: {self.recall:.4f} | "
            f"F1: {self.f1:.4f} | "
            f"Accuracy: {self.accuracy:.4f}"
        )


def evaluate(anomaly_positions: list[int],
             ground_truth_anomalies: set[int],
             total_positions: int) -> DetectionMetrics:
    detected = set(anomaly_positions)
    m = DetectionMetrics()
    m.tp = len(detected & ground_truth_anomalies)
    m.fp = len(detected - ground_truth_anomalies)
    m.fn = len(ground_truth_anomalies - detected)
    m.tn = total_positions - m.tp - m.fp - m.fn
    return m
