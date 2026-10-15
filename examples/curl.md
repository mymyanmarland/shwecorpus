# API examples (against the public demo)

Base URL: `https://shwecorpus.kmnapps.xyz`

## Health

```bash
curl https://shwecorpus.kmnapps.xyz/v1/health
```

## Proofread

```bash
curl -X POST https://shwecorpus.kmnapps.xyz/v1/proofread \
  -H 'Content-Type: application/json' \
  -d '{"text": "မြန်မာစာ စစ်ဆေးခြင်း", "fix": true}'
```

Response includes `r1_spurious_e`, `r2_wrong_aa`, `ay_vowel_spurious_aa`,
`r3_suspects`, and — with `"fix": true` — `fixed_text` plus `fixes_applied`.

## Tokenize

```bash
curl -X POST https://shwecorpus.kmnapps.xyz/v1/tokenize \
  -H 'Content-Type: application/json' \
  -d '{"text": "မြန်မာနိုင်ငံ"}'
```

## Word lookup

```bash
curl 'https://shwecorpus.kmnapps.xyz/v1/word/မြန်မာ'
```

Returns the word's codepoints, whether it is in the corpus, and up to three
example sentences from Myanmar Wikipedia.
