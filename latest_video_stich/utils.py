import os
import pandas as pd
import numpy as np
import cv2 as cv
from dataclasses import dataclass
#from re import A
from datetime import datetime
#from settings import OPTIONS#,INPUT_DIR,OUTPUT_DIR
from settings import OPTIONS, WORKSPACE_DIR, INPUT_DIR, OUTPUT_DIR, SPLITS_DIR, SPLITS_COMBINED_DIR
from subprocess import check_output
from moviepy import editor
import json
import csv
import shutil

@dataclass
class MediaItemDetail:
    """Class for keeping track of input video scripts metadata."""
    source_script_name: str = None
    source_script_format: str = None
    start_end_time: list[list] = None
    cut_script_topic: list[str] = list
    cut_script_format: str = '.mp4'


class SourceMediaFile:
    ### client will read config file and create dict having keys as src filenames and value as dict containing split detail eg {topic1:[23,34],topic2:[23,34]}
    def __init__(self,src_file,split_detail):
        self.media_source = src_file
        self.split_metadata = split_detail

    def get_media_item_detail(self) -> MediaItemDetail:
        md = MediaItemDetail()
        md.source_script_name, md.source_script_format = os.path.splitext(self.media_source)
        md.cut_script_topic,md.start_end_time = [],[]
        for k,v in self.split_metadata.items():
            md.cut_script_topic.append(k) 
            md.start_end_time.append(v) 
        return md


class FFMPEG_Convert_Media(SourceMediaFile):
    def __init__(self,src_file,split_detail,out_sub_dir):
        super().__init__(src_file,split_detail)
        self.out_sub_dir = out_sub_dir
        self.vcodec = 'libx264'

    def get_convert_format_options(self):
        #convert_cmd_snippets = []
        md = self.get_media_item_detail()
        convert_cmd_snippets = [ OPTIONS['multimedia_framework'],OPTIONS['input_file']\
        ,os.path.join(WORKSPACE_DIR, INPUT_DIR,md.source_script_name+md.source_script_format)\
        ,"-c:v",self.vcodec,os.path.join(OUTPUT_DIR,self.out_sub_dir,md.source_script_name+md.cut_script_format)\
            ]
        #.append(OPTIONS['multimedia_framework'])#.append(OPTIONS['input_file'])
            # .append(OPTIONS['input_file'])\
            # .append(os.path.join(INPUT_DIR,md.source_script_name+md.source_script_format))\
            # .append("-c:v").append(self.vcodec).append(os.path.join(OUTPUT_DIR,md.source_script_name+md.cut_script_format))
        return convert_cmd_snippets
                 # ffmpeg -i youtube.flv -c:v libx264 filename.mp4
                #["ffmpeg", "-v", "quiet", "-i", file, file.replace(argv[1], argv[2])]
   
    def get_split_clips(self):
        split_cmd_snippets = []
        md = self.get_media_item_detail()
        for topic_start_end in zip(md.cut_script_topic,md.start_end_time):
            #split_cmd_snippets.append(i)
            split_cmd_snippet = [ OPTIONS['multimedia_framework'],\
                OPTIONS['clip_start_time'],topic_start_end[1][0],OPTIONS['clip_end_time'],topic_start_end[1][1],\
                OPTIONS['input_file'],os.path.join(WORKSPACE_DIR, INPUT_DIR,md.source_script_name+md.source_script_format),OPTIONS['copy'],"copy",\
                os.path.join(WORKSPACE_DIR, OUTPUT_DIR,self.out_sub_dir,topic_start_end[0]+md.source_script_format)   #md.cut_script_format
            ]
            split_cmd_snippets.append(split_cmd_snippet)
        return split_cmd_snippets


    ## Convert video from one format to another
    # ffmpeg -i youtube.flv -c:v libx264 filename.mp4
    ##  split
    # ffmpeg -ss 00:01:00 -to 00:02:00  -i input.mp4 -c copy output.mp4

    
class FFMPEG_Simple_Split(SourceMediaFile):
     # ffmpeg -ss 00:01:00 -to 00:02:00  -i input.mp4 -c copy output.mp4
     def convert_source_format(self):
        pass


## Check if file path exists or not
def check_path(path):
    return bool(os.path.exists(path))


## create dir at given path if not exists
def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

## Added to split multiple files at once
# Define the function to create a dictionary from a CSV file
def create_split_config_mapping_from_csv(file_path):
    result_dict = {}
    # Open the CSV file
    with open(file_path, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        # Skip the header row
        next(reader)
        # Iterate over each row in the CSV file
        for row in reader:
            # Use the first column as the key
            key = int(row[0].strip())
            # Concatenate the rest of the columns as the value
            value = '-'.join([i.strip() for i in row[2:]])
            # Add the key-value pair to the dictionary
            result_dict[key] = value
    return result_dict

###Move all splits into sigle output folder
def move_splits_in_single_dir(src_dirs, dst_dir):
    for src_dir in src_dirs:
        for root, _, files in os.walk(src_dir):
            for file in files:
                src_file_path = os.path.join(root, file)
                dst_file_path = os.path.join(dst_dir, file)
                shutil.copy2(src_file_path, dst_file_path)
                print(f"Moved: {src_file_path} to {dst_file_path}")

## Change the codecs of a file 
def change_file_codecs(path,filename):
    codec='libx264'
    in_file,ext = os.path.splitext(filename)
    out_file = in_file+'_converted'+'.mp4'
    clip = editor.VideoFileClip(os.path.join(path,filename))
    clip.write_videofile(os.path.join(path,out_file), codec=codec)

## Resize a video clip
def resize_file(path,filename,width,height):
    in_file,ext = os.path.splitext(filename)
    out_file = in_file+'_converted'+ext
    clip = editor.VideoFileClip(os.path.join(path,filename))
    clip_resized = clip.resize(width=width, height=height)
    clip_resized.write_videofile(os.path.join(path,out_file))

## Combine video files
def combine_files(comb_output_path,file_listings):
    now = datetime.now().strftime("%m_%d_%Y_%H%M%S")
    output_file = "output_"+now+".mp4"
    clips = []
    for i in file_listings:
        clips.append(editor.VideoFileClip(i))
    concat_file = editor.concatenate_videoclips(clips)
    concat_file.write_videofile(os.path.join(comb_output_path,output_file), codec = 'libx264')



### OPTIONS['encoder_opt'],OPTIONS['encoder'],OPTIONS['split_video_filetr'],OPTIONS['split_scale'],
def concatenate_split_files():
    combine_cmd_snippets = []
    #md = self.get_media_item_detail()
    #for topic_start_end in zip(md.cut_script_topic,md.start_end_time):
        #split_cmd_snippets.append(i)
    combine_cmd_snippets = [ OPTIONS['multimedia_framework'],\
            OPTIONS['format'],OPTIONS['concat'],'-segment_time_metadata','1',OPTIONS['abs_path_safe'],OPTIONS['zero'],\
            OPTIONS['input_file'],os.path.join(WORKSPACE_DIR, SPLITS_COMBINED_DIR,OPTIONS['combine_lst']),'-vf', 'select=concatdec_select',\
            #OPTIONS['copy'],'copy',\
            '-af', 'aselect=concatdec_select,aresample=async=1',\
            os.path.join(WORKSPACE_DIR, SPLITS_COMBINED_DIR,'output.mp4')   #md.cut_script_format
        ]
    #return combine_cmd_snippets
    #split_cmd_snippets.append(split_cmd_snippet)
    #ffmpeg -f concat -i file-list.txt -c copy output.mp4
    #return combine_cmd_snippets
    try:
        tmp = check_output(combine_cmd_snippets).decode()        
    except Exception as e:
        print("An error occured:\n" + str(e))


# def get_file_statistics(input_dir):
#     files_stat = {}
#     for media in os.listdir(input_dir):
#         file_metadata = []
#         video = cv.VideoCapture(os.path.join(input_dir,media))
#         duration = video.get(cv.CAP_PROP_POS_MSEC)
#         frame_count = video.get(cv.CAP_PROP_FRAME_COUNT)
#         file_metadata.append([duration,frame_count])
#         files_stat[media] = file_metadata
#     return files_stat

def get_file_statistics(input_dir):
    '''This utilizes ffprobe Linux OS utility to find statistics'''
    files_stat = {}
    media_lst = []
    duration_lst = []
    fps_lst = []
    size_lst = []
    codec_lst = []
    dimensions_lst = []
    aspect_ratio_lst = []
    for media in os.listdir(input_dir):
        result = check_output(f'ffprobe -v quiet -show_streams -select_streams v:0 -of json "{os.path.join(input_dir,media)}"',shell=True).decode()
        fields = json.loads(result)['streams'][0]
        format = os.path.splitext(os.path.join(input_dir,media))[1]
        if format.lower() in ('.mp4','.ts'):
            rpart, dpart = fields['duration'].split('.')[0],fields['duration'].split('.')[1]
            min, sec = divmod(int(rpart), 60)
            hour, min = divmod(min, 60)
            hour, min,sec = ['0'+str(i) if len(str(i))==1 else i for i in [hour,min,sec]]
            duration = str(hour)+':'+str(min)+':'+str(sec)+'.'+dpart
        else:
            duration = fields['tags'].get('DURATION','') 
        codec = fields['codec_name']
        dimensions = str(fields['width']) + 'x' + str(fields['height'])
        #aspect_ratio = fields['display_aspect_ratio']
        fps = eval(fields['r_frame_rate'])
        size = round(os.stat(os.path.join(input_dir,media)).st_size/(1024*1024),2)
        media_lst.append(media)
        duration_lst.append(duration)
        fps_lst.append(fps)
        size_lst.append(size)
        codec_lst.append(codec)
        dimensions_lst.append(dimensions)
        #aspect_ratio_lst.append(aspect_ratio)      
    files_stat['File_Name'] = media_lst
    files_stat['Duration'] = duration_lst
    files_stat['FPS'] = fps_lst
    files_stat['Size'] = size_lst
    files_stat['codec'] = codec_lst
    files_stat['dimensions'] = dimensions_lst
    #files_stat['aspect_ratio'] = aspect_ratio_lst
    return files_stat





def abc(source_target_files_map,out_sub_dir):
    #print(source_target_files_map)
    for k,v in source_target_files_map.items():
        x = FFMPEG_Convert_Media(k,v,out_sub_dir)
        #y = x.get_convert_format_options()
        #print(y)

        #################tmp = check_output(["mkdir",out_dir])
        stime=datetime.now()
        print("started:",stime)
        #try:
            #tmp = check_output(y).decode()        
        #except Exception as e:
            #print("An error occured:\n" + str(e))
    
        print("*"*40,"Run Stats","*"*40)
        print("started:",stime)
        print("ended:",datetime.now())
        #print(k,'---->',v)

        y = x.get_split_clips()
        for i in y:
            try:
                tmp = check_output(i).decode()        
            except Exception as e:
                print("An error occured:\n" + str(e))


## Intially used to read metadata from files
# with open(r'/home/skumarbehl/Desktop/MOCK_DATA1.csv','r') as media_file:
#     header = next(media_file)
#     prev_input_media = None
#     for line in media_file:
#         current_input_media, start_time, end_time, output = line.strip('\n').split(',')
#         if current_input_media != prev_input_media:
#             output_files = {}
#             output_files[output] = [start_time,end_time]
#             source_target_files_map[current_input_media] = output_files   ### need to think
#         else:
#             source_target_files_map[current_input_media][output] = [start_time,end_time]
#         prev_input_media=current_input_media

def create_split_file_list(combine_dir,split_input_dir,file_list_as_per_order):
    with open(os.path.join(combine_dir,'mylist.txt'),'w') as concat_file_list:
        for item in file_list_as_per_order:
            concat_file_list.write('file '+"'"+os.path.join(split_input_dir,item)+"'"+'\n')