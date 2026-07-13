# Presentation brief v2 — speeding up dedoc's scanned-PDF pipeline

> Self-contained hand-off for building a presentation/report. All facts, numbers and context are below; no external
> context is required. This is **version 2**: v1 covered *Phase 1* (the parallel staged-pipeline architecture, ×4.1,
> byte-identical). This version adds *Phase 2* (GPU OCR + TensorRT + more parallelism + render + memory leaning), which
> takes the same 297-page document to **~82 s (×16.8 vs the original)**.
> Source data: `dedoc/pipeline/BENCHMARKS.md`, `TENSORRT_INT8.md`, `COMPONENT_QUALITY_REPORT.md`; design in `ARCHITECTURE.md`.

---

## 0. Headline (one slide)

We re-architected **dedoc's scanned-PDF / image OCR pipeline** into a parallel, GPU-accelerated, memory-bounded staged
pipeline, then moved the OCR itself onto the GPU. On a real **297-page annual report (59 MB, image-heavy)**:

| configuration | time | vs original | output |
|---|---|---|---|
| original dedoc (master, default) | **1377.6 s (~23 min)** | — | reference |
| **Phase 1** — parallel staged pipeline (Tesseract OCR) | **213.8 s (~3.6 min)** | **×6.4** | **byte-identical** |
| **Phase 2** — + GPU OCR + TensorRT + 2 GPU workers | **~82 s (~1.4 min)** | **×16.8** | quality-validated (F1 ≥ Tesseract) |

Two honest headlines to choose from:
- **"×6.4, output byte-identical"** — the safe, default-path story (Phase 1).
- **"×16.8 by moving OCR onto the GPU"** — the aggressive, opt-in story (Phase 2), where a *different* (measured
  equal-or-better) recognizer replaces Tesseract.

Peak RAM stays bounded (**6–8 GB**) on a 297-page document; CPU workers run at ~0.2 GB each.

---

## 1. Background / context (for the audience)

**dedoc** is an open-source system (ISP RAS) that converts documents of many formats into one structured representation
(text lines, tables, metadata, heading tree). Its hardest path is **scanned PDFs / images with no text layer**, handled
by `PdfImageReader`: each page becomes a bitmap processed by OCR + ML models.

**The per-page pipeline (what happens to each scanned page):**
1. **render** — rasterize the PDF page to a bitmap.
2. **binarize** — optional black/white cleanup.
3. **orientation / column detection** — a neural net (EfficientNet-B0) predicts rotation (0/90/180/270°) and 1-/2-column layout.
4. **deskew** — correct fine skew / perspective, apply the rotation.
5. **layout / figure detection** — a neural net (RT-DETR) finds figures to extract as attachments.
6. **table detection & recognition** — OpenCV contour analysis + OCR for cell text.
7. **OCR** — read the page text.
Then **whole-document steps** run once over all pages: header/footer detection, multi-page table merge, linking, paragraph classification, tree building.

**How the original code did it:** the whole per-page chain was one monolithic function, optionally parallelized across
pages by `joblib` but **defaulting to serial (n_jobs=1)**. GPU was used only for orientation (optional); the layout net
always ran on CPU; **OCR and table cells were Tesseract (CPU)**.

---

## 2. Goals

Make the scanned-PDF pipeline **much faster** by working on **orchestration and hardware placement**, not the ML
algorithms themselves:
- **Phase 1:** order the stages correctly, run pages in parallel (beat the GIL), offload the neural nets to a batched
  GPU worker, bound memory — *keeping output identical*.
- **Phase 2:** move the remaining CPU hot-spots — **OCR recognition** and **table cell OCR** — onto the GPU, accelerate
  them with TensorRT, parallelize the GPU worker, replace the renderer, and trim per-worker RAM — *keeping recognition
  quality equal-or-better*.

---

## 3. Diagnosis — where the time went (and moved)

Per-stage cost measured on the OCR path (Phase-1 profile, per page):

| stage | share | resource |
|---|---|---|
| **deskew** (skew/perspective) | **42%** | CPU |
| **OCR** (Tesseract) | **31%** | CPU |
| render | 8% | CPU (subprocess) |
| table detection + cell OCR | 7% | CPU |
| orientation NN | 6% | GPU-capable |
| layout NN | 5% | GPU-capable |

- **Insight #1:** the two dominant costs were both **CPU-bound (deskew + OCR = 73%)**; the neural nets were cheap. So
  Phase 1 = parallelize CPU work + move the NNs off the CPU.
- **Insight #2 (why the original didn't scale):** Tesseract is internally multi-threaded (OpenMP); N parallel OCR calls
  oversubscribe the cores (4 workers gave only ~1.68×). Cap Tesseract to 1 thread (`OMP_THREAD_LIMIT=1`) + parallelize
  across pages.
- **Insight #3 (what Phase 1 exposed):** once pages ran in parallel and the NNs were on the GPU, the pipeline was
  **still CPU-bound — on OCR and deskew**. Phase 2's target: move OCR itself to the GPU and cut deskew.

---

## 4. Phase 1 recap — the parallel staged architecture (byte-identical, ×6.4)

A **config-driven staged pipeline**: each stage declares `resource (CPU/GPU)`, `exec_mode (thread/process)`,
`batch_size`, and `blockers` (dependency edges). Core mechanisms:
- **Process-model scheduler** — builds a dependency graph from the blockers, runs pages in parallel, frees intermediate
  data as soon as it's consumed.
- **Persistent process workers** (beat the GIL; load models once, not per task).
- **Batched GPU worker** — GPU stages (orientation, layout) run in one dedicated process that batches pages into one
  forward pass; only this worker touches CUDA.
- **Shared-memory image transport** — page bitmaps (~12 MB) passed via shared memory, not pickled.
- **Lazy render + windowed admission** — pages rasterized on demand; a bounded number in flight → peak memory depends on
  worker count, not document size.
- **Graceful failures** — a failed page becomes a warning; the document still parses.

**Phase-1 wins (each measured):** processes >2× threads on GIL-bound work · `OMP_THREAD_LIMIT=1` unlocked OCR scaling ·
orientation NN on batched GPU (proc 1→8 went flat→×1.93) · layout NN forced onto GPU + batched (**119.8 s → 27.9 s, ~4×**) ·
persistent executor (cold→warm 15.3 s→7.9 s) · **deskew coarse-to-fine downscale (×1.43 more, matches the 91-step angle
on 55/56 pages)** · **OOM fix — free page images in place (peak 18.7 GB → 8.1 GB, OOM → completes)**.

Net Phase 1 on the 297-page doc: **1377.6 s → 213.8 s = ×6.4**, output **byte-identical** to master
(`text_sha` matched on matched hardware; nodes/tables/text-length identical on the full doc).

---

## 5. Phase 2 — moving OCR onto the GPU (the new work)

After Phase 1 the pipeline was CPU-bound on OCR. Phase 2 replaces the Tesseract OCR with a **GPU "hybrid" recognizer**
and pushes the GPU harder. Each item below is an independent, measured win.

1. **Hybrid GPU OCR engine (opt-in `ocr_engine="hybrid"`).** Replaces Tesseract with a **DBNet text detector
   (onnxruntime-CUDA) + PP-OCRv5 East-Slavic CRNN recognizer**. The detection preprocessing and line-metadata run on the
   CPU workers; only the neural forwards run on the GPU worker (`det_pre → ocr_gpu → ocr`). This took the full doc from
   **213.8 s (Tesseract) → 147 s**.

2. **TensorRT FP16 recognizer (`hybrid_rec_engine="trt_fp16"`).** Runs the CRNN on the standalone TensorRT runtime
   instead of the onnxruntime CUDA EP — **2× faster recognizer (210 → 105 ms/page)**, **−17 % full-pipeline wall
   (147 → 123 s)**, and **lossless** (bit-identical output to CUDA FP16). INT8 also works (2.3×) but costs ~1 % word-bag
   F1, so **FP16 is the recommended sweet spot**. (The onnxruntime TRT EP couldn't build this PaddlePaddle model; the raw
   TensorRT `Builder`/`OnnxParser` build it fine — see `TENSORRT_INT8.md`.)

3. **Two GPU workers (`gpu_workers=2`).** With the recognizer on TensorRT the GPU sat at ~20 % utilization and the wall
   was CPU-bound again; running two GPU-worker processes parallelizes the in-worker CPU work (box post-processing, crop
   extraction) and closes the gap: **~123 s → ~82–89 s**.

4. **pypdfium2 renderer + erode (replaces Poppler).** Rendering pages with PDFium (in-process, no subprocess) is
   **18 % faster** and **quality-neutral** — a 2×2 erode restores PDFium's slightly thinner glyph anti-aliasing to
   Poppler weight (verified to recover the −3.8 % short-text F1 exactly). PDFium isn't thread-safe → runs in the isolated
   worker processes with a per-worker document cache.

5. **GPU table-cell OCR (this session).** The OpenCV table detector OCR'd its cells with Tesseract (~530 ms/table-page,
   the dominant table cost). Feeding the stacked cell images through the hybrid recognizer instead is **2.2× faster
   (530 → 245 ms) and higher quality (word-bag F1 0.83 vs 0.74)**. Wired to piggyback the existing `ocr_gpu` stage so
   **table-free pages take no extra CPU↔GPU round-trip**: the table stage detects + masks cells on the CPU, the GPU
   worker OCRs the stacks, the metadata stage assembles the tables.

6. **Cheap table gate.** A ~7 ms/page line-crossing heuristic (reusing the detector's own line parameters) skips the
   ~360 ms OpenCV table detector on pages with no bordered table — **100 % table recall on 503 diverse tables**, skipping
   ~54 % of table-free pages (**−8 % wall**).

7. **Lean workers via lazy imports (this session).** The per-page workers were each importing heavy libraries they never
   use. Deferred: **Tesseract's `pytesseract` (pulls pandas+PIL)**, the **post-read components** (paragraph classifier,
   linker, header/footer, notes, GOST — pandas+sklearn), and the **bold classifier's sklearn/scipy** off the workers that
   don't call them. Result: **CPU workers ~0.2 GB RSS** (no pandas/torch/onnxruntime resident), **GPU worker 785 → 729 MB
   RSS** — output byte-identical (deferred code is unchanged, just imported on first real use).

**Cumulative Phase 2 on the 297-page doc: 213.8 s → ~82 s. Combined with Phase 1: 1377.6 s → 82 s = ×16.8.**

---

## 6. Benchmark results (tables to visualize)

Environment (footnote): NVIDIA RTX 3080 Laptop (16 GB VRAM), 16 logical cores, 34 GB RAM, Windows; `torch 2.2.2+cu121`,
`onnxruntime-gpu 1.18.1`, TensorRT 10.0; new-pipeline runs use `OMP_THREAD_LIMIT=1`. Absolute wall varies ±~10 %
run-to-run (GPU thermal/clock); relative gains are the stable figures.

### 6a. HEADLINE — full document (DAE India Annual Report, 297 pages, 59 MB)
| version | time | vs original | notes |
|---|---|---|---|
| original master (njobs=1) | 1377.6 s (~23 min) | — | 5626 nodes, 6 tables |
| Phase 1: staged pipeline, GPU NNs, Tesseract | 336.7 s → **213.8 s** | ×4.1 → **×6.4** | byte-identical; +deskew downscale +shared-mem |
| Phase 2: + hybrid GPU OCR (onnx) | 147 s | ×9.4 | recognizer swap |
| Phase 2: + TensorRT FP16 rec | 123 s | ×11.2 | lossless vs onnx |
| Phase 2: + 2 GPU workers (+ pdfium + gates) | **~82 s** | **×16.8** | current fastest config |

Best chart: a descending bar/waterfall — 1377 → 214 → 147 → 123 → 82 s.

### 6b. TensorRT recognizer (DAE 297p)
| recognizer | rec ms/page | full wall | quality (word-bag F1 long / short) |
|---|---|---|---|
| onnx CUDA FP16 | 210 | 147 s | 0.943 / 0.921 (baseline) |
| **TRT FP16** | ~105 (2.0×) | **123 s (−17 %)** | **lossless (= CUDA)** |
| TRT INT8 (entropy calib) | ~93 (2.3×) | 122 s | 0.935 / 0.907 (−0.8 / −1.4 %) |

### 6c. GPU table-cell OCR (real stacked cells)
| cell OCR | speed | word-bag F1 vs GT |
|---|---|---|
| Tesseract (`--psm 6`) | 530 ms/table-page | 0.738 |
| **hybrid recognizer** | **245 ms (2.2×)** | **0.827** |

### 6d. Recognition quality — hybrid (eslav) vs Tesseract (`gen_texts`, clean GT)
| set | Tesseract F1 | eslav F1 | note |
|---|---|---|---|
| long_text (EN) | 0.955 | 0.944–0.960 | **eslav ≥ Tesseract** |
| short_text (EN) | 0.936 | 0.913–0.966 | parity-to-better |
| RU prose (WER) | 0.066 | **0.100** | eslav 2.5–3× better than old EasyOCR (0.168); Tesseract still slightly ahead on clean RU prose |

Message: **the recognizer swap is not a recognition regression** — word-bag F1 is equal-or-better. The hybrid's real gap
is **reading order** (naive top-to-bottom mis-orders multi-block pages: WER 0.55 vs 0.06 *despite equal F1*), addressed
by an optional "borrow Tesseract's layout order" mode.

### 6e. Phase-1 scaling & layout (Catalana 24p, warm) — still valid
- proc 1→8: CPU flat (NN serializes) vs **GPU ×1.93**.
- layout NN: CPU 119.8 s → GPU 34.3 s → GPU batched **27.9 s** (~4×).

### 6f. Memory
- Phase-1 OOM fix: **18.7 GB → 8.1 GB** (freeing page images in place; OOM → completes).
- Phase-2 full-doc peak RAM **6.1–6.5 GB RSS**; CPU workers **~0.2 GB each**, GPU worker **~729 MB static** (torch ~534 MB
  is the floor — the TRT rec's CUDA buffers + orientation model both need it).
- VMS (commit charge) ~28 GB is **mostly reserved address space** (CUDA/torch/onnxruntime arenas + torch VRAM cache
  reserved 604 MB but only 25 MB used) — **not physical RAM**.

---

## 7. Correctness (the "faster AND correct" slide — now two-tier)

- **Phase 1 (default, Tesseract path): byte-identical.** A SHA-256 of the extracted text matches the original on matched
  hardware; on the full 297-page doc node/table/text-length counts are identical (the only byte divergence is GPU-vs-CPU
  floating-point rounding in the orientation NN reordering one borderline page — same length, not a bug).
- **Phase 2 (opt-in, hybrid GPU OCR): quality-validated, not byte-identical.** It is a *different recognizer*, so bytes
  differ by design. Measured: **recognition word-bag F1 ≥ Tesseract on English, a large win on Russian** (vs the old
  EasyOCR); **table cell OCR strictly better (F1 0.83 vs 0.74)**; TensorRT FP16 is lossless vs the CUDA recognizer.
  Full-pipeline structure is stable (tables=6, identical text length across cell-OCR variants).
- **Known tradeoff (state honestly):** the hybrid's naive reading order is worse than Tesseract's layout analysis on
  multi-block/multi-column pages (the #1 remaining quality lever); an optional Tesseract-reading-order mode recovers it.

Framing: *"The default path is byte-identical and ×6.4. The GPU-OCR path is ×16.8 with recognition quality measured
equal-or-better — the one caveat is reading order on complex layouts, which we can restore on demand."*

---

## 8. Key takeaways (the story)

1. **The bottleneck wasn't where you'd guess** — after profiling, the heaviest stages were CPU-bound **deskew + OCR
   (73%)**, not the neural nets.
2. **Phase 1: GPU's value was freeing the CPU, not maxing the GPU** — moving the NNs to a batched GPU worker removed a
   serial bottleneck so the CPU cores scaled on OCR.
3. **Phase 2: then move OCR itself to the GPU** — a DBNet+CRNN recognizer + TensorRT turned the last CPU hot-spot into a
   cheap GPU forward, and the same trick sped up table cells (2.2×, higher quality).
4. **Parallelism needs the right primitives** — processes (not threads), single-threaded Tesseract, batched GPU worker(s),
   shared memory, and lazy imports so workers stay lean (~0.2 GB).
5. **Large documents demand memory discipline** — lazy rendering + freeing consumed images kept an OOM run bounded at 6–8 GB.
6. **Net result: ×6.4 byte-identical (default), or ×16.8 with GPU OCR (recognition quality equal-or-better).**

---

## 9. Remaining / future work (closing slide)

- **Reading order** — the #1 quality lever for the hybrid engine; make the Tesseract-layout-order mode (or a lightweight
  geometric reorder) the default so complex layouts match Tesseract.
- **Deskew** — still a large CPU stage even after the coarse-to-fine fix; candidate for further optimization / GPU.
- **Cancellation** — kill the worker process-group cleanly on client disconnect (no orphaned OCR/Java subprocesses).
- **Per-machine TensorRT engines** — the `.trt` engines are GPU/driver-specific and must be rebuilt per deployment
  (one-time ~5 min); document/automate this.
- **INT8 where the recognizer dominates** — worth it on recognizer-heavy documents (2.3× rec) at ~1 % F1 cost.

---

## 10. Suggested slide outline (for the presentation agent)

1. **Title** — "Making dedoc's scanned-PDF pipeline up to ~17× faster."
2. **Headline** — the two-tier number: ×6.4 byte-identical / ×16.8 GPU-OCR; waterfall bar 1377 → 214 → 82 s.
3. **What dedoc's scanned-PDF path does** — per-page stage diagram (section 1).
4. **The problem** — original largely serial; parallelism didn't scale (Tesseract OMP oversubscription).
5. **Where the time goes** — per-stage breakdown (section 3) + the three insights.
6. **Phase 1 architecture** — one diagram: pages → [render → NN(GPU) → deskew → layout(GPU) → table → OCR] across process
   workers + a batched GPU worker; whole-doc steps after. Note "byte-identical, ×6.4."
7. **Phase 1 fix highlights** — GPU NN offload + scaling chart (6e), layout CPU→GPU, OOM fix (6f). 1–2 slides.
8. **Phase 2 — move OCR to the GPU** — the hybrid recognizer diagram (`det_pre → ocr_gpu → ocr`), waterfall 214 → 147 →
   123 → 82 (section 6a).
9. **TensorRT** — 6b table (2× rec, −17 % wall, lossless FP16).
10. **GPU table-cell OCR** — 6c (2.2× + higher F1), the piggyback design (no extra hop for table-free pages).
11. **Lean workers** — lazy imports; CPU 0.2 GB, GPU 729 MB; VMS-vs-RSS (reserved commit, not physical RAM).
12. **Correctness** — the two-tier slide (section 7): byte-identical default vs quality-validated GPU OCR + the reading-order caveat.
13. **Recognition quality evidence** — 6d table (eslav F1 ≥ Tesseract EN, big RU win).
14. **Takeaways + next steps** — sections 8 & 9.

**Chart suggestions:** (2)/(8) descending waterfall of wall-time; (5) pie or 100 % stacked bar for per-stage share;
(6e) grouped bar for scaling; (9)/(10)/(6c) before/after bars; keep a consistent 2-color scheme (Tesseract/original vs
GPU/new).

---

## Appendix — caveats to state honestly
- Benchmarks are from one laptop (RTX 3080 Laptop, 16 cores, 34 GB RAM); absolute times vary; wall is ±~10 % run-to-run.
- The fastest config uses `OMP_THREAD_LIMIT=1` and the **opt-in** hybrid GPU OCR (`ocr_engine="hybrid"`,
  `hybrid_rec_engine="trt_fp16"`, `gpu_workers=2`). The default path remains Tesseract (byte-identical, ×6.4).
- "×16.8" is the fastest config vs the original default. Phase 2 changes the OCR engine — quality is measured
  equal-or-better on recognition (word-bag F1), with a known reading-order tradeoff on complex layouts.
- TensorRT engines are GPU/driver-specific (rebuild per machine, one-time).
- The scanned-image OCR path is the target; text-layer PDFs use a different (fast) reader and are out of scope.
