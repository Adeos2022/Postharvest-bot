import math, re, glob, os
from collections import Counter

def _tok(s):
    return re.findall(r"[a-z0-9]+", s.lower())

class KB:
    def __init__(self, folder="kb", chunk_chars=700):
        self.chunks = []
        for path in sorted(glob.glob(os.path.join(folder, "*.md"))):
            name = os.path.basename(path)
            text = open(path, encoding="utf-8").read()
            buf = ""
            for para in re.split(r"\n\s*\n", text):
                if buf and len(buf) + len(para) > chunk_chars:
                    self.chunks.append((name, buf.strip()))
                    buf = ""
                buf += para + "\n\n"
            if buf.strip():
                self.chunks.append((name, buf.strip()))
        self.docs = [Counter(_tok(c[1])) for c in self.chunks]
        self.lens = [sum(d.values()) for d in self.docs]
        self.avg = sum(self.lens) / len(self.lens) if self.lens else 1
        self.df = Counter()
        for d in self.docs:
            self.df.update(d.keys())

    def search(self, query, k=3, k1=1.5, b=0.75):
        n = len(self.docs)
        scored = []
        for i, d in enumerate(self.docs):
            s = 0.0
            for t in set(_tok(query)):
                if t in d:
                    idf = math.log(1 + (n - self.df[t] + 0.5) / (self.df[t] + 0.5))
                    s += idf * d[t] * (k1 + 1) / (
                        d[t] + k1 * (1 - b + b * self.lens[i] / self.avg))
            scored.append((s, i))
        scored.sort(reverse=True)
        return [self.chunks[i] for s, i in scored[:k] if s > 0]
