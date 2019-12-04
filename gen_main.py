#!usr/bin/env python
import os
import shutil
from config_gen import *
from model_gen import *
from world_gen import *
from subprocess import call
import time
import cv2
from random import randint
from MengeFileGenerator import menge_generator
import xml.etree.ElementTree as et
import argparse

def modelFolderGenerator(heightmap, scene_name):

    #Creating our auto generated terrain model directory
    os.chdir(os.path.expanduser("~/.gazebo/models/"))
    path = os.getcwd()
    items = os.listdir(path)

    for item in items:
        if scene_name == item:
            shutil.rmtree(scene_name)

    os.mkdir(scene_name)

    #Changing the current working directory
    os.chdir(scene_name)

    #Creating the model.config file
    configGenerator()

    #Creatinf the model.sdf file
    modelGenerator(scene_name)

    #Creating the model materials folder
    os.mkdir("materials")
    os.chdir("materials")
    os.mkdir("textures")
    os.chdir("textures")

    cv2.imwrite("heightmap.png",heightmap)


def imageResizer(path):
    hm = cv2.imread(path)
    hm_resize = cv2.resize(hm,(129,129))
    return hm_resize

def behaviorMapGen(wall_map, xml_path, point_size):
    def DuplicationCheck(rgb, rgb_list):
        for item in rgb_list:
            if item == rgb:
                return False
        return True

    def get_node_bgr(node):
        r = int(node.attrib['r'])
        g = int(node.attrib['g'])
        b = int(node.attrib['b'])
        return tuple((b, g, r))
    
    behavior_map = wall_map
    rgb_list = []
    Scene_xml = et.parse(xml_path).getroot()
    for group_id, group_node in enumerate(Scene_xml.findall('Group')):
        for goal_set_id, goal_set_node in enumerate(group_node.findall('GoalSet')):
            bgr = get_node_bgr(goal_set_node.find('Color'))
            if DuplicationCheck(bgr,rgb_list):
                rgb_list.append(bgr)
        for goal_set_id, goal_set_node in enumerate(group_node.findall('Spawn')):
            bgr = get_node_bgr(goal_set_node.find('Color'))
            if DuplicationCheck(bgr,rgb_list):
                rgb_list.append(bgr)
    Spawn_point_number = len(rgb_list)
    Spawn_point_color = rgb_list
    for spid in range(Spawn_point_number):
        NotSucc = True
        while(NotSucc):
            x = randint(0,128)
            y = randint(0,128)
            if(behavior_map[x,y,0]==255 and behavior_map[x,y,1]==255 and behavior_map[x,y,2]==255):
                for x_offset in range(point_size):
                    for y_offset in range(point_size):
                        if(behavior_map[x+x_offset,y+y_offset,0]==255 and behavior_map[x+x_offset,y+y_offset,1]==255 and behavior_map[x+x_offset,y+y_offset,2]==255):
                            for cid in range(3):
                                behavior_map[x+x_offset,y+y_offset,cid] = Spawn_point_color[spid][cid]
                NotSucc = False
    return behavior_map

def main_process(scene_name, png_path, xml_path, output_dir):
    heightmap = imageResizer(png_path)
    wall_map = 255 - heightmap
    behavior_map = behaviorMapGen(wall_map, xml_path, point_size =3)

    # cv2.imshow('My Image', behavior_map)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    behavior_map = cv2.cvtColor(behavior_map,cv2.COLOR_BGR2RGB)
    wall_map = cv2.cvtColor(wall_map,cv2.COLOR_BGR2RGB)

    #Generate Menge Scene file
    menge_generator.menge_main(behavior_map, wall_map, xml_path, scene_name, output_dir)
    workspace = os.getcwd()
    #Creating a autogen_terrain folder with terrain information and also the world file
    modelFolderGenerator(heightmap, scene_name)
    os.chdir(workspace)
    os.chdir("textures")
    texture_path = os.getcwd()
    imgfiles = os.listdir(texture_path)
    for imgfile in imgfiles:
        command = "cp "+str(imgfile)+" ~/.gazebo/models/"+scene_name+"/materials/textures/"
        os.system(command)

    os.chdir(workspace)
    destination=os.path.join(output_dir,scene_name)
    if(not os.path.isdir(destination)):
        os.mkdir(destination)
    os.chdir(destination)

    #Creating our world file
    worldGenerator(scene_name)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--png_dir", help="path to the scenario png file folder", default='png')
    parser.add_argument("--output_dir", help="path to the output floder", default='output')
    parser.add_argument("--xml_dir", help="path to the scenario xml floder", default='xml')
    args = parser.parse_args()

    #Welcome text
    print ("WELCOME TO AUTOMATIC TERRAIN GENEREATOR")

    png_dir = args.png_dir
    output_dir = args.output_dir
    xml_dir = args.xml_dir
    cwd = os.getcwd()
    # Please make sure the files under xml_root folder have the corresponding file in png_path folder
    files = [f for f in os.listdir(xml_dir) if os.path.isfile(os.path.join(xml_dir, f))]

    for file in files:
        scene_name = file[:-4]
        png_path = os.path.join(png_dir, scene_name + '.png')
        xml_path = os.path.join(xml_dir, file)
        main_process(scene_name, png_path, xml_path, output_dir)
        os.chdir(cwd)

    print("successully generated")