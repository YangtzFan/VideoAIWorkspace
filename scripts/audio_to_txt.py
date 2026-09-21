"""Transcribe audio files to UTF-8 text with faster-whisper."""

from __future__ import annotations

import argparse
import ctypes
import importlib.util
import os
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_AUDIO_DIR = BASE_DIR / "audios"
DEFAULT_TEXT_DIR = BASE_DIR / "texts"
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".opus", ".aac"}
CUDA_DLL_DIRECTORY_HANDLES: list[object] = []
CUDA_LIBRARY_HANDLES: list[object] = []


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="使用 faster-whisper 批量将音频转写为 UTF-8 文本。"
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_AUDIO_DIR,
        help=f"音频目录（默认：{DEFAULT_AUDIO_DIR}）",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_TEXT_DIR,
        help=f"文本输出目录（默认：{DEFAULT_TEXT_DIR}）",
    )
    parser.add_argument(
        "--model",
        default="small",
        help="Whisper 模型名称或本地模型目录（默认：small）",
    )
    parser.add_argument(
        "--language",
        default="auto",
        help="语言代码，如 zh、en；auto 表示自动检测（默认：auto）",
    )
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "cuda"),
        default="auto",
        help="推理设备；auto 优先使用 CUDA，不可用时回退 CPU（默认：auto）",
    )
    parser.add_argument(
        "--compute-type",
        default=None,
        help="计算精度；默认在 CPU 使用 int8，在 CUDA 使用 float16",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="覆盖已经存在的 TXT 文件",
    )
    return parser.parse_args()


def find_audio_files(directory: Path) -> list[Path]:
    if not directory.is_dir():
        raise FileNotFoundError(f"音频目录不存在：{directory}")
    return sorted(
        (path for path in directory.iterdir() if path.suffix.lower() in AUDIO_EXTENSIONS),
        key=lambda path: path.name.lower(),
    )


def transcribe(model: object, audio_file: Path, language: str) -> tuple[str, str, float]:
    selected_language = None if language == "auto" else language
    segments, info = model.transcribe(
        str(audio_file),
        language=selected_language,
        beam_size=5,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
    )
    lines = [segment.text.strip() for segment in segments if segment.text.strip()]
    text = "\n".join(lines)
    probability = float(getattr(info, "language_probability", 0.0))
    return text, str(info.language), probability


def configure_cuda_dll_paths() -> None:
    """Expose CUDA DLLs installed by NVIDIA's Python packages on Windows."""
    if sys.platform != "win32" or CUDA_DLL_DIRECTORY_HANDLES:
        return

    dll_directories: dict[str, Path] = {}
    for module_name in ("nvidia.cublas", "nvidia.cuda_runtime"):
        try:
            spec = importlib.util.find_spec(module_name)
        except (ImportError, ModuleNotFoundError):
            continue
        if spec is None or spec.submodule_search_locations is None:
            continue
        for module_directory in spec.submodule_search_locations:
            dll_directory = Path(module_directory) / "bin"
            if dll_directory.is_dir():
                dll_directories[module_name] = dll_directory
                CUDA_DLL_DIRECTORY_HANDLES.append(
                    os.add_dll_directory(str(dll_directory))
                )

    libraries = (
        ("nvidia.cuda_runtime", "cudart64_12.dll"),
        ("nvidia.cublas", "cublasLt64_12.dll"),
        ("nvidia.cublas", "cublas64_12.dll"),
    )
    for module_name, library_name in libraries:
        dll_directory = dll_directories.get(module_name)
        if dll_directory is None:
            continue
        library_path = dll_directory / library_name
        if library_path.is_file():
            try:
                CUDA_LIBRARY_HANDLES.append(ctypes.WinDLL(str(library_path)))
            except OSError:
                pass


def cuda_is_available() -> bool:
    try:
        import ctranslate2

        return ctranslate2.get_cuda_device_count() > 0
    except Exception:
        return False


def load_model(
    model_name: str, device: str, requested_compute_type: str | None
) -> tuple[object, str]:
    from faster_whisper import WhisperModel

    compute_type = requested_compute_type or ("float16" if device == "cuda" else "int8")
    print(
        f"正在加载模型 {model_name}（device={device}, "
        f"compute_type={compute_type}）..."
    )
    model = WhisperModel(model_name, device=device, compute_type=compute_type)
    return model, compute_type


def main() -> int:
    args = parse_args()
    input_dir = args.input_dir.resolve()
    output_dir = args.output_dir.resolve()

    try:
        audio_files = find_audio_files(input_dir)
    except FileNotFoundError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1

    if not audio_files:
        extensions = ", ".join(sorted(AUDIO_EXTENSIONS))
        print(f"错误：{input_dir} 中没有支持的音频（{extensions}）。", file=sys.stderr)
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)
    pending_files = []
    for audio_file in audio_files:
        text_file = output_dir / f"{audio_file.stem}.txt"
        if text_file.exists() and not args.overwrite:
            print(f"跳过已有文本：{text_file.name}")
        else:
            pending_files.append(audio_file)

    if not pending_files:
        print(f"无需转写，{len(audio_files)} 个音频均已有对应文本。")
        return 0

    if args.device != "cpu":
        configure_cuda_dll_paths()

    try:
        import faster_whisper  # noqa: F401
    except ImportError:
        print(
            "错误：缺少 faster-whisper。请运行 "
            "`python -m pip install -r requirements.txt`。",
            file=sys.stderr,
        )
        return 1

    device = args.device
    allow_cpu_fallback = device == "auto"
    if device == "auto":
        device = "cuda" if cuda_is_available() else "cpu"
        if device == "cpu":
            print("未检测到可用的 CUDA 设备，将使用 CPU。")

    try:
        model, compute_type = load_model(args.model, device, args.compute_type)
    except Exception as exc:
        if allow_cpu_fallback and device == "cuda":
            print(f"CUDA 模型加载失败，将回退到 CPU：{exc}", file=sys.stderr)
            device = "cpu"
            try:
                model, compute_type = load_model(args.model, device, None)
            except Exception as cpu_exc:
                print(f"错误：CPU 模型加载失败：{cpu_exc}", file=sys.stderr)
                return 1
        else:
            print(f"错误：模型加载失败：{exc}", file=sys.stderr)
            return 1

    failures = 0
    for index, audio_file in enumerate(pending_files, start=1):
        text_file = output_dir / f"{audio_file.stem}.txt"
        print(f"[{index}/{len(pending_files)}] {audio_file.name} -> {text_file.name}")

        temporary_file = text_file.with_suffix(".tmp.txt")
        temporary_file.unlink(missing_ok=True)
        try:
            try:
                text, language, probability = transcribe(model, audio_file, args.language)
            except Exception as cuda_exc:
                if not (allow_cpu_fallback and device == "cuda"):
                    raise
                print(f"  CUDA 推理失败，将回退到 CPU：{cuda_exc}", file=sys.stderr)
                device = "cpu"
                model, compute_type = load_model(args.model, device, None)
                text, language, probability = transcribe(model, audio_file, args.language)
            temporary_file.write_text(text + ("\n" if text else ""), encoding="utf-8")
            temporary_file.replace(text_file)
            print(
                f"  转写完成：{len(text)} 个字符，语言={language} "
                f"（置信度={probability:.1%}）。"
            )
        except Exception as exc:
            failures += 1
            temporary_file.unlink(missing_ok=True)
            print(f"  转写失败：{exc}", file=sys.stderr)

    if failures:
        print(f"处理结束：{failures} 个文件失败。", file=sys.stderr)
        return 1

    print(f"处理完成，文本位于：{output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
