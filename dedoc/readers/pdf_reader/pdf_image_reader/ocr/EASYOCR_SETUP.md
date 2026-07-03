# EasyOCR engine setup (optional OCR backend)

dedoc's OCR engine is pluggable: set `config["ocr_engine"] = "easyocr"` to use EasyOCR instead of the
default Tesseract (see `easyocr_line_extractor.py`). EasyOCR is torch-based, Apache-2.0, with strong
Cyrillic support. It produces the same `PageWithBBox` structure as the Tesseract path, so the rest of the
pipeline is unchanged.

> Speed note: on CPU-rich hardware, parallel Tesseract (self-forking, one process per page) still beats a
> single GPU running EasyOCR on OCR **throughput** — a single GPU can't be parallelised across processes
> without CUDA MPS. EasyOCR is provided as a quality/multilingual option, not a speed default.

## 1. Install

EasyOCR pulls `torch`/`torchvision` as dependencies. To avoid clobbering an existing CUDA torch build,
install it without deps and add the non-torch deps explicitly:

```bash
pip install --no-deps easyocr
pip install python-bidi Shapely pyclipper scikit-image ninja PyYAML
```

Detection/recognition models download automatically on first use into the EasyOCR cache.

## 2. GPU: the DBNet detector needs a compiled CUDA op

The extractor defaults to the **DBNet18** detector (`config["easyocr_detector"] = "dbnet18"`), which is
~2.5x faster than EasyOCR's default CRAFT detector at full resolution. DBNet uses **deformable convolutions**
whose CUDA extension is **not prebuilt** in the pip package. Without it, on GPU you get:

```
RuntimeError: Input type is cuda, but 'deform_conv_cuda.*.so' is not imported successfully.
```

Either build the op once (below), or set `config["easyocr_detector"] = "craft"` to avoid the build (at
~2.5x slower detection).

### Build steps (once per environment)

Requires a CUDA toolkit with `nvcc` (same **major** version as torch's CUDA, e.g. 12.x — a minor mismatch
like 12.6 vs 12.1 only warns) and a C++ compiler (Windows: Visual Studio Build Tools / MSVC; Linux: gcc).

**Step 1 — patch the two CUDA kernels.** The vendored sources `#include <THC/THCAtomics.cuh>`, a header
removed in torch >= 1.11. In both files under
`<venv>/Lib/site-packages/easyocr/DBNet/assets/ops/dcn/src/`:

- `deform_conv_cuda_kernel.cu`
- `deform_pool_cuda_kernel.cu`

replace

```cpp
#include <THC/THCAtomics.cuh>
```

with

```cpp
#include <ATen/cuda/Atomic.cuh>
```

(The kernels only use the native CUDA `atomicAdd`, so this is a straight header swap.)

**Step 2 — build the extension** in a shell that has the compiler + CUDA on `PATH`:

Windows (from an x64 Developer Command Prompt, i.e. after `vcvars64.bat`):

```bat
set "CUDA_HOME=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.x"
cd <venv>\Lib\site-packages\easyocr\DBNet\assets\ops\dcn
python setup.py build_ext --inplace
```

Linux:

```bash
export CUDA_HOME=/usr/local/cuda-12.x
cd <venv>/lib/pythonX.Y/site-packages/easyocr/DBNet/assets/ops/dcn
python setup.py build_ext --inplace
```

This produces `deform_conv_cuda.*` (and `deform_pool_cuda.*`) in the `dcn/` directory; EasyOCR loads these
ahead-of-time modules instead of the failing just-in-time build.

**Step 3 — verify:**

```python
import easyocr
r = easyocr.Reader(["en"], gpu=True, detect_network="dbnet18")
print(len(r.readtext("some_page.png")))  # runs without the deform_conv error
```

## 3. Tunable config keys

| key | default | meaning |
|-----|---------|---------|
| `ocr_engine` | `"tesseract"` | `"easyocr"` to use this backend |
| `easyocr_detector` | `"dbnet18"` | `"craft"` to skip the CUDA-op build (slower) |
| `easyocr_canvas_size` | `2560` | detection resolution cap; lowering trades OCR quality for speed |
| `easyocr_batch_size` | `16` | recognition (CRNN) crop batch size |
