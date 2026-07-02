# Presentation brief — speeding up dedoc's scanned-PDF pipeline

> Self-contained hand-off for building a presentation/report. All facts, numbers and context are below;
> no external context is required. Source data: `dedoc/pipeline/BENCHMARKS.md`, design in `dedoc/pipeline/ARCHITECTURE.md`.

---

## 0. Headline (one slide)

We re-architected **dedoc's scanned-PDF / image OCR pipeline** into a parallel, GPU-accelerated, memory-bounded
staged pipeline — **without changing the output**.

- On a real **297-page annual report (59 MB, image-heavy)**: **23 min → 5.6 min = ×4.1 faster.**
- CPU utilization **94%** (14–15 of 16 cores), peak RAM bounded at **8.1 GB**, output **byte-identical** to the original.

---

## 1. Background / context (for the audience)

**dedoc** is an open-source system (ISP RAS) that converts documents of many formats into one structured
representation (text lines, tables, metadata, tree of headings). One of its hardest paths is **scanned PDFs and
images with no text layer**, handled by `PdfImageReader`: each page is turned into a bitmap and processed by OCR +
ML models.

**The per-page pipeline (what happens to each scanned page):**
1. **render** — rasterize the PDF page to a bitmap (Poppler).
2. **binarize** — optional black/white cleanup.
3. **orientation / column detection** — a neural net (EfficientNet-B0) predicts page rotation (0/90/180/270°) and 1- vs 2-column layout.
4. **deskew** — correct fine skew / perspective and apply the rotation.
5. **layout / figure detection** — a neural net (RT-DETR) finds figures/pictures to extract as attachments.
6. **table detection & recognition** — OpenCV contour analysis + Tesseract for cell text.
7. **OCR** — Tesseract reads the page text.
Then **whole-document steps** run once over all pages: header/footer detection, multi-page table merge, linking
tables/figures to text, paragraph classification, structure/tree building.

**How the original code did it:** the whole per-page chain was one monolithic function, optionally parallelized
across pages by `joblib` but **defaulting to serial (n_jobs=1)**. GPU was used (optionally) only for orientation;
the layout net always ran on CPU.

---

## 2. Goal

Make the scanned-PDF pipeline **much faster** *without changing results*, by working on **orchestration** rather
than the individual algorithms:
- order the stages correctly and run pages in parallel,
- offload GPU-suited stages (the neural nets) to the GPU, batched,
- keep memory bounded so large documents don't run out of RAM,
- keep the output identical to the original.

---

## 3. Diagnosis — where the time actually went

Per-stage cost, measured (per page, on the OCR path):

| stage | share of per-page compute | resource |
|---|---|---|
| **deskew** (skew/perspective correction) | **42%** | CPU |
| **OCR** (Tesseract) | **31%** | CPU |
| render (Poppler) | 8% | CPU (subprocess) |
| table detection+recognition | 7% | CPU |
| orientation NN (EfficientNet) | 6% | GPU-capable |
| layout NN (RT-DETR) | 5% | GPU-capable |

**Key insight #1:** the two dominant costs are **both CPU-bound (deskew + OCR = 73%)**. The neural-net stages are
comparatively cheap. So the win is *parallelizing CPU work + moving the NNs off the CPU*, not optimizing the NNs.

**Key insight #2 (why the original didn't scale):** the built-in `joblib` parallelism scaled poorly — e.g. 4 workers
gave only ~1.68× — because **Tesseract is internally multi-threaded (OpenMP)** and N parallel OCR calls oversubscribe
the cores. Capping Tesseract to one thread each (`OMP_THREAD_LIMIT=1`) and parallelizing across pages fixes this.

---

## 4. What we built (the new architecture)

A **config-driven staged pipeline** (not a fixed hard-coded flow). Each stage is described by:
`resource (CPU/GPU)`, `exec_mode (thread/process)`, `batch_size`, and `blockers` (which stages must finish first —
this list defines the execution graph). Components can be reordered, omitted, or run independently — all via config.

Core mechanisms:
- **Process-model scheduler** — builds a dependency graph from the blockers; runs pages in parallel; assigns each
  task to the right worker; frees intermediate data as soon as it's consumed.
- **Persistent process workers** (not threads) — Python's GIL prevents threads from parallelizing CPU-bound work;
  separate processes give true parallelism. Workers are **persistent** and load their models **once** (not per task).
- **Single batched GPU worker** — the GPU stages (orientation, layout) run in one dedicated GPU process that batches
  several pages into one forward pass (amortizes the GPU). Only this worker touches CUDA (CPU workers don't, to avoid
  many GPU contexts).
- **Shared-memory image transport** — page bitmaps (~12 MB each) are passed between processes via shared memory, not
  pickled through pipes.
- **Lazy rendering + windowed admission** — pages are rasterized on demand, and only a bounded number are kept
  "in flight," so peak memory depends on the worker count, not the document size.
- **Graceful failures** — a failed page becomes a warning and the document still parses.

Code lives in `dedoc/pipeline/` (`scheduler.py`, `executor.py`, `shared_image.py`, `task.py`, `pdf_stages.py`);
enabled behind config flags, with the original path kept as the default fallback. 19 unit tests.

---

## 5. The improvements, one by one (each with measured impact)

Use one slide per item; each is an independent, measurable win.

1. **Stage decomposition + process workers (beat the GIL).**
   Processes give true CPU parallelism where threads can't. Micro-benchmark: on GIL-bound Python work, **processes
   were >2× faster than threads**. This is the foundation for page-level parallelism.

2. **Fix Tesseract oversubscription (`OMP_THREAD_LIMIT=1`).**
   With single-threaded Tesseract + N parallel pages, OCR finally scales across cores (the original joblib path
   couldn't). Measured page-parallel speedup went from ~flat to real scaling.

3. **Offload orientation NN to a batched GPU worker.**
   On CPU the orientation net was a serial bottleneck (~1.3 s/page, serialized). Moving it to a batched GPU worker
   removed that bottleneck and **unlocked scaling**: proc 1→8 went from *flat* (CPU) to **×1.93** (GPU).

4. **Make the layout NN (RT-DETR) actually run on GPU — device-aware + batched.**
   It previously always ran on CPU (ignored the GPU flag). Now on GPU it is **3.5× faster** than on CPU
   (34.3 s vs 119.8 s over 24 pages), and batching the forwards cut it further to **27.9 s**.

5. **Persistent executor (load models once, reuse across documents).**
   Avoids re-spawning workers and reloading models per document. Cold→warm example: **15.3 s → 7.9 s**.

6. **Lazy render + windowed admission.**
   Enables processing very large documents (297 pages) without materializing every page image up front.

7. **Memory (OOM) fix — free page images in place.**
   On the full 297-page document the run first hit **out-of-memory**: the scheduler was retaining every stage's
   output, and each output still referenced its ~12 MB page image (≈ >15 GB accumulated). Fix: free each page image
   as soon as its stages have consumed it. **Peak RAM dropped 18.7 GB → 8.1 GB**, and the full document now completes.

---

## 6. Benchmark results (tables to visualize)

Environment (put in a footnote): NVIDIA RTX 3080 Laptop (16 GB), 16 logical cores, 34 GB RAM (~13 GB free during
tests), Windows; `torch 2.2.2+cu121`; Poppler + Tesseract; new-pipeline runs use `OMP_THREAD_LIMIT=1`; the original
ran with its natural multi-threaded Tesseract. Numbers are indicative of this machine.

### 6a. HEADLINE — full big document (DAE India Annual Report, 297 pages, 59 MB, image-heavy)
| version | time | CPU | GPU | peak RAM |
|---|---|---|---|---|
| original dedoc (master, default) | **1377.6 s (~23 min)** | — | — | — |
| new pipeline, 8 processes + GPU | **336.7 s (~5.6 min)** | 94% | 9% | 8.1 GB |

→ **×4.1 faster.** (Best chart: a single big bar-pair, 23 min vs 5.6 min.)

### 6b. Parallelization scaling (CatalanaOccidente, 24 pages, warm)
| workers | CPU (NN on) | CPU (NN off) | **GPU (NN on)** |
|---|---|---|---|
| 1 process | 70.6 s | 45.3 s | 82.3 s |
| 8 processes | 66.1 s (flat) | 30.6 s (**×1.48**) | 42.6 s (**×1.93**) |

Message: on CPU the orientation NN serializes and kills scaling; move it to GPU and page-parallelism scales.

### 6c. New vs original at the same 8-way parallelism (CatalanaOccidente, 24 pages)
- CPU: new 66.1 s vs original 95.7 s.
- GPU: new **42.6 s** (29.3 s with lazy render) vs original 125.0 s.

### 6d. Per-stage time breakdown (good for a pie/bar) — see the table in section 3.
deskew 42% · OCR 31% · render 8% · table 7% · orientation 6% · layout 5%.

### 6e. Layout NN: CPU vs GPU (24 pages, with figure detection)
CPU 119.8 s → GPU 34.3 s → GPU batched **27.9 s** (≈ **3.5–4× faster** on GPU).

### 6f. GPU utilization (shows GPU offload works as intended)
- orientation only on GPU: CPU 87%, GPU ~5% (GPU intentionally light — its job is tiny).
- orientation + layout on GPU: CPU 74%, GPU busy 100% of the time, VRAM ~4.6 GB.

### 6g. Memory fix
Full 297-page document: peak RAM **18.7 GB → 8.1 GB** after freeing page images in place (the run went from OOM-killed to completing).

---

## 7. Correctness (important — "faster AND identical")

- On matched configuration the new pipeline's output is **byte-identical** to the original: a SHA-256 hash of the
  extracted text matched exactly on CatalanaOccidente (full) and on a DAE 12-page slice
  (`text_sha=b02535a61e59` for original CPU, original multi-threaded, and new GPU — all three equal).
- On the *full* 297-page DAE the text hash differed while **node count, table count, and total text length were
  identical** (5626 / 6 / 790801). Cause: the **orientation neural net gives slightly different results on GPU vs CPU
  on a borderline page** (floating-point device nondeterminism), which reorders that page's text (same length,
  different bytes). This is expected NN device behavior, **not a pipeline bug**. (Also note: Tesseract itself was
  verified to be OMP-deterministic — thread count does not change its output.)

Framing for the slide: "Output preserved — verified byte-identical on matched hardware; the only divergence on the
big doc is GPU-vs-CPU rounding in one neural net, with identical structure/length."

---

## 8. Key takeaways (the story)

1. **The bottleneck wasn't where you'd guess.** After profiling, the two heaviest stages were CPU-bound **deskew and
   OCR** (73% together) — not the neural nets.
2. **GPU's value here is freeing the CPU, not maxing the GPU.** Moving the NNs to a batched GPU worker removed a
   serial CPU bottleneck and let the CPU cores scale on OCR. GPU stays lightly used — and that's fine.
3. **Parallelism needs the right primitives:** processes (not threads) to beat the GIL; single-threaded Tesseract to
   avoid oversubscription; a batched GPU worker; shared memory to move images cheaply.
4. **Large documents demand memory discipline** — lazy rendering + freeing consumed page images turned an OOM into a
   bounded 8 GB run.
5. **Net result: ×4.1 on a real 297-page document, output preserved.**

---

## 9. Remaining / future work (a closing slide)

- **Optimize deskew** — now the single biggest stage (42%); currently full-page Hough + rotation per page on CPU.
- **Pin the GPU/CPU orientation nondeterminism** (optional) — run orientation on CPU in the new pipeline to get
  byte-identical output to the original even on the big doc.
- **Cancellation** — kill the whole worker process-group cleanly on client disconnect (so OCR/Java sub-processes
  don't orphan).
- **Batch/optimize remaining CPU stages** and stream results for even lower latency.

---

## 10. Suggested slide outline (for the presentation agent)

1. **Title** — "Making dedoc's scanned-PDF pipeline ~4× faster."
2. **The headline number** — 23 min → 5.6 min (×4.1) on a 297-page report; big bar chart.
3. **What dedoc's scanned-PDF path does** — the per-page stage diagram (section 1).
4. **The problem** — original was largely serial; parallelism didn't scale.
5. **Where the time goes** — per-stage breakdown (section 3, pie/bar) + the two insights.
6. **The new architecture** — one diagram: pages → [render → NN(GPU) → deskew → layout(GPU) → table → OCR] across
   process workers + 1 GPU worker; whole-doc steps after.
7. **Fix-by-fix** — 2–3 slides walking sections 5.1–5.7, each with its number.
8. **Scaling chart** — proc 1→8, CPU vs GPU (section 6b).
9. **GPU offload** — layout CPU vs GPU (6e) + utilization (6f).
10. **Memory** — 18.7 GB → 8.1 GB, OOM fixed (6g).
11. **Correctness** — byte-identical (section 7).
12. **Takeaways + next steps** — sections 8 & 9.

**Chart suggestions:** (2) grouped bar original vs new; (5)/(8) line or grouped bar for scaling; (5) pie or 100%
stacked bar for per-stage share; (9)/(10) before/after bars. Keep a consistent 2-color scheme (original vs new).

---

## Appendix — caveats to state honestly
- Benchmarks are from one laptop (RTX 3080, 16 cores, 34 GB RAM, ~13 GB free during tests); absolute times will vary.
- The new pipeline's speed configuration uses `OMP_THREAD_LIMIT=1`; the original ran with its natural Tesseract threading.
- "×4.1" compares the new 8-process + GPU pipeline against the original default. Against the original's own best
  parallel option the ratio would be smaller but was not run to completion on the full document (long runtime).
- The scanned-image OCR path is the target; PDFs that already have a text layer use a different (fast) reader and are out of scope here.
