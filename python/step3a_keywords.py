import pandas as pd
import numpy as np
from collections import Counter
import re

df = pd.read_csv('data/clean/reviews_clean.csv')

# ── Working subsets ────────────────────────────────────────────────────────────
neg  = df[(df['Rating'] <= 2) & df['has_review_text']].copy()          # 2,201 rows
conf = df[df['rating_rec_conflict'] & df['has_review_text']].copy()    # 303 rows (nearly all have text)
pos  = df[(df['Rating'] == 5) & df['has_review_text']].copy()          # 13,019 rows

print(f'Negative reviews (1-2 star) with text: {len(neg)}')
print(f'Conflict rows with text: {len(conf)}')
print(f'5-star reviews with text (contrast): {len(pos)}')
print()

# ── Minimal stopwords — only truly empty words ─────────────────────────────────
# Keeping domain-relevant words like "small", "large", "good", "cheap", "tight"
STOPWORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves',
    'you', 'your', 'yours', 'yourself', 'he', 'him', 'his', 'she',
    'her', 'hers', 'it', 'its', 'they', 'them', 'their', 'what',
    'which', 'who', 'this', 'that', 'these', 'those', 'am', 'is',
    'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
    'had', 'do', 'does', 'did', 'will', 'would', 'shall', 'should',
    'may', 'might', 'must', 'can', 'could', 'a', 'an', 'the',
    'and', 'but', 'if', 'or', 'because', 'as', 'of', 'at', 'by',
    'for', 'with', 'about', 'against', 'between', 'through', 'during',
    'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'then',
    'so', 'than', 'too', 'very', 'just', 'also', 'not', 'no',
    'nor', 'both', 'few', 'more', 'most', 'other', 'some', 'such',
    'into', 'over', 'after', 'above', 'below', 'each', 'there',
    'when', 'where', 'why', 'how', 'all', 'any', 'both', 'here',
    'again', 'further', 'once', 'only', 'own', 'same', 'while',
}

def tokenize(text):
    if pd.isna(text):
        return []
    text = str(text).lower()
    text = re.sub(r"[^a-z\s'-]", ' ', text)
    tokens = [t.strip("'-") for t in text.split()]
    return [t for t in tokens if t and t not in STOPWORDS and len(t) > 1]

def get_ngrams(tokens, n):
    return [' '.join(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]

def top_terms(texts, label, top_n=40, ngram_sizes=(1, 2, 3)):
    all_ngrams = []
    for text in texts:
        tokens = tokenize(text)
        for n in ngram_sizes:
            all_ngrams.extend(get_ngrams(tokens, n))
    counts = Counter(all_ngrams)
    print(f'\n{"="*55}')
    print(f'TOP TERMS — {label} (n={len(texts)})')
    print(f'{"="*55}')
    for ngram_size in ngram_sizes:
        label_n = {1: 'Unigrams', 2: 'Bigrams', 3: 'Trigrams'}[ngram_size]
        filtered = {k: v for k, v in counts.items() if len(k.split()) == ngram_size}
        top = sorted(filtered.items(), key=lambda x: -x[1])[:top_n]
        print(f'\n  {label_n}:')
        for term, count in top:
            freq = round(count / len(texts) * 100, 1)
            print(f'    {count:>5}  ({freq:>5}%)  {term}')

# ── Analysis ───────────────────────────────────────────────────────────────────
top_terms(neg['Review Text'].tolist(), '1-2 STAR REVIEWS', top_n=30)
top_terms(conf['Review Text'].tolist(), 'CONFLICT REVIEWS (rating_rec_conflict)', top_n=25)
top_terms(pos['Review Text'].tolist(), '5-STAR REVIEWS (contrast)', top_n=20, ngram_sizes=(2, 3))

# ── Bigrams that appear MUCH more in negative vs positive ──────────────────────
print(f'\n{"="*55}')
print('NEGATIVE-SKEWED BIGRAMS')
print('(appear at least 2x more frequently in negative than positive)')
print(f'{"="*55}')

def ngram_freq_map(texts, n):
    all_ng = []
    for text in texts:
        tokens = tokenize(text)
        all_ng.extend(get_ngrams(tokens, n))
    counts = Counter(all_ng)
    total = len(texts)
    return {k: v / total for k, v in counts.items()}

neg_bi  = ngram_freq_map(neg['Review Text'].tolist(), 2)
pos_bi  = ngram_freq_map(pos['Review Text'].tolist(), 2)
neg_tri = ngram_freq_map(neg['Review Text'].tolist(), 3)
pos_tri = ngram_freq_map(pos['Review Text'].tolist(), 3)

skewed_bi = []
for term, freq in neg_bi.items():
    pos_freq = pos_bi.get(term, 0.0001)
    if freq >= 0.01 and freq / pos_freq >= 2.0:
        skewed_bi.append((term, freq, pos_freq, round(freq / pos_freq, 1)))

skewed_bi.sort(key=lambda x: -x[1])
print('\n  Bigrams:')
for term, nf, pf, ratio in skewed_bi[:30]:
    print(f'    {ratio:>5}x  neg={nf*100:>5.1f}%  pos={pf*100:>5.1f}%  "{term}"')

skewed_tri = []
for term, freq in neg_tri.items():
    pos_freq = pos_tri.get(term, 0.0001)
    if freq >= 0.005 and freq / pos_freq >= 2.5:
        skewed_tri.append((term, freq, pos_freq, round(freq / pos_freq, 1)))

skewed_tri.sort(key=lambda x: -x[1])
print('\n  Trigrams:')
for term, nf, pf, ratio in skewed_tri[:25]:
    print(f'    {ratio:>5}x  neg={nf*100:>5.1f}%  pos={pf*100:>5.1f}%  "{term}"')

# ── Conflict cases: what's different about them? ───────────────────────────────
print(f'\n{"="*55}')
print('CONFLICT CASE BREAKDOWN')
print(f'{"="*55}')
high_not_rec = conf[(conf['Rating'] >= 4) & (conf['Recommended IND'] == 0)]
low_but_rec  = conf[(conf['Rating'] <= 2) & (conf['Recommended IND'] == 1)]
print(f'\n  High rating (4-5) + Not Recommended: {len(high_not_rec)}')
print(f'  Low rating (1-2)  + Recommended:     {len(low_but_rec)}')

print('\n  Top bigrams in HIGH-RATING + NOT RECOMMENDED:')
hnr_bi = ngram_freq_map(high_not_rec['Review Text'].dropna().tolist(), 2)
for term, freq in sorted(hnr_bi.items(), key=lambda x: -x[1])[:20]:
    print(f'    {freq*100:>5.1f}%  "{term}"')

print('\n  Top bigrams in LOW-RATING + RECOMMENDED:')
lbr_bi = ngram_freq_map(low_but_rec['Review Text'].dropna().tolist(), 2)
for term, freq in sorted(lbr_bi.items(), key=lambda x: -x[1])[:20]:
    print(f'    {freq*100:>5.1f}%  "{term}"')
