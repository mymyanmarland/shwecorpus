# Benchmarks

How we measure ShweCorpus quality — and how you can add cases.

## Proofreader benchmark

`cases.jsonl` is **generated, not hand-written**: `make_cases.py` takes real
words from the corpus, injects the known corruption patterns (spurious
U+1031 before the "-ai" rhyme, swapped AA variants, spurious AA in the
ay-vowel), and records the correct form. No Burmese is ever hand-typed, so
the benchmark cannot inherit editor/typing quirks.

```bash
python3 benchmarks/make_cases.py 60   # regenerate cases
python3 benchmarks/run.py             # score the proofreader
```

A case passes when the corrupted input triggers its expected rule **and**
`fix_text()` restores the exact correct form. v0.1 target: 100%.

## Contributing cases

Real-world failure reports are the most valuable contribution. Open an issue
with:

1. the corrupted string (paste it — do not retype),
2. a screenshot or the output bytes (`python3 -c` codepoint dump),
3. where it came from (which model/tool produced it).

If it is a systematic pattern, add a rule + generator clause in
`make_cases.py` and extend `run.py`.
