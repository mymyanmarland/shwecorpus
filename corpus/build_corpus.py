#!/usr/bin/env python3
"""Rebuild corpus.db from Myanmar Wikipedia (rate-limit aware).

Strategy: generator=search with Burmese seed terms -> substantive articles.
Seed terms are codepoint lists (never hand-typed) to avoid editor quirks.

Usage: python3 build_corpus.py [target_total]   (default 250)

Source: Myanmar Wikipedia (https://my.wikipedia.org), CC BY-SA 4.0.
The resulting SQLite file is a derivative work — see README.md in this
directory for licensing.
"""
import os
import sqlite3
import sys
import time

import requests

API = 'https://my.wikipedia.org/w/api.php'
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'corpus.db')
UA = {'User-Agent': 'ShweCorpus/0.1 (open-source Burmese NLP; contact via repo issues)'}
SLEEP = 4
# seed terms as codepoint lists (never hand-typed)
SEEDS = [
    [0x1019, 0x103C, 0x1014, 0x1039, 0x1019, 0x102C],                       # myanma
    [0x101B, 0x1014, 0x103A, 0x1000, 0x102F, 0x1014, 0x103A],                # yankon
    [0x101E, 0x1019, 0x102D, 0x102F, 0x1004, 0x103A, 0x1038],                # thamaing
    [0x101E, 0x102D, 0x1015, 0x1039, 0x1015, 0x1036],                       # thippa
    [0x1015, 0x100A, 0x102C, 0x101B, 0x1031, 0x1038],                       # pyinyay
    [0x1005, 0x102E, 0x1038, 0x1015, 0x103D, 0x102C, 0x1038, 0x101B, 0x1031, 0x1038],
    [0x1000, 0x103B, 0x1014, 0x103A, 0x1038, 0x1019, 0x102C, 0x101B, 0x1031, 0x1038],
    [0x1021, 0x103C, 0x1030, 0x1000, 0x1005, 0x102C, 0x1038],                # akasa
    [0x101B, 0x102F, 0x1015, 0x103A, 0x101B, 0x103E, 0x1004, 0x103A],        # yokshin
    [0x101C, 0x1030, 0x101B, 0x1004, 0x103A, 0x1038, 0x101B, 0x1031, 0x1038],
    [0x1004, 0x102D, 0x102F, 0x1004, 0x103A, 0x1038, 0x101B, 0x1031, 0x1038],
    [0x1015, 0x100A, 0x102C, 0x1010, 0x102D, 0x102F, 0x1004, 0x103A, 0x1038],
]


def api(params, session):
    for attempt in range(6):
        try:
            r = session.get(API, params=params, headers=UA, timeout=30)
            if r.status_code == 429:
                wait = 10 + attempt * 10
                print('  429, waiting %ss' % wait, flush=True)
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException:
            print('  request failed, retrying', flush=True)
            time.sleep(5)
    raise RuntimeError('API failed after retries')


def main():
    target = int(sys.argv[1]) if len(sys.argv) > 1 else 250
    s = requests.Session()
    con = sqlite3.connect(DB)
    con.execute('CREATE TABLE IF NOT EXISTS docs '
                '(id INTEGER PRIMARY KEY, title TEXT UNIQUE, url TEXT, text TEXT)')
    have = {r[0] for r in con.execute('SELECT title FROM docs')}
    print('%d docs already' % len(have), flush=True)
    for seed in SEEDS:
        if len(have) >= target:
            break
        term = ''.join(chr(c) for c in seed)
        d = api({'action': 'query', 'format': 'json', 'generator': 'search',
                 'gsrsearch': term, 'gsrnamespace': 0, 'gsrlimit': 30,
                 'prop': 'extracts', 'explaintext': 1, 'exsectionformat': 'plain',
                 'exintro': 1}, s)
        new = 0
        for p in d.get('query', {}).get('pages', {}).values():
            title = p['title']
            if title in have:
                continue
            text = (p.get('extract') or '').strip()
            if len(text) < 150:
                continue
            have.add(title)
            con.execute('INSERT OR IGNORE INTO docs (title, url, text) VALUES (?,?,?)',
                        (title, 'https://my.wikipedia.org/wiki/' + title.replace(' ', '_'), text))
            new += 1
        con.commit()
        print('  seed -> +%d (%d/%d)' % (new, len(have), target), flush=True)
        time.sleep(SLEEP)
    cnt = con.execute('SELECT COUNT(*) FROM docs').fetchone()[0]
    print('total %d docs' % cnt)
    con.close()


if __name__ == '__main__':
    main()
