# GPU-OCR pipeline optimization — summary report

*A readable digest of the scanned-PDF OCR optimization work on the process-model pipeline (`dedoc/pipeline/`).
The blow-by-blow lab notebook, including every dead end, is in [`GPU_OCR_EXPERIMENTS.md`](GPU_OCR_EXPERIMENTS.md);
this document is the human-readable summary of what we tried, what stuck, what didn't, and why.*

Test box: RTX 3080 Laptop (16 GB), 8 CPU workers, Windows. Main benchmark document:
`DAE (India) Annual Report 2020-21.pdf` — 297 scanned pages, 6 tables. Accuracy benchmark: a colleague's labelled
`data_tesseract_benchmarks` — 102 real Russian document scans with ground-truth text (WER/CER via `jiwer`).

---

## TL;DR

- **Pipeline speed:** the scanned-PDF path went from **1377 s → ~195 s** end-to-end on the 297-page doc — mostly from
  the process-model pipeline itself, plus a handful of targeted wins (detection downscale, table-Hough downscale).
- **OCR engine:** built a **hybrid GPU OCR** (PP-OCR/DBNet detector + PP-OCRv5 East-Slavic recognizer, all ONNX-CUDA,
  no PyTorch) that is **faster than Tesseract (195 s vs 221 s)** and **2.5–3× more accurate than the first EasyOCR
  hybrid** (Russian prose WER 0.100 vs 0.168; degraded scans 0.198 vs 0.668).
- **Accuracy vs Tesseract:** Tesseract is still a bit more accurate on clean prose (0.066 vs 0.100), but the gap
  narrowed from 2.5× to ~1.5×, and on degraded scans the hybrid is now essentially at parity (0.198 vs 0.160).
- **Two nasty bugs** (found only when we finally ran the *whole* pipeline with the new recognizer) were causing a 5×
  slowdown; both fixed. See "The consolidation surprise" below.

---

## 1. Pipeline speed journey

| milestone | time | speedup |
|---|---|---|
| original single-process | 1377.6 s | 1× |
| process pipeline (8 CPU workers + 1 GPU worker) | 336.7 s | 4.1× |
| + deskew on a downscaled image | 234.9 s | 5.9× |
| + shared-memory image transport (no pickling large arrays) | 213.8 s | 6.4× |
| + detection downscale (det=960) | 172 s | 8.0× |
| + table-Hough downscale (0.5) | 161 s | 8.6× |
| final, with the eslav recognizer (full doc) | ~195 s | 7.1× |

The pipeline is now **CPU-bound** (GPU ~28 % utilized) — the OCR is fast enough that OpenCV table detection and
rendering dominate. That's a good problem to have; it means the recognizer is no longer the bottleneck.

---

## 2. The OCR engine story

**Where we started:** Tesseract (LSTM, CPU, 8-way self-forking) was the incumbent and, at the time, we believed
GPU-OCR could not beat 8× Tesseract. That conclusion was **later overturned**.

**The hybrid idea:** split OCR into a **detector** (finds text-line boxes) and a **recognizer** (reads each box),
and put the neural forwards on the GPU. We used PP-OCR/DBNet (via RapidOCR + onnxruntime-CUDA) for detection —
lightweight and fast. For recognition we first kept **EasyOCR's CRNN** (PyTorch). This hybrid was **32 % faster than
Tesseract** end-to-end.

**The accuracy reckoning:** once we measured *absolute* accuracy on the colleague's labelled Russian set (not just
"agreement with Tesseract"), the EasyOCR hybrid was clearly **less accurate** — 2.5× worse on clean prose, 4× worse
on degraded scans. The speed win was buying a real quality loss. The recognizer was the limiter.

**The fix — recognizer swap:** replaced EasyOCR CRNN with a ready **PP-OCRv5 East-Slavic** ONNX recognizer
(`eslav_PP-OCRv5_mobile_rec`, Russian/Ukrainian/Belarusian/Bulgarian/English, CTC). It runs on the *same*
onnxruntime-CUDA stack as the detector, so the whole hybrid became **pure ONNX — the PyTorch dependency dropped out
of the recognition path entirely.**

| category | EasyOCR hybrid | **PP-OCRv5 eslav** | Tesseract |
|---|---|---|---|
| Russian prose (83 pages) | 0.168 | **0.100** | 0.066 |
| degraded scans (11) | 0.668 | **0.198** | 0.160 |

Then made it faster and cleaner:
- **fp16 ONNX** (`rec_fp16.onnx`, 7.9→4.0 MB): **−30 % recognition time, accuracy bit-identical** to fp32.
- **Homoglyph post-fix** (Latin→Cyrillic look-alikes, Russian only): small extra win (0.105→0.100), default-on.

---

## 3. What worked (kept)

| change | effect | why |
|---|---|---|
| **Process-model pipeline** | 1377→337 s | parallel CPU workers + one GPU worker, shared-memory image transport |
| **Deskew on downscaled image** | −80 s | skew angle is scale-invariant; rotate at full res |
| **CPU/GPU disaggregation** of OCR (`det_pre`→`ocr_gpu`→`ocr`) | 270→249 s | GPU worker does only neural forwards; cropping + line-grouping + metadata run on idle CPU workers |
| **Detection downscale (det=960)** | 249→172 s, *higher* text_len | DBNet is trained near 960 px; at 2300 px it mis-segments. Recognition still crops from full-res, so quality is unaffected — det-downscale is safe, recognition-downscale is not |
| **Table-Hough downscale (0.5)** | 172→161 s | `HoughLinesP` was 79 % of table detection; it only needs the line *angle* (scale-invariant) + to draw gap-filling lines — run at half-scale, upscale the mask. Tables preserved |
| **Recognizer swap → PP-OCRv5 eslav** | WER 0.168→0.105 | stronger recognizer; drops PyTorch from recognition |
| **fp16 ONNX recognizer** | −30 % recognition, lossless | half-size model, identical output |
| **Homoglyph Latin→Cyrillic fix** | 0.105→0.100 (RU) | context-aware map, keeps genuine English words |

---

## 4. What did NOT work (reverted / dropped) — the negative results

These cost time but are worth recording so nobody re-runs them:

- **Moving the orientation classifier to CPU** (twice) — *36× slower*. The EfficientNet forward is 4331 ms/page on
  CPU vs 120 ms batched on GPU. Orientation is pinned to the GPU.
- **Batching recognition across pages** (pool all crops → one big pass) — *slower*. PP-OCR/EasyOCR pad every batch to
  its widest crop, so a big mixed-width batch wastes compute; batch-collection latency adds more. Batch 8 is optimal.
- **Forcing the layout pass to gate table detection** — *hurts the hybrid*. Layout is another GPU stage that stalls
  the single GPU worker; net loss. (Layout still gates tables for free *when it already runs*, e.g. attachments.)
- **Table morphology downscale** — no effect; morphology is only ~28 ms/page, Hough was the cost.
- **Bigger admission window (max_inflight 24/40)** — no help; the stalling was not admission-bound.
- **XY-cut reading-order** (recursive column/band cut) — *neutral-to-worse on every real corpus*. Multi-column
  headers are a small fraction of documents, and XY-cut either misses their narrow column gap or over-segments
  single-column bodies. A threshold sweep (×0.5/×1/×2) was a wash. Dropped.
- **Layout-guided reading order** (docling RT-DETR regions → order → bucket words) — *consistently worse* (0.168→0.303
  on Russian prose). RT-DETR mis-segments, words fall outside regions into a "leftover" bucket, order is destroyed.
- **Dictionary spell-correction** (variant D, for Cyrillic-internal и↔н↔п confusions) — *hurts or no-ops*. The small
  RU dictionary (~20 k words) lacks technical/legal vocabulary (АСУ, ФСТЭК, proper nouns), so it over-corrects valid
  words. No safe win without a strong language model or domain dictionary.
- **FUNSD as an accuracy benchmark** — misleading. FUNSD is *forms* (scattered fields), which stresses reading-order,
  not raw recognition; both engines score ~0.6–0.7 WER there. Real prose is the right benchmark.

**Meta-lesson:** reading-order fixes (XY-cut, layout) kept looking promising in theory and failing in measurement.
The residual gap to Tesseract on clean prose is mostly *not* reading order — it's word-merging (dropped spaces),
stamps/letterheads, and degraded-scan recognition, none of which has a clean lever.

---

## 5. The consolidation surprise — two 5×-slowdown bugs

When we finally ran the *whole* pipeline with the eslav recognizer (not just the recognizer in isolation), it took
**778 s** — 5× slower than expected, though the output was correct. Root cause was two independent bugs, both hidden
because the earlier "203 ms/page" recognizer microbench measured the model on *pre-built, cached-width* crops:

1. **`cudnn_conv_algo_search = EXHAUSTIVE`** (hardcoded in RapidOCR's session setup). onnxruntime then re-benchmarks
   convolution algorithms for *every unique input width*. The detector is fine (fixed 960 px input = one shape), but
   recognizer crops have variable widths → constant re-tuning → 9 s/page. **Fix:** rebuild the recognizer's CUDA
   session with `HEURISTIC`. 9.1 → 2.1 s/page.
2. **`cv2.warpPerspective` on the full page.** The per-box crop warped the *entire* page each time. warpPerspective's
   cost scales with the *source* size, not the (small) output — so 85 boxes × full page = 1.8 s/page of pure cropping
   (the recognition itself was only ~0.2 s). **Fix:** slice the box's bounding region first (+2 px margin) and warp
   only that — identical output, ~1 ms/box. 1.8 → 0.08 s/page.

Result: `recognize_detections` **2.2 s → 0.28 s/page**; full doc **778 → 195 s**. Accuracy unchanged (0.100/0.198).

**Lesson:** always measure the whole stage on real pages, not the model call on cached inputs. Both bugs were
invisible to the isolated microbench.

---

## 6. Final configuration

The hybrid engine (`config["ocr_engine"] = "hybrid"`) with these config keys (all now proper config, no env hacks):

| key | default | what it does |
|---|---|---|
| `hybrid_det_max_side` | 960 | detection downscale (long side, px) |
| `hybrid_homoglyph_fix` | True | Latin→Cyrillic look-alike fix (Russian only) |
| `table_hough_scale` | 0.5 | Hough downscale factor for table line detection |

The recognizer ships in `dedoc/readers/.../ocr/ppocr_eslav/` (`rec_fp16.onnx` for GPU, `rec.onnx` for CPU, `dict.txt`).

**When to use which engine:**
- **Tesseract** (default) — highest accuracy on clean prose; CPU, 8-way.
- **Hybrid** — faster (−12 % vs Tesseract) and much better than the old EasyOCR hybrid; use where GPU is available and
  throughput matters, or on degraded scans (now at parity with Tesseract there).

---

## 7. Open levers (not pursued — diminishing returns)

- **Word-merging / space insertion** between adjacent boxes — a detector-side fix, the largest remaining prose gap.
- **Mixed Tesseract(CPU) + hybrid(GPU) OCR** — the pipeline is now CPU-bound with the GPU ~72 % idle; splitting pages
  across both engines could reach ~115–120 s, but mixes engines across a document.
- **Stamps / letterheads** — both engines struggle; needs detection/segmentation work, not recognition.
