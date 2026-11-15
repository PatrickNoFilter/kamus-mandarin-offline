#!/usr/bin/env python3
"""Build kamus_data.js from CC-CPLUSDICT_id.u8 (Indonesian CC-CEDICT).

Source: R8VEN-LLC/CC-CPLUSDICT, dictionaries/CC-CPLUSDICT_id.u8
  124.769 entries, CC BY-SA 4.0, machine-translated ID glosses from CC-CEDICT.
Format per line: TRAD SIMP [[pinyin with tone numbers]] /sense1/sense2/CL:.../
Output: data/kamus_data.js with KAMUS_META + KAMUS rows:
  [simp, trad ('' if == simp), pinyin with tone marks, pinyin plain, gloss, classifiers]
Rows merged on (simp, pinyin-plain): same headword+reading keeps one row,
glosses concatenated, deduped.
"""
import json
import re
import sys
from collections import OrderedDict

SRC = "data/CC-CPLUSDICT_id.u8"
DST = "data/kamus_data.js"
HSK_SRC = "data/hsk_map.json"

LINE_RE = re.compile(r"^(\S+)\s+(\S+)\s+\[\[(.*)\]\]\s+/(.*)/\s*$")
SYL_RE = re.compile(r"[A-Za-z\xfc\xdc]+(?::)?[1-5]?")

TONED = {
    "a": ["ā", "á", "ǎ", "à", "a"],
    "e": ["ē", "é", "ě", "è", "e"],
    "i": ["ī", "í", "ǐ", "ì", "i"],
    "o": ["ō", "ó", "ǒ", "ò", "o"],
    "u": ["ū", "ú", "ǔ", "ù", "u"],
    "ü": ["ǖ", "ǘ", "ǚ", "ǜ", "ü"],
}


def tone_syllable(syl):
    """'xue2' -> 'xué', 'nu:3' -> 'nǚ', 'Lu:3' -> 'Lǚ', 'C' -> 'C', 'zi5' -> 'zi'."""
    m = re.match(r"^([A-Za-z\xfc\xdc]+)(:?)([1-5])?$", syl)
    if not m:
        return syl
    letters, colon, tone = m.group(1), m.group(2), m.group(3)
    if colon:
        letters = letters.replace("u", "ü").replace("U", "Ü")
    if not tone or tone in ("5",):
        return letters
    t = int(tone)
    low = letters.lower()
    idx = -1
    if "a" in low:
        idx = low.index("a")
    elif "e" in low:
        idx = low.index("e")
    elif "o" in low:
        idx = low.index("o")
    elif "iu" in low:
        idx = low.index("u")
    elif "ui" in low:
        idx = low.index("i")
    else:
        for i in range(len(low) - 1, -1, -1):
            if low[i] in "iuü":
                idx = i
                break
    if idx < 0:
        return letters
    ch = low[idx]
    marked = TONED[ch][t - 1]
    if letters[idx].isupper():
        marked = marked.upper()
    return letters[:idx] + marked + letters[idx + 1:]


def pinyin_to_marked(pinyin):
    return SYL_RE.sub(lambda m: tone_syllable(m.group(0)), pinyin)


def pinyin_to_plain(pinyin):
    s = re.sub(r"[0-9:]", "", pinyin)
    s = s.replace("ü", "u").replace("Ü", "u")
    return re.sub(r"[^a-z]", "", s.lower())


def parse_gloss(raw):
    senses, classifiers = [], []
    for part in raw.split("/"):
        part = part.strip()
        if not part:
            continue
        if part.startswith("CL:"):
            if part[3:].strip() not in classifiers:
                classifiers.append(part[3:].strip())
        elif part not in senses:
            senses.append(part)
    return senses, classifiers


def main():
    entries = []
    with open(SRC, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            m = LINE_RE.match(line)
            if not m:
                print("UNPARSED:", line[:120], file=sys.stderr)
                continue
            trad, simp, pinyin, gloss_raw = m.groups()
            senses, classifiers = parse_gloss(gloss_raw)
            if not senses:
                continue
            entries.append((trad, simp, pinyin, senses, classifiers))

    merged = OrderedDict()
    for trad, simp, pinyin, senses, classifiers in entries:
        plain = pinyin_to_plain(pinyin)
        key = (simp, plain)
        marked = pinyin_to_marked(pinyin)
        if key in merged:
            row = merged[key]
            if marked.lower() not in [p.lower() for p in row["pinyins"]]:
                row["pinyins"].append(marked)
            for s in senses:
                if s not in row["senses"]:
                    row["senses"].append(s)
            for c in classifiers:
                if c not in row["cl"]:
                    row["cl"].append(c)
        else:
            merged[key] = {
                "simp": simp,
                "trad": "" if trad == simp else trad,
                "pinyins": [marked],
                "plain": plain,
                "senses": list(senses),
                "cl": list(classifiers),
            }

    rows = []
    hsk = {}
    try:
        hsk = json.load(open(HSK_SRC, encoding="utf-8"))
    except FileNotFoundError:
        print("HSK map not found, continuing without level tags", file=sys.stderr)
    for r in merged.values():
        row = [r["simp"], r["trad"], " / ".join(r["pinyins"]), r["plain"], "; ".join(r["senses"]), "; ".join(r["cl"])]
        level = hsk.get(r["simp"])
        if level:
            row.append(level)
        rows.append(row)
    # sort by pinyin plain, then simp — stable browse order
    rows.sort(key=lambda r: (r[3], r[0]))

    meta = {
        "version": "1.0.0",
        "source": "CC-CPLUSDICT_id.u8 (R8VEN-LLC/CC-CPLUSDICT), CC BY-SA 4.0, derived from CC-CEDICT",
        "hsk_source": "drkameleon/complete-hsk-vocabulary (HSK 3.0 wordlists, levels 1-6)",
        "source_entries": len(entries),
        "entries": len(rows),
        "hsk_tagged": sum(1 for r in rows if len(r) > 6),
        "note": "Arti Indonesia adalah terjemahan mesin dari definisi Inggris CC-CEDICT; sebagian kecil entri masih mengandung bahasa Inggris.",
    }
    with open(DST, "w", encoding="utf-8") as f:
        f.write("// Kamus Mandarin Offline — data, dibangkitkan tools/build_data.py, JANGAN edit manual\n")
        f.write("// Sumber: CC-CPLUSDICT_id.u8 (CC BY-SA 4.0, turunan CC-CEDICT)\n")
        f.write("const KAMUS_META=" + json.dumps(meta, ensure_ascii=False, separators=(",", ":")) + ";\n")
        f.write("const KAMUS=" + json.dumps(rows, ensure_ascii=False, separators=(",", ":")) + ";\n")

    print(f"source entries: {len(entries)}")
    print(f"merged entries: {len(rows)}")
    print(f"sample: {rows[1000]}")
    print(f"sample: {[r for r in rows if r[0] == '学习']}")
    print(f"sample: {[r for r in rows if r[0] == '谢谢']}")
    print(f"sample: {[r for r in rows if r[0] == '印度尼西亚']}")


if __name__ == "__main__":
    main()
