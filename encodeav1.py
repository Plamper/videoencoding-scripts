import os
import sys
import subprocess
from pymediainfo import MediaInfo


def process_single_file(filename):
    media_info = MediaInfo.parse(filename)

    # lsmash does not work with vc-1
    is_vc1 = media_info.video_tracks[0].format == "VC-1"

    av1an_args = [
        "-x"
        "240"
        "-e"
        "svt-av1"
        "-c"
        "mkvmerge"
        "--resume"
        "--photon-noise"
        "5"
        "--verbose"
        "-a"
        " '-an' "
        "-v"
        "\""
        "--preset"
        "5"
        "--crf"
        "20"
        "--tune"
        "3"
        "--input-depth"
        "10"
        "--lookahead"
        "120"
        "--keyint"
        "-1"
        "--enable-qm"
        "1"
        "--qm-min"
        "0"
        "\""
    ]

    if is_vc1:
        av1an_args += ["-m", "ffms2"]
    else:
        av1an_args += ["-m", "lsmash"]

    av1an_args += ["-i", filename]

    av1an_args += ["-o"
                   "Baum.mkv"]

    av1an_process = subprocess.Popen()

    print("Executing: av1an {c}".format(c=av1an_args))
    print(av1an_process.stdout)
    print(av1an_process.stderr)


def encode_stream_in_opus(infile, outfile, index):
    mediainfo = MediaInfo.parse(infile)
    bitdepth = mediainfo.tracks[index + 1].bit_depth
    print(bitdepth)
    bit = "pcm_s16le"
    if bitdepth == 24:
        bit = "pcm_s24le"

    ffmpeg_process = subprocess.Popen([
        'ffmpeg', '-i', infile, '-map', '0:{c}'.format(c=index), '-c:a', bit,
        "-f", "wav", '-'
    ],
                                      stdout=subprocess.PIPE)
    opusenc_process = subprocess.Popen(['opusenc', '-', outfile],
                                       stdin=ffmpeg_process.stdout)
    # Wait for finish
    return opusenc_process


def find_relevant_audio_channel(mediainfo: MediaInfo, lang: str):
    tracks = filter(lambda a: a.language == lang, mediainfo.audio_tracks)
    if not tracks:
        return
    lossless_tracks = filter(lambda a: a.compression_mode == "Lossless", tracks)
    if not lossless_tracks:
        return tracks[0]
    return lossless_tracks[0]


if len(sys.argv) != 3:
    print("Usage: python encodeav1.py inputfolder outputfolder")

for f in os.listdir(sys.argv[1]):
    if f.endswith(".mkv"):
        # encode_stream_in_opus(f, "test.opus", 1)
        info = MediaInfo.parse(f)
        find_relevant_audio_channel(info, "German")
