"""
Phase 1-3 keyword classification.
Run from: customer-experience-intelligence/
Outputs:
  output/validation_results.csv
  output/classifications_tier1_keyword.csv
  output/product_complaint_rates.csv
"""
import pandas as pd
import re
from collections import Counter

# ── Ground truth (120 manual labels) ─────────────────────────────────────────
GT = {
    1:"FIT_CUT",2:"FIT_CUT",3:"MATERIAL_QUALITY",4:"SIZING_ACCURACY",
    5:"DESCRIPTION_MISMATCH",6:"FIT_CUT",7:"MATERIAL_QUALITY",
    8:"DESCRIPTION_MISMATCH",9:"FIT_CUT",10:"MATERIAL_QUALITY",
    11:"MATERIAL_QUALITY",12:"DESCRIPTION_MISMATCH",13:"UNCLEAR",
    14:"DESCRIPTION_MISMATCH",15:"MATERIAL_QUALITY",16:"MATERIAL_QUALITY",
    17:"DESCRIPTION_MISMATCH",18:"SIZING_ACCURACY",19:"STYLE_EXPECTATION",
    20:"MATERIAL_QUALITY",21:"MATERIAL_QUALITY",22:"MATERIAL_QUALITY",
    23:"SIZING_ACCURACY",24:"DESCRIPTION_MISMATCH",25:"FIT_CUT",
    26:"MATERIAL_QUALITY",27:"SIZING_ACCURACY",28:"FIT_CUT",
    29:"DESCRIPTION_MISMATCH",30:"DESCRIPTION_MISMATCH",
    31:"STYLE_EXPECTATION",32:"STYLE_EXPECTATION",33:"MATERIAL_QUALITY",
    34:"SIZING_ACCURACY",35:"STYLE_EXPECTATION",36:"STYLE_EXPECTATION",
    37:"FIT_CUT",38:"MATERIAL_QUALITY",39:"FIT_CUT",40:"FIT_CUT",
    41:"STYLE_EXPECTATION",42:"FIT_CUT",43:"PERSONAL_FIT",
    44:"SIZING_ACCURACY",45:"STYLE_EXPECTATION",46:"FIT_CUT",
    47:"MATERIAL_QUALITY",48:"SIZING_ACCURACY",49:"MATERIAL_QUALITY",
    50:"SIZING_ACCURACY",51:"MATERIAL_QUALITY",52:"MATERIAL_QUALITY",
    53:"DESCRIPTION_MISMATCH",54:"DESCRIPTION_MISMATCH",
    55:"FIT_CUT",56:"SIZING_ACCURACY",57:"MATERIAL_QUALITY",
    58:"MATERIAL_QUALITY",59:"STYLE_EXPECTATION",60:"DESCRIPTION_MISMATCH",
    61:"FIT_CUT",62:"MATERIAL_QUALITY",63:"STYLE_EXPECTATION",
    64:"PERSONAL_FIT",65:"SIZING_ACCURACY",66:"SIZING_ACCURACY",
    67:"DESCRIPTION_MISMATCH",68:"UNCLEAR",69:"UNCLEAR",
    70:"SIZING_ACCURACY",71:"MATERIAL_QUALITY",72:"STYLE_EXPECTATION",
    73:"FIT_CUT",74:"SIZING_ACCURACY",75:"DESCRIPTION_MISMATCH",
    76:"SIZING_ACCURACY",77:"UNCLEAR",78:"DESCRIPTION_MISMATCH",
    79:"FIT_CUT",80:"STYLE_EXPECTATION",81:"STYLE_EXPECTATION",
    82:"UNCLEAR",83:"FIT_CUT",84:"FIT_CUT",
    85:"SIZING_ACCURACY",86:"UNCLEAR",87:"MATERIAL_QUALITY",
    88:"DESCRIPTION_MISMATCH",89:"FIT_CUT",90:"UNCLEAR",
    91:"FIT_CUT",92:"UNCLEAR",93:"UNCLEAR",94:"UNCLEAR",
    95:"UNCLEAR",96:"STYLE_EXPECTATION",97:"UNCLEAR",
    98:"DESCRIPTION_MISMATCH",99:"UNCLEAR",100:"MATERIAL_QUALITY",
    101:"UNCLEAR",102:"UNCLEAR",103:"UNCLEAR",104:"FIT_CUT",
    105:"DESCRIPTION_MISMATCH",106:"MATERIAL_QUALITY",107:"FIT_CUT",
    108:"FIT_CUT",109:"DESCRIPTION_MISMATCH",110:"FIT_CUT",
    111:"UNCLEAR",112:"UNCLEAR",113:"UNCLEAR",114:"UNCLEAR",
    115:"UNCLEAR",116:"UNCLEAR",117:"UNCLEAR",118:"UNCLEAR",
    119:"UNCLEAR",120:"UNCLEAR",
}

# ── Keyword rules ─────────────────────────────────────────────────────────────

MQ = [
    # Zipper failures
    "zipper split","zipper broke","zipper break","zipper doesn't work",
    "zipper wouldn't","zipper would not","zipper kept","zipper jammed",
    "zipper stuck","zipper failed","zipper has no where",
    "zippers got stuck","zippers stuck",
    # Button/closure failures
    "button fell off","buttons fell off","button has fallen","buttons have fallen",
    "button through the button hole","buttons through the button hole",
    "button holes too small","no chance of getting the button",
    "impossible to button","difficult to button",
    # Seam/structural failures
    "hole in the seam","hole running down the seam","holes in the seam",
    "holes along the seam","seam split","seam came apart",
    "developed holes","arrived with a hole","arrived with holes",
    "new with a small hole",
    "ripped as soon as","ripped when i","ripped after","ripped the first",
    # Durability failures
    "started pilling","pilling after","pilling within","pilling a lot",
    "pills terribly","worst case of pilling",
    "shrunk after","shrank after",
    "fell apart","coming apart","falling apart",
    "color will bleed","color bleeds","colors will bleed","will bleed color",
    "stretched out within","sleeves stretched out",
    "first time i washed","after one wash","after washing it",
    "wore it once and washed",
    # Material texture/quality
    "itchy","itches","so scratchy","scratchy fabric","scratchy and",
    "scratchy, stiff","scratchy, itchy",
    "feels like sandpaper","like sandpaper",
    "feels like a napkin",
    "very thin fabric","so thin","is so thin","material is thin",
    "material was thin","material thin","thin material","thin fabric",
    "extremely thin","incredibly thin","the knit is so thin",
    "cheaply made","poorly made","poor quality","bad quality",
    "horrible quality","terrible quality","cheap material","cheap fabric",
    "low quality",
    # Sheerness (as defect)
    "super see through","super see-through","see through","see-through",
    # Staining/condition
    "stained dress","dirty stained","received stained","was stained",
    # Metallic thread irritation
    "metallic thread",
    # Patch: transparency/sheerness vocabulary gap
    "transparent","translucent",
    # Patch: dye-on-skin (distinct from color-bleeds-in-wash)
    "dye from the","dye left on","stained my skin",
    # Patch: pilling standalone forms
    "pills on my","pill on my",
    # Patch: shrinkage without "after" (e.g. "it shrunk 3 inches", "the shirt shrank")
    "it shrunk","has shrunk","shrank,","shirt shrank","sweater shrank",
    "dress shrank","skirt shrank","pants shrank","jacket shrank",
    # Patch: thin/filmy fabric
    "filmy",
]

FC = [
    # Arms / armholes
    "tight in the arms","tight across the arms",
    "arms are so tight","arms are too tight","arms too tight",
    "too small in the arms","too small in my arms","too tight in the arms",
    "runs super small in the upper arms","small in the upper arms",
    "upper arms","arms and shoulders","arms/shoulders","arms/shoulder",
    "arm holes","armholes","arm hole",
    "couldn't move my arms","couldn't stretch out my arms","couldn't lift my arms",
    "except for my arms","except in the arms","fit everywhere except",
    # Shoulders
    "shoulder area","shoulders are too tight","tight in the shoulders",
    "too small in the shoulders","tight across the shoulders",
    "shoulders too short",
    # Chest/bust (tight only — avoid matching positive bust references)
    "tight across the chest","tight around the chest","tight in the chest",
    "ridiculously tight across the chest",
    "tight around the bust","tight in the bust","too tight in the bust",
    "tight around the girls","around the girls",
    "bust area","side bust area",
    "across my chest","pulled across my chest",
    "not enough support",
    # Hips/thighs/calves
    "in the hip area","hip area","restrictive in the hip","too tight in the hip",
    "i have thighs","thigh area",
    "calves","calf area",
    "pant legs are tight","pant legs are very tight",
    # Neckline / head opening
    "elastic band at the neckline","neckline is too small","too tight at the neckline",
    # Crotch/rise
    "crotch area","front crotch","in the crotch",
    # Waist (when other areas fit)
    "the waist was huge","huge in the waist",
    # Back cut / bra issues
    "back is cut so low","too low in the back","back cut too low",
    "bra back band","bra band showed",
    # Cut for height
    "made for someone extremely tall","cut like full size","cut like a full size",
    # Patch: armpit fit restriction
    "armpit",
    # Patch: word-order variants of chest tightness (e.g. "across the chest are really tight")
    "chest are tight","chest is tight","chest are too tight","chest was tight",
    "chest are really tight","chest are very tight","across the chest are",
]

DM = [
    # Explicit photo/listing comparisons
    "not like the picture","nothing like the picture",
    "not as shown in the picture","not as shown in the photo",
    "not as shown in the photos","not as pictured","not as featured",
    "not at all like it's pictured","nothing like pictured",
    "doesn't look like the picture","didn't look like the picture",
    "doesn't look anything like","looks nothing like","looked nothing like",
    "not at all like the model","not at all like it's pictured on the model",
    "different from the picture","different than the picture",
    "not like the photo","not like what's shown",
    "pictures are very misleading","picture is misleading",
    "misleading photo","misleading picture",
    "catalog is not the same","catalog is slightly different",
    "doesn't match the photo","doesn't match the picture",
    "pictured on the model",
    "prettier in pic",
    # Online vs in-person
    "than it looks online","than pictured online",
    "online it looked","online they looked","online it looks",
    "looking online"," irl ","in real life",
    "in person it was","in person it is","in person it looks",
    "in person the","in person they",
    "like in the photo","like in the picture",
    # Color mismatch
    "color is darker","color was darker","color is lighter",
    "color was different","color looked different",
    "color is not","color isn't","color was not",
    "not the color","wrong color","different color",
    "neon orange","almost neon",
    # Shape/style mismatch
    "not straight and pencil","pencil-like as shown",
    "is not dropped at all","drop waist is not",
    # Sheerness not shown
    "more sheer than","sheerer than shown","sheer than it appears",
    # Size appearance mismatch from photo
    "don't look that wide in the picture","doesn't look that wide",
    "wider than in the picture",
    # Sleeve length mismatch
    "shorter than shown in the photo","shorter than shown in photos",
    "shorter than shown","shorter than it appears in",
    # Product type mismatch (e.g. pullover vs zippered)
    "picture doesn't match","retailer's picture doesn't match",
    # Fuller than expected
    "a lot fuller","lot fuller in real life","fuller in real life",
    # Stripe/pattern mismatch
    "stripes are gray","stripe colors are different",
    # Catalog
    "dress in the catalog",
]

SA = [
    # Classic sizing phrases
    "runs small","run small","running small","ran small",
    "runs very small","runs really small","runs quite small",
    "runs large","run large","running large","ran large",
    "runs very large","runs really large",
    # Size extreme mismatches
    "xl fit like an xs","xl fit like xs","xl looked like xs","xl is like an xs",
    "could fit a large","fit like an xs","fit like xs",
    "could comfortably fit",
    "enormous on","way too big","way too large",
    "ridiculously small","horribly small","horribly tiny",
    # Not true to size
    "not true to size","don't run true to size","doesn't run true",
    "not true-to-size","isn't true to size",
    "mis-marked","mislabeled",
    # Explicit major mismatch
    "fit a large and it's an xs","two sizes larger","two sizes smaller",
    "one maybe two sizes larger",
]

SE = [
    # Maternity/pregnancy silhouette
    "maternity top","looks like a maternity","like a maternity top",
    "pregnancy top","like a pregnancy top","looks like a pregnancy",
    "looks like i'm pregnant","like i'm pregnant","i look pregnant",
    # Tent/sack
    "like a tent","looks like a tent","like wearing a tent",
    "tent-like","tent like","so tent",
    # Shapeless/unflattering
    "no shape","gives no shape","it gave me no shape","gave me no shape",
    "shapeless","boxy",
    "unflattering","very unflattering","really unflattering",
    "so unflattering","incredibly unflattering","most unflattering",
    "not flattering","wasn't flattering",
    # Adds weight
    "adds weight","adds pounds","add pounds",
    "makes me look heavier","made me look heavier",
    "made me look bigger","makes me look bigger",
    "look heavier than i am","heavier than i am",
    "20 pounds to my frame","10 pounds to my frame",
    "bottom heavy","look bottom heavy",
    "frumpy",
    # Excess fabric
    "too much fabric","way too much fabric","so much fabric",
    "massive amount of material","too much material","too billowy","too flowy",
    # Comparisons
    "cargo shorts","i could find this anywhere",
    # Patch: additional unflattering vocabulary
    "matronly",
    "not very flattering","not at all flattering","isn't flattering",
    "wasn't very flattering","not particularly flattering",
]

PF = [
    "not my style","not my taste","not my preference",
    "not for me but","not for me although",
    "for my complexion","for my olive complexion",
    "for my skin tone","for my coloring","for my fair coloring",
    "which i do not prefer","which i prefer not",
    "i don't like asymmetrical","personal preference",
]

RULES = [
    ("MATERIAL_QUALITY",    MQ),
    ("FIT_CUT",             FC),
    ("DESCRIPTION_MISMATCH",DM),
    ("SIZING_ACCURACY",     SA),
    ("STYLE_EXPECTATION",   SE),
    ("PERSONAL_FIT",        PF),
]

def normalize(text):
    if pd.isna(text): return ""
    return re.sub(r'\s+', ' ', str(text).lower().strip())

def classify(text):
    t = normalize(text)
    matched = []
    for label, patterns in RULES:
        if any(p in t for p in patterns):
            matched.append(label)
    if not matched:
        return "UNDETERMINED", []
    return matched[0], matched

# ── Phase 2: Validate on 120 ground truth reviews ────────────────────────────
sample = pd.read_csv("output/manual_sample_120.csv")

# Combine title + review text for classification
def get_text(row):
    title = str(row.get("Title","")) if pd.notna(row.get("Title","")) else ""
    review = str(row["Review Text"]) if pd.notna(row["Review Text"]) else ""
    return (title + " " + review).strip()

results = []
for _, row in sample.iterrows():
    num = int(row["review_num"])
    truth = GT.get(num, "UNKNOWN")
    text = get_text(row)
    predicted, all_matched = classify(text)
    # Map UNCLEAR ground truth: correct if predicted is UNDETERMINED
    if truth == "UNCLEAR":
        correct = (predicted == "UNDETERMINED")
    else:
        correct = (predicted == truth)
    results.append({
        "review_num": num,
        "stratum": row["stratum"],
        "truth": truth,
        "predicted": predicted,
        "all_matched": "|".join(all_matched),
        "correct": correct,
    })

res_df = pd.DataFrame(results)
res_df.to_csv("output/validation_results.csv", index=False)

# Print validation report
total = len(res_df)
n_correct = res_df["correct"].sum()
print("=" * 55)
print("PHASE 2: VALIDATION RESULTS (120 ground truth reviews)")
print("=" * 55)
print(f"\nOverall accuracy: {n_correct}/{total} ({n_correct/total*100:.1f}%)")

# Per-label breakdown
print("\nPer-label accuracy:")
for label in ["MATERIAL_QUALITY","FIT_CUT","DESCRIPTION_MISMATCH",
              "SIZING_ACCURACY","STYLE_EXPECTATION","PERSONAL_FIT","UNCLEAR"]:
    sub = res_df[res_df["truth"] == label]
    if len(sub) == 0: continue
    nc = sub["correct"].sum()
    print(f"  {label:<22} {nc}/{len(sub)} ({nc/len(sub)*100:.0f}%)")

# Misclassifications
misses = res_df[~res_df["correct"]]
if len(misses):
    print(f"\nMisclassifications ({len(misses)} reviews):")
    for _, r in misses.iterrows():
        print(f"  #{int(r.review_num):03d} [{r.stratum:9s}]  "
              f"truth={r.truth:<22}  predicted={r.predicted}")
else:
    print("\nNo misclassifications.")

threshold_met = (n_correct / total) >= 0.75
print(f"\nThreshold (>=75%): {'PASS' if threshold_met else 'FAIL'}")

if not threshold_met:
    print("Stopping — refine rules before applying to Tier 1.")
    raise SystemExit(1)

# ── Phase 3: Apply to Tier 1 (2,556 reviews) ─────────────────────────────────
print("\n" + "=" * 55)
print("PHASE 3: APPLYING TO TIER 1 (2,556 REVIEWS)")
print("=" * 55)

df = pd.read_csv("data/clean/reviews_clean.csv")
tier1 = df[
    ((df["Rating"] <= 2) | ((df["Rating"] >= 4) & (df["Recommended IND"] == 0)))
    & df["has_review_text"]
].copy()
print(f"\nTier 1 reviews: {len(tier1)}")

def classify_row(row):
    text = (str(row.get("Title","")) if pd.notna(row.get("Title","")) else "") + " " + \
           (str(row["Review Text"]) if pd.notna(row["Review Text"]) else "")
    label, matched = classify(text.strip())
    return label, "|".join(matched)

labels, all_m = zip(*tier1.apply(classify_row, axis=1))
tier1["keyword_label"] = labels
tier1["all_matched_labels"] = all_m

# Save
out_cols = ["Clothing ID","Rating","Recommended IND","Department Name",
            "Class Name","is_truncated","rating_rec_conflict",
            "product_review_count","coverage_tier",
            "Title","Review Text","keyword_label","all_matched_labels"]
tier1[out_cols].to_csv("output/classifications_tier1_keyword.csv", index=False)

# Print distribution
print("\nLabel distribution:")
dist = tier1["keyword_label"].value_counts()
for label, count in dist.items():
    pct = count / len(tier1) * 100
    print(f"  {label:<22} {count:>5}  ({pct:.1f}%)")

n_det = len(tier1) - (dist.get("UNDETERMINED", 0))
print(f"\nDetermined (classifiable): {n_det}/{len(tier1)} ({n_det/len(tier1)*100:.1f}%)")
print(f"UNDETERMINED:              {dist.get('UNDETERMINED',0)}/{len(tier1)} "
      f"({dist.get('UNDETERMINED',0)/len(tier1)*100:.1f}%)")

# ── Phase 4 prep: Product-level complaint rates ───────────────────────────────
print("\n" + "=" * 55)
print("PRODUCT-LEVEL COMPLAINT RATES (sufficient-coverage products)")
print("=" * 55)

COMPLAINT_LABELS = ["MATERIAL_QUALITY","FIT_CUT","DESCRIPTION_MISMATCH",
                    "SIZING_ACCURACY","STYLE_EXPECTATION","PERSONAL_FIT"]

# For each product, compute: total reviews, tier1 reviews, label counts
prod_stats = []
for prod_id, group in df.groupby("Clothing ID"):
    total = len(group)
    if total < 20:
        continue  # thin coverage
    dept = group["Department Name"].iloc[0]
    cls  = group["Class Name"].iloc[0]

    # Tier 1 rows for this product (from classified df)
    t1 = tier1[tier1["Clothing ID"] == prod_id]
    n_tier1 = len(t1)
    tier1_rate = n_tier1 / total

    row = {
        "Clothing ID": prod_id,
        "Department": dept,
        "Class": cls,
        "total_reviews": total,
        "tier1_reviews": n_tier1,
        "tier1_rate": round(tier1_rate, 3),
        "undetermined": int((t1["keyword_label"] == "UNDETERMINED").sum()),
    }
    for lbl in COMPLAINT_LABELS:
        cnt = int((t1["keyword_label"] == lbl).sum())
        row[lbl] = cnt
        row[f"{lbl}_rate"] = round(cnt / total, 3)

    # Dominant label: highest count complaint label among determined Tier 1 reviews
    # Rate computed against tier1_reviews (not total) — honest concentration signal
    determined = t1[t1["keyword_label"].isin(COMPLAINT_LABELS)]
    if len(determined) > 0:
        dom = determined["keyword_label"].value_counts().idxmax()
        dom_cnt = determined["keyword_label"].value_counts().max()
        dom_t1rate = dom_cnt / n_tier1  # denominator = tier1_reviews
    else:
        dom = "NONE"
        dom_cnt = 0
        dom_t1rate = 0.0
    row["dominant_label"]    = dom
    row["dominant_label_cnt"] = dom_cnt
    row["dominant_label_t1rate"] = round(dom_t1rate, 3)
    prod_stats.append(row)

prod_df = pd.DataFrame(prod_stats).sort_values("dominant_label_t1rate", ascending=False)
prod_df.to_csv("output/product_complaint_rates.csv", index=False)

# Spotlight candidates:
#   >= 50 total reviews (sufficient overall coverage)
#   >= 5  Tier 1 reviews (minimum negative/conflict volume for stability)
#   >= 30% dominant label rate of tier1_reviews
spotlights = prod_df[
    (prod_df["total_reviews"]         >= 50) &
    (prod_df["tier1_reviews"]         >= 5)  &
    (prod_df["dominant_label_t1rate"] >= 0.30)
].sort_values("dominant_label_t1rate", ascending=False)

print(f"\nProduct spotlights (>=50 total, >=5 Tier1, dominant label >=30% of Tier1):")
print(f"  Found: {len(spotlights)} products\n")
if len(spotlights):
    print(f"  {'ID':>5}  {'Total':>5}  {'T1':>4}  {'Und':>4}  {'Dominant label':<22}  {'Dom':>4}  {'%T1':>5}  Dept/Class")
    print(f"  {'-'*95}")
    for _, r in spotlights.iterrows():
        und_pct = r["undetermined"] / r["tier1_reviews"] * 100
        print(f"  {int(r['Clothing ID']):>5}  {int(r['total_reviews']):>5}  "
              f"{int(r['tier1_reviews']):>4}  {int(r['undetermined']):>3}({und_pct:.0f}%)  "
              f"{r['dominant_label']:<22}  {int(r['dominant_label_cnt']):>4}  "
              f"{r['dominant_label_t1rate']*100:>4.0f}%  "
              f"{r['Department']}/{r['Class']}")
else:
    print("  (none at this threshold)")

print(f"\nDone. Files saved to output/")
