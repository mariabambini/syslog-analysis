import re
import json
import os
import sys
import logging

UTILS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "utils", "Drain3")
sys.path.insert(0, UTILS_DIR)

from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig
from drain3.masking import MaskingInstruction

from config import (
    DRAIN_SIM_TH, DRAIN_DEPTH, DRAIN_MAX_CHILDREN, DRAIN_MAX_CLUSTERS,
    DRAIN_MASKING, SYSLOG_REGEX, DATA_PARSED
)

logger = logging.getLogger(__name__)

def _build_drain_config() -> TemplateMinerConfig:
    cfg = TemplateMinerConfig()
    cfg.drain_sim_th       = DRAIN_SIM_TH
    cfg.drain_depth        = DRAIN_DEPTH
    cfg.drain_max_children = DRAIN_MAX_CHILDREN
    cfg.max_clusters       = DRAIN_MAX_CLUSTERS
    cfg.parametrize_numeric_tokens = True

    cfg.masking_instructions = [
        MaskingInstruction(m["regex_pattern"], m["mask_with"])
        for m in DRAIN_MASKING
    ]
    return cfg

_SYSLOG_RE = re.compile(SYSLOG_REGEX)

def extract_message(raw_line: str) -> str:
    m = _SYSLOG_RE.match(raw_line)
    return m.group(1).strip() if m else raw_line.strip()

class LogParser:
    def __init__(self):
        self.miner = TemplateMiner(config=_build_drain_config())
        self.templates: dict[int, str] = {}

    def parse_file(self, log_path: str) -> list[int]:
        event_ids: list[int] = []
        logger.info(f"Parseando: {log_path}")

        with open(log_path, "r", errors="replace") as f:
            for lineno, raw in enumerate(f, 1):
                raw = raw.strip()
                if not raw:
                    continue

                message = extract_message(raw)
                result  = self.miner.add_log_message(message)

                if result is None:
                    continue

                cid      = result["cluster_id"]
                template = result["template_mined"]

                self.templates[cid] = template
                event_ids.append(cid)

                if lineno % 5000 == 0:
                    logger.info(f"  {lineno} linhas processadas, {len(self.templates)} clusters")

        logger.info(f"  Concluído: {len(event_ids)} eventos, {len(self.templates)} templates únicos")
        return event_ids

    def parse_directory(self, directory: str) -> dict[str, list[int]]:
        results = {}
        for fname in sorted(os.listdir(directory)):
            if fname.endswith(".log"):
                path = os.path.join(directory, fname)
                results[fname] = self.parse_file(path)
        return results

    def save_results(self, sequences: dict[str, list[int]]):
        # Templates
        templates_path = os.path.join(DATA_PARSED, "templates.json")
        with open(templates_path, "w") as f:
            json.dump(self.templates, f, indent=2)
        logger.info(f"Templates salvos em: {templates_path}")

        # Sequências por arquivo
        for fname, ids in sequences.items():
            out_name = fname.replace(".log", ".eventids")
            out_path = os.path.join(DATA_PARSED, out_name)
            with open(out_path, "w") as f:
                f.write("\n".join(map(str, ids)))
            logger.info(f"Event IDs salvos em: {out_path}")

    def print_templates(self):
        print(f"\n{'─'*60}")
        print(f"  {len(self.templates)} templates descobertos pelo Drain3")
        print(f"{'─'*60}")
        for cid, tmpl in sorted(self.templates.items()):
            print(f"  [{cid:4d}] {tmpl}")
        print(f"{'─'*60}\n")

if __name__ == "__main__":
    import sys
    from config import DATA_RAW

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    target = sys.argv[1] if len(sys.argv) > 1 else DATA_RAW

    parser = LogParser()

    if os.path.isfile(target):
        fname    = os.path.basename(target)
        sequences = {fname: parser.parse_file(target)}
    else:
        sequences = parser.parse_directory(target)

    parser.save_results(sequences)
    parser.print_templates()
