#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

'''
This program is to detect the face in movie with two_entity_file and keyword_search_result (detect in specific frame)
input: 1.movie_file (video format) 2. search_result_file

'''

import sys
import os
import re

import cv2
import cv2.cv as cv

from modules import json_io
from modules import csv_io
from modules import time_format
from modules import cv_image
from modules import cv_face

FRAME_INTERVAL = 12
EXPAND_TIME = 3
OUTPUT_PATH = 'output/'
roles_foldr = 'input/roles/'

def video_processing(movie_file, search_result_file, role_list_file):

    # load frame-keyword files
    keyword_search_result = csv_io.read_csv(search_result_file)
    role_list = csv_io.read_csv(role_list_file)

    # load video
    videoInput = cv2.VideoCapture(movie_file)

    frame = {}
    keyword_id = 0
    face_number = 0
    for row in keyword_search_result:

        start_frame, end_frame, keyword = float(row[0]), float(row[1]), row[2]
        frame_position = round(start_frame) - 24 * EXPAND_TIME
        finish_frame = round(end_frame) + 24 * EXPAND_TIME
        
        keyword_id += 1
        keyword_time = keyword + '_t' + str(keyword_id)
        while frame_position <= finish_frame: 
            videoInput.set(cv2.cv.CV_CAP_PROP_POS_FRAMES, frame_position)
            flag, img = videoInput.read()
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.equalizeHist(gray)
            face_position_list, rects = cv_image.face_detect(gray, frame_position, (40, 40))
            
            # Press ESC for close window 
            if 0xFF & cv2.waitKey(5) == 27:
                cv2.destroyAllWindows()
                sys.exit(1)
            
            if len(face_position_list) >= 1:
                print "detect face..."
                
                image_name = OUTPUT_PATH + 'img/' + keyword_time + str(face_number) 
                cv_image.output_image(rects, img, image_name)
              
                count = 0
                for face_position in face_position_list:
                    role_name = role_identify( image_name + '-' + str(face_number) \
                            + str(count) + '.jpg', role_list)
                    count += 1
                    face_number += 1
                    if not role_name:
                        continue
                    if keyword_time not in frame:
                        frame[keyword_time] = {}  
                    if role_name in frame[keyword_time]:
                        frame[keyword_time][role_name]['weight'] += 1
                    else:
                        frame[keyword_time][role_name] = {'keyword' : keyword, 
                                                          'face_position' : face_position.tolist(),
                                                          'frame_position' : frame_position,
                                                          'keyword_id' : keyword_id,
                                                          'weight' : 1 } 
            frame_position += FRAME_INTERVAL

    #close video  
    videoInput.release()

    json_io.write_json(OUTPUT_PATH + 'keywordt_roles.json', frame) 

def role_identify(img_name, role_list):
    pattern = re.compile(r'(\D+)\d?\.') 
    similarity_rate = {}
    for root, _, files in os.walk(roles_foldr):
        for f in files:
            img2_name = roles_foldr + f 
            rate = cv_face.reg(img_name, img2_name)
            print img2_name
            try:
                role = pattern.search(f).groups()[0]
            except:
                sys.exit(1)

            if role in similarity_rate:
                similarity_rate[role] += rate
            else:
                similarity_rate[role] = rate
    
    max_similarity_role = max(similarity_rate, key=similarity_rate.get)
    
    return max_similarity_role if similarity_rate[role] >= 1.5 else [] #raw_input('Name is ?') 
        

if __name__ == '__main__':
    video_processing(sys.argv[1], sys.argv[2], sys.argv[3])
