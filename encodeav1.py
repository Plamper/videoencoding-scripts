import os
import sys
import subprocess
from pymediainfo import MediaInfo
import queue
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging


def process_single_file(
    filename, ffmpeg_audio_options, ffmpeg_video_options, output_filename
):
    media_info = MediaInfo.parse(filename)

    # lsmash does not work with vc-1
    is_vc1 = media_info.video_tracks[0].format == "VC-1"

    av1an_args = [
        "av1an",
        "-x",
        "240",
        "-w",
        "12",
        "-e",
        "svt-av1",
        "-c",
        "mkvmerge",
        "--resume",
        # "--photon-noise",
        # "15",
        "--verbose",
        "--ffmpeg",
        ffmpeg_video_options,
        # "-vf crop=1920:800:0:140",
        "-a",
        # "-an",
        ffmpeg_audio_options,
        "-v",
        "--preset 4 --tune 3 --keyint 0 --enable-variance-boost 1 --variance-boost-strength 2 --variance-octile 6 --film-grain 5 --lp 2 --scd 0 --color-primaries 1 --transfer-characteristics 1 --matrix-coefficients 1",
    ]

    if is_vc1:
        av1an_args += ["-m", "ffms2"]
    else:
        av1an_args += ["-m", "lsmash"]

    av1an_args += ["-i", filename]

    av1an_args += ["-o", output_filename]

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


def get_bitrate(media_info: MediaInfo, track_id: int) -> int:
    channels = media_info.audio_tracks[track_id].channel_s
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
    en_track = find_relevant_audio_tracks(media_info, "en")
    de_track = find_relevant_audio_tracks(media_info, "de")

    options = ""

    if en_track:
        track_id = en_track[1]
        if en_track[0]:
            bitrate = get_bitrate(track_id)
            options += format_opus_string(track_id, bitrate)
        else:
            options += format_copy_string(track_id)

    if de_track:
        track_id = de_track[1]
        if de_track[0]:
            bitrate = get_bitrate(track_id)
            options += format_opus_string(track_id, bitrate)
        else:
            options += format_copy_string(track_id)
    return options


def process_queue(file_queue):
    while True:
        if not file_queue.empty():
            file_path = file_queue.get()
            process_single_file(file_path[0], "", "", file_path[1])
            file_queue.task_done()


class NewFileHandler(FileSystemEventHandler):
    def __init__(self, file_queue):
        self.file_queue = file_queue

    def on_created(self, event):
        if event.is_directory:
            return
        logging.info(f"New file detected: {event.src_path}")
        self.file_queue.put(event.src_path)


if len(sys.argv) != 3:
    print("Usage: python encodeav1.py inputfolder outputfolder")

logging.basicConfig(
    filename="encodeav1.log",
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
)

in_folder: str = sys.argv[1]
out_folder: str = sys.argv[2]

file_queue = queue.Queue()

logging.info("Searching for Files")
for file_name in os.listdir(in_folder):
    in_file_path = os.path.join(in_folder, file_name)
    logging.info(f"File detected: {in_file_path}")
    out_file_path = os.path.join(out_folder, file_name)
    if os.path.isfile(in_file_path):
        file_queue.put((in_file_path, out_file_path))

# Start processing thread
processing_thread = threading.Thread(
    target=process_queue, args=(file_queue,), daemon=True
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
