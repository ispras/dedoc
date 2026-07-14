# CPU-only speedups for the scanned-PDF pipeline

Branch **`feature/cpu-optimizations`** (from `master` @ `187baf5`, v2.7). A series of *isolated, CPU-only* fixes to
the existing `PdfImageReader` pipeline — no architecture rework, no multiprocessing changes, no GPU. Each fix is
either **bit-identical** to master or **quality-validated as non-degraded** (proven with tests). The fixes were
mined commit-by-commit from the experimental `feature/staged-gpu-pdf-pipeline` branch (which proved the gains) and
re-applied / re-implemented against master's real code paths.

## Headline

On the **DAE (India) Annual Report 2020-21** (297 pages, scanned, image pipeline, `n_jobs=1`, `lang=eng`, single
launch — the slow current pipeline):

| configuration | wall | vs master |
|---|---|---|
| master baseline | **1517.0 s** | — |
| **+ all 4 default fixes** (metadata, HoughLinesP, table-gate, deskew) | **1092.9 s** | **−28.0%**, quality-preserving |
| + opt-in pdfium render (`DEDOC_RENDER=pdfium`) | 1011.4 s | −33.3%, but **degrades OCR on Tesseract** (see below) |

Output is preserved: **tables = 6** at every step; body-text word-bag F1 vs the baseline stays **≥ 0.99993** through
the deskew step.

## Method

- **Speed**: full 297-page run through master's `PdfImageReader` (Tesseract OCR, poppler render, CPU orientation),
  `n_jobs=1`, single launch. Fixes applied cumulatively; each row's Δ is vs the previous row.
- **Quality**, per fix, using the constraint *bit-identical OR non-degraded (proven)*:
  - `text_sha` + `anno_sha` (SHA of every extracted line + every annotation) for bit-identical claims.
  - Diff-vs-baseline **word-bag F1** (order-independent) of body text + table cells on the full doc.
  - Re-run **word-bag F1 on the labelled `pdf_profiling` set**: `gen_tables` cell-recall (table fixes), `gen_texts`
    OCR F1 (render), and `skew` angle vs the 91-step reference (deskew).

## Results (cumulative)

| # | fix | commit | wall | Δ | cum. vs master | quality verdict |
|---|---|---|---|---|---|---|
| 1 | metadata: vectorized valley binarizer + cv2.threshold, SIMD color annotation, drop no-op `rid_spaces` | `6041b60 8ebfa0d 69375bf f0c530f` | *(folded into #2)* | ~−17 s (isolated) | — | **bit-identical**: `text_sha` + `anno_sha` match over 40 pages (45 749 annotations) |
| 2 | HoughLinesP downscale (`table_hough_scale=0.5`) | `0ef5461` | 1360.5 s | **−156.5 s** (incl. metadata) | −10.3% | gen_tables cell-recall **0.6066 → 0.6066** (identical), tables=6, body F1 **0.99996** |
| 3 | table line-crossing gate (skip detector on tableless pages) | `faf4b23` | 1339.3 s | **−21.2 s** | −11.7% | gen_tables recall identical; gate ON vs OFF **byte-identical over 60 pages** (0/69 827 anno diff); tables=6 |
| 4 | deskew coarse-to-fine (`FastSkewCorrector`) | `9443a86` | 1092.9 s | **−246.4 s** | **−28.0%** | skew angle **29/30 exact** vs 91-step; body F1 **0.99993**, cells identical, tables=6 |
| 5 | pdfium render + erode — **OPT-IN, not default** | `799dd03` | 1011.4 s | −81.5 s | −33.3% | ⚠️ **degrades**: gen_texts F1 **0.9212 → 0.9177** (−0.38%), body F1 0.988 |

## Per-fix notes

**1. Metadata (binarizer / color / bold).** Vectorized the bold classifier's valley-emphasis Otsu (`cv2.calcHist` +
cumsum), replaced its two-pass binarization with `cv2.threshold`, replaced the color-annotation's 5-pass numpy mask +
3 boolean-index gathers with `cv2.inRange` + `cv2.sumElems/countNonZero`, and dropped `__get_rid_spaces` (a proven
no-op — its `len(not_space) > 3` guard is the column count, always true). All bit-identical: over 40 pages both the
extracted text **and** every annotation (`anno_sha = eabddd30…`, 45 749 annotations) match master exactly. Per-page
CPU saving ~59 ms; below single-run noise on the full wall, so folded into run #2.

**2. HoughLinesP downscale.** `HoughLinesP` (line detection for bordered tables) runs on a 0.5× copy — it only needs
the line angle (scale-invariant) and gap-filling mask. On the labelled `gen_tables` set the cell-recall is *identical*
to full-res; on the DAE body text is 99.996% identical. The DAE table **cells** are segmented slightly more finely
(+8%, cell F1 0.84) but with no labelled-recall loss and tables=6 preserved.

**3. Table line-crossing gate.** A ~7 ms/page signal (built from the *detector's own* line params — fixed-225
threshold, short h/v kernels floored at `TableTree.min_w/h_cell`) counts grid crossings and skips the ~360 ms
detector when a page has < 2 (config `table_line_gate_min_cross`). Recall preserved (gen_tables identical, tables=6).
Proven a no-op on tableless pages: gate ON vs OFF is byte-identical over 60 pages (the gate returns the original
image, which equals the detector's `np.copy` when it finds nothing). A residual full-doc `anno_sha` nuance on a late
page touches only bold/color metadata — text, cells and table count are identical. Modest win here (−1.6%) because
the Hough downscale (#2) already cut most of the detector cost.

**4. Deskew coarse-to-fine — the biggest win.** `dedocutils.SkewCorrector` rotates the full page 91 times per page
(one per candidate angle) — the dominant CPU cost of the scanned-image pipeline. `FastSkewCorrector` (a drop-in
subclass wired into `PdfImageReader`) brackets the peak with a coarse 3° sweep on a ≤512 px thumbnail, refines ±4° at
1° on a 1000 px image, and skips the final rotation when the angle is 0 (`rotate_image(x,0)` is an identity warp).
Same projection-profile scoring → **29/30 exact** vs the 91-step on the adversarial skew set (the lone divergence is a
>28° page where the peak is inherently ambiguous), exact on realistic skew ≤12°. DAE body text **99.993%** identical,
cells identical.

**5. pdfium render — OPT-IN, excluded from the default.** In-process PDFium rendering is ~7% faster end-to-end than
`pdf2image`/`pdftoppm` (no poppler subprocess, no per-batch re-parse). But on **master's Tesseract path** it is *not*
quality-neutral: PDFium's glyph anti-aliasing is ~1 px thinner, and even with a 2×2 erode (which was tuned for the
*hybrid* recognizer on the experimental branch, not Tesseract) it shifts Tesseract's output — measured **−0.38%
gen_texts F1** and **0.988 body-text F1** on the DAE (below the 99.5% bar). Per the no-degradation constraint it is
kept **opt-in** via `DEDOC_RENDER=pdfium`; the default (`_split_pdftoppm`) is the original poppler code,
byte-identical to before. Re-tuning the erode for Tesseract could make it quality-neutral — open follow-up.

## What was deliberately **not** ported

GPU/hybrid OCR (DBNet + PP-OCRv5 + TensorRT), the 2-GPU-worker parallelism, shared-memory transport, lazy-import RAM
trims, and orientation/layout NN batching — all excluded as GPU-oriented, multiprocessing, or architecture changes,
per scope. OCR itself (Tesseract, 31% of runtime) is untouched — speeding it up means swapping the engine (out of
scope).

## Merge-readiness

The **4 default fixes (`6041b60`…`9443a86`) are ready to merge to main**: CPU-only, isolated, each bit-identical or
quality-validated non-degraded, −28% on the 297-page benchmark, tables and text preserved. The **render fix
(`799dd03`) is opt-in** and should stay opt-in until the erode is re-tuned for Tesseract (or left as a documented
speed/quality knob).

All commits authored `OligerMan <ol104940@gmail.com>`. Raw run log: `scratchpad/RESULTS.log`.
