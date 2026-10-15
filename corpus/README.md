# Corpus data

`corpus.db` is a SQLite database of Myanmar Wikipedia article extracts
(table `docs`: `id`, `title`, `url`, `text`). v0.1 ships 205 articles.

## Licensing — read this

- **Source:** Myanmar Wikipedia (https://my.wikipedia.org), which is
  licensed **CC BY-SA 4.0**.
- `corpus.db` is a **derivative work** of that source, so it is distributed
  under **CC BY-SA 4.0** as well. If you redistribute the database (or a
  modified version), keep this notice, credit Wikipedia and its contributors,
  and share under the same license.
- The **code** in this repository (proofreader, tokenizer, API, build
  scripts) is **MIT** licensed — see the root `LICENSE`. The MIT license
  covers code only, not the corpus data.

## Rebuilding

```bash
pip install requests
python3 corpus/build_corpus.py 500   # fetch up to 500 articles
```

The script is rate-limit aware (4s between seeds, backoff on 429).
Seed terms are codepoint lists, never hand-typed, to avoid Myanmar-script
editor quirks.
