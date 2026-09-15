#!/usr/bin/env python3
"""Local slide-review site for several Beamer decks.

    python3 review/serve.py            # serves http://localhost:8765

For each deck <d> in DECKS: renders <d>.pdf to review/slides/<d>/ (rebuilding
when the PDF is newer), shows each slide beside a textarea, writes edits to
review/comments-<d>.md, commits on blur, and archives finished passes to
review/passes/<d>/<timestamp>.md.
"""
import json, os, re, shutil, subprocess, sys, time
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REVIEW = os.path.join(ROOT, "review")
PORT = int(os.environ.get("PORT", "8765"))

DECKS = [  # (key, title). key.pdf and key-frames.tex must exist in ROOT.
    ("refresher", "Refresher"),
    ("condexp", "Conditional Expectation"),
    ("entropy", "Entropy"),
    ("stochproc", "Stochastic Processes"),
    ("quiz03", "Quiz 3"),
    ("quiz03_solutions", "Quiz 3 solutions"),
]
DECK_KEYS = [k for k, _ in DECKS]

def paths(deck):
    if deck not in DECK_KEYS:
        raise ValueError("unknown deck " + deck)
    return {
        "pdf": os.path.join(ROOT, deck + ".pdf"),
        "frames": os.path.join(ROOT, deck + "-frames.tex"),
        "slides": os.path.join(REVIEW, "slides", deck),
        "comments": os.path.join(REVIEW, "comments-" + deck + ".md"),
        "passes": os.path.join(REVIEW, "passes", deck),
    }

def pdftoppm():
    return shutil.which("pdftoppm") or os.path.expanduser("~/.local/bin/pdftoppm")

def frame_titles(deck):
    f = paths(deck)["frames"]
    if not os.path.exists(f):
        return []
    src = open(f, encoding="utf-8").read()
    src = re.sub(r"(?m)^\s*%.*$", "", src)
    titles = re.findall(r"\\begin\{frame\}\{(.*?)\}\s*$", src, flags=re.M)
    return [re.sub(r"\$|\\[a-zA-Z]+|[{}]", "", t).strip() for t in titles]

def render_slides(deck):
    P = paths(deck)
    os.makedirs(P["slides"], exist_ok=True)
    pngs = sorted(f for f in os.listdir(P["slides"]) if f.endswith(".png"))
    if pngs and all(os.path.getmtime(os.path.join(P["slides"], f)) >= os.path.getmtime(P["pdf"]) for f in pngs):
        return
    for f in pngs:
        os.remove(os.path.join(P["slides"], f))
    subprocess.run([pdftoppm(), "-png", "-r", "150", P["pdf"], os.path.join(P["slides"], "s")], check=True)
    print("rendered", deck)

def slide_list(deck):
    P = paths(deck)
    pngs = sorted(f for f in os.listdir(P["slides"]) if f.endswith(".png"))
    titles = frame_titles(deck)
    return [{"n": i + 1, "png": f, "title": titles[i] if i < len(titles) else ""} for i, f in enumerate(pngs)]

def header(deck):
    title = dict(DECKS)[deck]
    return f"# Slide comments: {title}\n\nOne section per slide. Edited through review/serve.py; safe to edit by hand.\n"

def parse_comments(text):
    """-> {slide_number: (title, text)}"""
    out, cur = {}, None
    for line in text.split("\n"):
        m = re.match(r"^## Slide (\d+)(?::\s*(.*))?$", line)
        if m:
            cur = int(m.group(1)); out[cur] = [m.group(2) or "", []]
        elif cur is not None:
            out[cur][1].append(line)
    return {k: (t, "\n".join(v).strip()) for k, (t, v) in out.items()}

def read_comments(deck):
    f = paths(deck)["comments"]
    if not os.path.exists(f):
        return {}
    return {k: v for k, (t, v) in parse_comments(open(f, encoding="utf-8").read()).items()}

def write_comments(deck, comments):
    parts = [header(deck)]
    for s in slide_list(deck):
        text = comments.get(s["n"], "")
        if text:
            parts.append(f"\n## Slide {s['n']}: {s['title']}\n\n{text}\n")
    open(paths(deck)["comments"], "w", encoding="utf-8").write("".join(parts))

def read_passes(deck):
    """Earlier passes, oldest first: [{name, comments: {slide: {title, text}}}]"""
    d = paths(deck)["passes"]
    out = []
    if not os.path.isdir(d):
        return out
    for f in sorted(os.listdir(d)):
        if f.endswith(".md"):
            parsed = parse_comments(open(os.path.join(d, f), encoding="utf-8").read())
            out.append({"name": f[:-3], "comments": {str(k): {"title": t, "text": v} for k, (t, v) in parsed.items() if v}})
    return out

def git_commit(deck):
    rel = os.path.relpath(paths(deck)["comments"], ROOT)
    subprocess.run(["git", "add", rel], cwd=ROOT, check=True)
    if subprocess.run(["git", "diff", "--cached", "--quiet", "--", rel], cwd=ROOT).returncode == 0:
        return "nothing to commit"
    msg = f"Slide comments ({deck}) " + time.strftime("%Y-%m-%d %H:%M:%S")
    subprocess.run(["git", "commit", "-q", "-m", msg, "--", rel], cwd=ROOT, check=True)
    return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()

def archive_pass(deck):
    if not any(read_comments(deck).values()):
        return {"archived": None, "note": "no comments to archive"}
    git_commit(deck)
    P = paths(deck)
    os.makedirs(P["passes"], exist_ok=True)
    name = time.strftime("%Y-%m-%d-%H%M")
    dest = os.path.join(P["passes"], name + ".md")
    shutil.copyfile(P["comments"], dest)
    write_comments(deck, {})
    subprocess.run(["git", "add", os.path.relpath(dest, ROOT), os.path.relpath(P["comments"], ROOT)], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-q", "-m", f"Archive review pass {name} ({deck}) and clear comments"], cwd=ROOT, check=True)
    return {"archived": name}

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=REVIEW, **kw)

    def log_message(self, fmt, *args):
        if args and isinstance(args[0], str) and "/api/" in args[0]:
            return
        super().log_message(fmt, *args)

    def send_json(self, obj, code=200):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/":
            self.path = "/index.html"
        elif u.path == "/api/state":
            deck = parse_qs(u.query).get("deck", [DECK_KEYS[0]])[0]
            if deck not in DECK_KEYS:
                return self.send_json({"error": "unknown deck"}, 404)
            render_slides(deck)
            return self.send_json({
                "decks": [{"key": k, "title": t} for k, t in DECKS],
                "deck": deck,
                "slides": slide_list(deck),
                "comments": {str(k): v for k, v in read_comments(deck).items()},
                "passes": read_passes(deck),
                "pdf_built": time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(paths(deck)["pdf"]))),
            })
        elif u.path.startswith("/api/"):
            return self.send_json({"error": "use POST"}, 405)
        return super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        n = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(n) or b"{}")
        deck = body.get("deck", DECK_KEYS[0])
        if deck not in DECK_KEYS:
            return self.send_json({"error": "unknown deck"}, 404)
        if path == "/api/save":
            comments = read_comments(deck)
            comments[int(body["slide"])] = body.get("text", "")
            write_comments(deck, comments)
            result = {"saved": time.strftime("%H:%M:%S")}
            if body.get("commit"):
                result["commit"] = git_commit(deck)
            return self.send_json(result)
        if path == "/api/commit":
            return self.send_json({"commit": git_commit(deck)})
        if path == "/api/archive":
            return self.send_json(archive_pass(deck))
        self.send_json({"error": "unknown endpoint"}, 404)

if __name__ == "__main__":
    for k in DECK_KEYS:
        if os.path.exists(paths(k)["pdf"]):
            render_slides(k)
            if not os.path.exists(paths(k)["comments"]):
                write_comments(k, {})
    print(f"review site: http://localhost:{PORT}  (Ctrl-C to stop)")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
