# Tesseract layout reading-order for the hybrid OCR engine

The hybrid OCR engine (PP-OCR/DBNet detector + PP-OCRv5 East-Slavic recognizer) recognizes text well but orders it
with a naive top-to-bottom line grouping, which mis-orders **multi-block / multi-column** pages. Tesseract's page
layout analysis (`AnalyseLayout` — segmentation only, *no* recognition) produces the correct block reading order, so
we borrow **only its ordering** and keep the (more accurate) eslav recognition.

Measured on `pdf_profiling/gen_texts` (multi-block, clean embedded-text GT):

| | WER | word-bag F1 | notes |
|---|---|---|---|
| hybrid, naive order | 0.55 | 0.94 | recognition is fine; order is wrong |
| **hybrid + Tesseract layout** | **0.09–0.13** | 0.94 | −79 % WER end-to-end; F1 unchanged (pure reorder) |
| Tesseract full OCR | 0.06 | 0.95 | reference |

Full-doc cost (DAE, 297 pp): **+5.5 s (+3.6 %)** — `AnalyseLayout` (~0.3–0.7 s/page) runs on the CPU thread pool and
is absorbed by CPU headroom (the pipeline is GPU-worker-bound).

## How to enable

Off by default (needs the optional `tesserocr` dependency). Set in the reader config:

```python
config["hybrid_reading_order"] = "tesseract"   # default "naive"
```

The value is forwarded to the worker readers (`PdfBaseReader._get_stage_executor`). If `tesserocr` fails to load or
`AnalyseLayout` errors, `page_from_detections` **falls back to naive ordering** (logged), so OCR never breaks.
`PyTessBaseAPI` is not thread-safe, so the extractor keeps a **thread-local** API (the `ocr` stage runs in a thread
pool). `TESSDATA_PREFIX` must point at the tessdata dir (already required by the Tesseract OCR engine).

## Installing `tesserocr`

### Linux (production)
```bash
apt-get install tesseract-ocr libtesseract-dev libleptonica-dev   # or the distro equivalent
pip install tesserocr
```
Usually conflict-free (manylinux/system libs are compatible).

### Windows — build a **self-contained** wheel (avoids a DLL conflict)
On Windows a plain source build links `tesserocr` dynamically against the (conda) `tesseract`/`leptonica` DLLs, which
then clash with the `libpng`/`zlib` that `torch`/`onnxruntime`/`opencv` bundle — whichever loads first wins, and
`tesserocr` crashes ("the OS cannot run %1"). Fix: build the wheel, then **statically bundle its DLL deps with
`delvewheel`** so it has no external shared DLLs. Against a conda `tesseract` (here 5.5.2, at `%CONDA%\Library`):

```powershell
$L = "$env:CONDA_PREFIX\Library"           # dir with include\tesseract, lib\tesseract*.lib, bin\*.dll
Copy-Item "$L\lib\tesseract55.lib"     "$L\lib\tesseract.lib" -Force   # tesserocr links -ltesseract / -llept
Copy-Item "$L\lib\leptonica-1.87.0.lib" "$L\lib\lept.lib"    -Force
$env:INCLUDE  = "$L\include;$L\include\tesseract;$env:INCLUDE"
$env:LIB      = "$L\lib;$env:LIB"
$env:LIBPATH  = "$L\lib"
$env:TESSERACT_VERSION = "5.5.2"

pip install delvewheel
pip wheel tesserocr --no-deps -w .\wheelbuild
delvewheel repair --add-path "$L\bin" .\wheelbuild\tesserocr-*.whl -w .\wheelfixed
pip install .\wheelfixed\tesserocr-*.whl                                # self-contained, coexists with torch
```

The repaired wheel bundles `tesseract55.dll`, `leptonica`, `libpng`, `zlib`, … into `tesserocr.libs` with mangled
names, so it imports fine regardless of load order — no preload hack needed. (Alternative: install `torch`/
`onnxruntime`/`opencv` from conda-forge into the same env so everything shares one native stack.)
