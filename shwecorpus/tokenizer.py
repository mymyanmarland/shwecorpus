#!/usr/bin/env python3
"""Rule-based Burmese syllable tokenizer for ShweSearch (v0.1).

Syllable boundaries with lookahead:
- consonant + U+103A ASAT  -> coda, stays in current syllable
- U+1004 NA + U+1036 ANUSVARA -> the vowel -in:, stays in current syllable
- consonant after U+1039 VIRAMA -> stacked, stays in current syllable
- otherwise a consonant starts a new syllable
Latin/digit runs are their own tokens; whitespace separates.
"""
import unicodedata

_CONS = lambda o: 0x1000 <= o <= 0x1021
_MYA = lambda o: 0x1000 <= o <= 0x109F
_ASAT, _VIR, _ANU, _NA = '\u103a', '\u1039', '\u1036', '\u1004'

def syllables(text):
    toks, cur = [], ''
    chs = list(text)
    n = len(chs)
    i = 0
    while i < n:
        ch = chs[i]
        o = ord(ch)
        nxt = chs[i + 1] if i + 1 < n else ''
        if ch.isspace():
            if cur:
                toks.append(cur); cur = ''
        elif _CONS(o):
            coda = (nxt == _ASAT)
            in_vowel = (o == 0x1004 and nxt == _ANU)
            stacked = (cur and cur[-1] == _VIR)
            if coda or in_vowel or stacked:
                cur += ch
            else:
                if cur:
                    toks.append(cur)
                cur = ch
        elif _MYA(o):
            cur += ch
        elif ch.isalnum():
            if cur and not _MYA(ord(cur[-1])):
                cur += ch
            else:
                if cur:
                    toks.append(cur)
                cur = ch
        else:
            if cur:
                toks.append(cur); cur = ''
        i += 1
    if cur:
        toks.append(cur)
    return [t for t in toks if t.strip()]

def tokenize(text):
    return [t.lower() for t in syllables(text)]

if __name__ == '__main__':
    for t in ['မြန်မာနိုင်ငံ', 'ဒီနေ့ သတင်း', 'ရန်ကုန်မြို့', 'ကျောင်းသား',
              'အောင်မြင်မှု', 'ငါးဟင်း', 'Python programming', 'သတင်းစာ']:
        print(t, '->', tokenize(t))
