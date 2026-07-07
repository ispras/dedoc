# GPU-OCR pipeline optimization — experiment log

A running lab notebook of the scanned-PDF OCR pipeline optimization on the process-model pipeline
(`dedoc/pipeline/`). Records **every** experiment, including the ones that failed or were reverted — a negative
result is a result. Newest sections at the bottom.

## Setup / environment (Windows, one dev box)

- Hardware: NVIDIA RTX 3080 Laptop (16 GB), 33.2 GB RAM (~15.6 GB free), 8 CPU workers used.
- Env: `venv\Scripts\python.exe` (Python 3.10). poppler+tesseract from conda `dedocbin`. `PYTHONUTF8=1`,
  `OMP_THREAD_LIMIT=1`, `OMP_NUM_THREADS=1` (Tesseract single-threaded, as in the real 8-way pipeline).
- **`HF_HOME` was `E:\hf-cache` on a now-removed drive** → the docling layout model (`docling-project/docling-layout-heron`)
  failed to load with `FileNotFoundError: 'E:\'`, cascading to `table` (KeyError 'image') and `ocr_gpu`. Fixed
  2026-07: relocated `HF_HOME` to `C:\Users\OligerMan\.cache\huggingface` (persistent) + re-downloaded the model.
  Always export `HF_HOME=C:\Users\OligerMan\.cache\huggingface` in run commands.
- Other required fixes: torch CUDA build (`2.2.2+cu121`), JBR java for tabby, tessdata + `TESSDATA_PREFIX`.
  onnxruntime-gpu needs the CUDA-12 ORT build + cuDNN 9; DLL dirs added at runtime (torch/lib, nvidia/cudnn/bin,
  nvidia/cublas/bin) after popping `CUDA_PATH`.

## Benchmark methodology

- **Main doc:** `test_docs/DAE (India) Annual Report 2020-21.pdf` — 297 pages, scanned, 6 tables, ~2300 px long side.
- Harness: `scratchpad/bench_full.py` — warm run, reports wall time, node count, table count, `text_len`,
  `text_sha` (sha of normalized text — same sha = byte-identical output), CPU/GPU avg %, peak process-tree RSS.
- Per-stage timing: `DEDOC_STAGE_TIMING=<dir>` dumps per-worker `stage_<pid>.json` (unwrap/compute/write per stage);
  `scratchpad/agg_stage_times.py` aggregates. GPU/CPU idle-gap trace: `DEDOC_GPU_TRACE=<dir>` +
  `analyze_trace.py` / `analyze_all.py`.
- Quality: `scratchpad/compare_quality.py` — word-bag recall/precision of hybrid vs Tesseract on a page range.
- nvidia-smi util×wall is UNRELIABLE for bursty kernels — use `torch.profiler` self_cuda_time or empirical throughput.

## Baseline & pipeline infrastructure

| milestone | time | note |
|---|---|---|
| original single-process | 1377.6 s | pre-pipeline |
| process pipeline, 8 workers + GPU | 336.7 s | ×4.1 |
| + deskew downscale | 234.9 s | ×5.9 |
| + shared-memory image return | 213.8 s | ×6.4 |
| **Tesseract baseline (re-measured, current code)** | **221 s** | reference for all OCR work |
| stub-OCR floor (skip OCR entirely) | 114 s | pipeline floor without OCR |

Committed optimizations (clean commits):
- **deskew via downscaled angle detection** (`9fafcb1`): detect skew on a downscaled image (long side floored at
  1000 px), rotate at full res. Node count 5626→5611 (±1° detection precision, accepted as not-a-bug).
- **shared-memory image return + layout table-gate** (`3777960`): parent-owned buffer pool; layout (docling RT-DETR,
  class 8 = table) gates the OpenCV table detector. Lossless when layout runs (with_attachments).
- **pluggable OCR engine** (`509dc12`) + **EasyOCR/DBNet setup docs** (`c35edee`).

## GPU-OCR engine investigation

- **Tesseract** (LSTM, CPU, self-forks, `image_to_data --psm 3`): best quality + throughput at the time
  (~2.57 pg/s ×8 at OMP=1). Initial conclusion: GPU-OCR could not beat 8× Tesseract — LATER OVERTURNED (see hybrid).
- **EasyOCR** (CRAFT / DBNet18 detector + CRNN recognizer, torch): added as a parallel engine. DBNet is ~94% GPU-bound
  (~1232 ms/page kernels), not CPU-bound as first mis-measured. CRAFT slower with bigger batches.
- **CUDA-DCN** compiled for DBNet18 (deformable-conv op; patched `<THC/THCAtomics.cuh>` → `<ATen/cuda/Atomic.cuh>`
  for torch ≥ 1.11; VS2022 + nvcc 12.6). Built successfully.
- **PP-OCR via RapidOCR** (onnxruntime, MobileNet DBNet detector + CRNN, no Paddle framework): got a clean CUDA number.
  Lightweight detector, fast.
- **Hybrid = PP-OCR detector (RapidOCR/onnxruntime-CUDA) + EasyOCR recognizer (torch-CUDA)**: 535 ms/page single-stream,
  2.3× faster than EasyOCR-DBNet, cleaner quality. Downsides: line-level boxes, column reading-order. PP-OCR's OWN
  recognizer was NOT used — EasyOCR recognizer kept for quality (rus+eng on our scans).
- Vetoed: reducing RECOGNITION resolution / EasyOCR `canvas_size` (hurts small-text quality; "Tesseract can do the same").
  NOTE: DETECTION resolution is a different knob — see det=960 below, which turned out safe.

## Hybrid full-pipeline optimization (chronological)

All on the 297-page doc. "verdict" = kept / reverted.

| # | change | time | RAM | result | verdict |
|---|---|---|---|---|---|
| 1 | naive hybrid (OCR stage → GPU) | 269.7 s | 8.0 GB | slower than Tesseract 221 | — |
| 2 | + move orient stage to CPU | 348.4 s | 9.3 GB | WORSE — orient EfficientNet forward is 36× slower on CPU (per-page, no GPU batch) | reverted |
| 3 | disaggregate: det_pre (CPU) → ocr (GPU) | 303.5 s | **16.8 GB** | WORSE — det_prepro pickled worker→parent + 8× onnxruntime on CPU workers → memory pressure/swap | superseded |
| 4 | + shm for det_prepro (generalized buffer pool to N array fields) + standalone numpy det-preprocess (no RapidOCR/onnxruntime on CPU workers) | 286.1 s | 11.7 GB | memory fixed (no 8× onnxruntime); GPU util 27→44% | kept |
| 5 | + batch rec (pool crops across pages → one CRNN pass) | 310.9 s | — | WORSE — batch-collection latency + padding to global max width; CRNN compute unchanged | reverted |
| 6 | meta-split: `ocr_gpu` (GPU: infer+post+recognize) → `ocr` (CPU: line-grouping + metadata) | 248.9 s | — | GPU-worker ocr dropped 1063→550 ms; parallelism ×3.55→×5.46 | kept |
| 7 | table-gate for hybrid (force layout) | 286.9 s | 12 GB | HURTS hybrid — layout (159 ms) adds to the GPU-worker bottleneck | reverted (env-flag only) |
| 8 | **det=960 (detection long side ≤ 960, was full ~2300)** | **172 s** | 11.2 GB | BIG WIN — det_prepro 47→14 MB (transport 46→11 s), infer + preprocess cheaper; text_len HIGHER (804999) — DBNet detects better in its native range | **kept** |
| 9 | line-building offload (ocr_gpu returns raw detections; meta builds the page) | 171 s | — | neutral (the ~93 ms ocr_gpu "overhead" was transport + plumbing, not line-grouping) | kept (cleaner) |
| 10 | batch rec again at det=960 | 180 s | — | still worse | reverted |
| 11 | max_inflight 24 / 40 (was 16) | 171.4 / 178 s | — | no help — stalling is not admission-window-bound | reverted |
| 12 | **table Hough downscale 0.5** | **160.9 s** | 11.1 GB | BIG WIN — HoughLinesP was 79% of table detection (542→127 ms/page); table stage 534→210 s. tables=6, text_len preserved | **kept** |
| 13 | table morphology downscale 0.5 | 169.7 s | — | no effect — morphology is only ~28 ms/page; Hough is the cost | reverted |
| 14 | orient → CPU retry (after all above) | 249.6 s | 12.4 GB | WORSE again — orient = 4331 ms/page on CPU vs 120 ms batched on GPU (36×). Confirms orient is pinned to GPU | reverted |
| 15 | **fp16 recognizer** (`DEDOC_REC_FP16`, `torch.autocast` fp16 around the CRNN) | 175 s | — | recognition **22 % faster** (172→135 ms/page, clean micro-bench); wall **−5-6 %** (~9.5 s: back-to-back A/B fp32 184.5 / fp16 175.0 on a lightly-loaded box → ~160.9→~151 unloaded). BiLSTM stays partly fp32 under autocast, so not 2×. text_len +0.02 % (fp16 numerical, near-lossless — verify on a WER set before default-on) | **kept** (env-gated pending WER check) |

Note: the fp16 A/B and the earlier fp16 full-doc (193 s) were run on a lightly-loaded machine (ALL stages inflated
~15 %); trust the back-to-back A/B delta (−5-6 %) and the isolated micro-bench (−22 % on recognition), not the absolute
numbers. Machine-load contamination is a recurring hazard — always A/B back-to-back in one command.

### det=960 detail (sweep on pages 1:60, cold)

| detection long side | time | text_len | note |
|---|---|---|---|
| full (~2300, `limit_type=min`) | 69.9 s | 180487 | |
| 1280 | 58.8 s | 184958 | |
| **960** | **45.0 s** | **188491** | fastest AND highest text_len |

Reasoning: PP-OCR DBNet is trained at ~960; at 2300 px it over/under-segments. Recognition still crops from the
FULL-res image → recognition quality unaffected. This is why det-downscale is safe while recognition-downscale is not.

## Table detection

- `table` was the single biggest stage (1732–1801 ms/page, ~534 s total) because with attachments off there is no
  layout pass, so the OpenCV contour detector runs on ALL pages (it produces nothing on the ~289 non-table pages).
- **cProfile hotspot: `HoughLinesP` = 4.34 s of 5.46 s (79%), ~540 ms/page.** Morphology (erode/dilate) only ~28 ms.
- **Fix (kept): Hough downscale** (`DEDOC_TABLE_HOUGH_SCALE=0.5`) — Hough only needs the line ANGLE (scale-invariant)
  + drawing gap-filling lines; run it on a ½-scale copy (length/gap params scaled), upscale the line mask back.
  Cell OCR + contours stay full-res. HoughLinesP 542→127 ms; tables=6, text preserved.
- Rejected: gating table via layout — hurts the hybrid (layout on the GPU-worker bottleneck) and was a wash for
  Tesseract too (layout adds a mid-chain GPU stage that stalls). Morphology downscale — no effect.

## Diagnosis / profiling of the current best (det=960 + hough 0.5, ~155–161 s)

Per-stage compute (total across 297 pages) and resource:

| stage | total | ms/page | resource |
|---|---|---|---|
| deskew | ~270 s | 897 | CPU (8 workers) |
| render | ~259 s | 872 | parent thread pool |
| table | ~210 s | 706 | CPU (8 workers) |
| ocr_gpu (det infer + CRNN recognize) | ~96–100 s | 323–338 | **GPU worker** |
| ocr (line-grouping + metadata) | ~47–50 s | 158–167 | CPU |
| orient | ~36–40 s | 120–135 | **GPU worker** |
| det_pre | ~17–30 s | 55–101 | CPU |

**GPU-worker idle-gap trace:** span 146 s, busy 135 s → **92–93 % utilized**. Idle ~11 s = one-time ramp (~5.5 s: first
ocr_gpu waits for page 1 to cross the whole chain) + ~9 s dispatch latency before ocr_gpu (25–30 ms/page, det_prepro
handoff/unwrap) + ~2 s before orient. Steady-state stalling is ~3 %.

**CPU/render idle-gap trace:** cpu_process workers **49 % utilized** (564 s busy / 581 s idle); render (8 parent
threads) **22 % utilized** (259 s busy / 934 s idle). Both are idle *because* the chain is gated by the single GPU
worker (deskew waits ~1030 ms before each run, blocked on orient which is on the GPU worker). Huge CPU headroom exists
but cannot absorb the GPU-bound OCR work (both GPU stages pinned to GPU). Only mixed Tesseract(CPU)+hybrid(GPU) OCR
could use it — estimated balance ~110 s each side → wall ~115–120 s, but mixes OCR engines across pages.

## Quality

- Hybrid (det=960) vs Tesseract, word-bag on pages 1:20: **recall 0.975** (hybrid captures 97.5 % of Tesseract's
  words), **precision 0.953**; hybrid finds slightly MORE words (7645 vs 7472). Differences are word-spacing artifacts
  (EasyOCR line-grouping merges "of the"→"ofthe") and short noise tokens, not lost content.
- `tables=6` and `text_len` preserved across det=960 and Hough-0.5.

### FUNSD WER (absolute, `jiwer`; harness `scratchpad/wer_funsd.py`, HF `nielsr/funsd-layoutlmv3` test, 50 forms)

| engine | WER | CER | word-F1 |
|---|---|---|---|
| hybrid fp16 | 0.714 | 0.450 | 0.607 |
| hybrid fp32 | 0.714 | 0.450 | 0.607 |
| tesseract | 0.610 | 0.447 | 0.674 |

- **fp16 == fp32 bit-for-bit** across all 50 forms → **fp16 (#15) is quality-neutral**, safe to default-on.
- On FUNSD **Tesseract beats the hybrid** (WER 0.61 vs 0.71, word-F1 0.67 vs 0.61; CER ~equal). BUT **FUNSD is FORMS**
  (scattered fields/labels/tables) — it stresses exactly the hybrid's known weakness (line-level grouping + reading
  order on scattered layouts; Tesseract psm 3 does layout analysis). The ~0.6-0.7 WER for *both* is reading-order
  mismatch, not raw character accuracy. **Not representative of our prose reports** (where hybrid ≈ Tesseract, 97.5 %
  word recall). Use a PROSE set (OCR-Quality) for a fair comparison of the real use case.

## Reading order (XY-cut) — `DEDOC_XYCUT`

The hybrid orders lines by a naive top-to-bottom sort (`_detections_to_lines`), which merges multi-column text
left↔right and mis-orders scattered layouts. **Recursive XY-cut** (`hybrid_line_extractor._xy_cut_detection_blocks`):
recursively cut the page at the widest column/band whitespace gap (pure geometry on the word-detection boxes, ~ms/page,
negligible CPU), partition into blocks in reading order, then line-group WITHIN each block. Threshold = median box height.

- **First attempt applied XY-cut to already-grouped LINES → total no-op** (text_sha byte-identical on FUNSD AND DAE):
  the lines already span columns (grouping merged them across the page), so no column gap is visible between lines.
  Wrong level. Fixed by cutting the raw DETECTIONS before line-grouping.
- **FUNSD (50 forms): negligible** — hybrid WER 0.714 → +xycut 0.712 (CER/F1 unchanged). Forms aren't multi-column;
  their disorder is GT-annotation-order + irregular field layout, which XY-cut doesn't address (that needs
  Tesseract-style layout analysis — the `tesserocr.AnalyseLayout` "borrow from Tesseract" option, ~free on the idle CPU).
- **DAE prose (pp. 40:80): reorders** (text_sha 0c9d… → 72ce…, same text_len, nodes 617→693). Confirms it is live on
  prose, but the node increase hints at possible OVER-SEGMENTATION on single-column pages, and the benefit on genuine
  multi-column pages is UNVALIDATED (no labelled multi-column set yet). **Kept env-gated, NOT default** until validated
  on a 2-column corpus (e.g. academic papers in OCR-Quality). CPU cost is negligible either way.

### Layout-guided reading order (docling RT-DETR regions → order regions → bucket words → per-region line-group)

Idea: layout runs anyway in some pipelines (attachments / table gate), and its region boxes give a cleaner block
structure than XY-cut on noisy word boxes. Harness engine `hybrid+layout` (`scratchpad/wer_funsd.py`): RT-DETR regions,
ordered by XY-cut, words bucketed into the region whose box contains their center, unassigned words appended last.

| FUNSD 50 | WER | CER | word-F1 |
|---|---|---|---|
| hybrid (naive) | 0.714 | 0.449 | 0.607 |
| hybrid + xycut | 0.712 | 0.449 | 0.607 |
| **hybrid + layout** | **0.772** | **0.530** | 0.607 |
| tesseract | 0.610 | 0.447 | 0.674 |

- **Layout ordering is WORSE on FUNSD** (WER 0.772). RT-DETR (docling, trained on DocLayNet prose/business docs) does
  not segment FUNSD FORMS well → many words fall outside all regions → dumped into the trailing "leftover" bucket →
  order destroyed. word-F1 unchanged (order-only).
- **Verdict for forms:** neither XY-cut nor layout helps; Tesseract's own layout analysis wins on forms.
- **BUT FUNSD (forms) is the wrong benchmark for these approaches** — both XY-cut and layout-ordering target
  multi-column / block PROSE (RT-DETR's home turf). The reading-order question is UNRESOLVED until tested on a
  labelled multi-column PROSE corpus (OCR-Quality academic papers). FUNSD gives misleading negatives here.

## ⚠ Absolute quality on REAL prose (colleague's `data_tesseract_benchmarks`) — REFRAMES the whole tradeoff

A labelled benchmark from the team (ISP RAS owncloud): 102 real document page scans + UTF-8 ground-truth text, in
4 categories. Harness `scratchpad/wer_bench.py` (recognize once/image, reorder 3 ways; `jiwer`). lang=rus+eng
(downloaded `rus.traineddata` for Tesseract; EasyOCR `['ru','en']`), english-words at eng.

| category | engine | WER | CER | word-F1 |
|---|---|---|---|---|
| **tz-npa-vkr** (83, RU prose) | hybrid | 0.168 | 0.072 | 0.885 |
| | hybrid + xycut | 0.172 | 0.076 | 0.885 |
| | hybrid + layout | 0.303 | 0.203 | 0.885 |
| | **tesseract** | **0.066** | 0.042 | 0.963 |
| **low_quality** (11) | hybrid | 0.668 | 0.289 | 0.397 |
| | **tesseract** | **0.160** | 0.066 | 0.858 |
| **others** (3) | hybrid | 0.215 | 0.059 | 0.813 |
| | **tesseract** | **0.187** | 0.139 | 0.865 |
| **english-words** (5) | hybrid | 0.581 | 0.529 | 0.425 |
| | **tesseract** | **0.563** | 0.533 | 0.437 |

**Conclusions (this overturns earlier assumptions):**
1. **Tesseract is more accurate than the hybrid in EVERY category** — RU prose 0.066 vs 0.168 WER (2.5×), degraded
   scans 0.160 vs 0.668 (4×), and marginally on English. The hybrid's speed (−32 %) buys a **real accuracy loss**.
   The earlier "97.5 % word recall vs Tesseract" measured *agreement*, not accuracy — Tesseract is the accurate one,
   and the hybrid (EasyOCR recognizer) diverges, especially on degraded scans.
2. **XY-cut (#reading-order): drop it** — neutral-to-slightly-worse (0.168→0.172) via over-segmentation on
   single-column prose. Never helped on any real corpus tested.
3. **Layout-guided ordering: drop it** — consistently WORSE (0.168→0.303). The word-buckets/leftover scheme mis-orders.
4. **fp16 remains quality-neutral** (validated on FUNSD; orthogonal to accuracy).

**Reframed recommendation:** for a quality-first library, **Tesseract stays the default OCR** (clearly more accurate on
real docs). The hybrid is a **speed option** (−32 % wall) with a known accuracy cost — reasonable only where throughput
≫ accuracy or on clean single-column prose. To make the hybrid competitive on accuracy, its recognizer (EasyOCR CRNN)
is the limiter — would need a stronger recognizer (see ONNX / alternative-recognizer levers), not more pipeline speed.

### Error analysis of the hybrid vs Tesseract (worst-gap examples, `scratchpad/wer_diff.py`)

Two distinct failure modes:
1. **Degraded scans (low_quality) → catastrophic**: EasyOCR CRNN collapses into near-gibberish ("Глава 1. ИСТОРИЯ
   НОРВЕГИИ" → "Tмaшэ 1 ИСтоРия НОРВНИИ"), Tesseract's LSTM stays robust (WER 0.14). Fundamental recognizer limit,
   not config-fixable.
2. **Clean prose → systematic character confusions** (text is readable): (a) **Cyrillic↔Latin look-alikes** — outputs
   Latin for Cyrillic (ТТО→'TTO', АТО→'ATO', О→O, С→C), each such word counts as wrong (different codepoints);
   (b) Cyrillic-internal look-alikes (и↔н↔п, л↔к, ц↔н).

### Homoglyph post-normalization (`DEDOC_HOMOGLYPH`, Russian only) — kept

Fixes failure-mode 2a: map a token's Latin homoglyphs → Cyrillic UNLESS the token has a foreign-only Latin letter
(b,d,f,g,…) and no Cyrillic (keeps 'Pentium'/'SQL'). `hybrid_line_extractor._homoglyph`, applied in
`recognize_detections` when `'ru'` in the languages. ~free (string map).

| category | hybrid | **hybrid+homo** | tesseract |
|---|---|---|---|
| tz-npa-vkr (83) | 0.167 | **0.149** (F1 .885→.903) | 0.066 |
| others (3) | 0.215 | **0.188** (≈ tesseract) | 0.187 |
| low_quality (11) | 0.668 | 0.651 | 0.160 |
| english-words (5) | 0.581 | 0.448* | 0.563 |

Real cheap win on Russian (WER −11 %); does NOT close the Tesseract gap (remaining = Cyrillic-internal confusions +
low_quality collapse). *english-words is 5-image noise and homoglyph on English is risky → gated to Russian only.
Variants considered: A always-convert (breaks English), B mixed-token-only (misses fully-Latinised words), **C
context-aware (chosen)**, D dictionary-based (tested below).

### Dictionary correction (variant D) for Cyrillic-internal confusions (и↔н↔п, л↔к) — DROPPED

`pyspellchecker` RU (only **19 880** words). Meant to fix failure-mode 2b.

| tz-npa-vkr | hybrid+homo | +dict (naive edit-dist) | +dict (confusion-constrained) | tesseract |
|---|---|---|---|---|
| WER | 0.132 | **0.156** (worse) | 0.132 (no change) | 0.052 |

- **Naive edit-distance correction HURTS** (0.074→0.156 on a 10-img slice): the tiny dictionary + technical/legal
  vocabulary (АСУ, ФСТЭК, proper nouns) means many valid words are "unknown" → over-corrected to wrong frequent words.
- **Confusion-constrained** (correct only if a single known-look-alike swap и↔н↔п / л↔к / ц→н yields a dictionary
  word): safe but **neutral** — the small dict doesn't contain the correct technical forms, so the swap rarely finds
  a candidate → almost no corrections fire.
- Fundamental dilemma: a bigger dict raises recall but ALSO raises over-correction risk on technical/legal vocabulary.
  No mode gives a clean win with the available dictionary. **Dropped.** Closing failure-mode 2b safely needs a strong
  language model / a domain dictionary, or (better) a stronger recognizer — not naive spell-correction.

## ★ Recognizer swap: EasyOCR CRNN → PP-OCRv5 East-Slavic (drop-in, big accuracy win)

Research pointed to a stronger recognizer. Found a ready ONNX PP-OCRv5 Cyrillic recognizer:
`monkt/paddleocr-onnx` → `languages/eslav/{rec.onnx (7.9 MB), dict.txt (517 chars), config.json}` —
`eslav_PP-OCRv5_mobile_rec` (Russian/Bulgarian/Ukrainian/Belarusian/English), CTC, input (N,3,**48**,W) — note the
config.json says height 32 but the ONNX is 48; use `rec_img_shape=[3,48,320]`, output 519 = 517 dict + blank + space.
Runs on the SAME RapidOCR/onnxruntime-CUDA stack as our detector (`TextRecognizer` with `use_cuda`,
`rec_keys_path=dict.txt`). Harness `scratchpad/wer_ppocr.py` (same detector boxes for easyocr & ppocr).

| category | easyocr (CRNN) | **PP-OCRv5 eslav** | tesseract | gap-to-Tesseract closed |
|---|---|---|---|---|
| tz-npa-vkr (83) | 0.168 | **0.105** (−37 %) | 0.066 | 62 % |
| low_quality (11) | 0.668 | **0.198** (−70 %) | 0.160 | **93 %** |

- **Catastrophic degraded-scan failure essentially fixed** (0.668→0.198, now near Tesseract's 0.160).
- Prose gap to Tesseract shrank 0.102 → 0.039.
- Bonus: an all-ONNX recognizer **drops the EasyOCR/PyTorch dependency** for recognition (no fp16-autocast, no
  cuDNN-9-for-torch juggling). The whole hybrid becomes RapidOCR det + RapidOCR eslav rec (pure ONNX-CUDA).
- **WIRED IN (2026-07):** shipped `ocr/ppocr_eslav/{rec.onnx,dict.txt,config.json}`; `recognize_detections` now crops
  each box (`_rotate_crop`) → `_ensure_ppocr_rec()` (RapidOCR `TextRecognizer`, ONNX-CUDA) → detections. Verified the
  extractor path matches the standalone eslav measurement. EasyOCR/torch recognizer + fp16-autocast dropped from the
  path (EasyOCR now only supplies `_detections_to_lines`/`_map_languages` utilities). Still slightly behind Tesseract
  on clean prose but a genuine speed/accuracy tradeoff now (−32 % wall). Homoglyph post-norm kept (env-gated).
- **Speed check (clean run — earlier numbers were contaminated by background GPU tasks):** recognition-only ms/page —
  easyocr fp16 (torch) ~191 (incl. crop), eslav **fp32** onnx ~293 (excl. crop), eslav **fp16** onnx ~203. Bigger
  rec batch HURTS eslav (batch 32/64 → 760/840 ms — PP-OCR pads each batch to its widest crop; batch 8 is optimal).
- **fp16-ONNX conversion** (`onnxconverter_common.float16.convert_float_to_float16(keep_io_types=True)` → `rec_fp16.onnx`,
  7.9→4.0 MB, IO stays fp32 so it's drop-in): **−30 % recognition time (293→203 ms), accuracy IDENTICAL** to fp32
  (tz-npa-vkr 0.105/0.105, low_quality 0.199/0.198). So eslav-fp16 ≈ easyocr-fp16 speed but 2.5–3× more accurate —
  the accuracy win with ~no speed cost. WIRED: `_ensure_ppocr_rec` uses `rec_fp16.onnx` on GPU, `rec.onnx` on CPU.
- **Homoglyph on eslav:** small win (tz-npa-vkr 0.105→0.100, low_quality ~flat) — eslav is already a cleaner model
  than EasyOCR so has fewer Latin look-alikes to fix (vs −11 % on EasyOCR). Kept, now **default-on for Russian**
  (`DEDOC_HOMOGLYPH=0` to disable).
- **Error analysis eslav-fp16 vs Tesseract** (`scratchpad/wer_diff_eslav.py`): eslav's RECOGNITION is good (no
  EasyOCR-style gibberish); the residual gap to Tesseract (0.100 vs 0.066) is mostly NON-recognition —
  (a) **reading order on multi-column headers** (TZ_21/34, LAW_003: columns interleaved — biggest; XY-cut/layout is
  genuinely applicable here, unlike single-column prose); (b) **word merging / dropped spaces** ("ФГУП«ЦНИИ",
  "ксфере"); (c) residual Cyrillic↔Latin (partly fixed by homoglyph); (d) stamps/letterheads (both engines struggle);
  (e) degraded low_quality (eslav weaker but readable).
- **Reading-order (XY-cut block ordering) on eslav — WASH, dropped** (`scratchpad/wer_xycut.py`, threshold sweep):
  tz-npa-vkr naive 0.100 vs xycut ×0.5/×1/×2 = 0.101/0.101/0.100; low_quality flat. The multi-column headers are a
  small fraction of the corpus and XY-cut either doesn't catch their (narrow) column gap or over-segments the
  single-column bodies — net zero at every threshold. Layout-model ordering was already worse (RT-DETR mis-segments).
  Reading-order is not a productive lever here. Word-merging (space insertion) remains an open, detector-side lever.
- **Bottom line:** hybrid = RapidOCR det + PP-OCRv5-eslav-fp16 rec + homoglyph → **0.100 / 0.198** (prose / low_quality)
  vs EasyOCR 0.168 / 0.668 and Tesseract 0.066 / 0.160, at ≈EasyOCR speed, pure ONNX. The remaining ~0.034 prose gap
  to Tesseract has no clean lever (reading-order wash, word-merging needs detector work, stamps/low-quality are
  recognizer limits) → diminishing returns; consolidate.
- TODO: full-pipeline bench_full with eslav-fp16 (end-to-end speed); clean up dead EasyOCR recognizer methods.

## Current best config

`ocr_engine=hybrid`, `DEDOC_DET_MAX_SIDE=960`, `DEDOC_TABLE_HOUGH_SCALE=0.5`, `DEDOC_REC_FP16=1`, orient on GPU.
**~151 s vs Tesseract 221 s (≈ −32 %)**, quality ≈ Tesseract (97.5 % word recall), tables preserved.
(env flags to be promoted to config on consolidation.)

## Remaining levers (open)

1. ~~fp16 recognizer~~ — DONE (#15): −5-6 % wall, −22 % recognition, near-lossless.
2. **EasyOCR recognizer → ONNX** (same weights, onnxruntime-CUDA fp16, incl. the BiLSTM which autocast leaves in
   fp32) — quality-preserving, could beat autocast on the RNN; more effort than #1.
3. Mixed Tesseract(CPU)+hybrid(GPU) OCR to use the idle CPU — ~115–120 s but mixes engines.
4. Deeper scheduler work to shave the ~3 % steady-state GPU-worker stalling — low expected return.

## Quality metric TODO (WER)

Current quality signal is word-bag recall/precision vs Tesseract (relative, 97.5 %). Replace with ABSOLUTE WER/CER
on a labelled OCR set (`jiwer`). Candidate datasets: FUNSD (HF `nielsr/funsd`, forms, tiny — smoke), OmniAI OCR
benchmark (HF `getomni-ai/ocr-benchmark`), OCR-Quality (arXiv 2510.21774, 1000 PDF→PNG pages — closest to our scans),
UNLV-ISRI (classic). Harness: dataset image → pipeline → normalize → `jiwer.wer/cer(gt, hyp)`, hybrid vs Tesseract.
Also use it to confirm fp16 (#15) and det=960 (#8) are quality-neutral in absolute terms.

## Measurement-only scaffolding (remove before final commit)

`DEDOC_STUB_OCR` (skip OCR), `DEDOC_STAGE_TIMING`, `DEDOC_GPU_TRACE`, executor `_TRACE`/`_record_stage`,
`DEDOC_TABLE_GATE_LAYOUT`, dead `_ocr_gpu_batch`/`recognize_boxes_batch` (batch rec did not help).

## Consolidation (2026-07): cleanup, config flags, and TWO critical recognizer-speed bugs

Cleaned the measurement scaffolding and promoted the tuned knobs to config. Then the first honest full-pipeline run
with the eslav recognizer exposed a **5x speed regression** (778 s vs the ~161 s EasyOCR baseline) — correct output
(tables=6, warns=0) but far too slow. Root-caused to two independent bugs, both in the recognition path:

- **Bug 1 — `cudnn_conv_algo_search=EXHAUSTIVE`.** RapidOCR's `OrtInferSession` hardcodes EXHAUSTIVE cuDNN conv-algo
  search. onnxruntime then re-benchmarks conv algorithms for *every unique input width*. The detector is fine (fixed
  960 px input = one shape), but recognizer crops have variable widths, so it re-tuned per batch → ~9 s/page. Fix:
  after building the `TextRecognizer`, rebuild its CUDA session with `cudnn_conv_algo_search=HEURISTIC`
  (`_ensure_ppocr_rec`). 9.1 s → 2.1 s/page.
- **Bug 2 — `cv2.warpPerspective` on the full page.** `_rotate_crop` warped the *entire* page per detection box.
  warpPerspective's cost scales with the SOURCE size, not the (small) output, so 85 boxes × full page = ~1.8 s/page
  of pure cropping (the rec itself was only ~210 ms). Fix: slice the box's axis-aligned bounding region (+2 px margin
  for INTER_CUBIC edge sampling) and warp only that — identical output, ~1 ms/box. 1.8 s → 0.08 s/page.
  This was the dominant cost and had silently inflated every eslav "recognition" measurement (the earlier 203 ms
  microbench used pre-built crops, so it never showed).

Net: `recognize_detections` 2.2 s → **0.28 s/page** on DAE. Lesson: the eslav rec was never intrinsically slow — the
microbench that "proved ≈EasyOCR speed" measured the rec in isolation and missed the per-page cropping + onnxruntime
per-shape re-tuning that only appear in the full detect→crop→recognize loop. Always measure the whole stage on real
pages, not the model call on cached inputs.

**Config flags (env → `config`):** `DEDOC_DET_MAX_SIDE` → `hybrid_det_max_side` (default 960);
`DEDOC_HOMOGLYPH` → `hybrid_homoglyph_fix` (default True, Russian-gated); `DEDOC_TABLE_HOUGH_SCALE` →
`table_hough_scale` (default 0.5). Removed scaffolding: `DEDOC_STUB_OCR`, `DEDOC_STAGE_TIMING`, `DEDOC_GPU_TRACE`,
executor `_TRACE`/`_record_stage`/`_dump_stage_stats`, `DEDOC_TABLE_GATE_LAYOUT`, dead `_ocr_gpu_batch`,
`recognize_boxes_batch`/`infer_batch`/`_ensure_rec` (EasyOCR recognizer), and the XY-cut block-ordering code.

## Layout table-gate re-evaluated (2026-07) — still a net loss, reframes the bottleneck

After OCR was sped up (eslav + crop fix), the pipeline looked "CPU-bound" (CPU 61 %, GPU 26 %), so the layout gate
(run docling RT-DETR on all pages, skip the OpenCV table detector where class 8 is absent) looked cheap again. Wired
it (`build_specs(table_gate_layout=...)`, `table` blocks on `layout`, `_table` skips on `layout_has_table is False`)
and measured the full 297-page doc: **235 s vs 195 s baseline — +40 s, tables=6 preserved.** Reverted to default OFF.

Why it lost, and the correction it forces: **the single GPU worker is the throughput bottleneck, not the CPU.** GPU
*device* utilization (26 %) is low because the worker stalls on CPU hand-offs between its stages — but its serial
*queue* (orient ~120 ms + ocr_gpu ~330 ms per page) is what gates the chain. Adding layout (~159 ms/page) to that
queue = +47 s of GPU-worker work, which is the real critical path; the CPU table savings don't help because the CPU
already has headroom (61 %). "GPU idle → layout is free" was wrong: idle *device* ≠ idle *worker*.

**Consequence for future work:** wall time is bounded by the GPU worker's serial per-page cost (orient + ocr_gpu),
not by CPU stages. Table/deskew/render gating (CPU) can't move the wall while the GPU worker is the bottleneck. The
productive levers are the ones that *reduce GPU-worker work*: gate/skip orientation on likely-upright pages, cut
recognition cost, or overlap orient/ocr_gpu better — not CPU-side gating. The `table_gate_layout` flag is kept
(default off) since a CPU-only engine, where the GPU worker only runs orient, could still benefit.

## Orient preprocessing disaggregated to CPU (2026-07) — WIN, −45 s

After the layout-gate loss reframed the bottleneck as the single GPU worker's serial queue, profiled the orient stage
itself: the EfficientNet-B0 *forward* is cheap (~19 ms/page batched at 1200x1200; 3.6 ms at 512), but the PIL
preprocessing (`my_resize` resize+white-pad + ToTensor + Normalize of the full ~2300 px page) costs **91 ms/page** and
ran ON the GPU worker. So orient's ~120 ms was ~85 % CPU-side resize, not model compute — and it sat on the bottleneck.

Fix (mirrors det_pre): new CPU stage `orient_pre` does the resize/pad in **cv2** (`preprocess_cpu`, 91→35 ms, uint8
canvas, INTER_AREA) on the parallel CPU workers; the GPU stage (`predict_prepared`) does only normalize (to [-1,1] on
GPU) + the forward. cv2-vs-PIL predictions agree **20/20** on raw pages (prediction-preserving).

- **194.6 s → 149.0 / 149.4 s (two clean runs) = −45 s / −23 %.** CPU 61→70 % (absorbs the resize), GPU worker
  unburdened, RSS unchanged (~11 GB). tables=6.
- **First run was contaminated** (266 s, GPU 45 %, RSS 13.4 GB = a foreign GPU job) — re-ran clean twice to confirm.
  The contamination nearly caused a wrong "revert" conclusion; always re-run a surprising result on a verified-idle GPU.
- **Pipeline output is non-deterministic run-to-run** (text_len 818521 vs 818554 across two runs of identical code;
  nodes ±7; ~0.004 %). Pre-existing (not from this change — one run matched the PIL baseline's 818555); likely
  parallel OCR/table tie-break ordering or float non-associativity in GPU batches. Small, but noted.
- Contrast with the layout gate: adding a GPU-worker stage lost 40 s; removing GPU-worker work (this) won 45 s.
  Consistent single rule: **wall time tracks the GPU worker's serial per-page cost — cut it, don't add to it.**
- Open orient levers (not done): 512 input + retrain (forward already cheap, modest); non-square input skip-the-pad
  (~30 % fewer forward pixels, needs retrain/validation); reuse an upstream downscaled copy (couples stages).
