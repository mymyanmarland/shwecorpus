#!/usr/bin/env python3
"""ShweCorpus quickstart — library usage without the HTTP API."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from shwecorpus import proofread_text, fix_text, tokenize

# 1. Proofread (detect only)
text = "မြန်မာစာ စစ်ဆေးခြင်း"  # replace with your own text
result = proofread_text(text)
print("clean:", result["clean"])
print("R1 hits:", len(result["r1_spurious_e"]))
print("R2 hits:", len(result["r2_wrong_aa"]))
print("R3 suspects:", len(result["r3_suspects"]))

# 2. Auto-fix the deterministic rules (R1 + R2 + ay-vowel)
fixed, n = fix_text(text)
print("fixes applied:", n)

# 3. Syllable tokenization
print("tokens:", tokenize("မြန်မာနိုင်ငံ"))
