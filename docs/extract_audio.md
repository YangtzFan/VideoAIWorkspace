# extract_audio.py 使用说明

`scripts/extract_audio.py` 批量读取一个目录中的视频，提取每个视频的第一条音轨，编码为 192 kbps MP3，并将结果写到输出目录。脚本可从任何工作目录启动，默认路径始终相对于项目根目录计算。

## 基本用法

在项目根目录运行：

```powershell
python scripts\extract_audio.py
```

默认读取 `videos`，写入 `audios`。支持 `.mp4`、`.mov`、`.mkv`、`.avi`、`.webm` 和 `.m4v`，扩展名匹配不区分大小写。

## 参数

```text
--input-dir PATH    视频输入目录
--output-dir PATH   MP3 输出目录
--bitrate VALUE     MP3 比特率，默认 192k
--overwrite         覆盖已有 MP3
-h, --help          显示帮助
```

示例：

```powershell
python scripts\extract_audio.py --input-dir D:\Videos --output-dir D:\Audio --bitrate 128k
python scripts\extract_audio.py --overwrite
```

## FFmpeg 查找顺序

1. 使用系统 `PATH` 中的 `ffmpeg`。
2. 使用 `imageio-ffmpeg` Python 包附带的 FFmpeg。

如果两者均不可用，请安装项目依赖：

```powershell
python -m pip install -r requirements.txt
```

## 输出和错误处理

输入 `videos/example.mp4` 会生成 `audios/example.mp3`。已有文件默认跳过。转换时先写入同目录临时文件，FFmpeg 成功退出后才替换正式输出，因此中断或失败不会留下看似完整的 MP3。任一输入失败时，程序继续处理其余文件，最后以退出码 `1` 结束。

如果视频没有音轨，FFmpeg 会报告无法匹配 `0:a:0`，该文件会记为失败。
