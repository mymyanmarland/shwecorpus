#!/usr/bin/env python3
"""Generate proofreading benchmark cases WITHOUT hand-typing Burmese.

Method: take real words from the corpus, inject the known corruption
patterns, and record (corrupted, expected_rule, correct_form).

Corruption patterns (the ones the proofreader targets):
  - R1: insert U+1031 before U+101A U+103A ("-ai" rhyme)
  - R2: swap the AA variant (U+102B <-> U+102C) after a consonant
  - AY: insert U+102B between U+1031 and U+1038

Usage: python3 benchmarks/make_cases.py [n_per_rule]  -> benchmarks/cases.jsonl
"""
import json
import os
import random
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from shwecorpus.proofread import (AA, AA_TALL, ASAT, AUK, E, TALL_AA_CONSONANTS,
                                  YA, is_consonant, load_reference)

random.seed(42)


def find_rhyme_words(ref, n):
    """Words ending in U+101A U+103A with no preceding U+1031 (correct form)."""
    out = []
    for w in ref:
        if w.endswith(YA + ASAT) and not w.endswith(E + YA + ASAT) and len(w) <= 12:
            out.append(w)
        if len(out) >= n * 4:
            break
    return random.sample(out, min(n, len(out)))


VIRAMA = chr(0x1039)


def find_aa_words(ref, n):
    """Words with C+AA where the AA variant is corpus-correct.

    Stacked consonants are excluded: R2 deliberately skips them (both AA
    variants are attested in correct words there), so a swapped-AA case on
    a stack must not be expected to trigger.
    """
    out = []
    for w in ref:
        for i in range(len(w) - 1):
            if (is_consonant(w[i]) and w[i + 1] in (AA, AA_TALL)
                    and not (i > 0 and w[i - 1] == VIRAMA)
                    and len(w) <= 12):
                want = AA_TALL if w[i] in TALL_AA_CONSONANTS else AA
                if w[i + 1] == want:
                    out.append(w)
                    break
        if len(out) >= n * 4:
            break
    return random.sample(out, min(n, len(out)))


def find_ay_words(ref, n):
    """Words with E+VISARGA directly adjacent (correct ay-vowel)."""
    out = []
    for w in ref:
        if E + AUK in w and len(w) <= 12:
            out.append(w)
        if len(out) >= n * 4:
            break
    return random.sample(out, min(n, len(out)))


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    ref = load_reference()
    cases = []

    for w in find_rhyme_words(ref, n):
        bad = w[:-(len(YA + ASAT))] + E + YA + ASAT
        cases.append({"corrupted": bad, "rule": "R1", "correct": w})

    for w in find_aa_words(ref, n):
        for i in range(len(w) - 1):
            if is_consonant(w[i]) and w[i + 1] in (AA, AA_TALL):
                swap = AA_TALL if w[i + 1] == AA else AA
                bad = w[:i + 1] + swap + w[i + 2:]
                cases.append({"corrupted": bad, "rule": "R2", "correct": w})
                break

    for w in find_ay_words(ref, n):
        bad = w.replace(E + AUK, E + AA_TALL + AUK, 1)
        if bad != w:
            cases.append({"corrupted": bad, "rule": "AY", "correct": w})

    random.shuffle(cases)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cases.jsonl')
    with open(out, 'w', encoding='utf-8') as f:
        for c in cases:
            f.write(json.dumps(c, ensure_ascii=False) + '\n')
    print("wrote %d cases -> %s" % (len(cases), out))


if __name__ == '__main__':
    main()
