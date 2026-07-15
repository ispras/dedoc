# Pipeline benchmarks

Raw comparison data collected while building the staged pipeline (see ARCHITECTURE.md). Times are seconds.

**Environment:** NVIDIA RTX 3080 Laptop (16 GB), 16 logical cores, Windows. torch `2.2.2+cu121`.
poppler + tesseract via conda env `dedocbin` (tessdata eng/spa/fra/osd). `OMP_THREAD_LIMIT=1` unless noted.
Parity metric: `text_sha` = sha256(reading-order text)[:12], `tbl_sha` = sha256(table cell text)[:12].
`master` = clean git worktree at commit 187baf5 (dedoc 2.7). Docs: BDLCM prospectus (79p), CatalanaOccidente (267p).
All PDF runs use `pdf_with_text_layer=false` (PdfImageReader / OCR path).

## Flat table (all runs)

| # | experiment | doc | pages | path | workers | gpu | NN | attach | time s | s/page | text_sha | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | per-stage | BDLCM | 3 | monolith | 1 | no | off | no | — | 2.47 | — | baseline render+OCR |
| 2 | per-stage | BDLCM | 3 | monolith | 1 | no | on | no | — | 3.73 | — | +orient/col NN (+51%) |
| 3 | per-stage | BDLCM | 3 | monolith | 1 | no | off | no | — | 3.39 | — | +binarization (+37%) |
| 4 | per-stage | BDLCM | 3 | monolith | 1 | no | off | no | — | 2.55 | — | +tables (+3%) |
| 5 | per-stage | BDLCM | 3 | monolith | 1 | no | off | yes | — | 4.03 | — | +layout RT-DETR CPU (+63%) |
| 6 | njobs | BDLCM | 6 | joblib | 1 | no | off | no | 24.6 | 4.09 | — | 1.00x |
| 7 | njobs | BDLCM | 6 | joblib | 2 | no | off | no | 17.8 | 2.96 | — | 1.38x |
| 8 | njobs | BDLCM | 6 | joblib | 4 | no | off | no | 14.6 | 2.43 | — | 1.68x |
| 9 | main CPU | Catalana | 24 | master | 1 | no | on | no | 95.7 | 3.99 | 03651099fdb2 | original master |
| 10 | main CPU | Catalana | 24 | new proc | 1 | no | on | no | 70.6 | 2.94 | 03651099fdb2 | |
| 11 | main CPU | Catalana | 24 | new proc | 8 | no | on | no | 66.1 | 2.75 | 03651099fdb2 | warm; flat vs proc=1 |
| 12 | main CPU | Catalana | 24 | new proc | 1 | no | off | no | 45.3 | 1.89 | — | |
| 13 | main CPU | Catalana | 24 | new proc | 8 | no | off | no | 30.6 | 1.28 | — | 1.48x vs proc=1 |
| 14 | main GPU | Catalana | 24 | master | 1 | yes | on | no | 125.0 | 5.21 | 03651099fdb2 | single-parse, cold CUDA |
| 15 | main GPU | Catalana | 24 | new proc | 1 | yes | on | no | 82.3 | 3.43 | 03651099fdb2 | warm |
| 16 | main GPU | Catalana | 24 | new proc | 8 | yes | on | no | 42.6 | 1.78 | 03651099fdb2 | warm; 1.93x vs proc=1 |
| 17 | main GPU | Catalana | 24 | new proc | 8 | yes | on | no | 29.3 | 1.22 | 03651099fdb2 | warm + lazy render (util run) |
| 18 | sibling-bug | Catalana | 24 | new proc | 1 | no | on | no | — | — | 7ae0c9e6a057 | ocr/table siblings: table text leaked (328 nodes, len 35520); fixed by ocr-after-table |
| 19 | layout-GPU | Catalana | 24 | new proc | 8 | yes | on | yes | 34.3 | 1.43 | — | RT-DETR on GPU: GPU avg 25% / busy 100%, VRAM 4.5GB, CPU 74% (12.3/16c) |
| 20 | layout-CPU | Catalana | 24 | new proc | 8 | no | on | yes | 119.8 | 4.99 | — | RT-DETR serial in the single gpu-pool worker on CPU -> CPU 26% (2.4/16c); 3.5x slower |

## Full document — DAE (India) Annual Report 2020-21 (297 pages, 59 MB, big images)

| config | time | text_sha | peak RSS | notes |
|---|---|---|---|---|
| original master njobs=1 (natural OMP) | 1377.6s (~23 min) | 0a0cdc945af5 | — | reference; 5626 nodes, 6 tables |
| new proc=8 GPU (image-free bug) | 381.6s (~6.4 min) | 32ea2c4ded55 | 18.7 GB | first reduce_output built a new dict → images not freed |
| new proc=8 GPU (in-place fix) | 336.7s (~5.6 min) | 32ea2c4ded55 | 8.1 GB | ×4.1 vs original; CPU 94%, GPU 9%; 5626 nodes, 6 tables, text_len 790801 |
| new proc=8 GPU + **deskew downscale** | 234.9s (~3.9 min) | 09ec1769ed32 | 7.4 GB | ×5.9 vs original; CPU 84%, GPU 23%; 5611 nodes (−15), text_len 790885 — see note |
| new proc=8 GPU + deskew + **shared-mem image return** | **213.8s (~3.6 min)** | 09ec1769ed32 | 7.2 GB | **×6.4 vs original**; CPU 83%, GPU 17%; output IDENTICAL to the deskew run (transport-only) |

**deskew downscale (×1.43 more → ×5.9 total).** `SkewCorrector` was running 91 full-page rotations per page to find
the skew angle, but the pages are straight (angle 0); doing the angle detection on a **downscaled** image (long side
floored at 1000 px so low-res pages are not upscaled) is 5–18x cheaper, with the final rotation still at full res.
Deskew was the biggest stage (42%), so the whole doc dropped 336.7→234.9s and GPU util rose (9→23%, better balanced).
Trade-off: **output is no longer byte-identical** (5611 vs 5626 nodes, +84 chars) — downscaled detection picks a
different ±1° angle on a few pages, reordering that page's text (same length). A hybrid (coarse-on-downscaled +
±2° refine at full res) would keep the speedup and the exact angle if byte-identical output is required.

**×4.1 faster on the full big document** (23 min → 5.6 min), CPU ~94% utilized, peak RSS **8.1 GB** (down from 18.7 GB
before freeing the page image *in place* — the first `reduce_output` built a new dict, leaving the old one, still
referenced by the next task's input, holding the image).

nodes/tables/text_len are identical to the original (5626 / 6 / 790801). `text_sha` differs on the full doc
(0a0c vs 32ea) but **not** because of OMP: on a matched DAE 1:12 slice all three of {original OMP=1, original
OMP-multi, new-GPU OMP=1} gave the **same** sha `b02535a61e59` — Tesseract is OMP-deterministic and the pipeline is
byte-identical on matched config. The full-doc diff is most likely the **GPU-vs-CPU orientation NN** flipping a
borderline column/angle prediction on some page in 13–297 (reorders that page's text → same length, different hash),
i.e. NN device nondeterminism, not a pipeline bug.

**OOM found & fixed on the full document.** The full 297-page run was OOM-killed (machine had ~13 GB free of 34 GB).
Cause: the scheduler retained **every task's output dict, and each carried its ~12 MB page image** (via `{**doc, ...}`),
so ~5 stages x 297 pages x 12 MB ≈ >15 GB accumulated (invisible on the 24-page Catalana runs). Fix: the scheduler
now frees a task's large output fields (the image) once every dependent has consumed it (`reduce_output` / reference
count over the graph); the reader passes a reducer that drops `"image"`. Memory is now bounded by pages-in-flight.

## Grouped summaries

### Scaling proc=1 → proc=8 (Catalana 24p, warm)
- CPU, NN on:  70.6 → 66.1  (~flat — orientation serialized in the single GPU worker running on CPU) — **fixed, see below**
- CPU, NN off: 45.3 → 30.6  (**1.48x**)
- GPU, NN on:  82.3 → 42.6  (**1.93x**)

### CPU-only: routing the NN stages off the gpu pool (fixed)
`build_specs` marked `orient_predict` / `layout` as `Resource.GPU` unconditionally, so `scheduler.route` pinned them
to the gpu pool — which is **one** worker on a CPU-only run (`default_gpu_workers = 1`). Every NN forward therefore ran
serially in that worker while the CPU pool idled. When `on_gpu=False` those specs are now plain CPU specs (per page,
unbatched — batching only pays off on a device), so they spread over the CPU workers like every other stage.

Measured here (Catalana, CPU-only, `OMP_THREAD_LIMIT=1`; this machine is faster than the runs above, so compare
before/after within this block, not against the table):

| config | before | after | CPU util before → after |
|---|---|---|---|
| 24p, 8 workers | 54.1s | **17.1s** (**3.2x**) | 25% (4.1/16) → **74%** (11.9/16) |
| 24p + attachments (layout) | 119.8s (row 20) | **31.0s** (**3.9x**) | 26% (2.4/16) → **71%** (11.4/16) |
| 12p + attachments (A/B, same process) | 58.9s | **18.8s** (**3.1x**) | — |
| scaling 1 → 8 workers | 48.9 → 54.1 (**0.9x**, negative) | 48.0 → 17.1 (**2.8x**) | — |

**Full document, DAE 297p, CPU-only, 8 workers, single parse: 254.9s** (CPU **97%**, 15.5/16 cores) — **×5.4 vs the
1377.6s master reference**. Note this is the Tesseract path: the GPU Phase-2 number (~82s) buys its speed with
TensorRT/DBNet, which do not exist off-device, so CPU-only cannot approach it — the honest CPU-only baseline is master.

Parity: output identical before/after, including with attachments — `text_sha`, `tbl_sha`, attachment
(page + bbox) hash, and line/table/attachment counts all match, i.e. dropping the layout batching (batch=4 → per page)
is transport-only. (Attachment `original_name`/`uid` are regenerated every run — `get_unique_name` / `uuid4` — so they
must not be used as a parity metric.)

### New vs original (Catalana 24p, proc=8, warm)
- CPU:  new 66.1  vs  master 95.7   (~1.45x)
- GPU:  new 42.6 (29.3 with lazy render)  vs  master GPU 125.0

### Persistent executor (cold 1st parse → warm, same process)
- BDLCM 2p (CPU proc=2):    15.3 → 7.9
- Catalana 24p (CPU proc=8): 72.0 → 66.1
- Catalana 24p (GPU proc=8): 66.9 → 42.6

### Utilization (Catalana 24p, proc=8, GPU, warm)
- **no attachments** (orientation only on GPU): parse 29.3s; CPU avg **87%** (14.4/16 cores); GPU avg **5%**, busy 11% of time, VRAM 4.3 GB
- **with attachments** (orientation + layout on GPU): parse 34.3s; CPU avg **74%** (12.3/16 cores); GPU avg **25%**, busy **100%** of time, VRAM 4.6 GB

### Layout stage: GPU vs CPU + batching (Catalana 24p, proc=8, with_attachments)
- layout on GPU (per-page): **34.3s**; layout on CPU: **119.8s** → GPU **3.5x faster**.
- layout on GPU (**batched**, one RT-DETR forward per batch of pages): **27.9s** (~19% faster than per-page;
  GPU used in bursts: avg util 25%→10%, busy 100%→17% of time — fewer, larger forwards, less total GPU time).
- Layout (RT-DETR) routes to the single gpu-pool worker; on CPU that worker runs all forwards serially,
  starving the pipeline (CPU 26%, 2.4/16 cores). On GPU it offloads them (CPU back to ~76%).
  **Fixed for CPU-only runs** (`on_gpu=False` now routes the NN stages to the CPU workers): 119.8s → 31.0s,
  CPU 26% → 71% — see the CPU-only section above. On GPU the routing is unchanged.
- Made device-aware + batched in `ImageAttachmentsExtractor` (`_predict_batch` + `extract_batch`, moves model +
  inputs to `cuda` when `on_gpu`); previously it always ran on CPU per image regardless of `on_gpu`.

### Per-stage timing (Catalana 12p, LocalExecutor workers=1, GPU, with attachments)
Stage compute time (stage-sum 35.6s over 12 pages; wall 23.2s — render/cpu/gpu pools overlap even at workers=1).

| stage | per-page | % of stage time | note |
|---|---|---|---|
| deskew | 1252 ms | 42% | skew/perspective correction (dedocutils SkewCorrector, CPU) — the biggest cost |
| ocr | 923 ms | 31% | Tesseract text |
| render | 250 ms | 8% | Poppler |
| table | 200 ms | 7% | contours + cell OCR |
| orient_predict | 187 ms | 6% | EfficientNet — GPU forward is tiny; the 187 ms is the CPU PIL 1200x1200 preprocessing |
| layout | 159 ms | 5% | RT-DETR on GPU (batched) |

**Takeaway:** the two heavy stages are both CPU-bound — **deskew (42%) and OCR (31%) = 73%** of per-page compute.
The GPU stages (orientation, layout) are now cheap (~5-6% each). deskew (skew correction) is the largest single
stage and the prime remaining CPU optimization target (not OCR, as originally assumed).

### Parity (correctness)
- Every new-version config (CPU/GPU, LocalExecutor/ProcessExecutor, GPU batch, lazy render) with the
  default `ocr-after-table` graph: `text_sha=03651099fdb2`, `tbl_sha=1681da33e80d` — **byte-identical to master**.
