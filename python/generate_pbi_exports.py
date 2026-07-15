"""
Generate two Power BI export files:
  output/category_summary.csv       -- pre-aggregated label counts for KPI cards
  output/spotlight_products.csv     -- 21 flagged products with notes and priority tier
Run from: customer-experience-intelligence/
"""
import pandas as pd

# ── Load source files ─────────────────────────────────────────────────────────
t1   = pd.read_csv("output/classifications_tier1_keyword.csv")
prod = pd.read_csv("output/product_complaint_rates.csv")

TIER1_TOTAL      = len(t1)                                          # 2,556
CLASSIFIED_TOTAL = int((t1["keyword_label"] != "UNDETERMINED").sum())  # 1,251

# ── 1. category_summary.csv ───────────────────────────────────────────────────
COMPLAINT_LABELS = [
    "MATERIAL_QUALITY",
    "FIT_CUT",
    "DESCRIPTION_MISMATCH",
    "SIZING_ACCURACY",
    "STYLE_EXPECTATION",
    "PERSONAL_FIT",
    "UNDETERMINED",
]

DISPLAY_NAMES = {
    "STYLE_EXPECTATION":      "Style / Silhouette",
    "MATERIAL_QUALITY":       "Material Quality",
    "SIZING_ACCURACY":        "Sizing Accuracy",
    "FIT_CUT":                "Fit & Cut",
    "DESCRIPTION_MISMATCH":   "Description Mismatch",
    "PERSONAL_FIT":           "Personal Preference",
    "UNDETERMINED":           "Unclassified",
}

# Consistent brand-neutral color palette for Power BI
COLORS = {
    "STYLE_EXPECTATION":    "#E07B54",   # warm orange-red
    "MATERIAL_QUALITY":     "#5B8DB8",   # steel blue
    "SIZING_ACCURACY":      "#8ABF69",   # muted green
    "FIT_CUT":              "#9B72AA",   # soft purple
    "DESCRIPTION_MISMATCH": "#E8B84B",   # amber
    "PERSONAL_FIT":         "#A8A8A8",   # grey
    "UNDETERMINED":         "#D0D0D0",   # light grey
}

SORT_ORDER = {
    "STYLE_EXPECTATION": 1,
    "MATERIAL_QUALITY":  2,
    "SIZING_ACCURACY":   3,
    "FIT_CUT":           4,
    "DESCRIPTION_MISMATCH": 5,
    "PERSONAL_FIT":      6,
    "UNDETERMINED":      7,
}

rows = []
vc = t1["keyword_label"].value_counts()
for lbl in COMPLAINT_LABELS:
    cnt = int(vc.get(lbl, 0))
    rows.append({
        "complaint_label":      lbl,
        "display_name":         DISPLAY_NAMES[lbl],
        "tier1_count":          cnt,
        "pct_of_tier1":         round(cnt / TIER1_TOTAL * 100, 1),
        "pct_of_classified":    round(cnt / CLASSIFIED_TOTAL * 100, 1) if lbl != "UNDETERMINED" else None,
        "is_classified":        lbl != "UNDETERMINED",
        "color_hex":            COLORS[lbl],
        "sort_order":           SORT_ORDER[lbl],
    })

cat_df = pd.DataFrame(rows).sort_values("sort_order")
cat_df.to_csv("output/category_summary.csv", index=False)
print("category_summary.csv written:")
print(cat_df[["display_name","tier1_count","pct_of_tier1","pct_of_classified"]].to_string(index=False))

# ── 2. spotlight_products.csv ─────────────────────────────────────────────────
# Apply spotlight filter (same as final run):
#   >= 50 total_reviews, >= 5 tier1_reviews, dominant_label_t1rate >= 0.30
spotlights = prod[
    (prod["total_reviews"]          >= 50) &
    (prod["tier1_reviews"]          >= 5)  &
    (prod["dominant_label_t1rate"]  >= 0.30)
].copy()

# Hand-authored notes — specific for anchors, label-based templates for rest
ANCHOR_NOTES = {
    868:  ("Largest product in dataset (430 reviews). Tent/maternity silhouette complaints "
           "dominate; qualitative review analysis shows polarised reactions — majority find "
           "the shape unflattering, a minority describe it as tailored. Design ambiguity, "
           "not a defect."),
    860:  ("High-volume SE product (288 reviews). Shapeless/boxy silhouette with excess "
           "fabric; reviewers consistently describe it as unflattering across body types. "
           "Second-highest volume SE flag in the dataset."),
    831:  ("High-volume MQ flag in Tops/Blouses (164 reviews). Recurring durability language "
           "across independent reviewers — fabric quality and construction concerns. "
           "Pattern suggests a supplier or batch-level issue rather than isolated defects."),
    1056: ("High-volume MQ flag in Bottoms/Pants (213 reviews). Material quality and "
           "durability complaints concentrated across this product; second-highest review "
           "volume among MQ spotlights."),
}

LABEL_TEMPLATES = {
    "STYLE_EXPECTATION":    ("{dept}/{cls}: silhouette/shape complaints — garment described as "
                             "shapeless, boxy, or unflattering when worn. Complaint is about "
                             "presentation gap between product photography and real-world wear."),
    "MATERIAL_QUALITY":     ("{dept}/{cls}: material quality and/or durability complaints — "
                             "thinness, sheerness, pilling, shrinkage, or structural failures "
                             "reported by multiple independent reviewers."),
    "SIZING_ACCURACY":      ("{dept}/{cls}: sizing accuracy complaints — garment does not fit "
                             "true to size label; reviewers report needing significantly "
                             "different sizes than expected."),
    "FIT_CUT":              ("{dept}/{cls}: fit and cut complaints — specific body-area "
                             "tightness (arms, shoulders, bust, hips) despite correct size."),
    "DESCRIPTION_MISMATCH": ("{dept}/{cls}: description mismatch — product color, sheerness, "
                             "or silhouette differs materially from listing photographs."),
}

def priority_tier(row):
    if row["total_reviews"] >= 150:
        return "High"
    elif row["total_reviews"] >= 75:
        return "Medium"
    else:
        return "Standard"

def spotlight_note(row):
    pid = int(row["Clothing ID"])
    if pid in ANCHOR_NOTES:
        return ANCHOR_NOTES[pid]
    tmpl = LABEL_TEMPLATES.get(row["dominant_label"], "Flagged for review.")
    return tmpl.format(dept=row["Department"], cls=row["Class"])

spotlights["is_spotlight"]     = True
spotlights["priority_tier"]    = spotlights.apply(priority_tier, axis=1)
spotlights["spotlight_note"]   = spotlights.apply(spotlight_note, axis=1)
spotlights["undetermined_pct"] = (
    spotlights["undetermined"] / spotlights["tier1_reviews"] * 100
).round(1)

# Column order for Power BI
out_cols = [
    "Clothing ID","Department","Class",
    "total_reviews","tier1_reviews","undetermined","undetermined_pct",
    "dominant_label","dominant_label_cnt","dominant_label_t1rate",
    "MATERIAL_QUALITY","FIT_CUT","DESCRIPTION_MISMATCH",
    "SIZING_ACCURACY","STYLE_EXPECTATION","PERSONAL_FIT",
    "is_spotlight","priority_tier","spotlight_note",
]
out_cols = [c for c in out_cols if c in spotlights.columns]
spotlights[out_cols].sort_values(
    ["priority_tier","dominant_label_t1rate"],
    ascending=[True, False]
).to_csv("output/spotlight_products.csv", index=False)

print(f"\nspotlight_products.csv written: {len(spotlights)} products")
print()
print(f"  {'ID':>5}  {'Total':>5}  {'T1':>4}  {'Dom label':<22}  {'%T1':>5}  Priority  Dept/Class")
print(f"  {'-'*80}")
for _, r in spotlights.sort_values("dominant_label_t1rate", ascending=False).iterrows():
    print(f"  {int(r['Clothing ID']):>5}  {int(r['total_reviews']):>5}  "
          f"{int(r['tier1_reviews']):>4}  {r['dominant_label']:<22}  "
          f"{r['dominant_label_t1rate']*100:>4.0f}%  "
          f"{r['priority_tier']:<8}  {r['Department']}/{r['Class']}")

print("\nDone.")
