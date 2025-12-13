import os
#OUTPUT_DIR_NAME=os.
OPTIONS={
    "multimedia_framework":"ffmpeg",
    "input_file": "-i",
    "clip_start_time": "-ss",
    "clip_end_time": "-to",
    "copy":"-c",
    "concat": "concat",
    "combine_lst":"mylist.txt",
    "format": "-f",
    "abs_path_safe":"-safe",
    "zero": "0",
    "split_video_filetr":"-vf",
    "split_scale" : "scale=1920:1080",
    "encoder_opt": "-c:v",
    "encoder": "libvpx"
}

WORKSPACE_DIR = r"/home/skumarbehl/Desktop/workspace"
SPLIT_FILE_LIST_DIR = "split_config"
INPUT_DIR = "input_media"
OUTPUT_DIR = "output_media"
SPLITS_DIR = "all_split_media"
SPLITS_COMBINED_DIR = "combined_splits_output_media"
SPLITS_SINGLE_OUT_DIR = "output_media_final"


### Split Map
##split_string = input("\nNote:   
##Please provide split duration ( format -> hh:mm:ss.ms-hh:mm:ss.ms )\n\teg. 00:10:45.2-00:15:35.5  
##( Here milliseconds(.ms) part is optional - Required for more precise cuts )\n\nEnter Duration ### ")
'''sno_split_period_map = {
    0: "00:00:08-00:10:06",
    1: "00:00:15-00:06:37",
    2: "",
    3: "",
    4: "",
    5: "",
    6: "",
    7: "",
    8: "",
    9: "",
    10: ""
}'''