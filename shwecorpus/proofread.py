#!/usr/bin/env python3
"""Burmese proofreader — importable library + CLI.

Checks Burmese text for known generation-corruption patterns, verified
against the Myanmar Wikipedia corpus shipped in ``corpus/corpus.db``.

Rules (all verified against Wikipedia):
  R1: "-ai" rhyme (e.g. the rhyme in U+101A U+103A words) = U+101A U+103A,
      NEVER preceded by U+1031.
  R2: AA vowel: after U+1001 U+1002 U+1012 U+1015 U+101D use TALL AA U+102B;
      after all other consonants use U+102C. (The "aw" vowel U+1031+U+102B
      never triggers this: U+1031 always sits between C and AA there.)
      Stacked consonants (after U+1039) are skipped: the corpus attests
      both variants in correct words there, so the rule is word-specific.
  R3: Spurious insertions: for each unknown word, delete one
      U+1031/U+103D/U+1038 — if the result is a known Wikipedia word,
      the mark is spurious. Report-only (needs human judgment).
  AY-VOWEL (deterministic): the "ay" vowel is U+1031 + U+1038 with NO AA
      between them. U+1031 [U+102B|U+102C] U+1038 is always a corruption;
      dropping the AA restores the intended word (Wikipedia 1392:1).

Library usage:
    from shwecorpus import proofread_text, fix_text
    result = proofread_text("...")
    fixed, n = fix_text("...")

CLI usage:
    python -m shwecorpus.proofread <file> [--fix] [--db PATH]
"""

import os
import re
import sqlite3
import sys

# All combining-mark constants are built from explicit codepoints so the
# source never depends on editor/rendering quirks for Myanmar diacritics.
TALL_AA_CONSONANTS = ''.join(chr(c) for c in (0x1001, 0x1002, 0x1012, 0x1015, 0x101D))
E = chr(0x1031)
AA_TALL = chr(0x102B)
AA = chr(0x102C)
YA = chr(0x101A)
ASAT = chr(0x103A)
WA = chr(0x103D)
AUK = chr(0x1038)
VIRAMA = chr(0x1039)

PKG_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB = os.path.normpath(os.path.join(PKG_DIR, '..', 'corpus', 'corpus.db'))

# Whitelist: verified-correct words that R3's deletion test false-positives on.
# R3 skips these entirely. Each entry documents the independent verification —
# add a word here only after verifying its spelling against the Wikipedia
# corpus (never on a hunch).
WHITELIST = {
    # ay-vowel "give" (E+VISARGA, no AA) — Wikipedia pattern 1392:1,
    # verified 2026-10-10. Bare form is absent from the token set only
    # because it is almost always suffixed; R3 flags it because the bare
    # form minus visarga is also a known word.
    chr(0x1015) + chr(0x1031) + chr(0x1038): 'ay-vowel "give", verified 2026-10-10',
}


def is_consonant(ch):
    return '\u1000' <= ch <= '\u1021'


def load_reference(db_path=None):
    """Load the set of known Myanmar-script words from the corpus DB."""
    db_path = db_path or DEFAULT_DB
    ref = set()
    con = sqlite3.connect(db_path)
    for (text,) in con.execute("SELECT text FROM docs"):
        for w in re.findall(r'[\u1000-\u109f]+', text or ''):
            if len(w) >= 2:
                ref.add(w)
    con.close()
    return ref


def check_r1(text):
    """Spurious U+1031 before U+101A U+103A. Returns [(pos, label)]."""
    return [(m.start(), 'R1-spurious-E') for m in re.finditer(E + YA + ASAT, text)]


def check_r2(text):
    """Wrong AA variant. Returns [(pos, detail)].

    Stacked consonants (preceded by U+1039 VIRAMA) are SKIPPED: the corpus
    writes both AA variants after stacks in correct words (e.g. U+102C in
    "meaning", U+102B in Pali loans like the Ganga river name), so the
    tall-AA rule is word-specific there and must not auto-apply.
    """
    issues = []
    i = 0
    while i < len(text):
        if (i + 1 < len(text) and text[i + 1] in (AA_TALL, AA)
                and is_consonant(text[i])
                and not (i > 0 and text[i - 1] == VIRAMA)):
            want = AA_TALL if text[i] in TALL_AA_CONSONANTS else AA
            if text[i + 1] != want:
                issues.append((i, 'R2-AA: U+%04X should take U+%04X'
                               % (ord(text[i]), ord(want))))
            i += 2
        else:
            i += 1
    return issues


def check_ay_vowel(text):
    """Spurious AA between E and visarga. Deterministic — safe to auto-fix."""
    return [(m.start(), 'ay-vowel-spurious-AA: drop U+%04X' % ord(m.group(0)[1]))
            for m in re.finditer(E + '[' + AA_TALL + AA + ']' + AUK, text)]


def check_r3(text, ref):
    """Spurious-insertion suspects via Wikipedia deletion test.

    Returns [(word, candidate, dropped_mark, count)]. Report-only.
    """
    suspects = []
    words = {}
    for w in re.findall(r'[\u1000-\u109f]+', text):
        if len(w) >= 2:
            words[w] = words.get(w, 0) + 1
    for w in words:
        if w in ref or w in WHITELIST:
            continue
        for i, ch in enumerate(w):
            if ch in (E, WA, AUK):
                cand = w[:i] + w[i + 1:]
                if cand in ref:
                    suspects.append((w, cand, 'U+%04X' % ord(ch), words[w]))
                    break
    return suspects


def proofread_text(text, ref=None, db_path=None):
    """Run all checks. Returns a JSON-serialisable dict."""
    if ref is None:
        ref = load_reference(db_path)
    r1 = check_r1(text)
    r2 = check_r2(text)
    ray = check_ay_vowel(text)
    r3 = check_r3(text, ref)
    return {
        'r1_spurious_e': [{'pos': p, 'label': l} for p, l in r1],
        'r2_wrong_aa': [{'pos': p, 'detail': d} for p, d in r2],
        'ay_vowel_spurious_aa': [{'pos': p, 'detail': d} for p, d in ray],
        'r3_suspects': [
            {'word': w, 'candidate': c, 'dropped_mark': m, 'count': n}
            for w, c, m, n in r3
        ],
        'clean': not (r1 or r2 or ray or r3),
    }


def fix_text(text):
    """Apply deterministic R1/R2/ay-vowel fixes. Returns (fixed, count)."""
    n = 0
    c = text.count(E + YA + ASAT)
    text = text.replace(E + YA + ASAT, YA + ASAT)
    n += c
    c = len(re.findall(E + '[' + AA_TALL + AA + ']' + AUK, text))
    text = re.sub(E + '([' + AA_TALL + AA + '])' + AUK, E + AUK, text)
    n += c
    out = []
    i = 0
    while i < len(text):
        if (i + 1 < len(text) and text[i + 1] in (AA_TALL, AA)
                and is_consonant(text[i])
                and not (i > 0 and text[i - 1] == VIRAMA)):
            want = AA_TALL if text[i] in TALL_AA_CONSONANTS else AA
            if text[i + 1] != want:
                n += 1
            out.append(text[i])
            out.append(want)
            i += 2
        else:
            out.append(text[i])
            i += 1
    return ''.join(out), n


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    path = argv[1]
    do_fix = '--fix' in argv
    db = None
    for a in argv:
        if a.startswith('--db='):
            db = a.split('=', 1)[1]

    text = open(path, encoding='utf-8').read()
    result = proofread_text(text, db_path=db)

    print("R1 (spurious E before YA+ASAT): %d" % len(result['r1_spurious_e']))
    print("R2 (wrong AA variant): %d" % len(result['r2_wrong_aa']))
    for item in result['r2_wrong_aa'][:10]:
        print("    @%d: %s" % (item['pos'], item['detail']))
    print("AY-VOWEL (spurious AA between E and visarga): %d"
          % len(result['ay_vowel_spurious_aa']))
    print("R3 (spurious-insertion suspects): %d" % len(result['r3_suspects']))
    for s in sorted(result['r3_suspects'], key=lambda x: x['word'])[:20]:
        print("    %s -> %s (drop %s) x%d"
              % (s['word'], s['candidate'], s['dropped_mark'], s['count']))

    if do_fix and not result['clean']:
        text, n = fix_text(text)
        open(path, 'w', encoding='utf-8').write(text)
        print("\nApplied %d automatic fixes (R1+R2+ay-vowel). "
              "R3 suspects need manual review." % n)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
