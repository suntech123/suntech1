from genericpath import isdir
import os
import pandas as pd
import numpy as np
import cv2 as cv
import platform
import subprocess
import argparse
import logging
from subprocess import check_output
from datetime import datetime
from sys import argv
from pathlib import Path
import logging
import json
from settings import WORKSPACE_DIR, INPUT_DIR, OUTPUT_DIR, SPLITS_DIR, SPLITS_COMBINED_DIR, SPLIT_FILE_LIST_DIR, SPLITS_SINGLE_OUT_DIR
import utils
from tabulate import tabulate
import re
#################################################################################################################################################


if __name__=='__main__':
    #print("What are you going to perform - Split(0)/Combine(1)? : ")
    while True:
        sc_opt = input("What are you going to perform:\n\n[0] Split\n[1] Combine\n[Enter] Exit\n\nSelect Given Options: ")
        if sc_opt.strip() == '0':
            ## commented this path-20240527
            #source_target_files_map = {}
            input_path = os.path.join(WORKSPACE_DIR, INPUT_DIR)
            if not utils.check_path(input_path):
                utils.create_directory(input_path)
            if os.path.isdir(input_path):
                output_path = os.path.join(WORKSPACE_DIR, OUTPUT_DIR)
            if not utils.check_path(output_path):
                utils.create_directory(output_path)
            output_path_final = os.path.join(WORKSPACE_DIR, OUTPUT_DIR, SPLITS_SINGLE_OUT_DIR)
            if not utils.check_path(output_path_final):
                utils.create_directory(output_path_final)
            xyz = utils.get_file_statistics(input_path)
            df = pd.DataFrame(xyz)
            sc_opt1 = input("What are you going to perform in Split:\n\n[00] Generate Split Config File Only\n[11] Split Config File to Splits\n\nSelect Given Options: ")
            if sc_opt1.strip() == '00':
                # Reset index and rename the index column to 'sno'
                df_reset = df.reset_index(drop=False).rename(columns={'index': 'sno', 'File_Name': 'file_name'})
                df_reset['start'] = ''
                df_reset['end'] = ''
                sel_cols = [c for c in df_reset.columns if c not in ['Duration', 'FPS', 'Size', 'codec', 'dimensions']]
                df_reset = df_reset[sel_cols]
                print(tabulate(df, headers='keys', tablefmt='psql'))
                print("Split File Generated at Below Location\n")
                print(os.path.join(WORKSPACE_DIR, SPLIT_FILE_LIST_DIR))
                df_reset.to_csv(os.path.join(WORKSPACE_DIR, SPLIT_FILE_LIST_DIR, "split_config.csv"), index=False)
                break
            elif sc_opt1.strip() == '11':
                sno_split_period_map = utils.create_split_config_mapping_from_csv(os.path.join(WORKSPACE_DIR, SPLIT_FILE_LIST_DIR, "split_config.csv"))
                output_sub_dir_lst = []
                #print(sno_split_period_map)
                #break
            else:
                break
            
            ### check setting sno_split_period_map key for this
            ##sno = input('\nWhich file(by serial number) you want to split? : ')
            for sno, split_string in sno_split_period_map.items():
                source_target_files_map = {}
                selected_file_df = df.iloc[[sno]]
                selected_file = selected_file_df.iloc[0]['File_Name']
                selected_file_ext = os.path.splitext(selected_file)[1]
                selected_file_compact = re.sub(' +', '_', os.path.splitext(selected_file)[0])
                print("\nYou have selected below file for processing\n")
                print(tabulate(selected_file_df.T, headers='firstrow', tablefmt='plain'))
                if split_string.strip() == "":
                    break
                split_list = [st.strip() for st in split_string.split(',')]
                #print(split_list)
                #break             
                output_files = {}
                output_start_end = []
                for out_split in split_list:
                    #print(selected_file_compact)
                    output = '__'.join(out_split.split('-')).replace(':','_')
                    ##output_files['output_'+output] = out_split.split('-')  ###commented on 2023-08-13 and added line below it to get filename in output dir
                    output_files[selected_file_compact+'_'+output] = out_split.split('-')
                #print(output_files)
                #break
                source_target_files_map[selected_file] = output_files
                #print(source_target_files_map)
                #break
                df1 = pd.DataFrame(output_files)
                print(tabulate(df1.T, headers='firstrow', tablefmt='plain'))
                OUTPUT_SUB_DIR = selected_file_compact
                OUTPUT_SUB_DIR_PATH = os.path.join(WORKSPACE_DIR, OUTPUT_DIR, OUTPUT_SUB_DIR)
                #print("OUTPUT_SUB_DIR:", OUTPUT_SUB_DIR)
                #print("OUTPUT_SUB_DIR_PATH:", OUTPUT_SUB_DIR_PATH)
                #break
                if not utils.check_path(OUTPUT_SUB_DIR_PATH):
                    utils.create_directory(OUTPUT_SUB_DIR_PATH)
                    output_sub_dir_lst.append(OUTPUT_SUB_DIR_PATH)
                utils.abc(source_target_files_map,OUTPUT_SUB_DIR)
            utils.move_splits_in_single_dir(output_sub_dir_lst, output_path_final)
        elif sc_opt.strip() == '1':
            #print("Here we are going to combine")
            selected_file_lst = []
            split_input_path = os.path.join(WORKSPACE_DIR, SPLITS_DIR)
            split_combined_path = os.path.join(WORKSPACE_DIR, SPLITS_COMBINED_DIR)
            if not utils.check_path(split_input_path):
                utils.create_directory(split_input_path)
            if not utils.check_path(split_combined_path):
                utils.create_directory(split_combined_path)
            xyz1 = utils.get_file_statistics(split_input_path)
            #print(xyz1)
            df_splits = pd.DataFrame(xyz1)
            ##Added to assist in getting combine order
            df_splits_copy = df_splits.copy()
            df_splits_copy['File_Name_SrNo'] = df_splits_copy['File_Name'].str.split('_', n=1).apply(lambda x: x[0])
            final_df = df_splits_copy.sort_values(by='File_Name_SrNo')
            actual_combine_order = list(final_df.index)
            ####
            print(tabulate(df_splits, headers='keys', tablefmt='psql'))
            ####display actual combine order
            print(actual_combine_order)
            ## Here provide the serial numbers of files to convert codecs to default()
            dim_conv_flag = input("Do you want to convert dimensions (Yes-1/No-0): ")
            if dim_conv_flag == '1':
                sno_order_conversion = input('\nPlease provide order as per serial number for file conversion(eg. 2 wxh,1 wxh,3 wxh,0 wxh) : ')
                sno_order_conversion1 = [ i.strip() for i in sno_order_conversion.split(',') ]
                for s in sno_order_conversion1:
                    sno,wh = s.split()
                    w,h = wh.split('x')
                    #print(df_splits.iat[int(sno),0],w,h)
                    utils.resize_file(split_input_path,df_splits.iat[int(sno),0],int(w),int(h))
            else:
                pass


            # file_list_to_convert = {}
            # for i in sno_order_conversion1:
            #     utils.change_file_codecs(split_input_path,df_splits.iat[i,0])
                #print(os.path.splitext(df_splits.iat[i,0])[0])

            sno_custom_order = input('\nPlease provide order as per serial number for file concatenation(eg. 2,1,3,0) : ')
            sno_custom_order1 = [int(i.strip()) for i in sno_custom_order.split(',')]
            selected_file_df1 = df_splits.iloc[sno_custom_order1]
            print(tabulate(selected_file_df1, headers='keys', tablefmt='psql'))

            for i in sno_custom_order1:
                selected_file_lst.append(os.path.join(split_input_path, df_splits.iloc[i]['File_Name']))
                      #print(selected_file_lst)
            #utils.create_split_file_list(split_combined_path,split_input_path,selected_file_lst)
                      #combine_cmd_snippets = 
            #print(selected_file_lst)
            utils.combine_files(split_combined_path,selected_file_lst)
                      #print(combine_cmd_snippets)
        else:
            print("Thank you for your visit")
            break

            
    