# Extract 120-review manual classification sample and print one batch at a time.
# Usage: python extract_batches.py --batch A   (A=1-30, B=31-60, C=61-90, D=91-120)
# Run from project root: customer-experience-intelligence/

import argparse
import pandas as pd
import os

SEED_3B = 42   # Step 3b seed — for reconstructing excluded indices
SEED    = 123  # New sample seed

def build_sample(df):
    # Reconstruct Step 3b exclusions
    s_t = df[df['is_truncated'] & df['has_review_text']].sample(5, random_state=SEED_3B)
    s_c = df[df['rating_rec_conflict'] & df['has_review_text'] & ~df.index.isin(s_t.index)].sample(5, random_state=SEED_3B)
    s_n = df[(df['Rating'] <= 2) & df['has_review_text'] & ~df.index.isin(s_t.index.union(s_c.index))].sample(5, random_state=SEED_3B)
    s_p = df[(df['Rating'] == 5) & df['has_review_text'] & ~df.index.isin(s_t.index.union(s_c.index).union(s_n.index))].sample(5, random_state=SEED_3B)
    excl = s_t.index.union(s_c.index).union(s_n.index).union(s_p.index)

    # NEGATIVE: 1-2 star, Rec=No, not excluded (pure negatives — not conflict)
    neg_pool = df[(df['Rating'] <= 2) & (df['Recommended IND'] == 0) & df['has_review_text'] & ~df.index.isin(excl)]
    s_neg = neg_pool.sample(60, random_state=SEED).copy()
    s_neg['stratum'] = 'NEGATIVE'

    # CONFLICT: rating_rec_conflict, not excluded, not already in neg
    excl2 = excl.union(s_neg.index)
    conf_pool = df[df['rating_rec_conflict'] & df['has_review_text'] & ~df.index.isin(excl2)]
    s_conf = conf_pool.sample(30, random_state=SEED).copy()
    s_conf['stratum'] = 'CONFLICT'

    # TRUNCATED: is_truncated, not excluded, not in neg or conf
    excl3 = excl2.union(s_conf.index)
    trunc_pool = df[df['is_truncated'] & df['has_review_text'] & ~df.index.isin(excl3)]
    s_trunc = trunc_pool.sample(20, random_state=SEED).copy()
    s_trunc['stratum'] = 'TRUNCATED'

    # POSITIVE: 5 star, Rec=Yes, not excluded, not in above
    excl4 = excl3.union(s_trunc.index)
    pos_pool = df[(df['Rating'] == 5) & (df['Recommended IND'] == 1) & df['has_review_text'] & ~df.index.isin(excl4)]
    s_pos = pos_pool.sample(10, random_state=SEED).copy()
    s_pos['stratum'] = 'POSITIVE'

    # Combine: NEG (1-60) -> CONF (61-90) -> TRUNC (91-110) -> POS (111-120)
    combined = pd.concat([s_neg, s_conf, s_trunc, s_pos]).reset_index(drop=False)
    combined.rename(columns={'index': 'orig_idx'}, inplace=True)
    combined.insert(0, 'review_num', range(1, len(combined) + 1))
    return combined

def print_batch(sample, start, end, label):
    batch = sample[(sample['review_num'] >= start) & (sample['review_num'] <= end)]
    print("=" * 70)
    print(f"BATCH {label}: Reviews {start}-{end} ({batch['stratum'].iloc[0]} stratum)")
    print("=" * 70)
    print()
    for _, row in batch.iterrows():
        title = str(row.get('Title', '')) if pd.notna(row.get('Title', '')) else ''
        text  = str(row['Review Text'])
        conf_flag  = ' [CONFLICT]'  if row['rating_rec_conflict'] else ''
        trunc_flag = ' [TRUNCATED]' if row['is_truncated']        else ''
        rec_str    = 'YES' if row['Recommended IND'] else 'NO'
        print("-" * 70)
        print(f"#{row['review_num']:03d} [{row['stratum']}]{conf_flag}{trunc_flag}")
        print(f"Rating: {int(row['Rating'])}/5 | Rec: {rec_str} | ID: {row['Clothing ID']} | {row.get('Department Name','')} / {row.get('Class Name','')}")
        if title and title != 'nan':
            print(f"Title: {title}")
        print(f"Text: {text}")
        print()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch', choices=['A','B','C','D'], default='A',
                        help='Which batch to print: A=1-30, B=31-60, C=61-90, D=91-120')
    args = parser.parse_args()

    df = pd.read_csv(os.path.join('data', 'clean', 'reviews_clean.csv'))

    out_path = os.path.join('output', 'manual_sample_120.csv')
    if os.path.exists(out_path):
        sample = pd.read_csv(out_path)
    else:
        sample = build_sample(df)
        sample.to_csv(out_path, index=False)
        print(f"Sample saved to {out_path}")
        print(sample['stratum'].value_counts().to_string())
        print()

    ranges = {'A': (1, 30), 'B': (31, 60), 'C': (61, 90), 'D': (91, 120)}
    start, end = ranges[args.batch]
    print_batch(sample, start, end, args.batch)

if __name__ == '__main__':
    main()
