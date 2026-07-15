import pandas as pd
import numpy as np
import html
import re
import os

# ── Load raw ───────────────────────────────────────────────────────────────────
df = pd.read_csv('data/raw/reviews_raw.csv')
before_rows = len(df)
before_cols = len(df.columns)

# ── Step 1: Drop unnamed index column ─────────────────────────────────────────
df = df.drop(columns=['Unnamed: 0'])

# ── Step 3: Drop 14 null category rows ────────────────────────────────────────
null_cat_mask = df['Division Name'].isna() | df['Department Name'].isna() | df['Class Name'].isna()
rows_dropped_nullcat = int(null_cat_mask.sum())
df = df[~null_cat_mask].copy().reset_index(drop=True)

# ── Step 2: Drop 2 confirmed genuine text duplicates ──────────────────────────
dup1 = (df['Clothing ID'] == 1022) & df['Review Text'].notna() & df.duplicated(subset=['Clothing ID', 'Review Text'], keep='first')
dup2 = (df['Clothing ID'] == 1081) & df['Review Text'].notna() & df.duplicated(subset=['Clothing ID', 'Review Text'], keep='first')
rows_dropped_dups = int((dup1 | dup2).sum())
df = df[~(dup1 | dup2)].copy().reset_index(drop=True)

# ── Step 4: Flag content-free reviews ─────────────────────────────────────────
df['has_review_text'] = df['Review Text'].notna()

# ── Step 5: Flag truncated reviews ────────────────────────────────────────────
df['is_truncated'] = df['Review Text'].fillna('').str.len() >= 500

# ── Step 6: Unescape HTML entities — loop to convergence ──────────────────────
ENTITY_PATTERN = re.compile(r'&(?:#\d+|#x[\da-fA-F]+|[a-zA-Z]+);')

def unescape_full(text):
    if pd.isna(text):
        return text
    for _ in range(6):
        decoded = html.unescape(text)
        if decoded == text:
            break
        text = decoded
    return text

before_html = int(df['Review Text'].fillna('').apply(lambda x: bool(ENTITY_PATTERN.search(x))).sum())
df['Review Text'] = df['Review Text'].apply(unescape_full)
df['Title']       = df['Title'].apply(unescape_full)
after_html = int(df['Review Text'].fillna('').apply(lambda x: bool(ENTITY_PATTERN.search(x))).sum())

# ── Step 7: Normalize whitespace ──────────────────────────────────────────────
def normalize_ws(text):
    if pd.isna(text):
        return text
    text = text.strip()
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text

df['Review Text'] = df['Review Text'].apply(normalize_ws)
df['Title']       = df['Title'].apply(normalize_ws)

# ── Step 8: Product review count and coverage tier ────────────────────────────
df['product_review_count'] = df.groupby('Clothing ID')['Clothing ID'].transform('count')
df['coverage_tier'] = df['product_review_count'].apply(lambda x: 'sufficient' if x >= 20 else 'thin')

# ── Step 9: Age bands ─────────────────────────────────────────────────────────
df['age_band'] = pd.cut(
    df['Age'],
    bins=[18, 30, 40, 50, 60, 100],
    labels=['18-29', '30-39', '40-49', '50-59', '60+'],
    right=False
)

# ── Step 10: Rating / Recommended IND conflict flag ───────────────────────────
df['rating_rec_conflict'] = (
    ((df['Rating'] >= 4) & (df['Recommended IND'] == 0)) |
    ((df['Rating'] <= 2) & (df['Recommended IND'] == 1))
)

# ── Save ───────────────────────────────────────────────────────────────────────
os.makedirs('data/clean', exist_ok=True)
df.to_csv('data/clean/reviews_clean.csv', index=False)

after_rows = len(df)
after_cols = len(df.columns)

# ── QA REPORT ─────────────────────────────────────────────────────────────────
sep = '=' * 55

print(sep)
print('PHASE 2 QA REPORT')
print(sep)

print()
print('ROW COUNT')
print(f'  Raw input:                        {before_rows}')
print(f'  Dropped - null category (Step 3): {rows_dropped_nullcat}')
print(f'  Dropped - text duplicates (Step 2): {rows_dropped_dups}')
print(f'  Clean output:                     {after_rows}')
print(f'  Net change:                       {after_rows - before_rows:+d}')

print()
print('COLUMN COUNT')
print(f'  Raw input:   {before_cols}')
print(f'  Dropped:     1  (Unnamed: 0)')
print(f'  Added:       6')
print(f'  Clean output: {after_cols}')

print()
print('NEW COLUMNS ADDED')
new_cols = [
    ('has_review_text',      'bool',     'True if Review Text is not null'),
    ('is_truncated',         'bool',     'True if review text >= 500 chars (hit scrape ceiling)'),
    ('product_review_count', 'int',      'Total reviews for this Clothing ID in clean dataset'),
    ('coverage_tier',        'category', '"sufficient" (>=20 reviews) or "thin" (<20)'),
    ('age_band',             'category', '18-29 / 30-39 / 40-49 / 50-59 / 60+'),
    ('rating_rec_conflict',  'bool',     'Rating>=4 & Not Recommended, OR Rating<=2 & Recommended'),
]
for name, dtype, desc in new_cols:
    print(f'  {name:<26} [{dtype}]  {desc}')

print()
print('STEP-BY-STEP VALIDATION')

s_true  = int(df['has_review_text'].sum())
s_false = int((~df['has_review_text']).sum())
print(f'  Step 4  has_review_text    True={s_true}  False={s_false}')

trunc   = int(df['is_truncated'].sum())
trunc_pct = round(trunc / s_true * 100, 1)
print(f'  Step 5  is_truncated       True={trunc}  ({trunc_pct}% of reviews with text)')

print(f'  Step 6  HTML entities      Before={before_html}  After={after_html}')

suf_prod = int(df[df['coverage_tier'] == 'sufficient']['Clothing ID'].nunique())
suf_rev  = int((df['coverage_tier'] == 'sufficient').sum())
thn_prod = int(df[df['coverage_tier'] == 'thin']['Clothing ID'].nunique())
thn_rev  = int((df['coverage_tier'] == 'thin').sum())
print(f'  Step 8  sufficient         {suf_prod} products  {suf_rev} reviews')
print(f'  Step 8  thin               {thn_prod} products  {thn_rev} reviews')

age_nulls = int(df['age_band'].isna().sum())
print(f'  Step 9  age_band nulls:    {age_nulls}')

conflict_n   = int(df['rating_rec_conflict'].sum())
conflict_pct = round(conflict_n / after_rows * 100, 2)
high_not_rec = int(((df['Rating'] >= 4) & (df['Recommended IND'] == 0)).sum())
low_but_rec  = int(((df['Rating'] <= 2) & (df['Recommended IND'] == 1)).sum())
print(f'  Step 10 rating_rec_conflict: {conflict_n} rows ({conflict_pct}%)')
print(f'           -> Rating 4-5 + Not Recommended: {high_not_rec}')
print(f'           -> Rating 1-2 + Recommended:     {low_but_rec}')

print()
print('AGE BAND DISTRIBUTION')
for band, count in df['age_band'].value_counts().sort_index().items():
    pct = round(count / after_rows * 100, 1)
    print(f'  {band}:  {count:>5}  ({pct}%)')

print()
print('FINAL SCHEMA')
print(df.dtypes.to_string())

size_kb = round(os.path.getsize('data/clean/reviews_clean.csv') / 1024, 1)
print()
print('OUTPUT FILE')
print(f'  data/clean/reviews_clean.csv  {size_kb} KB')
