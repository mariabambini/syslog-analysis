# syslog-analysis

Ferramenta de detecção de anomalias em logs de sistema, combinando o parser **Drain3** com o modelo de aprendizado profundo **DeepLog** (LSTM), além de um detector de acessos fora do horário permitido.

Desenvolvida para análise de logs enviados de máquinas virtuais, o sistema é capaz de identificar padrões anômalos de comportamento tanto por sequência de eventos quanto por horário de acesso.

---

## Sumário

- [Visão Geral](#visão-geral)
- [Arquitetura](#arquitetura)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Guia de Execução](#guia-de-execução)
  - [Pipeline Completo](#1-pipeline-completo-full)
  - [Somente Parse](#2-somente-parse-parse)
  - [Somente Treino](#3-somente-treino-train)
  - [Somente Detecção DeepLog](#4-somente-detecção-detect)
  - [Verificação de Horário](#5-verificação-de-horário-timescan)
- [Módulos](#módulos)
- [Saídas Geradas](#saídas-geradas)
- [Configurações](#configurações)
- [Formato de Log Suportado](#formato-de-log-suportado)

---

## Visão Geral

O sistema opera em duas frentes de detecção independentes e complementares:

**1. Detecção por sequência (DeepLog + Drain3)**
O Drain3 agrupa as linhas de log em templates, atribuindo a cada uma um identificador de evento (event ID). A sequência desses IDs é então usada para treinar um modelo LSTM que aprende os padrões normais de comportamento do sistema. Durante a inferência, linhas cujo event ID não está entre as previsões esperadas pelo modelo são classificadas como anomalias.

**2. Detecção por horário (Time Detector)**
Regras baseadas em tempo identificam acessos SSH, execuções de `sudo` e trocas de usuário (`su`) realizados fora de uma janela de horário configurável. Para cada evento suspeito, o sistema registra o horário exato, o usuário envolvido, o hostname da máquina afetada e o endereço IP ou identificador de origem.

---

## Arquitetura

```
Logs da VM (.log)
       │
       ▼
┌─────────────┐
│   Drain3    │  ← Agrupa linhas em templates, gera Event IDs
│  (parser)   │
└──────┬──────┘
       │  sequência de Event IDs
       ▼
┌─────────────┐
│   DeepLog   │  ← LSTM treinado nos padrões normais
│   (LSTM)    │
└──────┬──────┘
       │  posições anômalas
       ▼
┌──────────────────┐
│  Time Detector   │  ← Regras de horário (paralelo ao DeepLog)
└──────┬───────────┘
       │
       ▼
  Relatórios JSON + Terminal
```

---

## Estrutura do Projeto

```
syslog-analysis/
│
├── data/
│   ├── raw/            ← logs brutos da VM (.log)
│   ├── parsed/         ← templates e event IDs gerados pelo Drain3
│   └── sequences/      ← sequências processadas
│
├── output/
│   ├── models/         ← modelo treinado (deeplog.pt)
│   └── reports/        ← relatórios de anomalia em JSON
│
├── src/
│   ├── main.py         ← entry point CLI
│   ├── config.py       ← parâmetros centrais do projeto
│   ├── parser.py       ← integração com Drain3
│   ├── classifier.py   ← modelo DeepLog (LSTM)
│   ├── detector.py     ← orquestra parser + classifier
│   ├── time_detector.py← detecção de acessos fora do horário
│   ├── metrics.py      ← métricas de avaliação (precision, recall, F1)
│   └── report.py       ← geração de relatórios
│
└── utils/
    ├── Drain3/         ← biblioteca Drain3 (local)
    └── DeepLog/        ← biblioteca DeepLog (local)
```

---

## Requisitos

- Python 3.10+
- PyTorch 2.0+
- Drain3

```
torch
drain3
```

---

## Instalação

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/syslog-analysis.git
cd syslog-analysis

# Instale as dependências
pip install torch drain3
```

Não é necessário instalar o Drain3 ou o DeepLog via pip — ambos estão incluídos localmente em `utils/`.

---

## Guia de Execução

Todos os comandos são executados a partir da raiz do projeto.

### Preparação

Coloque os arquivos de log da VM no diretório `data/raw/`. O sistema aceita qualquer arquivo com extensão `.log` no formato syslog padrão.

```
data/raw/
├── servidor-01.log
├── servidor-02.log
└── ...
```

---

### 1. Pipeline Completo (`full`)

Executa as três etapas em sequência: parse com Drain3, treino do DeepLog e detecção de anomalias, incluindo a verificação de horário.

```bash
python src/main.py full --logs data/raw
```

**Com horário personalizado:**

```bash
python src/main.py full --logs data/raw --start 08:00 --end 18:00
```

**Sem verificação de horário:**

```bash
python src/main.py full --logs data/raw --no-time-check
```

**O que acontece internamente:**

1. O Drain3 lê cada linha dos arquivos `.log`, extrai a mensagem útil (sem timestamp e hostname) e agrupa linhas semelhantes em templates. Cada template recebe um `cluster_id`.
2. A sequência de `cluster_id`s é usada para treinar o modelo LSTM. O modelo aprende quais event IDs tendem a aparecer após uma determinada janela de contexto.
3. Durante a detecção, cada posição da sequência é avaliada: se o event ID real não está entre as `top-k` previsões do modelo, a posição é marcada como anomalia.
4. Em paralelo, o detector de horário varre os arquivos em busca de eventos de acesso (SSH, sudo, su) fora da janela configurada.

---

### 2. Somente Parse (`parse`)

Executa apenas o Drain3, sem treinar ou detectar anomalias. Útil para inspecionar os templates gerados antes de treinar o modelo.

```bash
python src/main.py parse --logs data/raw
```

**Saída no terminal:**

```
────────────────────────────────────────────────────
  42 templates descobertos pelo Drain3
────────────────────────────────────────────────────
  [   1] Failed password for <*> from <IP> port <NUM>
  [   2] Accepted publickey for <*> from <IP> port <NUM>
  [   3] session opened for user <*> by <*>
  ...
────────────────────────────────────────────────────

Arquivos processados: 2
  servidor-01.log: 8432 eventos
  servidor-02.log: 5219 eventos
```

Os event IDs e templates são salvos em `data/parsed/`.

---

### 3. Somente Treino (`train`)

Executa o parse e treina o modelo DeepLog, sem rodar a detecção. Use quando quiser treinar com logs normais antes de analisar logs novos.

```bash
python src/main.py train --logs data/raw
```

O modelo treinado é salvo em `output/models/deeplog.pt`.

**Parâmetros de treino configuráveis em `config.py`:**

| Parâmetro | Padrão | Descrição |
|---|---|---|
| `DEEPLOG_EPOCHS` | 100 | Épocas de treino |
| `DEEPLOG_WINDOW_SIZE` | 10 | Tamanho da janela de contexto |
| `DEEPLOG_HIDDEN_SIZE` | 64 | Neurônios na camada LSTM |
| `DEEPLOG_TOP_K` | 9 | Quantas previsões são consideradas normais |
| `DEEPLOG_LR` | 0.001 | Taxa de aprendizado |

---

### 4. Somente Detecção (`detect`)

Usa um modelo já treinado para detectar anomalias em novos logs. É necessário informar o número de classes (número de templates únicos gerados na etapa de treino).

```bash
python src/main.py detect --logs data/raw --classes 50
```

O valor de `--classes` corresponde ao número de templates listados na saída do modo `parse`. Também pode ser consultado contando as entradas em `data/parsed/templates.json`.

**Com verificação de horário habilitada (padrão):**

```bash
python src/main.py detect --logs data/raw/novos --classes 50 --start 07:30 --end 23:00
```

---

### 5. Verificação de Horário (`timescan`)

Detecta exclusivamente acessos fora do horário permitido, sem envolver o DeepLog. É mais rápido e não requer modelo treinado.

```bash
python src/main.py timescan --logs data/raw
```

**Com horário personalizado:**

```bash
python src/main.py timescan --logs data/raw --start 09:00 --end 17:00
```

**Exemplo de saída:**

```
═════════════════════════════════════════════════════════════════
  ACESSOS FORA DO HORÁRIO  (07:30 – 23:00)
  Total: 3 evento(s) de 2 origem(ns) distinta(s)
═════════════════════════════════════════════════════════════════

  🖥  Origem: 192.168.1.55  (2 evento(s))
  ───────────────────────────────────────────────────────
    02:13:44  [ssh_login   ]  host=servidor-vm  user=root
    03:41:09  [ssh_login   ]  host=servidor-vm  user=root

  🖥  Origem: servidor-vm  (1 evento(s))
  ───────────────────────────────────────────────────────
    04:55:21  [sudo        ]  host=servidor-vm  user=user
```

**Tipos de eventos detectados:**

| Tipo | Trigger no log | Origem reportada |
|---|---|---|
| `ssh_login` | `Accepted password/publickey for user from IP` | IP remoto |
| `ssh_failed` | `Failed password for user from IP` | IP remoto |
| `sudo` | Execução de sudo com `USER=` e `COMMAND=` | Hostname local |
| `su` | `session opened for user X by Y` | Hostname local |

---

## Módulos

### `config.py`

Centraliza todos os parâmetros do projeto. É o único arquivo que precisa ser editado para ajustar o comportamento do sistema sem alterar a lógica dos outros módulos.

Parâmetros relevantes do Drain3:

- `DRAIN_SIM_TH` — limiar de similaridade entre clusters (0.0 a 1.0). Valores menores agrupam mais linhas num mesmo template; valores maiores criam mais templates distintos. O recomendado é entre `0.3` e `0.5`.
- `DRAIN_MASKING` — lista de expressões regulares aplicadas antes do parse para mascarar valores variáveis como IPs, números e UUIDs.
- `SYSLOG_REGEX` — expressão regular usada para extrair a mensagem útil de uma linha syslog, removendo timestamp, hostname e nome do processo.

### `parser.py`

Integra o Drain3 ao pipeline. Lê arquivos `.log` linha a linha, aplica a regex de extração de mensagem, processa cada mensagem pelo `TemplateMiner` e coleta a sequência de `cluster_id`s resultante. Salva os templates em `data/parsed/templates.json` e as sequências em arquivos `.eventids`.

### `classifier.py`

Implementa o modelo DeepLog como uma rede LSTM com PyTorch. Recebe sequências de event IDs, treina o modelo para prever o próximo event ID a partir de uma janela de contexto, e durante a inferência retorna as posições onde o evento real não estava entre as top-k previsões.

### `detector.py`

Orquestra o pipeline completo, chamando `parser.py` e `classifier.py` em sequência. Expõe métodos para execução por fase (`run_parser`, `run_training`, `run_detection`) e para o pipeline completo (`full_pipeline`).

### `time_detector.py`

Detector de anomalias baseado em regras temporais. Independente do DeepLog — não requer treino. Varre os logs em busca de eventos de acesso (SSH, sudo, su) e verifica se o horário do evento está dentro da janela configurada. Agrupa os resultados por máquina de origem no relatório.

### `metrics.py`

Fornece a classe `DetectionMetrics` com cálculo de precision, recall, F1 e accuracy. Útil quando ground truth está disponível para avaliar a qualidade da detecção.

### `report.py`

Gera relatórios das anomalias detectadas pelo DeepLog, tanto no terminal quanto em arquivo JSON em `output/reports/`.

---

## Saídas Geradas

| Arquivo | Localização | Conteúdo |
|---|---|---|
| `templates.json` | `data/parsed/` | Mapeamento `cluster_id → template` |
| `<nome>.eventids` | `data/parsed/` | Sequência de event IDs por arquivo de log |
| `deeplog.pt` | `output/models/` | Pesos do modelo LSTM treinado |
| `anomalies_<ts>.json` | `output/reports/` | Anomalias detectadas pelo DeepLog |
| `time_anomalies_<ts>.json` | `output/reports/` | Acessos fora do horário permitido |

---

## Configurações

Todos os parâmetros ficam em `src/config.py`. Os principais:

```python
# Horário padrão (também configurável via CLI com --start e --end)
ALLOWED_START = time(7, 30)
ALLOWED_END = time(23, 0)

# Drain3
DRAIN_SIM_TH = 0.4 # ajustar se templates ficarem ruins

# DeepLog
DEEPLOG_TOP_K = 9 # aumentar reduz falsos positivos
DEEPLOG_WINDOW_SIZE = 10 # janela de contexto da LSTM
DEEPLOG_EPOCHS = 100  # aumentar para logs maiores
```

---

## Formato de Log Suportado

O sistema espera logs no formato **syslog padrão**:

```
May  3 22:45:01 hostname processo[pid]: mensagem do evento
```

Exemplos reais:

```
May  3 02:13:44 servidor-vm sshd[1234]: Accepted password for root from 192.168.1.10 port 22 ssh2
May  3 04:55:21 servidor-vm sudo[5678]: user : TTY=pts/0 ; PWD=/home/user ; USER=root ; COMMAND=/bin/bash
May  3 07:02:11 servidor-vm kernel: [12345.678] OUT OF MEMORY: Kill process 999
```

Caso os logs apresentem um formato diferente (por exemplo, timestamp ISO 8601 do journald ou formato customizado), a regex `SYSLOG_REGEX` em `config.py` pode ser ajustada sem alterar nenhum outro arquivo.
