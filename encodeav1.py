import os
import subprocess
from pymediainfo import MediaInfo
import queue
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging
import re
import random


def process_single_file(filename, output_filename):
    media_info = MediaInfo.parse(filename)

    ffmpeg_audio_options = build_ffmpeg_options(media_info)

    ffmpeg_video_options = get_crop_parameters(filename, media_info)

    logging.info(f"Got video Options: {ffmpeg_video_options}")

    av1an_args = [
        "av1an",
        "-i",
        filename,
        "-o",
        output_filename,
        "-x",
        "240",
        "-w",
        "12",
        "--set-thread-affinity=2",
        "-e",
        "svt-av1",
        "-c",
        "mkvmerge",
        "--resume",
        "-m",
        "ffms2",
        # "--photon-noise",
        # "15",
        "--verbose",
        "--ffmpeg",
        ffmpeg_video_options,
        # "-vf crop=1920:800:0:140",
        "-a",
        # "-an",
        ffmpeg_audio_options,
        # --color-primaries 1 --transfer-characteristics 1 --matrix-coefficients 1 will force BT709
        "-v",
        "--preset 4 --crf 20  --variance-boost-strength 2 --variance-octile 6 --film-grain 5 --lp 2 --keyint 0 --scd 0 --input-depth 10 --color-primaries 1 --transfer-characteristics 1 --matrix-coefficients 1 ",
    ]

    av1an_process = subprocess.Popen(av1an_args)

    logging.info("Executing: {c}".format(c=av1an_args))
    av1an_process.wait()


def find_relevant_audio_tracks(mediainfo: MediaInfo, lang: str) -> tuple:
    tracks = [i for i in mediainfo.audio_tracks if i.language == lang]
    if not tracks:
        return
    lossless_tracks = [
        [i] for i in mediainfo.audio_tracks if i.compression_mode == "lossless"
    ]

    if not lossless_tracks:
        return (False, int(tracks[0].track_id))
    return (True, int(lossless_tracks[0].track_id))


def format_opus_string(track_id: int, bitrate: int) -> str:
    return '-c:a:{i} libopus -b:a:{i} {b}k -filter:a:{i} aformat=channel_layouts="7.1|5.1|stereo" '.format(
        i=track_id, b=bitrate
    )


def format_copy_string(track_id: int) -> str:
    return f"-c:a:{track_id} copy "


def get_bitrate(track) -> int:
    channels = track.channel_s
    match channels:
        case 2:
            return 128
        case 6:
            return 256
        case 7:  # I have only seen this in lotr
            return 320
        case 8:
            return 450
        case _:
            raise NotImplementedError("Bitrate for this format is not set")


def build_ffmpeg_options(media_info: MediaInfo) -> str:
    '''Build string of the form:
    -c:a:0 libopus -b:a:0 128k -filter:a:0 aformat=channel_layouts="7.1|5.1|stereo"'''
    # en_track = find_relevant_audio_tracks(media_info, "en")
    # de_track = find_relevant_audio_tracks(media_info, "de")

    options = ""

    pattern = r"atmos"

    track_id = 0
    for track in media_info.audio_tracks:
        # Do not reencode Atmos tracks as object Data is lost
        # Thanks Dolby!!!
        is_atmos = re.search(pattern, track.commercial_name, re.IGNORECASE)
        if track.compression_mode.lower() == "lossless" and not is_atmos:
            bitrate = get_bitrate(track)
            options += format_opus_string(track_id, bitrate)
        else:
            options += format_copy_string(track_id)
        track_id += 1

    return options


def get_video_duration(media_info):
    """
    Get the duration of the video in seconds using mediainfo.
    """

    duration = float(media_info.video_tracks[0].duration) / 1000
    logging.info(f"Video Duration is: {duration}")
    return duration


def get_crop_parameters_at_time(video_file, timestamp):
    """
    Find the crop parameters at a specific timestamp using ffmpeg's cropdetect filter.
    """
    # Run ffmpeg with the cropdetect filter at a specific timestamp
    command = [
        "ffmpeg",
        "-ss",
        str(timestamp),
        "-i",
        video_file,
        "-vf",
        "cropdetect=24:16:0",
        "-vframes",
        "3000",
        "-f",
        "null",
        "-",
    ]

    result = subprocess.run(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    output = result.stderr.decode("utf-8")

    # Find the last occurrence of the crop parameter in the output
    crop_params = None
    for line in output.split("\n"):
        if "crop=" in line:
            crop_params = line

    # Extract the crop parameters using regex
    if crop_params:
        match = re.search(r"crop=(\d+:\d+:\d+:\d+)", crop_params)
        if match:
            return match.group(1)

    return None


def get_crop_parameters(video_file, media_info, num_samples=5):
    """
    Get crop parameters by analyzing the video at multiple random timestamps.
    If no params are found or they vary an empty string is returned.
    """
    duration = get_video_duration(media_info)
    crop_params_list = []

    for _ in range(num_samples):
        timestamp = random.uniform(0, duration)
        crop_params = get_crop_parameters_at_time(video_file, timestamp)
        logging.info(f"Got Crop: {crop_params}")
        if crop_params:
            crop_params_list.append(crop_params)

    if not crop_params_list:
        return ""

    if all(x == crop_params_list[0] for x in crop_params_list):
        logging.info("All Crops are identical cropping Video")
        return f"crop={crop_params}"
    logging.info("Crops differ not cropping Video")
    return ""


def process_queue(file_queue, in_folder, out_folder):
    while True:
        if not file_queue.empty():
            file_path = file_queue.get()
            in_path = os.path.join(in_folder, file_path)
            out_path = os.path.join(out_folder, file_path)
            process_single_file(in_path, out_path)
            file_queue.task_done()


class NewFileHandler(FileSystemEventHandler):
    def __init__(self, file_queue):
        self.file_queue = file_queue

    def on_created(self, event):
        if event.is_directory:
            return
        file_name = os.path.basename(event.src_path)
        logging.info(f"New file detected: {file_name}")
        self.file_queue.put(file_name)


logging.basicConfig(
    filename="encodeav1.log",
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
)

in_folder: str = "in"
out_folder: str = "out"

file_queue = queue.Queue()

logging.info("Searching for Files")
for file_name in os.listdir(in_folder):
    if (
        os.path.isfile(os.path.join(in_folder, file_name))
        and not file_name == "put_input_files_here"
    ):
        logging.info(f"File detected: {file_name}")
        file_queue.put(file_name)


# Start processing thread
processing_thread = threading.Thread(
    target=process_queue, args=(file_queue, in_folder, out_folder), daemon=True
)
processing_thread.start()

# setup Observer
event_handler = NewFileHandler(file_queue)
observer = Observer()
observer.schedule(event_handler, in_folder, recursive=False)
observer.start()


try:
    observer.join()
except KeyboardInterrupt:
    observer.stop()

observer.join()
