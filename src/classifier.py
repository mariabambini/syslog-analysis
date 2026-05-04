"""
classifier.py
─────────────
Modelo DeepLog: LSTM que aprende sequências normais de event IDs
e detecta anomalias quando a previsão falha.
"""

import os
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import logging

from config import (
    DEEPLOG_WINDOW_SIZE, DEEPLOG_TOP_K,
    DEEPLOG_INPUT_SIZE, DEEPLOG_HIDDEN_SIZE, DEEPLOG_NUM_LAYERS,
    DEEPLOG_EPOCHS, DEEPLOG_BATCH_SIZE, DEEPLOG_LR,
    OUTPUT_MODELS
)

logger = logging.getLogger(__name__)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ── Dataset ────────────────────────────────────────────────────────────────

class LogSequenceDataset(Dataset):
    """
    Janelas deslizantes sobre uma sequência de event IDs.
    Entrada: janela de tamanho WINDOW_SIZE
    Alvo:    próximo event ID
    """
    def __init__(self, event_ids: list[int], window_size: int = DEEPLOG_WINDOW_SIZE):
        self.window_size = window_size
        self.samples: list[tuple[list[int], int]] = []

        for i in range(len(event_ids) - window_size):
            window = event_ids[i : i + window_size]
            target = event_ids[i + window_size]
            self.samples.append((window, target))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        window, target = self.samples[idx]
        x = torch.tensor(window, dtype=torch.float32).unsqueeze(-1)  # (W, 1)
        y = torch.tensor(target, dtype=torch.long)
        return x, y


# ── Modelo LSTM ────────────────────────────────────────────────────────────

class DeepLogLSTM(nn.Module):
    def __init__(self, num_classes: int,
                 input_size:  int = DEEPLOG_INPUT_SIZE,
                 hidden_size: int = DEEPLOG_HIDDEN_SIZE,
                 num_layers:  int = DEEPLOG_NUM_LAYERS):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True
        )
        self.fc = nn.Linear(hidden_size, num_classes)

    def forward(self, x):
        out, _ = self.lstm(x)          # (B, W, H)
        out     = out[:, -1, :]        # último passo de tempo (B, H)
        return self.fc(out)            # (B, num_classes)


# ── Treino ─────────────────────────────────────────────────────────────────

class DeepLogClassifier:
    def __init__(self, num_classes: int):
        self.num_classes = num_classes
        self.model = DeepLogLSTM(num_classes).to(DEVICE)
        self.model_path = os.path.join(OUTPUT_MODELS, "deeplog.pt")

    def train(self, event_ids: list[int]):
        dataset = LogSequenceDataset(event_ids)
        if len(dataset) == 0:
            raise ValueError("Sequência muito curta para treinar (precisa de mais linhas que WINDOW_SIZE).")

        loader = DataLoader(dataset, batch_size=DEEPLOG_BATCH_SIZE, shuffle=True)
        optimizer = torch.optim.Adam(self.model.parameters(), lr=DEEPLOG_LR)
        criterion = nn.CrossEntropyLoss()

        self.model.train()
        for epoch in range(1, DEEPLOG_EPOCHS + 1):
            total_loss = 0.0
            for x, y in loader:
                x, y = x.to(DEVICE), y.to(DEVICE)
                optimizer.zero_grad()
                logits = self.model(x)
                loss   = criterion(logits, y)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()

            if epoch % 10 == 0:
                avg = total_loss / len(loader)
                logger.info(f"  Epoch {epoch:3d}/{DEEPLOG_EPOCHS} | loss={avg:.4f}")

        torch.save(self.model.state_dict(), self.model_path)
        logger.info(f"Modelo salvo em: {self.model_path}")

    def load(self):
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Modelo não encontrado: {self.model_path}")
        self.model.load_state_dict(torch.load(self.model_path, map_location=DEVICE))
        self.model.eval()
        logger.info("Modelo carregado.")

    # ── Inferência ─────────────────────────────────────────────────────────

    def predict_anomalies(self, event_ids: list[int],
                          top_k: int = DEEPLOG_TOP_K,
                          window_size: int = DEEPLOG_WINDOW_SIZE
                          ) -> list[dict]:
        """
        Retorna lista de dicionários com info de cada posição anômala.
        Uma posição é anômala quando o event ID real NÃO está entre
        as top_k previsões do modelo.
        """
        self.model.eval()
        anomalies = []

        with torch.no_grad():
            for i in range(len(event_ids) - window_size):
                window = event_ids[i : i + window_size]
                target = event_ids[i + window_size]

                x = torch.tensor(window, dtype=torch.float32).unsqueeze(0).unsqueeze(-1).to(DEVICE)
                logits = self.model(x)                       # (1, num_classes)
                topk   = torch.topk(logits, top_k, dim=1).indices.squeeze().tolist()

                if isinstance(topk, int):
                    topk = [topk]

                if target not in topk:
                    anomalies.append({
                        "position": i + window_size,
                        "event_id": target,
                        "expected_topk": topk,
                    })

        return anomalies
