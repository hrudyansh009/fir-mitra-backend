import os
import re
import json


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def split_en(text: str) -> dict[int, str]:
    parts = re.split(r"===\s*SECTION\s*(\d+)\s*===", text, flags=re.IGNORECASE)
    out = {}
    for i in range(1, len(parts), 2):
        sec = int(parts[i])
        out[sec] = parts[i + 1].strip()
    return out


def split_mr(text: str) -> dict[int, str]:
    parts = re.split(r"===\s*कलम\s*(\d+)\s*===", text)
    out = {}
    for i in range(1, len(parts), 2):
        sec = int(parts[i])
        out[sec] = parts[i + 1].strip()
    return out


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    en_path = os.path.join(base_dir, "data", "corpus", "scst", "scst_act_en.txt")
    mr_path = os.path.join(base_dir, "data", "corpus", "scst", "scst_act_mr.txt")
    out_jsonl = os.path.join(base_dir, "data", "corpus", "scst_offences", "offences.jsonl")

    if not os.path.exists(en_path):
        raise SystemExit(f"Missing: {en_path}")
    if not os.path.exists(mr_path):
        raise SystemExit(f"Missing: {mr_path}")

    en_map = split_en(read_text(en_path))
    mr_map = split_mr(read_text(mr_path))

    os.makedirs(os.path.dirname(out_jsonl), exist_ok=True)

    n = 0
    with open(out_jsonl, "w", encoding="utf-8") as w:
        for sec in range(1, 24):
            en = en_map.get(sec, "")
            mr = mr_map.get(sec, "")
            if not en and not mr:
                continue

            # ✅ IMPORTANT: numeric id for AnyIndex (it casts id to int)
            doc_id = sec  # int 1..23

            text = f"SCST Act Section {sec}\n\n[MR]\n{mr}\n\n[EN]\n{en}".strip()
            meta = {"section_no": sec, "section_key": f"scst_section_{sec:02d}"}

            w.write(json.dumps({"id": doc_id, "text": text, "meta": meta}, ensure_ascii=False) + "\n")
            n += 1

    print(f"✅ Built {n} records -> {out_jsonl}")


if __name__ == "__main__":
    main()