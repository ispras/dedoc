# TensorRT FP16/INT8 for the eslav recognizer on GPU — working guide

Speeds up the hybrid recognizer (`ocr_gpu`, the biggest GPU-worker cost) **2–2.5×** by running the PP-OCRv5 CRNN on
TensorRT instead of the onnxruntime CUDA EP. Opt-in via `config["hybrid_rec_engine"] = "trt_fp16" | "trt_int8"`
(default `"onnx"`). Measured on the RTX 3080 Laptop; engines are device/TRT-version specific (rebuild per machine).

## Results (DAE, 297 pages; profile max width 2560)

| recognizer | rec ms/page | full-pipeline wall | quality (word-bag F1 long / short) |
|---|---|---|---|
| onnx CUDA fp16 (default) | 210 | 147 s | 0.943 / 0.921 (baseline) |
| **TRT fp16** | ~105 (2.0×) | **123 s (−17 %)** | 0.943 / 0.921 — **lossless (= CUDA)** |
| TRT int8 (entropy calib) | ~93 (2.3×) | 122 s (−17 %) | 0.935 / 0.907 (−0.8 / −1.4 %) |

Absolute wall varies ±~10 % run-to-run (GPU thermal/clock state); the **−17 % relative** gain is the stable figure.

**Recommendation: TRT fp16.** It's lossless (matches the CUDA fp16 output) and, at the pipeline level, as fast as
INT8 — the INT8 recognizer is ~12 ms/page faster but that's lost in run-to-run pipeline noise, while INT8 costs
~1 % word-bag F1. INT8 only pays off where the recognizer dominates more of the wall. (Min-max INT8 calibration was
tried and was clearly worse — F1 0.841 on short text — so entropy calibration on real crops is the one to use.)

## Why not the onnxruntime TensorRT EP

The onnxruntime TRT EP loads (once the version matches, below) but **fails to build an engine** for this
PaddlePaddle-exported model: `TensorRT EP failed to create engine from network`. The raw TensorRT
`Builder`/`OnnxParser` build the SAME model fine — so the recognizer runs on the **standalone TensorRT runtime**
(`_TRTRec` in `hybrid_line_extractor.py`), bypassing the opaque ORT EP. (The CUDA EP itself cannot do INT8 at all —
it runs QDQ in fp32, ~22× slower; TensorRT is the only real GPU-INT8 path, on the RTX 3080's INT8 Tensor Cores.)

## Step 1 — version-matched TensorRT (the fiddly part)

`onnxruntime-gpu 1.18.1` needs **TensorRT 10.x** (`nvinfer_10.dll`). Pitfalls: `pip install tensorrt` pulls
`tensorrt-cu12 11.x` (`nvinfer_11`, too new → EP silently unused); the 10.x pypi.org packages are broken stubs; the
~2 GB wheels + pip cache fill the disk. **Working install — libs only, from the NVIDIA index, no cache:**

```bash
pip install tensorrt-cu12-libs==10.0.1 tensorrt-cu12-bindings==10.0.1 \
    --index-url https://pypi.nvidia.com --no-deps --no-cache-dir
```

At runtime add the DLL dir before importing (Windows): `os.add_dll_directory(<site-packages>/tensorrt_libs)`, then
`import tensorrt_bindings as trt` (the `tensorrt` meta package is 11.x — don't install it; the bindings module works).

## Step 2 — build the engines (one-time, cached to the model dir)

`scratchpad/trt_infer.py` (fp16) and `scratchpad/calib_int8.py` (int8) build serialized engines:

```python
builder = trt.Builder(logger)
net = builder.create_network(1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH))
trt.OnnxParser(net, logger).parse(open("rec_sim.onnx", "rb").read())   # rec_sim = onnx-simplified rec (folds consts)
cfg = builder.create_builder_config(); cfg.set_flag(trt.BuilderFlag.FP16)
prof = builder.create_optimization_profile()                            # dynamic (N,3,48,W):
prof.set_shape("x", (1,3,48,48), (8,3,48,480), (16,3,48,2560))          # min / opt / max
cfg.add_optimization_profile(prof)
open("rec_fp16.trt","wb").write(builder.build_serialized_network(net, cfg))   # ~5 min build, cached
```

For INT8 add `cfg.set_flag(trt.BuilderFlag.INT8)` + `cfg.int8_calibrator = Calib(real_crop_batches)` (an
`IInt8EntropyCalibrator2`/`MinMaxCalibrator` yielding preprocessed `(8,3,48,480)` crop batches) + a fixed calibration
profile. ~10 min build. Both flags on ⇒ TensorRT picks INT8 where it helps and keeps FP16 elsewhere.

The prebuilt engines ship next to the ONNX model: `ppocr_eslav/rec_fp16.trt`, `rec_int8.trt` (+ `rec_sim.onnx`,
`calib*.cache`). **They are GPU- and TRT-version-specific** — rebuild on a different card/driver.

## Step 3 — runtime (`_TRTRec`, in `hybrid_line_extractor.py`)

`_TRTRec` deserializes the engine, and on each call copies the `(N,3,48,W)` batch to a torch CUDA tensor, sets the
dynamic input shape, runs `execute_async_v3`, and returns the logits — a drop-in for the recognizer's session
(`TextRecognizer` calls `self.session(batch)[0]`). Input width is clamped to the engine's optimization-profile range
(read from the engine at load, currently **[48, 2560]**) via GPU bilinear interp. The dataset's max observed line
width is 2011 px (long_text; nothing exceeds 2560 across 7 393 crops / 6 groups), so at 2560 the clamp never fires —
no aspect distortion in practice. `_ensure_ppocr_rec` selects it when
`hybrid_rec_engine` is `trt_fp16`/`trt_int8` and the `.trt` file exists (else falls back to the onnx CUDA session).
It coexists with onnxruntime-CUDA (detector) and torch (orient) in the same GPU-worker process — verified in the full
pipeline (tables=6, no crash).

## Follow-on: the pipeline is now CPU-bound → GPU-worker parallelism

With the recognizer on TensorRT, the GPU dropped to ~20% utilization and the wall became CPU-bound (adding CPU workers
past the 8 physical cores hurts). Per-stage profiling (env-gated `DEDOC_STAGE_PROF=<dir>` in `executor.py`, aggregated
across worker PIDs) on the 297-page doc showed the real costs: `render` ~720 ms/page, `deskew` ~360 ms, and the single
**GPU worker is itself CPU-bound** — its "GPU" stage (`ocr_gpu`) is ~56% CPU (box post-processing + warpPerspective crop
extraction + rec resize/CTC-decode) and only ~44% GPU forwards, which is why GPU utilization stayed at ~20%.

**Win — run more than one GPU worker** (`config["gpu_workers"]`, default 1). A 2nd/3rd GPU worker process parallelizes
that in-worker CPU work across cores and overlaps GPU compute (one worker computes while another does pre/post):

| gpu_workers | wall (DAE 297p) | CPU | GPU | peak RSS |
|---|---|---|---|---|
| 1 | 124–127 s | 71 % | 20 % | 11 GB |
| **2** | **104 s (−16 %)** | 84 % | 27 % | 13 GB |
| 3 | 100 s (−19 %) | 82 % | 27 % | 15 GB |

Output is identical (tables=6, same text). Diminishing past 2 (GPU util plateaus ~27%; the wall is then bound by the
CPU stages `render`/`deskew`). Each worker replicates the models on the GPU (~+2 GB RSS), so `gpu_workers` is left at
default 1 for portability — set it to 2 on a GPU with headroom.

**Win — faster page rendering (`_render` via pypdfium2 + erode).** `render` was the biggest CPU stage. `pdf2image`
shells out to `pdftoppm`, which spawns a subprocess **and re-parses the whole PDF per page** (~300 ms/page of pure
overhead on top of the ~165 ms rasterization). Switching to **pypdfium2** (Apache-2.0, PDFium) rendering in-process
with a per-worker cached `PdfDocument` removes that overhead — **−18 % full-pipeline wall (127 → 104 s, within-session,
measured cleanly since cross-session numbers drift ±10 %)**. PDFium is not thread-safe, so `render` runs in the
isolated worker processes (`exec_mode=THREAD`), and the document is loaded from bytes (a path makes PDFium hold a
Windows file lock that fights the temp-file cleanup). PDFium's glyph anti-aliasing renders text ~1 px thinner than
Poppler, which alone costs ~3.8 % word-bag F1 on short-text pages; a **2×2 `cv2.erode`** thickens the glyphs back to
Poppler weight and recovers it exactly (verified on gen_texts: short 0.898 → 0.936 = pdftoppm; long unaffected) at
~1 ms/page. Falls back to `pdf2image` if pypdfium2 is missing or rejects a PDF; `DEDOC_RENDER=pdftoppm` forces the old
path. *(Aside: a bigger in-flight window and a dedicated render pool were both measured and gave nothing / oversubscribed
the 8 cores — the pipeline is CPU-core-bound, so reordering doesn't add capacity.)*

**Not worth it (measured, reverted):**
- *Table-presence layout gate* — skips the 650 ms/page OpenCV table detector on tableless pages (cuts it 42%→2% of CPU
  time), but the layout NN is a GPU stage and its extra CPU→GPU→CPU→GPU round-trip cost +29 s even with the GPU idle.
- *Splitting `ocr_gpu` into det_gpu→crop(CPU)→rec_gpu* — moves the crop/post CPU work off the GPU worker; helps with a
  single GPU worker (−11 %) but is a net loss at `gpu_workers>=2` (round-trip + crop-list transport outweigh it, and
  extra GPU workers already parallelize the in-worker CPU work for free).

## Follow-on: table cell OCR on the GPU (hybrid engine)

The OpenCV table detector OCRs its cells with Tesseract (`--psm 6` on a vertically-stacked cell image), ~530 ms/table-page
and the dominant table cost. On the same real stacked cells the hybrid recognizer (DBNet + eslav TRT rec) is **2.2× faster
(245 ms) and more accurate — word-bag F1 0.83 vs 0.74** (Tesseract mis-segments dense grids; the recognizer reads clean
printed cells, incl. Latin/digits, well). Measured with `scratchpad/cell_scenario_test.py` (both on the *same* stacked cells).

Wiring (hybrid only) piggybacks the existing det_pre→ocr_gpu→ocr flow — **no new pipeline stage, so table-free pages take no
extra CPU↔GPU hop** (the +29 s lesson above):
- **`table` stage (CPU)** — `TableRecognizer.detect_tables_prepared`: detect + filter + mask cells + stack them, *without*
  OCR. Returns the cleaned image (body OCR reads it) + a `prepared` dict (pruned tree + stacked cell images), ~360 KB/page
  pickled, table pages only. `TableTree.__getstate__` drops its unpicklable `config`/`logger` for transport.
- **`ocr_gpu` stage (GPU)** — recognizes each stacked-cell image alongside the page detections (`_hybrid_stack_ocr`).
- **`ocr` stage (CPU)** — `assemble_tables_from_ocr`: assign cell text onto the tree, rebuild the (already-filtered)
  ScanTables. Tables now surface from the ocr-stage output (`pdf_base_reader` reads `field("ocr", …, "tables")`).

DAE 270–290 (6 table pages): **−7 % wall** (scales with table-page count), table-text F1 **0.58 vs 0.50** vs the Tesseract
cell path. Opt out with `DEDOC_TABLE_CELL_OCR=tesseract`. Tesseract-engine / non-pipeline paths keep the in-stage cell OCR.

## Follow-on: leaner pipeline workers (lazy imports)

Every worker builds a `PdfImageReader`, but the per-page stages use only 7 of its components (`ocr`, `table_recognizer`,
`metadata_extractor`, `binarizer`, `column_orientation_classifier`, `attachments_extractor`, `config`). Two eager imports
loaded heavy deps a worker never uses:
- **Tesseract** (`ocr_utils.py`): `import pytesseract` pulls pandas + PIL (~58 MB) at module load, but the hybrid engine
  recognizes page and table text with its own recognizer and never calls Tesseract (only the optional reading-order
  layout borrow uses `tesserocr`, already lazy). Deferred to the call sites.
- **Post-read components** (`pdf_base_reader.py`): the linker / paragraph classifier / header-footer / notes / GOST
  recognizer run only in the main-process post-read assembly, never in a worker. The paragraph classifier alone imports
  a pandas + sklearn feature chain. Made lazy `@property` — the worker's reader is ~44 MB leaner and loads no pandas;
  the main process builds them on first access. CPU workers sit at ~0.2 GB RSS.
- **Bold classifier** (`bold_classifier/agglomerative_clusterizer.py`): the line-metadata stage's bold detection uses
  `sklearn.cluster.AgglomerativeClustering` + `scipy.stats.norm` (~55 MB). It runs only in the CPU ocr-metadata stage;
  the GPU workers (orient/layout/ocr_gpu only) and the main process build the reader but never call it. Deferred both
  imports into the methods that use them, so those processes never load sklearn/scipy: **GPU worker 785 → 729 MB RSS**.
  sklearn is kept (not swapped for a lighter clusterer) — a scipy-Ward replacement changed 98.6% of pages after the
  F-criterion, so bold detection stays bit-for-bit identical.

GPU-worker host RAM (static, one worker) breaks down as torch ~534 MB (import + CUDA context + the orientation model —
load-bearing: the TRT rec's CUDA I/O buffers are torch tensors), models ~125 MB (DBNet onnx + TRT rec engine), reader
~40 MB. torch dominates and is effectively irreducible without dropping GPU recognition.

## Follow-on: VMS (commit charge) — cap per-worker BLAS/OMP threads

Most of the process-tree **VMS is reserved address space, not resident RAM** (RSS). The largest tunable reserve was
per-worker math-library threads: each spawned worker started a BLAS/OMP pool sized to all 16 cores, and **OpenBLAS alone
reserves ~500 MB VMS per worker** (measured 552 → 47 MB at 1 thread) — × ~10 workers, plus 160-thread oversubscription of
16 cores. The pipeline parallelizes across pages/workers, so per-worker math libs must be single-threaded. Setting
`OPENBLAS/OMP/MKL/NUMEXPR_NUM_THREADS=1` in the executor before the pools spawn (children inherit on spawn; `setdefault`
so an explicit override wins) drops full-doc **peak VMS 28.9 → 22.6 GB (−6.3 GB, −22 %)**, wall neutral (71 vs 72 s),
output unchanged. It also self-caps Tesseract to one thread — the scaling the image path previously needed a manual
`OMP_THREAD_LIMIT=1` for. (The shared-memory buffer pool was likewise sized from the measured page distribution:
64 → 32 MB per buffer, ~3.75 → 1.9 GB, speed-neutral.)

## Reproducing the numbers

```
DEDOC_OCR_ENGINE=hybrid DEDOC_REC_ENGINE=trt_fp16  python scratchpad/bench_full.py <doc> --gpu --workers 8
DEDOC_OCR_ENGINE=hybrid DEDOC_REC_ENGINE=trt_int8  python scratchpad/bench_full.py <doc> --gpu --workers 8
# table cell OCR A/B (hybrid recognizer vs Tesseract on cells):
DEDOC_OCR_ENGINE=hybrid DEDOC_REC_ENGINE=trt_fp16 DEDOC_TABLE_CELL_OCR=hybrid|tesseract  python scratchpad/bench_full.py <doc> --gpu
```
Quality: `scratchpad/wer_trt.py` (CUDA fp16 vs TRT fp16 vs TRT int8, word-bag F1 on gen_texts clean GT).
