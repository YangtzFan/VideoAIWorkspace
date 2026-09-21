# audio_to_txt.py 使用说明

`scripts/audio_to_txt.py` 使用 faster-whisper 批量转写音频。它默认加载多语言
`small` 模型，在 CPU 上以 `int8` 精度运行，并通过语音活动检测过滤长静音。

## 基本用法

在项目根目录运行：

```powershell
python scripts\audio_to_txt.py
```

默认读取 `audios`，将 UTF-8 TXT 写入 `texts`。支持 `.mp3`、`.wav`、`.m4a`、
`.flac`、`.ogg`、`.opus` 和 `.aac`。

首次使用某个模型时会从 Hugging Face 下载文件。下载完成后，后续运行使用本机
缓存。默认 `small` 模型在速度和准确率之间较均衡；模型越大，通常越准确，也越慢、
占用更多内存。

## 参数

```text
--input-dir PATH       音频输入目录
--output-dir PATH      TXT 输出目录
--model NAME_OR_PATH   模型名称或本地模型目录，默认 small
--language CODE        zh、en 等语言代码；默认 auto
--device cpu|cuda      推理设备，默认 cpu
--compute-type TYPE    计算精度；CPU 默认 int8，CUDA 默认 float16
--overwrite            覆盖已有 TXT
-h, --help             显示帮助
```

常用示例：

```powershell
# 固定中文并覆盖旧结果
python scripts\audio_to_txt.py --language zh --overwrite

# 使用更快、更省内存但准确率较低的模型
python scripts\audio_to_txt.py --model base

# 使用本地模型，适合离线环境
python scripts\audio_to_txt.py --model D:\Models\faster-whisper-small

# 在已经正确安装 CUDA 和 cuDNN 运行库的机器上使用显卡
python scripts\audio_to_txt.py --device cuda
```

## 输出格式和错误处理

每个识别片段占一行，文件使用 UTF-8 编码。例如 `audios/example.mp3` 生成
`texts/example.txt`。脚本先写临时文件，转写成功后才替换正式输出；已有文本默认
跳过。单个音频失败不会阻止后续音频处理，但最终退出码为 `1`。

## GPU 说明

检测到 NVIDIA 显卡并不代表 CUDA 推理环境已经完整。faster-whisper 使用
CTranslate2，CUDA 模式需要相匹配的 NVIDIA 驱动、CUDA 和 cuDNN 动态库。如果出现
缺少 `cublas` 或 `cudnn` DLL 的错误，请安装匹配版本的运行库，或去掉
`--device cuda`，使用默认 CPU 模式。
