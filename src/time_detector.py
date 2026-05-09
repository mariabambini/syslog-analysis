import re
import os
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, time

logger = logging.getLogger(__name__)

# horário de aula
ALLOWED_START = time(7, 30)
ALLOWED_END   = time(23, 0)

def is_allowed(t: time) -> bool:
    return ALLOWED_START <= t <= ALLOWED_END

_TS_RE = re.compile(
    r"^(?P<month>\w{3})\s+(?P<day>\d{1,2})\s+(?P<hour>\d{2}):(?P<min>\d{2}):(?P<sec>\d{2})"
    r"\s+(?P<hostname>\S+)" # nome da máquina destino
    r"\s+(?P<process>\S+):" # processo[pid]:
    r"\s+(?P<message>.*)" # mensagem
)

ACCESS_PATTERNS = [
    # SSH aceito: extrai IP de origem
    {
        "name": "ssh_login",
        "regex": re.compile(
            r"Accepted (?:password|publickey) for (?P<user>\S+) from (?P<src_ip>\S+)"
        ),
        "src_field": "src_ip",
    },
    # SSH falhou (também vale registrar fora do horário)
    {
        "name": "ssh_failed",
        "regex": re.compile(
            r"Failed (?:password|publickey) for (?:invalid user )?(?P<user>\S+) from (?P<src_ip>\S+)"
        ),
        "src_field": "src_ip",
    },
    # sudo: usa o hostname como origem (acesso local)
    {
        "name": "sudo",
        "regex": re.compile(
            r"(?P<user>\S+)\s*:.*USER=(?P<target_user>\S+)\s*;.*COMMAND=(?P<command>.+)"
        ),
        "src_field": None, # origem = hostname da linha
    },
    # su - mudança de usuário
    {
        "name": "su",
        "regex": re.compile(
            r"session opened for user (?P<user>\S+) by (?P<by_user>\S+)"
        ),
        "src_field": None,
    },
]

@dataclass
class TimeAnomaly:
    timestamp_raw: str # "May  3 02:13:44"
    time_of_day:   str # "02:13:44"
    hostname: str # máquina onde ocorreu
    source: str # IP ou hostname de origem
    user: str # usuário envolvido
    event_type: str # ssh_login, sudo, etc.
    message: str # linha completa do log
    log_file: str # arquivo de origem


def parse_line(raw: str, log_file: str) -> TimeAnomaly | None:
    m = _TS_RE.match(raw)
    if not m:
        return None

    hour     = int(m.group("hour"))
    minute   = int(m.group("min"))
    second   = int(m.group("sec"))
    t        = time(hour, minute, second)
    hostname = m.group("hostname")
    message  = m.group("message")
    ts_raw   = f"{m.group('month')} {m.group('day'):>2} {m.group('hour')}:{m.group('min')}:{m.group('sec')}"

    if is_allowed(t):
        return None

    for pattern in ACCESS_PATTERNS:
        pm = pattern["regex"].search(message)
        if not pm:
            continue

        user = pm.groupdict().get("user", "?")

        src_field = pattern["src_field"]
        if src_field and src_field in pm.groupdict():
            source = pm.group(src_field)
        else:
            source = hostname

        return TimeAnomaly(
            timestamp_raw = ts_raw,
            time_of_day   = f"{hour:02d}:{minute:02d}:{second:02d}",
            hostname      = hostname,
            source        = source,
            user          = user,
            event_type    = pattern["name"],
            message       = raw.strip(),
            log_file      = log_file,
        )

    return None

class TimeAnomalyDetector:

    def __init__(self,
                 allowed_start: time = ALLOWED_START,
                 allowed_end:   time = ALLOWED_END):
        self.allowed_start = allowed_start
        self.allowed_end   = allowed_end

    def scan_file(self, log_path: str) -> list[TimeAnomaly]:
        anomalies = []
        log_file  = os.path.basename(log_path)

        with open(log_path, "r", errors="replace") as f:
            for raw in f:
                anomaly = parse_line(raw, log_file)
                if anomaly:
                    anomalies.append(anomaly)

        logger.info(
            f"{log_file}: {len(anomalies)} acessos fora do horário "
            f"({self.allowed_start.strftime('%H:%M')}–{self.allowed_end.strftime('%H:%M')})"
        )
        return anomalies

    def scan_directory(self, directory: str) -> list[TimeAnomaly]:
        all_anomalies = []
        for fname in sorted(os.listdir(directory)):
            if fname.endswith(".log"):
                path = os.path.join(directory, fname)
                all_anomalies.extend(self.scan_file(path))
        return all_anomalies

    def print_report(self, anomalies: list[TimeAnomaly]):
        if not anomalies:
            print("\n✓ Nenhum acesso fora do horário permitido encontrado.\n")
            return

        # Agrupa por máquina de origem
        by_source: dict[str, list[TimeAnomaly]] = {}
        for a in anomalies:
            by_source.setdefault(a.source, []).append(a)

        print(f"\n{'═'*65}")
        print(f"  ACESSOS FORA DO HORÁRIO  ({self.allowed_start.strftime('%H:%M')} – {self.allowed_end.strftime('%H:%M')})")
        print(f"  Total: {len(anomalies)} evento(s) de {len(by_source)} origem(ns) distinta(s)")
        print(f"{'═'*65}")

        for source, events in sorted(by_source.items(), key=lambda x: -len(x[1])):
            print(f"\n  🖥  Origem: {source}  ({len(events)} evento(s))")
            print(f"  {'─'*55}")
            for e in events:
                print(
                    f"    {e.time_of_day}  "
                    f"[{e.event_type:12s}]  "
                    f"host={e.hostname}  "
                    f"user={e.user}"
                )

        print(f"\n{'═'*65}\n")

    def save_json(self, anomalies: list[TimeAnomaly], output_dir: str):
        os.makedirs(output_dir, exist_ok=True)
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(output_dir, f"time_anomalies_{ts}.json")

        payload = {
            "generated_at":  datetime.now().isoformat(),
            "allowed_window": {
                "start": self.allowed_start.strftime("%H:%M"),
                "end":   self.allowed_end.strftime("%H:%M"),
            },
            "total": len(anomalies),
            "anomalies": [asdict(a) for a in anomalies],
        }

        with open(path, "w") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        logger.info(f"Relatório salvo em: {path}")
        return path


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    target = sys.argv[1] if len(sys.argv) > 1 else "data/raw"

    detector = TimeAnomalyDetector()

    if os.path.isfile(target):
        anomalies = detector.scan_file(target)
    else:
        anomalies = detector.scan_directory(target)

    detector.print_report(anomalies)
    detector.save_json(anomalies, "output/reports")
