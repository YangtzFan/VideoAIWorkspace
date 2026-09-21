"""Batch-extract MP3 audio tracks from videos."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_VIDEO_DIR = BASE_DIR / "videos"
DEFAULT_AUDIO_DIR = BASE_DIR / "audios"
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="批量提取视频音轨，并保存为同名 MP3 文件。"
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_VIDEO_DIR,
        help=f"视频目录（默认：{DEFAULT_VIDEO_DIR}）",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_AUDIO_DIR,
        help=f"MP3 输出目录（默认：{DEFAULT_AUDIO_DIR}）",
    )
    parser.add_argument(
        "--bitrate",
        default="192k",
        help="MP3 比特率（默认：192k）",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="覆盖已经存在的 MP3 文件",
    )
    return parser.parse_args()


def find_ffmpeg() -> str:
    """Return a usable FFmpeg executable from PATH or imageio-ffmpeg."""
    executable = shutil.which("ffmpeg")
    if executable:
        return executable

    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except (ImportError, RuntimeError) as exc:
        raise RuntimeError(
            "没有找到 FFmpeg。请安装 FFmpeg 并加入 PATH，或运行 "
            "`python -m pip install imageio-ffmpeg`。"
        ) from exc


def find_videos(directory: Path) -> list[Path]:
    if not directory.is_dir():
        raise FileNotFoundError(f"视频目录不存在：{directory}")
    return sorted(
        (path for path in directory.iterdir() if path.suffix.lower() in VIDEO_EXTENSIONS),
        key=lambda path: path.name.lower(),
    )


def extract_audio(
    ffmpeg: str, video_file: Path, audio_file: Path, bitrate: str
) -> None:
    temporary_file = audio_file.with_suffix(".tmp.mp3")
    temporary_file.unlink(missing_ok=True)
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(video_file),
        "-map",
        "0:a:0",
        "-vn",
        "-codec:a",
        "libmp3lame",
        "-b:a",
        bitrate,
        str(temporary_file),
    ]
    try:
        subprocess.run(command, check=True)
        temporary_file.replace(audio_file)
    except Exception:
        temporary_file.unlink(missing_ok=True)
        raise


def main() -> int:
    args = parse_args()
    input_dir = args.input_dir.resolve()
    output_dir = args.output_dir.resolve()

    try:
        ffmpeg = find_ffmpeg()
        video_files = find_videos(input_dir)
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1

    if not video_files:
        extensions = ", ".join(sorted(VIDEO_EXTENSIONS))
        print(f"错误：{input_dir} 中没有支持的视频（{extensions}）。", file=sys.stderr)
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"找到 {len(video_files)} 个视频文件。")
    print(f"FFmpeg：{ffmpeg}")

    failures = 0
    for index, video_file in enumerate(video_files, start=1):
        audio_file = output_dir / f"{video_file.stem}.mp3"
        print(f"[{index}/{len(video_files)}] {video_file.name} -> {audio_file.name}")
        if audio_file.exists() and not args.overwrite:
            print("  已存在，跳过。")
            continue

        try:
            extract_audio(ffmpeg, video_file, audio_file, args.bitrate)
            print("  转换完成。")
        except subprocess.CalledProcessError as exc:
            failures += 1
            print(f"  转换失败（FFmpeg 退出码 {exc.returncode}）。", file=sys.stderr)
        except OSError as exc:
            failures += 1
            print(f"  转换失败：{exc}", file=sys.stderr)

    if failures:
        print(f"处理结束：{failures} 个文件失败。", file=sys.stderr)
        return 1

    print(f"处理完成，音频位于：{output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
