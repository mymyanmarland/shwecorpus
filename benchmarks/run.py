#!/usr/bin/env python3
"""Run the proofreader over benchmarks/cases.jsonl and report scores.

A case passes when the corrupted input triggers its expected rule AND
fix_text() restores the exact correct form.

Usage: python3 benchmarks/run.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from shwecorpus.proofread import fix_text, proofread_text

RULE_KEY = {
    'R1': 'r1_spurious_e',
    'R2': 'r2_wrong_aa',
    'AY': 'ay_vowel_spurious_aa',
}


def main():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cases.jsonl')
    if not os.path.exists(path):
        print("cases.jsonl not found — run benchmarks/make_cases.py first")
        return 1
    total = passed = 0
    by_rule = {}
    with open(path, encoding='utf-8') as f:
        for line in f:
            c = json.loads(line)
            total += 1
            st = by_rule.setdefault(c['rule'], [0, 0])
            st[1] += 1
            res = proofread_text(c['corrupted'])
            detected = bool(res[RULE_KEY[c['rule']]])
            fixed, _ = fix_text(c['corrupted'])
            ok = detected and fixed == c['correct']
            if ok:
                passed += 1
                st[0] += 1
            else:
                print("FAIL %-3s detected=%s fixed_match=%s" %
                      (c['rule'], detected, fixed == c['correct']))
    print("\n%d/%d passed (%.1f%%)" % (passed, total, 100.0 * passed / total))
    for rule, (p, t) in sorted(by_rule.items()):
        print("  %s: %d/%d" % (rule, p, t))
    return 0 if passed == total else 1


if __name__ == '__main__':
    sys.exit(main())
