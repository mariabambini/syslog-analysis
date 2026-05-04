import os

# ── Diretórios ─────────────────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_RAW      = os.path.join(BASE_DIR, "data", "raw")
DATA_PARSED   = os.path.join(BASE_DIR, "data", "parsed")
DATA_SEQ      = os.path.join(BASE_DIR, "data", "sequences")
OUTPUT_MODELS = os.path.join(BASE_DIR, "output", "models")
OUTPUT_REPORTS= os.path.join(BASE_DIR, "output", "reports")

for _dir in [DATA_RAW, DATA_PARSED, DATA_SEQ, OUTPUT_MODELS, OUTPUT_REPORTS]:
    os.makedirs(_dir, exist_ok=True)

# ── Drain3 ─────────────────────────────────────────────────────────────────
DRAIN_SIM_TH       = 0.4   # limiar de similaridade entre clusters
DRAIN_DEPTH        = 4     # profundidade da árvore de parse
DRAIN_MAX_CHILDREN = 100
DRAIN_MAX_CLUSTERS = 1000

# Máscaras aplicadas ANTES do Drain3 (ordem importa)
DRAIN_MASKING = [
    {"regex_pattern": r"(\d{1,3}\.){3}\d{1,3}(:\d+)?", "mask_with": "<IP>"},
    {"regex_pattern": r"[0-9a-fA-F]{8}-[0-9a-fA-F-]{27}", "mask_with": "<UUID>"},
    {"regex_pattern": r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "mask_with": "<DT>"},
    {"regex_pattern": r"\b\d+\b", "mask_with": "<NUM>"},
]

# Regex para extrair a mensagem útil de uma linha syslog:
# Ex.: "May  3 12:34:01 hostname sshd[123]: Failed password for root"
#       → "Failed password for root"
SYSLOG_REGEX = (
    r"^\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\s+"   # timestamp
    r"\S+\s+"                                        # hostname
    r"\S+:\s+"                                       # processo[pid]:
    r"(.*)"                                          # mensagem (grupo 1)
)

# ── DeepLog ────────────────────────────────────────────────────────────────
DEEPLOG_WINDOW_SIZE = 10    # tamanho da janela de contexto (h)
DEEPLOG_TOP_K       = 9     # top-k predições consideradas normais
DEEPLOG_INPUT_SIZE  = 1     # 1 event ID por passo
DEEPLOG_HIDDEN_SIZE = 64    # neurônios LSTM
DEEPLOG_NUM_LAYERS  = 2     # camadas LSTM
DEEPLOG_EPOCHS      = 100
DEEPLOG_BATCH_SIZE  = 128
DEEPLOG_LR          = 0.001
