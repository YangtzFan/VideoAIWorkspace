import subprocess
from pathlib import Path


# ============================================================
# 路径配置
# ============================================================

# 当前脚本所在目录：xxx/scripts/
SCRIPT_DIR = Path(__file__).resolve().parent

# 项目根目录：xxx/
BASE_DIR = SCRIPT_DIR.parent

# 视频目录
VIDEO_DIR = BASE_DIR / "videos"

# 音频目录
AUDIO_DIR = BASE_DIR / "audios"


# ============================================================
# 创建输出目录
# ============================================================

AUDIO_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 查找视频文件
# ============================================================

# 只处理文件名以 001、002、003…… 开头的 MP4 文件
video_files = sorted([
    file
    for file in VIDEO_DIR.glob("*.mp4")
    if file.stem[:3].isdigit()
])


if not video_files:
    print(f"在目录中没有找到符合要求的 MP4 文件：")
    print(VIDEO_DIR)
    exit(0)


print(f"找到 {len(video_files)} 个视频文件。\n")


# ============================================================
# MP4 → MP3
# ============================================================

for video_file in video_files:

    # 输出文件名与输入文件名相同，只修改扩展名
    audio_file = AUDIO_DIR / f"{video_file.stem}.mp3"

    print("=" * 60)
    print(f"输入：{video_file.name}")
    print(f"输出：{audio_file.name}")

    # 如果 MP3 已经存在，则跳过
    if audio_file.exists():
        print("该文件已经存在，跳过。")
        continue

    command = [
        "ffmpeg",

        # 输入视频
        "-i", str(video_file),

        # 不处理视频，只提取音频
        "-vn",

        # 使用 MP3 编码器
        "-codec:a", "libmp3lame",

        # MP3 比特率
        "-b:a", "192k",

        # 输出文件
        str(audio_file)
    ]

    try:
        subprocess.run(
            command,
            check=True
        )

        print("转换完成！")

    except subprocess.CalledProcessError:
        print("转换失败！")


print("\n" + "=" * 60)
print("全部处理完成！")
print(f"MP3 文件保存位置：{AUDIO_DIR}")
