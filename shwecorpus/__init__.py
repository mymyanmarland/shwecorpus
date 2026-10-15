"""ShweCorpus — open Burmese language data infrastructure.

Cleaned Myanmar Wikipedia corpus, a Wikipedia-verified Burmese proofreader,
a rule-based syllable tokenizer, and a small HTTP API on top.
"""

from .proofread import proofread_text, fix_text
from .tokenizer import syllables, tokenize

__version__ = "0.1.0"
__all__ = ["proofread_text", "fix_text", "syllables", "tokenize"]
