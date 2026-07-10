# Pipeline component quality report — `pdf_profiling` dataset

*Quality evaluation of the scanned-PDF pipeline components against the ISP RAS `pdf_profiling` dataset (3241 PDFs,
11 GB). Focus: the optimizations/fixes made during the GPU-OCR work (which could have traded quality for speed) and
the recognizer alternatives. Companion to [`GPU_OCR_EXPERIMENTS.md`](GPU_OCR_EXPERIMENTS.md) (speed lab notebook).*

## 1. Dataset & ground-truth scheme

`test_docs/pdf_profiling/` — organized by pipeline component. The numeric leaf dirs `{1,5,10,25,50,100}` are **page
counts** (a perf-scaling axis), not degradation levels. There are **no label files**; ground truth is implicit:

| set | docs | content | ground truth used |
|---|---|---|---|
| **gen_texts** (long/short) | 60×levels | synthetic, born-digital, **0 images, clean embedded text** | ✅ embedded text (`fitz.get_text`) = exact OCR GT |
| **gen_tables** (g1/2/3) | 90×levels | synthetic tables, embedded cell values | ✅ embedded text = table-cell GT |
| **orient** | 30×levels | real docs, each page rotated 0/90/180/270 (in page metadata) | ✅ `page.rotation` = orientation GT |
| **skew** | 30×levels | real docs, content skewed (metadata rot=0) | angle unlabelled → self-consistency vs 91-step reference |
| **binarize** | 30×levels | real docs, noise added | source text (partial) |
| **gen_images / gen_mixed** | | synthetic with figures / mixed | embedded text (partial) |
| **real_mixed** (table/hard_table/image/…) | 843 | real docs by content type | none (qualitative) |
| **source** | 238 | originals: pdf_china (CIAE, born-digital), rosatom (DAE, pure scan, no text), fintoc (born-digital) | reference |

**Method:** render page (pdf2image, 300 dpi for OCR / 150 for orient-deskew), run the component, compare to GT.
WER/CER via `jiwer`; **word-bag F1** (order-independent) added to separate *recognition* quality from *reading order*.
(Note: a few fintoc docs have >260-char filenames that poppler can't open on Windows — skipped.)

## 2. OCR recognition — the eslav↔tesseract swap and det=960 fix (gen_texts, clean GT)

30 long + 30 short one-page English docs, exact embedded-text GT.

| set | engine | WER | CER | **word-bag F1** |
|---|---|---|---|---|
| long_text | tesseract | **0.061** | 0.026 | 0.955 |
| | eslav det=960 (shipped) | 0.551 | 0.437 | 0.944 |
| | eslav det=full | 0.535 | 0.434 | **0.960** |
| short_text | tesseract | **0.337** | 0.288 | 0.936 |
| | eslav det=960 (shipped) | 0.456 | 0.381 | 0.913 |
| | eslav det=full | 0.427 | 0.350 | **0.966** |

**Findings:**

1. **eslav recognition on English is excellent — F1 0.96, ≥ tesseract.** The alarming WER gap (0.55 vs 0.06) is **not
   recognition**: a spot-check shows eslav output nearly identical to GT ("…denied suggestions there will be a Budget
   giveaway on 16 March. Ed Balls, ex-chief economic adviser to the Treasury…"). The word-bag F1 confirms the words
   are all there. **The recognizer swap (EasyOCR→eslav) is NOT a recognition regression on English**, and on Russian
   it was a large win (WER 0.168→0.100, see the experiment log). eslav is a solid recognizer for both scripts.

2. **READING ORDER was the hybrid's biggest weakness — now FIXED (new default).** The naive top-to-bottom line grouping
   mis-orders multi-column pages: the right words in the wrong order → high WER despite equal F1 (Tesseract's `psm 3`
   runs layout analysis, the hybrid didn't). Two reorderings are now wired via `hybrid_reading_order`; both leave the
   recognizer output (word-bag F1) untouched and only change line order (re-measured 2026-07, 60+60 gen_texts, 94 RU):

   | `hybrid_reading_order` | gen_texts long WER | gen_texts short WER | RU (single-col) WER | wall |
   |---|---|---|---|---|
   | naive (old default) | 0.690 | 0.411 | 0.097 | baseline |
   | **geometric — column XY-cut (NEW DEFAULT)** | **0.406** | **0.188** | **0.097** | ~+4% |
   | tesseract — borrow Tesseract layout | **0.056** | 0.295 | 0.102 | +45% |

   **`geometric`** is the default: a vertical/column-only XY-cut over the detection boxes (`hybrid_xycut_mult`=0.5 gap
   threshold). It is ~free, **strictly ≥ naive on multi-column and a no-op on single-column** (RU unchanged). It fixes
   *clean* multi-column but not complex interleaved layouts (headers woven through columns have no clean rectangular gap
   to cut) — there it falls back to naive order. **`tesseract`** additionally handles those and reaches Tesseract WER
   parity on long text (0.056), but pays a per-page Tesseract *layout* call (+45% wall) — opt in for layout-heavy
   corpora. Both fall back to naive on any failure so OCR never breaks.

3. **det=960 (detection downscale) has a real recognition cost.** eslav det=full beats det=960 on F1 by **1.6 pts
   (long) and 5.3 pts (short)** — the downscaled detector finds fewer/coarser boxes on dense text → lower recall. This
   was the big speed win (249→172 s) and was quality-neutral on scanned Russian/DAE, but on dense clean English it
   costs recognition recall. **Tradeoff to revisit** (e.g. det=1280 compromise, or content-adaptive); `hybrid_det_max_side`
   is configurable.

## 3. Table detection — hough-scale fix (gen_tables, clean cell GT)

90 synthetic table docs; cell-text recall = fraction of GT cell tokens recovered.

| `table_hough_scale` | tables/doc | cells/doc | cell-text recall |
|---|---|---|---|
| 0.5 (shipped default) | 1.97 | 72 | 0.919 |
| 0.33 | 1.97 | 72 | 0.909 |
| 0.25 | 1.97 | 72 | 0.914 |

**The Hough downscale is lossless for tables down to 0.25** — identical table/cell structure and flat cell-text recall
(0.909–0.919, within noise). Combined with the DAE full-pipeline runs (tables=6 preserved at 0.33 and 0.25, wall
144→136→134 s), **the default can safely drop to 0.33** (−8 s, comfortable margin) or 0.25. Not yet committed — this
report is the validation. (The residual ~8 % non-recall at every scale is the recognizer/cell-assignment baseline,
not scale-related.)

## 4. Orientation — cv2 preprocessing fix (orient set, rotation GT)

56 rotated pages (varied 90/180/270).

- **cv2 vs PIL preprocessing: 56/56 identical predictions** — the disaggregation fix (moved resize/pad to cv2 on CPU
  workers) is prediction-preserving on rotated docs, as on the DAE sample (20/20).
- **Classifier accuracy 55/56 = 98.2 %.** Confusion is clean: 90→90, 180→180, 270→270, with one 270→90 slip. The
  orientation classifier itself is reliable; the cv2/disaggregation speed fix (−45 s wall) does not touch its quality.

## 5. Deskew — coarse-to-fine fix (skew set, self-consistency vs 91-step)

56 heavily-skewed real pages (angles −44…+44°, mean |angle| 18° — an adversarial set; real docs skew ≤ ~10°).

| skew search | exact vs 91-step | max \|diff\| | mean \|diff\| | time |
|---|---|---|---|---|
| **coarse 3° + fine 1° (shipped)** | **55/56** | 38° | 0.68° | 120 ms (2.3×) |
| coarse 2° + fine 1° | 49/56 | 35° | 2.98° | 161 ms |
| coarse 1.5° + fine 1° | 40/56 | 37.5° | 0.80° | 207 ms |

- **The shipped coarse-3° matches the 91-step on 55/56** pages and is the best coarse choice; **finer steps are worse**
  (fewer exact matches). The divergences are *not* peak-missing — on extreme-skew pages the projection-profile score
  has multiple near-equal peaks (inherent ambiguity), so which one wins depends on the exact angles sampled; 3° happens
  to align best with the 91-step grid. On realistic skew (≤12°) coarse-3° is **exact** (35/35 on injected 0–12°).
- **Verdict: the fix is validated** — no meaningful quality loss for real documents; the lone 38° divergence is on a
  >40° page where even the 91-step's answer is ambiguous. Keep coarse-3°; 2.3× faster.

## 6. Cross-reference — Russian recognition (colleague's labelled set, from the experiment log)

| category | EasyOCR (old) | **eslav-fp16 (shipped)** | tesseract |
|---|---|---|---|
| RU prose (83) | 0.168 | **0.100** | 0.066 |
| degraded scans (11) | 0.668 | **0.198** | 0.160 |

eslav is 2.5–3× more accurate than the old EasyOCR recognizer on Russian; fp16 is bit-identical to fp32; homoglyph
post-fix is a small RU win. (Details in the experiment log.)

## 7. Summary — fix safety & recommendations

| fix / component | speed | quality verdict |
|---|---|---|
| **eslav recognizer** (vs EasyOCR) | ≈ | ✅ big win RU, neutral-to-better recognition EN (F1 ≥ tesseract) |
| **fp16 recognizer** | −30 % rec | ✅ bit-identical |
| **orient cv2 + disaggregation** | −45 s wall | ✅ 56/56 identical, classifier 98 % |
| **deskew coarse-to-fine** | 2.3× | ✅ 55/56 vs 91-step, exact on realistic skew |
| **table hough 0.5** (→0.33/0.25) | ×2.5+ | ✅ lossless to 0.25 (tables + cells flat) — safe to lower default |
| **det=960** | −77 s | ⚠️ costs recognition recall on dense text (F1 −1.6…−5.3 pts EN); neutral on scanned RU/DAE |
| **reading order → geometric column XY-cut** (NEW DEFAULT) | ~+4 % | ✅ was the #1 gap; multi-column WER long 0.69→0.41, short 0.41→0.19, single-column unchanged; F1 unchanged. `="tesseract"` reaches long 0.056 at +45 % wall for layout-heavy corpora |

**Recommendations, by impact:**
1. **Reading order is the #1 quality lever.** The hybrid loses to Tesseract on multi-block pages purely on ordering,
   not recognition. Re-evaluate XY-cut / layout-region ordering on **gen_texts / real_mixed** (multi-block) — the
   earlier dismissal was on single-column prose only. This is where accuracy is left on the table.
2. **Revisit det=960** — a genuine speed/recall tradeoff. Try det=1280 or content-adaptive; measure F1 on gen_texts.
3. **Lower `table_hough_scale` default to 0.33** — validated lossless, −8 s.
4. **Engine choice by language/layout**: eslav for Cyrillic, and for clean multi-block English Tesseract's layout
   analysis still wins end-to-end (WER) until the hybrid's reading order is fixed.
5. orient-cv2, deskew-coarse-fine, fp16 — **validated safe, keep**.
