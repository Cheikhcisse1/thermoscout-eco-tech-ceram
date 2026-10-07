"""RAG léger: découpe les documents du dossier knowledge/ et les retrouve par BM25 (sans dépendance externe).

Réindexation automatique quand un fichier est ajouté, modifié ou supprimé.
"""
import math
import re
import threading
import unicodedata
from collections import Counter
from pathlib import Path

KB_DIR = Path(__file__).parent / "knowledge"
EXTS = {".md", ".txt"}
MAX_FILE = 1_000_000
CHUNK_CHARS = 600
STOP = set("""le la les un une des du de d l et ou en au aux a à est sont ce cet cette ces se sa son ses leur leurs
que qui quoi dont ne pas plus par pour sur sous dans avec sans il elle ils elles on nous vous je tu y mais donc car
the of to and is are be it as at by on or an quel quelle quels quelles comment pourquoi peut peux faire fait qu quoi
ca cela ceci alors aussi tout tous toute toutes etre avoir ete""".split())


SUFFIXES = ("issements", "issement", "ements", "ement", "ations", "ation", "ateurs", "ateur", "ees", "es", "ee",
            "er", "ez", "s", "x", "e")


def tokens(text: str) -> list[str]:
    t = unicodedata.normalize("NFKD", text.lower()).encode("ascii", "ignore").decode()
    out = []
    for w in re.findall(r"[a-z0-9]+", t):
        if w in STOP or len(w) < 2:
            continue
        for suf in SUFFIXES:  # radical français léger: financé / finance / financement → financ
            if w.endswith(suf) and len(w) - len(suf) >= 4:
                w = w[:-len(suf)]
                break
        out.append(w)
    return out


def _chunks(name: str, text: str):
    """Découpe par titres puis par paragraphes; chaque passage garde son titre."""
    title, buf, sections = name, [], []
    for line in text.splitlines():
        if re.match(r"^#{1,4}\s", line):
            if buf:
                sections.append((title, "\n".join(buf).strip()))
            title, buf = line.lstrip("# ").strip(), []
        else:
            buf.append(line)
    if buf:
        sections.append((title, "\n".join(buf).strip()))
    for title, body in sections:
        if not body:
            continue
        cur = ""
        # une « unité » = une ligne (puce ou paragraphe d'une ligne); on regroupe jusqu'à CHUNK_CHARS
        for unit in (u for u in body.splitlines() if u.strip()):
            while len(unit) > CHUNK_CHARS:  # ligne géante: coupe à la dernière phrase
                cut = unit.rfind(". ", 0, CHUNK_CHARS) + 1 or CHUNK_CHARS
                if cur:
                    yield title, cur.strip()
                    cur = ""
                yield title, unit[:cut].strip()
                unit = unit[cut:].strip()
            if cur and len(cur) + len(unit) > CHUNK_CHARS:
                yield title, cur.strip()
                cur = ""
            cur += unit + "\n"
        if cur.strip():
            yield title, cur.strip()


class Index:
    def __init__(self):
        self.lock = threading.Lock()
        self.sig = None
        self.docs: list[dict] = []
        self.df: Counter = Counter()
        self.avg = 1.0

    def _signature(self):
        if not KB_DIR.exists():
            return ()
        return tuple(sorted((p.name, p.stat().st_mtime_ns, p.stat().st_size) for p in KB_DIR.iterdir()
                            if p.suffix.lower() in EXTS and p.is_file()))

    def refresh(self):
        sig = self._signature()
        if sig == self.sig:
            return
        with self.lock:
            if sig == self.sig:
                return
            docs, df = [], Counter()
            for p in sorted(KB_DIR.iterdir()) if KB_DIR.exists() else []:
                if p.suffix.lower() not in EXTS or not p.is_file() or p.stat().st_size > MAX_FILE:
                    continue
                try:
                    text = p.read_text(encoding="utf-8-sig")
                except (UnicodeDecodeError, OSError):
                    continue
                m = re.search(r"^#\s+(.+)$", text, re.M)
                doc_title = m.group(1) if m else p.stem.replace("_", " ")
                for title, body in _chunks(p.stem, text):
                    toks = tokens(doc_title + " " + title + " " + title + " " + body)  # titres de document et de section
                    if not toks:
                        continue
                    docs.append({"file": p.name, "title": title, "text": body, "tf": Counter(toks), "len": len(toks)})
                    df.update(set(toks))
            self.docs, self.df = docs, df
            self.avg = (sum(d["len"] for d in docs) / len(docs)) if docs else 1.0
            self.sig = sig

    def search(self, query: str, k: int = 4, min_score: float = 1.0):
        self.refresh()
        q = tokens(query)
        if not q or not self.docs:
            return []
        n, k1, b = len(self.docs), 1.5, 0.75
        scored = []
        for d in self.docs:
            s = 0.0
            for t in set(q):
                f = d["tf"].get(t)
                if not f:
                    continue
                idf = math.log(1 + (n - self.df[t] + 0.5) / (self.df[t] + 0.5))
                s += idf * f * (k1 + 1) / (f + k1 * (1 - b + b * d["len"] / self.avg))
            if s >= min_score:
                scored.append((s, d))
        scored.sort(key=lambda x: -x[0])
        return [{"score": round(s, 2), "file": d["file"], "title": d["title"], "text": d["text"]} for s, d in scored[:k]]

    def files(self):
        self.refresh()
        out = Counter(d["file"] for d in self.docs)
        return [{"file": f, "passages": c} for f, c in sorted(out.items())]


INDEX = Index()
