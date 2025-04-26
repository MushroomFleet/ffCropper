#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime

# Try to import ffmpeg-python as a fallback
try:
    import ffmpeg
    HAVE_FFMPEG_PYTHON = True
except ImportError:
    HAVE_FFMPEG_PYTHON = False

def parse_timestamp(timestamp):
    """Convert HHMMSS timestamp to seconds."""
    if not timestamp.isdigit() or len(timestamp) != 6:
        raise ValueError(f"Invalid timestamp: {timestamp}. Must be in HHMMSS format (6 digits)")
    
    hours = int(timestamp[0:2])
    minutes = int(timestamp[2:4])
    seconds = int(timestamp[4:6])
    
    if hours > 23 or minutes > 59 or seconds > 59:
        raise ValueError(f"Invalid time values in timestamp: {timestamp}")
    
    total_seconds = hours * 3600 + minutes * 60 + seconds
    return total_seconds

def format_output_filename(output_path, source_path):
    """Format the output filename with timestamp."""
    # Normalize path separators to OS-specific format
    output_path = os.path.normpath(output_path)
    
    if '[timestamp]' in output_path:
        # Add milliseconds to ensure uniqueness
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S%f')[:19]  # Include 3 digits of milliseconds
        output_path = output_path.replace('[timestamp]', timestamp)
    
    # Check if output path is a directory or ends with separator
    if os.path.isdir(output_path) or output_path.endswith(os.sep) or (output_path.endswith('/') or output_path.endswith('\\')):
        # Extract source filename components
        source_basename = os.path.basename(source_path)
        source_name, source_ext = os.path.splitext(source_basename)
        # Add milliseconds to ensure uniqueness
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S%f')[:19]  # Include 3 digits of milliseconds
        
        # Combine directory path with formatted filename
        output_path = os.path.join(output_path, f"{source_name}-{timestamp}{source_ext}")
    
    # Final normalization to ensure OS-compatible path
    output_path = os.path.normpath(output_path)
    print(f"Normalized output path: {output_path}")
    
    return output_path

def process_video(source, in_timestamp, out_timestamp, output):
    """Process a single video using ffmpeg."""
    # Check if source file exists
    if not os.path.exists(source):
        raise FileNotFoundError(f"Source file not found: {source}")
    
    try:
        in_seconds = parse_timestamp(in_timestamp)
    except ValueError as e:
        raise ValueError(f"Invalid IN timestamp: {e}")
    
    try:
        out_seconds = parse_timestamp(out_timestamp)
    except ValueError as e:
        raise ValueError(f"Invalid OUT timestamp: {e}")
    
    duration = out_seconds - in_seconds
    
    if duration <= 0:
        raise ValueError(f"OUT timestamp ({out_timestamp}) must be greater than IN timestamp ({in_timestamp})")
    
    # Format the output path
    output_path = format_output_filename(output, source)
    
    # Ensure the output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Check for ffmpeg installation before proceeding
    ffmpeg_available = False
    try:
        result = subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        ffmpeg_available = result.returncode == 0
    except Exception:
        ffmpeg_available = False
    
    if not ffmpeg_available and not HAVE_FFMPEG_PYTHON:
        print("\nERROR: FFMPEG is not installed or not in your system PATH.")
        print("Please install FFMPEG to use this script:")
        print("- Windows: Download from https://ffmpeg.org/download.html and add to PATH")
        print("- macOS: Use Homebrew: brew install ffmpeg")
        print("- Linux: Use your package manager, e.g., apt install ffmpeg\n")
        print("Alternatively, you can specify the path to the ffmpeg executable using --ffmpeg-path")
        return False
    
    # Create output directory
    output_dir = os.path.dirname(output_path)
    try:
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            print(f"Created output directory: {output_dir}")
    except Exception as e:
        print(f"Error creating output directory: {e}")
        return False
    
    # Try using system ffmpeg if available
    if ffmpeg_available:
        try:
            cmd = [
                'ffmpeg',
                '-i', source,
                '-ss', str(in_seconds),
                '-t', str(duration),
                '-c', 'copy',  # Copy stream without re-encoding for speed
                '-y',  # Overwrite output file if exists
                output_path
            ]
            
            print(f"Running command: {' '.join(cmd)}")
            subprocess.run(cmd, check=True)
            print(f"Successfully processed: {source} -> {output_path}")
            return True
        except subprocess.SubprocessError as e:
            print(f"Error processing with system ffmpeg: {e}")
            # Fall through to ffmpeg-python if available
    
    # Try ffmpeg-python if available
    if HAVE_FFMPEG_PYTHON:
        try:
            print(f"Trying ffmpeg-python library")
            
            # Debug output path
            print(f"Output path for ffmpeg-python: {output_path}")
            
            try:
                # Test if ffmpeg-python can actually run
                try:
                    print("Testing if ffmpeg-python can access ffmpeg...")
                    ffmpeg.probe(source)
                    print("ffmpeg-python can access ffmpeg")
                except Exception as test_error:
                    print(f"ffmpeg-python test failed: {test_error}")
                    print("ERROR: This suggests ffmpeg is not properly installed or not accessible.")
                    print("Please install FFMPEG as described above.")
                    return False
                
                (
                    ffmpeg
                    .input(source, ss=in_seconds)
                    .output(output_path, t=duration, c='copy')
                    .overwrite_output()
                    .run()
                )
                print(f"Successfully processed (using ffmpeg-python): {source} -> {output_path}")
                return True
            except Exception as fe:
                print(f"ffmpeg-python error: {fe}")
                return False
        except Exception as e:
            print(f"Error in ffmpeg-python processing: {e}")
            return False
    else:
        print("Error: Both system ffmpeg and ffmpeg-python are unavailable")
        return False

def process_batch(config_path):
    """Process multiple videos defined in a config file."""
    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        # Handle different config formats
        configs = []
        if isinstance(config_data, list):
            # Format is an array of config objects
            configs = config_data
        elif isinstance(config_data, dict):
            # Format might be a single config object
            if all(key in config_data for key in ['source', 'in', 'out', 'output']):
                configs = [config_data]
            else:
                # Format might be {config1: {...}, config2: {...}, ...}
                for key, value in config_data.items():
                    if isinstance(value, dict) and all(k in value for k in ['source', 'in', 'out', 'output']):
                        configs.append(value)
        
        if not configs:
            print("No valid configurations found in the config file")
            return False
        
        success_count = 0
        total_count = len(configs)
        
        print(f"Found {total_count} video(s) to process in config file")
        
        for i, config in enumerate(configs):
            print(f"\nProcessing video {i+1}/{total_count}")
            try:
                if not all(key in config for key in ['source', 'in', 'out', 'output']):
                    missing_keys = [key for key in ['source', 'in', 'out', 'output'] if key not in config]
                    print(f"Config #{i+1} is missing required parameters: {', '.join(missing_keys)}")
                    continue
                
                if process_video(
                    config['source'],
                    config['in'],
                    config['out'],
                    config['output']
                ):
                    success_count += 1
            except Exception as e:
                print(f"Error processing config #{i+1}: {e}")
        
        print(f"\nBatch processing summary: Successfully processed {success_count} out of {total_count} videos")
        return success_count > 0
    except json.JSONDecodeError as e:
        print(f"Error parsing config file: {e}")
        print("Make sure the config file is valid JSON")
        return False
    except Exception as e:
        print(f"Error reading config file: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Crop video using FFMPEG based on timestamps')
    
    # Create two mutually exclusive groups
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--config', help='Path to config.json for batch processing')
    group.add_argument('--source', help='Path to input video file')
    
    # Other arguments for single video processing
    parser.add_argument('--in', dest='in_timestamp', help='IN timestamp in HHMMSS format')
    parser.add_argument('--out', dest='out_timestamp', help='OUT timestamp in HHMMSS format')
    parser.add_argument('--output', help='Path for the output video, with optional [timestamp] placeholder')
    
    # Add explicit ffmpeg path option
    parser.add_argument('--ffmpeg-path', help='Path to ffmpeg executable, if not in system PATH')
    
    args = parser.parse_args()
    
    # Check if explicit ffmpeg path is provided
    ffmpeg_cmd = 'ffmpeg'
    if hasattr(args, 'ffmpeg_path') and args.ffmpeg_path:
        ffmpeg_cmd = args.ffmpeg_path
        print(f"Using provided ffmpeg path: {ffmpeg_cmd}")
    
    # Check if ffmpeg is available
    system_ffmpeg = False
    try:
        result = subprocess.run([ffmpeg_cmd, '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            print(f"Using system FFMPEG: {ffmpeg_cmd}")
            system_ffmpeg = True
        else:
            print(f"FFMPEG check returned non-zero code: {result.returncode}")
            print(f"STDERR: {result.stderr.decode('utf-8', errors='replace')}")
    except Exception as e:
        print(f"Error checking FFMPEG: {e}")
    
    if not system_ffmpeg:
        if HAVE_FFMPEG_PYTHON:
            print("System FFMPEG not found, using ffmpeg-python library")
            # Check if ffmpeg-python can actually run
            try:
                print("Testing ffmpeg-python...")
                ffmpeg.probe(r"C:\Projects\clip-project\qmSFWmA54IA.mp4")
                print("ffmpeg-python can access ffmpeg")
            except Exception as e:
                print(f"ffmpeg-python test failed: {e}")
                print("This suggests ffmpeg is not properly installed or not accessible to ffmpeg-python")
                print("\nIMPORTANT: FFMPEG IS REQUIRED TO USE THIS SCRIPT")
                print("Please install FFMPEG:")
                print("- Windows: Download from https://ffmpeg.org/download.html and add to PATH")
                print("- macOS: Use Homebrew: brew install ffmpeg")
                print("- Linux: Use your package manager, e.g., apt install ffmpeg")
                print("\nAfter installing, make sure the ffmpeg command is in your system PATH")
                print("or use the --ffmpeg-path argument to specify the location of the ffmpeg executable.")
                print("\nFor more information, visit: https://ffmpeg.org/download.html\n")
                return 1
        else:
            print("Error: FFMPEG is not installed and ffmpeg-python library is not available")
            return 1
    
    # Process based on arguments
    if args.config:
        print(f"Starting batch processing with config: {args.config}")
        if not os.path.exists(args.config):
            print(f"Error: Config file not found: {args.config}")
            return 1
        
        success = process_batch(args.config)
        if success:
            print("Batch processing completed successfully")
        else:
            print("Batch processing completed with errors")
        return 0 if success else 1
    else:
        print(f"Processing single video: {args.source}")
        # Check required arguments for single video processing
        if not args.in_timestamp:
            print("Error: --in is required when not using --config")
            return 1
        if not args.out_timestamp:
            print("Error: --out is required when not using --config")
            return 1
        if not args.output:
            print("Error: --output is required when not using --config")
            return 1
        
        # Process single video
        try:
            success = process_video(
                args.source,
                args.in_timestamp,
                args.out_timestamp,
                args.output
            )
            if success:
                print("Video processing completed successfully")
            else:
                print("Video processing completed with errors")
            return 0 if success else 1
        except Exception as e:
            print(f"Error: {e}")
            return 1

if __name__ == "__main__":
    sys.exit(main())
