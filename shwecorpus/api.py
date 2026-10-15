#!/usr/bin/env python3
"""ShweCorpus HTTP API (Flask).

Endpoints:
    GET  /                  service info
    GET  /v1/health         {ok, docs, version}
    POST /v1/proofread      {text, fix?} -> rule violations (+ fixed text)
    POST /v1/tokenize       {text} -> {syllables}
    GET  /v1/word/<word>    {word, codepoints, in_corpus, examples}

Run:
    SHWECORPUS_DB=corpus/corpus.db gunicorn "shwecorpus.api:app" -b 127.0.0.1:3005
"""

import os
import re
import sqlite3

from flask import Flask, jsonify, request, send_file

from .proofread import DEFAULT_DB, fix_text, load_reference, proofread_text
from .tokenizer import syllables

MAX_TEXT = 50000
MAX_WORD = 40

app = Flask(__name__)
app.json.ensure_ascii = False  # serve real Myanmar characters, not \uXXXX escapes
DB_PATH = os.environ.get("SHWECORPUS_DB", DEFAULT_DB)
PKG_DIR = os.path.dirname(os.path.abspath(__file__))

_ref = None
_doc_count = None


def get_ref():
    global _ref
    if _ref is None:
        _ref = load_reference(DB_PATH)
    return _ref


def get_doc_count():
    global _doc_count
    if _doc_count is None:
        con = sqlite3.connect(DB_PATH)
        _doc_count = con.execute("SELECT COUNT(*) FROM docs").fetchone()[0]
        con.close()
    return _doc_count


def _examples(word, limit=3, window=40):
    """Up to `limit` context snippets for `word` from the corpus."""
    con = sqlite3.connect(DB_PATH)
    rows = con.execute(
        "SELECT text FROM docs WHERE text LIKE ? LIMIT 20", ("%" + word + "%",)
    ).fetchall()
    con.close()
    out = []
    for (text,) in rows:
        i = text.find(word)
        if i < 0:
            continue
        s = max(0, i - window)
        e = min(len(text), i + len(word) + window)
        out.append(text[s:e].replace("\n", " ").strip())
        if len(out) >= limit:
            break
    return out


@app.get("/")
def index():
    """Try-it page (falls back to JSON service info if the file is missing)."""
    page = os.path.normpath(os.path.join(PKG_DIR, "..", "web", "index.html"))
    if os.path.exists(page):
        return send_file(page)
    return jsonify({
        "name": "ShweCorpus",
        "version": "0.1.0",
        "description": "Open Burmese language data infrastructure",
        "endpoints": [
            "GET /v1/health",
            "POST /v1/proofread",
            "POST /v1/tokenize",
            "GET /v1/word/<word>",
        ],
    })


@app.get("/v1/health")
def health():
    return jsonify({"ok": True, "version": "0.1.0", "docs": get_doc_count()})


@app.post("/v1/proofread")
def api_proofread():
    data = request.get_json(force=True, silent=True) or {}
    text = data.get("text", "")
    if not isinstance(text, str) or len(text) > MAX_TEXT:
        return jsonify({"error": "text must be a string up to %d chars" % MAX_TEXT}), 400
    result = proofread_text(text, ref=get_ref())
    if data.get("fix"):
        fixed, n = fix_text(text)
        result["fixed_text"] = fixed
        result["fixes_applied"] = n
    return jsonify(result)


@app.post("/v1/tokenize")
def api_tokenize():
    data = request.get_json(force=True, silent=True) or {}
    text = data.get("text", "")
    if not isinstance(text, str) or len(text) > MAX_TEXT:
        return jsonify({"error": "text must be a string up to %d chars" % MAX_TEXT}), 400
    return jsonify({"syllables": syllables(text)})


@app.get("/v1/word/<path:word>")
def api_word(word):
    word = word.strip()
    if not word or len(word) > MAX_WORD or not re.fullmatch(r"[\u1000-\u109f]+", word):
        return jsonify({"error": "word must be 1-%d Myanmar-script chars" % MAX_WORD}), 400
    return jsonify({
        "word": word,
        "codepoints": ["U+%04X" % ord(c) for c in word],
        "in_corpus": word in get_ref(),
        "examples": _examples(word),
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=3005)
