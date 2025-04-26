# ffCropper

A powerful Python utility for cropping video files based on timestamps using FFmpeg.

## Overview

ffCropper is a command-line tool that allows you to extract specific segments from video files by defining "in" and "out" points using a simple HHMMSS timestamp format. It supports both single video processing and batch operations through a JSON configuration file.

The tool uses system FFmpeg for processing when available and falls back to the Python FFmpeg library if needed, ensuring compatibility across different environments.

## Features

- **Simple Timestamp Format**: Define video segments using easy-to-understand HHMMSS format (hours, minutes, seconds)
- **Dual Operation Modes**:
  - Single video mode with command-line parameters
  - Batch processing using JSON configuration
- **Smart Output Naming**:
  - Automatic timestamp insertion in filenames
  - Creates output directories if they don't exist
- **FFmpeg Integration**:
  - Primarily uses system FFmpeg for optimal performance
  - Falls back to Python FFmpeg library if system FFmpeg is unavailable
- **Robust Error Handling**: Detailed feedback and error reporting during processing

## Requirements

- Python 3.6 or higher
- FFmpeg installed on your system (recommended)
- Optional: ffmpeg-python library (as fallback)

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/ffCropper.git
   cd ffCropper
   ```

2. Install required dependencies:
   ```bash
   pip install ffmpeg-python
   ```

3. Ensure FFmpeg is installed on your system (recommended for better performance):
   - **Ubuntu/Debian**:
     ```bash
     sudo apt update
     sudo apt install ffmpeg
     ```
   - **macOS** (using Homebrew):
     ```bash
     brew install ffmpeg
     ```
   - **Windows**:
     Download from [FFmpeg official website](https://ffmpeg.org/download.html) and add to your PATH

## Usage

### Single Video Processing

```bash
python ffCropper.py --source "path/to/video.mp4" --in HHMMSS --out HHMMSS --output "path/to/output.mp4"
```

Parameters:
- `--source`: Path to the input video file
- `--in`: Starting timestamp in HHMMSS format (e.g., 000130 for 1 minute and 30 seconds)
- `--out`: Ending timestamp in HHMMSS format
- `--output`: Path for the output video file (can include a [timestamp] placeholder)

### Batch Processing

```bash
python ffCropper.py --config "path/to/config.json"
```

Parameters:
- `--config`: Path to a JSON configuration file containing multiple video processing tasks

## Step-by-Step Examples

### Example 1: Trim a Single Video

Let's say you have a video file `lecture.mp4` that's 1 hour long and you want to extract a segment from the 10-minute mark to the 15-minute mark:

1. Prepare your command:
   ```bash
   python ffCropper.py --source "lecture.mp4" --in 001000 --out 001500 --output "lecture-segment-[timestamp].mp4"
   ```

2. Execute the command. The tool will:
   - Validate the timestamps
   - Calculate the duration (5 minutes)
   - Replace [timestamp] with the current date/time
   - Process the video using FFmpeg
   - Output a new file named something like `lecture-segment-20230415_123045.mp4`

### Example 2: Batch Process Multiple Videos

1. Create a file named `batch_config.json` with the following content:
   ```json
   [
     {
       "source": "lecture1.mp4",
       "in": "000500",
       "out": "001000",
       "output": "outputs/lecture1-intro-[timestamp].mp4"
     },
     {
       "source": "lecture2.mp4",
       "in": "002000",
       "out": "002500",
       "output": "outputs/lecture2-summary-[timestamp].mp4"
     },
     {
       "source": "interview.mp4",
       "in": "001500",
       "out": "003000",
       "output": "outputs/interview-highlights-[timestamp].mp4"
     }
   ]
   ```

2. Run the batch processing command:
   ```bash
   python ffCropper.py --config "batch_config.json"
   ```

3. The tool will:
   - Process each video sequentially
   - Create the `outputs` directory if it doesn't exist
   - Extract each segment with proper naming
   - Provide feedback on each operation

### Example 3: Using a Directory as Output

If you specify a directory as the output path, ffCropper will automatically generate filenames based on the source:

```bash
python ffCropper.py --source "presentation.mp4" --in 000000 --out 003000 --output "segments/"
```

This will create a file like `segments/presentation-20230415_124530.mp4`

## JSON Configuration Format

The configuration file can use any of the following formats:

### Array of Objects (Recommended)

```json
[
  {
    "source": "video1.mp4",
    "in": "000100",
    "out": "000200",
    "output": "output/video1-trimmed.mp4"
  },
  {
    "source": "video2.mp4",
    "in": "000030",
    "out": "000130",
    "output": "output/video2-trimmed.mp4"
  }
]
```

### Single Object

```json
{
  "source": "video1.mp4",
  "in": "000100",
  "out": "000200",
  "output": "output/video1-trimmed.mp4"
}
```

### Named Objects

```json
{
  "task1": {
    "source": "video1.mp4",
    "in": "000100",
    "out": "000200",
    "output": "output/video1-trimmed.mp4"
  },
  "task2": {
    "source": "video2.mp4",
    "in": "000030",
    "out": "000130",
    "output": "output/video2-trimmed.mp4"
  }
}
```

## Troubleshooting

### FFmpeg Not Found

If you get an error that FFmpeg is not found:

1. Make sure FFmpeg is installed on your system
2. Ensure FFmpeg is in your PATH environment variable
3. Install the ffmpeg-python library as a fallback:
   ```bash
   pip install ffmpeg-python
   ```

### Invalid Timestamp Format

Timestamps must be exactly 6 digits in HHMMSS format:
- **Correct**: 001530 (15 minutes, 30 seconds)
- **Incorrect**: 1530 (missing leading zeros)

### OUT Timestamp Before IN Timestamp

The OUT timestamp must represent a later point in the video than the IN timestamp. Check your timestamp values if you get this error.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

Created by [Your Name]

---

If you find ffCropper useful, please consider giving it a star on GitHub!