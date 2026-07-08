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

## Reproducing the numbers

```
DEDOC_OCR_ENGINE=hybrid DEDOC_REC_ENGINE=trt_fp16  python scratchpad/bench_full.py <doc> --gpu --workers 8
DEDOC_OCR_ENGINE=hybrid DEDOC_REC_ENGINE=trt_int8  python scratchpad/bench_full.py <doc> --gpu --workers 8
```
Quality: `scratchpad/wer_trt.py` (CUDA fp16 vs TRT fp16 vs TRT int8, word-bag F1 on gen_texts clean GT).
