"""
The script expects a file named "config.json" in the parent directory of the root.
The config file should specify the locations of the ffmpeg installation, the directory where the source videos are,
the directory where the modified videos are placed, etc:
{
  "ffmpeg_dir": "D:\\ffmpeg_dir",
  "source_dir": "D:\\videos\\source",
  "target_dir": "D:\\videos\\target",
  "file_extension_filter" : "mkv"
}

"""
import json
import os
import subprocess
from pathlib import Path


def load_json_from_file(file_path: Path):
    # Check if the file exists
    if not file_path.exists():
        raise FileNotFoundError(f"File '{file_path}' does not exist.")

    # Read the contents of the file
    with open(file_path, 'r') as file:
        # Load JSON contents from the file
        json_data = json.load(file)

    return json_data


CONFIG = load_json_from_file(Path(os.getcwd()).parent / "config.json")

FFMPEG_DIR = CONFIG["ffmpeg_dir"]
VIDEO_SOURCE_DIR = CONFIG["source_dir"]
VIDEO_TARGET_DIR = CONFIG["target_dir"]
FILE_EXTENSION = CONFIG["file_extension_filter"]

ENV_PATH = FFMPEG_DIR + os.pathsep + os.environ['PATH']

SOURCE_PATH = Path(VIDEO_SOURCE_DIR)
TARGET_PATH = Path(VIDEO_TARGET_DIR)

# Outputs the stream data of the input video file
FFMPEG_INSPECT_COMMAND_HEAD = ['ffprobe', '-v', 'error', '-show_entries', 'stream=index,codec_type:stream_tags=language', '-of', 'json']
FFMPEG_REMOVE_HUN_AUDIO_COMMAND_P1 = ['ffmpeg', '-i'] # The root of the commands
FFMPEG_REMOVE_HUN_AUDIO_COMMAND_P2 = [  # Command arguments - these are appended after the input video file name
    '-map', '0:v',  # Selects all video streams
    '-map', '0:s',  # Selects all subtitle streams
    '-map', '-0:a:0',  # Selects the first audio stream to be excluded
    '-map', '0:a:1',  # Selects the first audio stream to be included
    '-c:v', 'copy',  # Copies the selected video streams
    '-c:a', 'copy',  # Copies the selected audio streams
    '-c:s', 'copy']  # Copies the selected subtitle streams


def get_video_files_from_path(dir_path: Path, extension: str = FILE_EXTENSION):
    return [dir_path / file for file in dir_path.iterdir() if file.suffix.lower() == f'.{extension}']


def remove_hun_audio_from_files(video_files: list[Path], target_dir: Path):
    """
    Invokes ffmpeg to remove the 1st audio stream from the video files
    :param video_files:  the video files
    :param target_dir: the directory to which they are copied
    """
    for video_file in video_files:
        output_file_path = str(target_dir / video_file.parts[-1])
        command = FFMPEG_REMOVE_HUN_AUDIO_COMMAND_P1[:] + [str(video_file)] + FFMPEG_REMOVE_HUN_AUDIO_COMMAND_P2[:] + [output_file_path]
        print(f"Removing HUN audio from video {video_file.name}")
        print(f"Command arguments: {command}")
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Process failed with this error message:\n{result.stderr}")
            raise RuntimeError
        print(f"Removed HUN audio from video {video_file.name}")


def get_file_data_list_raw(video_files: list[Path]) -> list[str]:
    """
    Invokes ffprobe for each file. See get_file_data().
    :param video_files: the list of video files to process
    :return: the raw json string data produced by ffprobe in a list
    """
    return [get_file_data(file) for file in video_files]


def get_file_data(video_file: Path) -> str:
    """
    Invokes ffprobe to output info about the streams in the video_file.
    The streams our printed into the standard output of the process in json format.
    :param video_file: the video file
    :return: the outputted json
    """
    ffprobe_command = FFMPEG_INSPECT_COMMAND_HEAD[:] + [str(video_file)]
    result = subprocess.run(ffprobe_command, capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout
    else:
        return ""


def get_processed_data(raw_data: list[str]):
    """
    Converts the json video data produced by ffprobe to python objects.
    :param raw_data: raw json like string data for the video files
    :return: python objects
    """
    return[json.loads(data) for data in raw_data]


def print_file_data_raw(video_files: list[Path]):
    for video_file in video_files:
        ffprobe_command = FFMPEG_INSPECT_COMMAND_HEAD[:] + [str(video_file)]
        result = subprocess.run(ffprobe_command, capture_output=True, text=True)
        if result.returncode == 0:
            print(result.stdout)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # The PATH environment variable is prepended with the ffmpeg bin directory so that the invoked subprocesses find it
    os.environ['PATH'] = ENV_PATH

    # Creates a filtered list of ".mkv" file from the files in the source directory
    video_source_files = get_video_files_from_path(SOURCE_PATH)

    # Print ffmpeg data for debugging reasons
    # for d in get_processed_data(get_file_data_list_raw(video_source_files)):
    #     print(d)

    # This executes the command that removes certain streams from the videos in the source dir and creates the altered
    # videos in the target dir
    remove_hun_audio_from_files(video_source_files, TARGET_PATH)



