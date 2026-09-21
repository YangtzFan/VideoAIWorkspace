# VideoWorkspace

将 `videos` 目录中的视频批量提取为 `audios` 目录中的 MP3，再使用 faster-whisper 将音频转写为 `texts` 目录中的 UTF-8 文本。输入与输出保留相同的文件名，仅扩展名发生变化。

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
- Xmake 3.1 或更高版本
- 首次转写时可以访问 Hugging Face，以下载 Whisper 模型
- 可选：系统 FFmpeg。没有安装时，程序自动使用 `imageio-ffmpeg` 附带的版本
- 可选：支持 CUDA 的 NVIDIA 显卡及其驱动。程序默认优先使用 CUDA，CUDA 不可用时自动回退到 CPU

建议在项目根目录创建独立虚拟环境：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Windows 上如需使用 NVIDIA GPU，请继续安装项目测试过的 CUDA 12.8 运行库。该安装约需额外下载 568 MB，无需安装完整 CUDA Toolkit：

```powershell
python -m pip install -r requirements-gpu.txt
```

本机已将 Xmake 安装到 `D:\xmake` 并加入当前用户 `PATH`，同时设置 `XMAKE_GLOBALDIR=D:\xmake` 和 `XMAKE_TMPDIR=D:\xmake\tmp`，使 Xmake 的全局缓存和临时文件也保存在 D 盘。新终端可以直接运行 `xmake --version`；如果当前终端尚未刷新环境变量，可以使用 `D:\xmake\xmake.exe`。

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

首次运行第 3 步会下载默认的 `small` 模型，后续运行复用本机缓存。已有输出默认跳过；需要重新生成时给相应命令加 `--overwrite`。

中文音频可以固定语言以减少自动检测误差：

```powershell
python scripts\audio_to_txt.py --language zh
```

也可以通过 Xmake 执行各阶段或完整流程：

```powershell
xmake run extract-audio
xmake run transcribe
xmake run pipeline
```

Xmake 会优先使用项目 `.venv` 中的 Python，未找到虚拟环境时使用系统 `python`。

## 清理生成文件

运行以下命令可一键删除 `audios` 和 `texts` 中的生成文件、Python 缓存及 Xmake 构建产物：

```powershell
xmake clean
```

清理后会重新创建空的 `audios` 和 `texts` 目录。`videos` 目录及其中由用户放入的所有视频不会被删除，`.venv` 也会保留。

## 设备选择

默认的 `--device auto` 会优先使用 CUDA；没有检测到 CUDA 设备，或 CUDA 在模型加载、实际推理时不可用，程序会自动切换到 CPU 并重试。CPU 默认使用 `int8`，CUDA 默认使用 `float16`。

可以显式强制使用某种设备：

```powershell
python scripts\audio_to_txt.py --device cpu
python scripts\audio_to_txt.py --device cuda
```

显式指定 `--device cuda` 时不会自动回退，这适合检查 CUDA 环境配置是否正确。

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
├── requirements-gpu.txt
├── xmake.lua
└── README.md
```

## 更多用法

- [视频转音频脚本](docs/extract_audio.md)
- [音频转文字脚本](docs/audio_to_txt.md)

两个程序成功时退出码为 `0`。找不到输入、依赖缺失或任一文件处理失败时退出码为 `1`，因此可以直接用于批处理或自动化任务。

## 常见问题

**提示无法下载模型**

首次转写需要联网访问 Hugging Face。确认网络连接后重新运行；已经成功下载的模型会保存在 Hugging Face 的本机缓存中。

**CUDA 模式提示缺少 DLL**

Windows 用户运行 `python -m pip install -r requirements-gpu.txt` 即可安装项目测试过的 CUDA 12.8 cuBLAS 和 CUDA Runtime。CTranslate2 自带所需的 cuDNN 9，脚本会自动注册这些 DLL 的安装目录。NVIDIA 驱动必须支持 CUDA 12.8；可以通过 `nvidia-smi` 查看。使用默认的 `--device auto` 时，CUDA 仍然失败会自动回退到 CPU；使用显式的 `--device cuda` 时会报告错误并退出。

**输出文件没有更新**

程序为避免误覆盖而跳过已有文件。加入 `--overwrite` 即可重新生成。
