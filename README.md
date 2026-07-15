# Customer-Experience-Intelligence-Platform
Found that "unflattering silhouette" — not sizing or quality — is the #1 driver of negative reviews in a 23K-review e-commerce dataset. AI-assisted complaint classification, validated and documented end-to-end.
# Customer Experience Intelligence Platform

**Women's E-Commerce Clothing Reviews — Complaint Pattern Analysis**

`Python` `pandas` `Power BI` `Keyword NLP` `PostgreSQL-ready`

---

## Executive Summary

This project analyzes 23,470 customer reviews from a women's e-commerce clothing retailer to identify which products and categories show systematic complaint patterns that reduce recommendation rates. The analysis reveals that **silhouette and shape complaints** — garments that look unflattering or shapeless on real customers — are the leading category of classifiable negative feedback (37.8% of classified complaints), followed by **material quality and durability failures** (28.9%). Twenty-one products are flagged for concentrated complaint patterns, including four high-volume products with ≥150 total reviews where a single complaint type dominates at least 30% of their negative review pool.

---

## Business Problem

E-commerce clothing retailers face a structural challenge: customers cannot touch, try, or return a garment before purchase. The written review is the primary signal of product-experience mismatch — but at scale, that signal is buried in thousands of unstructured text entries.

This project asks a specific, answerable business question:

> **Which product categories and individual products show a systematic pattern of poor quality, poor fit accuracy, or description mismatch — and what specific recurring complaints would most improve the recommendation rate?**

The 82.2% overall recommendation rate suggests most customers are satisfied, but the 1-2 star review pool and the unusual "high rating, do not recommend" conflict signal reveal a distinct cohort of customers experiencing specific, recurring failures. Identifying and ranking those failures by product creates an actionable remediation list — which products need photography review, which need supplier QA escalation, and which need better size guidance.

---

## Dataset

**Source:** Women's E-Commerce Clothing Reviews — publicly available on Kaggle.

> **Dataset not included in this repository.** `data/raw/` and `data/clean/` are excluded from version control (see `.gitignore`). To reproduce the analysis:
> 1. Download the dataset from Kaggle: [Women's E-Commerce Clothing Reviews](https://www.kaggle.com/datasets/nicapotato/womens-ecommerce-clothing-reviews)
> 2. Place the downloaded file at `data/raw/reviews_raw.csv`
> 3. Run `python python/phase2_clean.py` to generate `data/clean/reviews_clean.csv`
> 4. All `output/` files are committed and do not need to be regenerated

| Attribute | Value |
|---|---|
| Raw records | 23,486 rows |
| After cleaning | 23,470 rows |
| Unique products | 1,199 |
| Columns (raw) | 11 |
| Columns (engineered) | 16 |
| Overall recommendation rate | 82.2% |
| Average rating | 4.20 / 5 |
| Five-star share | 55.9% |
| 1–2 star share | 10.3% |

**Fields used:** Clothing ID, Age, Title, Review Text, Rating, Recommended IND, Positive Feedback Count, Division Name, Department Name, Class Name

**Records removed:**
- 14 rows: null product category (Division / Department / Class all missing — unclassifiable). All 14 belonged to 7 Clothing IDs that had no other reviews in the dataset; removing them reduces the unique product count from 1,206 (raw) to 1,199 (clean).
- 2 rows: genuine text duplicates (same customer, same review text, different row indices — confirmed before dropping)

**Engineered columns added:** `has_review_text`, `is_truncated`, `product_review_count`, `coverage_tier`, `age_band`, `rating_rec_conflict`

**Key limitation identified in cleaning:** 303 reviews are flagged as `rating_rec_conflict` — a rating of ≥4 stars combined with "Do Not Recommend," or ≤2 stars combined with "Recommend." Manual review of a 30-record sample found that approximately 20% of these are fully positive reviews with apparent star-rating entry errors, not genuine contradictions. The true conflict count is closer to 240. This finding is documented but not corrected, as there is no reliable way to programmatically distinguish an error from a genuine nuanced response at scale.

---

## Methodology

### 1. Scope Definition — Tier 1 Complaint Signal

The full 23,470-review dataset contains significant positivity bias (55.9% five-star). Analyzing all reviews equally would dilute the complaint signal. **Tier 1** is defined as reviews most likely to contain specific, actionable product complaints:

- **Rating ≤ 2 stars**, OR
- **Rating ≥ 4 stars + "Do Not Recommend"** (the conflict signal — customers who liked the product in some way but still would not recommend it)
- Must contain review text

This produces **2,556 Tier 1 reviews** — 10.9% of the cleaned dataset, but the most information-dense portion for complaint identification.

### 2. Complaint Classification System

Six complaint categories were defined from the data rather than imposed from outside. Categories were derived by:
- Analyzing the most negatively-skewed unigrams, bigrams, and trigrams (terms appearing ≥2× more frequently in 1-2 star reviews than in 5-star reviews)
- Manually reading and labeling 120 representative reviews across four strata (NEGATIVE, CONFLICT, TRUNCATED, POSITIVE)
- Iterating on category definitions until labels were mutually exclusive and grounded in observed review language

| Label | What it captures |
|---|---|
| `STYLE_EXPECTATION` | Garment described as shapeless, boxy, tent-like, or unflattering — a silhouette/presentation gap |
| `MATERIAL_QUALITY` | Durability failures (shrinkage, pilling, zipper/button failure) and texture issues (thinness, sheerness, itchiness) |
| `SIZING_ACCURACY` | Garment does not fit true to size label — requires a significantly different size than expected |
| `FIT_CUT` | Body-area tightness despite correct size: arms, shoulders, bust, hips do not accommodate the customer's body |
| `DESCRIPTION_MISMATCH` | Color, sheerness, or silhouette differs materially from listing photographs or description |
| `PERSONAL_FIT` | Acknowledged personal taste, not a product defect (kept in taxonomy for completeness; 0.2% of classified reviews) |

### 3. Keyword Rule Validation

Priority-ordered keyword rules were built for each category (MQ → FC → DM → SA → SE → PF; first match wins). Rules were validated against the 120 manually labeled reviews:

- **Overall accuracy: 81.7%** (threshold: ≥75%)
- Strongest: FIT\_CUT 91%, DESCRIPTION\_MISMATCH 89%, MATERIAL\_QUALITY 83%
- Weakest: SIZING\_ACCURACY 67% (sizing language overlaps with description-mismatch phrasing)
- Reviews not matching any rule → `UNDETERMINED`

### 4. Product Spotlight Criteria

For each of the 168 products with ≥20 reviews (sufficient coverage), the dominant complaint rate was calculated against that product's own Tier 1 review count — not total reviews — to give an honest concentration signal. Products are flagged as spotlights if they meet all three criteria:

- ≥ 50 total reviews (sufficient overall scale)
- ≥ 5 Tier 1 reviews (minimum negative/conflict volume for stability)
- Dominant complaint label ≥ 30% of their Tier 1 reviews

---

## How AI Was Used

This project uses AI in a deliberate, cost-conscious, and auditable way — not as a black box classifier applied at scale.

**The approach: AI-assisted manual labeling → keyword rule derivation → automated matching**

Classifying 2,556 complaint reviews with an LLM API would cost approximately $0.30–$1.50 using a small model (claude-haiku-4-5) and would produce labels that are fast but opaque — the reasoning is not inspectable, errors are hard to diagnose, and the system cannot be handed off to a colleague without an API dependency. For a dataset of this size and a business context where the goal is to produce *explainable* category definitions that stakeholders can understand and challenge, that trade-off is not obviously worth it.

Instead, the approach was:

1. **Stratified sampling:** 120 reviews were selected across four strata (NEGATIVE, CONFLICT, TRUNCATED, POSITIVE) using a reproducible random seed.

2. **Manual classification via Claude Code:** Each of the 120 reviews was read and labeled directly through Claude Code — the AI reading review text and assigning one of six labels, with the analyst reviewing, challenging, and confirming each batch. This produced a 120-label ground truth set with documented edge cases, tie-breaking rules, and label rationale.

3. **Keyword rule design:** The ground truth labels were cross-referenced with a frequency analysis of negatively-skewed n-grams (unigrams, bigrams, trigrams appearing more often in 1-2 star reviews than 5-star reviews). This produced a set of phrase-level patterns for each category, grounded in actual review language rather than invented.

4. **Validation:** The keyword rules were applied to the 120-review ground truth set and achieved 81.7% accuracy — above the pre-set 75% threshold — confirming the rules were stable enough to apply at scale.

5. **Extrapolation:** The validated rules were applied to all 2,556 Tier 1 reviews. Reviews not matching any rule are reported as `UNDETERMINED` rather than force-assigned to a category.

**What this approach produces that pure API classification does not:**
- Deterministic, inspectable rules that can be reviewed or extended by anyone
- A documented accuracy figure against a labeled validation set
- Explicit UNDETERMINED tracking (a methodological honesty that pure API classification tends to suppress)
- No ongoing API cost for re-running the analysis or sharing the pipeline

**What it costs:** The 51.1% UNDETERMINED rate is the direct consequence of this choice. Keyword rules cannot match complaint language they were not designed for. This is documented as the primary limitation of the analysis.

---

## Key Findings

### Finding 1 — Silhouette complaints are the leading classifiable complaint category

**473 of 1,251 classified complaints (37.8%) describe garments that look shapeless, boxy, tent-like, or unflattering when worn.**

This category — STYLE\_EXPECTATION — is distinct from both sizing issues (the garment is the wrong numerical size) and fit issues (the garment doesn't accommodate a specific body area). STYLE\_EXPECTATION complaints arise when the garment fits in the sense that the customer can wear it, but the silhouette makes them look unflattering. The recurring vocabulary: *"shapeless," "boxy," "no shape," "like a tent," "maternity top," "unflattering," "frumpy."*

This represents a presentation gap between product photography — where garments are often clipped, pinned, or modeled on standardized body types — and how those same garments drape on a wider range of customers. No size guide change or fabric improvement resolves this; it requires honest product description ("relaxed/boxy silhouette") and more representative photography.

### Finding 2 — Material quality and durability failures rank second

**361 classified complaints (28.9%) describe quality failures that become apparent after purchase or first wash.**

Unlike silhouette complaints (which are apparent at try-on), material quality complaints cluster around post-purchase events: first wash reveals significant shrinkage; fabric pills within weeks of wear; zippers split or stick after limited use; seams develop holes. Multiple independent reviews describing the same specific failure on the same product (e.g., "zipper jammed after three wears") is the signal here — isolated defect reports could be attributed to individual defective units, but repeated identical failures suggest a product-level or supplier-level issue.

The most negatively-skewed bigrams corroborating this finding include *"poor quality" (59.9× more common in negative reviews), "material thin" (6.8×), "going back" (47.6×).*

### Finding 3 — 21 products show concentrated, systematic complaint patterns

Applying the spotlight criteria (≥50 total reviews, ≥5 Tier 1, dominant label ≥30% of Tier 1) yields 21 flagged products. Key entries:

| Product | Total Reviews | Tier 1 | Dominant Category | Dominant % of T1 | Priority |
|---|---|---|---|---|---|
| 868 — Tops/Knits | 430 | 64 | STYLE\_EXPECTATION | 38% | High |
| 860 — Tops/Knits | 288 | 30 | STYLE\_EXPECTATION | 30% | High |
| 831 — Tops/Blouses | 164 | 14 | MATERIAL\_QUALITY | 36% | High |
| 1056 — Bottoms/Pants | 213 | 17 | MATERIAL\_QUALITY | 35% | High |
| 984 — Jackets | 175 | 11 | STYLE\_EXPECTATION | 36% | High |
| 1008 — Bottoms/Skirts | 186 | 9 | STYLE\_EXPECTATION | 33% | High |

**Product 868** (the dataset's highest-review-count product) is the clearest anchor case. Its Tier 1 reviews consistently describe a tent or maternity-like silhouette. A small number of positive reviews describe the same product as "tailored to the body, not loose and wide" — suggesting the garment's drape is genuinely dependent on body type in ways the product photography does not communicate. This is a design-communication problem, not a defect.

**Products 831 and 1056** present a different pattern: multiple independent reviewers across a 164-review and 213-review product base report similar material quality failures. The consistency across unrelated reviewers elevates these from individual defect reports to potential supplier QA issues.

### Finding 4 — The conflict-signal dataset contains a non-trivial rate of rating entry errors

303 reviews were initially flagged as `rating_rec_conflict` (high rating + Do Not Recommend, or low rating + Recommend). Manual review of a 30-review sample revealed that approximately 6 of those 30 (20%) are fully positive reviews — enthusiastic language, no complaints — with a 1- or 2-star rating that is almost certainly a tap/click error on a mobile interface. Extrapolating to the full 303-record pool, approximately 60–75 conflict signals are likely data entry errors rather than genuine nuanced product assessments. This matters for any analysis that uses the conflict signal as a quality indicator; the true conflict count should be treated as approximately 230–240, not 303.

---

## Business Recommendations

| Priority | Category | Recommendation |
|---|---|---|
| High | Style / Silhouette | Audit photography for all 21 spotlight SE products. Add explicit silhouette descriptors to product copy: "relaxed and boxy," "full through the body," "flowy through the skirt." Recruit models with diverse body types for products flagged as tent-like or shapeless. |
| High | Material Quality | Escalate Products 831 and 1056 to supplier QA review. Require documented wash/durability testing for products where ≥3 independent reviewers report the same specific failure (shrinkage, pilling, zipper failure) within the same review period. |
| Medium | Material Quality | Add wash care prominence (not buried in description) for products with known shrinkage complaints. Consider adding a "fabric weight" indicator to product pages for categories where thinness is a recurring complaint. |
| Medium | Sizing Accuracy | Extend size guide detail for Product 1091 (Dresses) and other SA-flagged products. Cross-reference with returns data if available to identify which products generate the most size-related returns. |
| Medium | Description Mismatch | Conduct a color accuracy audit for products with color mismatch complaints: compare listing photography to physical samples under standard lighting. Standardize color naming between photography and product copy (e.g., avoid "dusty rose" when the product photographs closer to terracotta). |
| Low | Platform / Data Quality | Investigate whether the mobile/app rating interface has a UX issue causing accidental star selections. A single confirmation step for 1-star and 2-star ratings on products with an otherwise strong review history could meaningfully reduce data noise. |

---

## Limitations

**UNDETERMINED rate — primary limitation.** 51.1% of Tier 1 reviews (1,305 of 2,556) did not match any keyword rule and were classified as UNDETERMINED. All findings above are based on the 1,251 classifiable reviews only (48.9%). The true distribution of complaint categories across all 2,556 Tier 1 reviews is unknown. Diagnostic sampling confirmed that a substantial portion of UNDETERMINED reviews contain genuine complaints expressed in vocabulary not covered by the keyword rules — they are not inherently vague reviews.

**In-sample validation.** The 120-review ground truth set informed both the keyword rule design and the validation measurement. A fully independent held-out test set would provide a more rigorous accuracy estimate. The 81.7% figure should be interpreted as an internal consistency check rather than a true out-of-sample performance measure.

**Static snapshot.** The dataset contains no date or timestamp column. No trend analysis, seasonality assessment, or before/after comparison is possible. All findings describe a cross-sectional state of the review corpus at an unknown point in time.

**Single retailer.** Findings are specific to this retailer's product mix, customer base, and photography standards. They may not generalize to other e-commerce clothing contexts.

**Positivity skew.** 55.9% of reviews are five-star and 82.2% recommend the product. The dataset underrepresents mild dissatisfaction (3-star reviews were excluded from Tier 1 scope). The complaint patterns identified here reflect the most acute negative experiences, not the full spectrum of customer disappointment.

**No purchase or returns data.** The dataset contains no information on return rates, refund requests, or purchase volume per product. Financial impact of complaint categories cannot be quantified from this data alone.

---

## Future Improvements

- **LLM classification of UNDETERMINED reviews.** Applying an LLM to the 1,305 unclassified Tier 1 reviews would recover the signal currently lost to keyword rule gaps. With the 120-label ground truth set and documented accuracy requirements already in place, prompt design and validation would be straightforward.

- **Rating 3 secondary analysis.** Three-star reviews were excluded from Tier 1 scope to keep the complaint signal clean. A secondary analysis of 3-star reviews could surface mild dissatisfaction patterns that Tier 1 misses — particularly for categories like PERSONAL\_FIT and DESCRIPTION\_MISMATCH where the complaint does not necessarily drive a 1-2 star rating.

- **Temporal analysis.** If a date-stamped version of this dataset becomes available, complaint trends over time could reveal whether product quality issues are improving or worsening, and whether specific products improved after catalog updates.

- **Unsupervised topic modeling.** Applying LDA or BERTopic to the full review corpus would allow complaint categories to emerge from the data without predefined labels — potentially surfacing complaint types not covered by the current six-category taxonomy.

- **Integration with business metrics.** Linking complaint category rates to returns data, refund rates, or repeat purchase rates would allow financial impact quantification — converting a "35% of Tier 1 reviews are MQ complaints for Product 1056" finding into a dollar figure.

---

## Project Structure

```
customer-experience-intelligence/
├── data/                                # gitignored — see Dataset section for download
│   ├── raw/
│   │   └── reviews_raw.csv              # Original dataset — never modified
│   └── clean/
│       └── reviews_clean.csv            # 23,470 rows × 16 columns (generated by phase2_clean.py)
├── output/                              # committed — analysis outputs ready to use
│   ├── manual_sample_120.csv            # 120-review stratified ground truth sample
│   ├── validation_results.csv           # Keyword rule accuracy vs. ground truth
│   ├── classifications_tier1_keyword.csv # 2,556 Tier 1 reviews with predicted labels
│   ├── product_complaint_rates.csv      # Per-product complaint rates (168 products)
│   ├── category_summary.csv             # Pre-aggregated category counts (Power BI)
│   └── spotlight_products.csv           # 21 flagged products with notes (Power BI)
├── python/
│   ├── phase2_clean.py                  # Data cleaning pipeline (raw → clean, Steps 1–10)
│   ├── step3a_keywords.py               # Negative-skewed n-gram frequency analysis
│   ├── extract_batches.py               # Generates the 120-review stratified sample
│   ├── phase3_keyword_classify.py       # Keyword rule validation + full Tier 1 classification
│   └── generate_pbi_exports.py          # Power BI export files (category_summary, spotlights)
├── powerbi/
│   └── customer_intelligence.pbix       # Power BI dashboard (data loaded; visuals in progress)
├── CLAUDE.md
└── README.md
```

---

## How to Run

**Requirements**

```
Python 3.9+
pandas >= 1.5
```

Install dependencies:

```bash
pip install pandas
```

All `output/` files are committed and ready to use without re-running anything. To reproduce the analysis from scratch after downloading the dataset:

```bash
# 1. Generate the cleaned dataset from raw (requires data/raw/reviews_raw.csv)
python python/phase2_clean.py

# 2. Validate keyword rules and classify all 2,556 Tier 1 reviews
#    (requires data/clean/reviews_clean.csv and output/manual_sample_120.csv)
python python/phase3_keyword_classify.py

# 3. Regenerate Power BI export files
python python/generate_pbi_exports.py
```

`python/step3a_keywords.py` and `python/extract_batches.py` are included for reference — they were used during analysis to derive complaint categories and generate the ground truth sample respectively, but do not need to be re-run to reproduce the final outputs. `data/raw/reviews_raw.csv` is never modified by any script.

---

*This project was completed as part of a data analytics portfolio. Dataset: Women's E-Commerce Clothing Reviews, publicly available via Kaggle / UCI Machine Learning Repository.*


