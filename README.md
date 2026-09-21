# VideoWorkspace

将 `videos` 目录中的视频批量提取为 `audios` 目录中的 MP3，再使用
faster-whisper 将音频转写为 `texts` 目录中的 UTF-8 文本。输入与输出保留相同的
文件名，仅扩展名发生变化。

```text
videos/001_xxx.mp4
        │ extract_audio.py
        ▼
audios/001_xxx.mp3
        │ audio_to_txt.py
        ▼
texts/001_xxx.txt
```

## 环境要求

- Python 3.9 或更高版本
- 首次转写时可以访问 Hugging Face，以下载 Whisper 模型
- 可选：系统 FFmpeg。没有安装时，程序自动使用 `imageio-ffmpeg` 附带的版本
- 可选：支持 CUDA 的 NVIDIA 环境。默认 CPU 模式无需显卡

建议在项目根目录创建独立虚拟环境：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 快速开始

1. 将视频放入 `videos`。支持 MP4、MOV、MKV、AVI、WebM 和 M4V。
2. 提取音频：

   ```powershell
   python scripts\extract_audio.py
   ```

3. 转写音频：

   ```powershell
   python scripts\audio_to_txt.py
   ```

首次运行第 3 步会下载默认的 `small` 模型，后续运行复用本机缓存。已有输出默认
跳过；需要重新生成时给相应命令加 `--overwrite`。

中文音频可以固定语言以减少自动检测误差：

```powershell
python scripts\audio_to_txt.py --language zh
```

## 目录结构

```text
VideoWorkspace/
├── videos/                 # 输入视频
├── audios/                 # 生成的 MP3
├── texts/                  # 生成的 TXT
├── scripts/
│   ├── extract_audio.py    # 视频转音频
│   └── audio_to_txt.py     # 音频转文字
├── docs/
│   ├── extract_audio.md
│   └── audio_to_txt.md
├── requirements.txt
└── README.md
```

## 更多用法

- [视频转音频脚本](docs/extract_audio.md)
- [音频转文字脚本](docs/audio_to_txt.md)

两个程序成功时退出码为 `0`。找不到输入、依赖缺失或任一文件处理失败时退出码为
`1`，因此可以直接用于批处理或自动化任务。

## 常见问题

**提示无法下载模型**

首次转写需要联网访问 Hugging Face。确认网络连接后重新运行；已经成功下载的模型
会保存在 Hugging Face 的本机缓存中。

**CUDA 模式提示缺少 DLL**

CUDA 推理还需要与当前 faster-whisper/CTranslate2 版本匹配的 CUDA 和 cuDNN 动态库。
可以先使用默认 CPU 模式完成工作，或在安装相应运行库后使用 `--device cuda`。

**输出文件没有更新**

程序为避免误覆盖而跳过已有文件。加入 `--overwrite` 即可重新生成。
