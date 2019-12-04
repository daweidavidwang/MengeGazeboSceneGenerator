import os
import argparse
import imageio
import scipy.misc
import xml.dom.minidom as xdm
import xml.etree.ElementTree as et
from MengeFileGenerator import graph_generator
from MengeFileGenerator import square_generator
from MengeFileGenerator import wall_generator
from MengeFileGenerator import xml_generator

SCENARIO_NAME = None
BEHAVIOR_IMAGE = None
WALL_IMAGE = None

COLOR_DICTIONARY = {}
SPAWNS = []

def create_color_dictionary(image):
    height = image.shape[0]
    width = image.shape[1]
    color_coords = {}
    for x in range(width):
        for y in range(height):
            rgb = tuple(image[y][x][:3])
            if color_coords.get(rgb) is None:
                color_coords[rgb] = []
            color_coords[rgb].append((x, height - y))
    return color_coords


def get_node_rgb(node):
    r = int(node.attrib['r'])
    g = int(node.attrib['g'])
    b = int(node.attrib['b'])
    return tuple((r, g, b))


def add_agents(group_id, group_node, min_x, min_y, max_x, max_y, SCENE_XML):

    speed = 1
    try:
        speed = int(group_node.attrib['speed'])
    except KeyError:
        print("[WARNING] Missing 'speed' attribute in group %d. Using default value %d." % (group_id, speed))
    except ValueError:
        print("[WARNING] Invalid type for 'speed' attribute in group %d. Using default value %d." % (group_id, speed))
    finally:
        node = xml_generator.make_agent_profile(group_id, speed)
        SCENE_XML.append(node)

    amount = 1
    try:
        amount = int(group_node.attrib['amount'])
    except KeyError:
        print("[WARNING] Missing 'amount' attribute in group %d. Using default value %d." % (group_id, amount))
    except ValueError:
        print("[WARNING] Invalid type for 'amount' attribute in group %d. Using default value %d." % (group_id, amount))
    finally:
        node = xml_generator.make_agent_group(group_id, amount, min_x, min_y, max_x, max_y)
        SCENE_XML.append(node)


def add_goal_sets(group_id, group_node, total_goalsets, BEHAVIOR_XML):

    for goal_set_id, goal_set_node in enumerate(group_node.findall('GoalSet')):

        capacity = 1
        try:
            capacity = int(goal_set_node.attrib['capacity'])
        except KeyError:
            print("[WARNING] Missing 'capacity' attribute in group %d goal set %d. Using default value %d." %
                  (group_id, goal_set_id, capacity))
        except ValueError:
            print("[WARNING] Invalid type for 'capacity' attribute in group %d goal set %d. Using default value %d." %
                  (group_id, goal_set_id, capacity))

        rgb = None
        try:
            rgb = get_node_rgb(goal_set_node.find('Color'))
        except KeyError:
            print("[ERROR] Missing 'r', 'g', 'b' attributes in group %d goal set %d color." %
                  (group_id, goal_set_id))
            return False
        except ValueError:
            print("[ERROR] Invalid type for 'r', 'g', 'b' attributes in group %d goal set %d." %
                  (group_id, goal_set_id))
            return False

        destinations = None
        try:
            destinations = COLOR_DICTIONARY[rgb]
        except KeyError:
            print("[ERROR] Could not find pixels with an RGB value of %s in %s.png when trying to create group %d goal set %d." %
                  (rgb, SCENARIO_NAME, group_id, goal_set_id))
            return False

        node = xml_generator.make_goal_set(goal_set_id + total_goalsets, capacity, destinations)
        BEHAVIOR_XML.append(node)

    return True


def add_spawn(group_id, group_node, BEHAVIOR_XML, SCENE_XML):

    min = 0
    try:
        min = int(group_node.find('Spawn').attrib['min'])
    except KeyError:
        print("[WARNING] Missing 'min' attribute in group %d spawn. Using default value %d." %
              (group_id, min))
    except ValueError:
        print("[WARNING] Invalid type for 'min' attribute in group %d spawn. Using default value %d." %
              (group_id, min))

    max = 0
    try:
        max = int(group_node.find('Spawn').attrib['max'])
    except KeyError:
        print("[WARNING] Missing 'max' attribute in group %d spawn. Using default value %d" %
              (group_id, max))
    except ValueError:
        print("[WARNING] Invalid type for 'max' attribute in group %d spawn. Using default value %d." %
              (group_id, max))

    rgb = None
    try:
        rgb = get_node_rgb(group_node.find('Spawn').find('Color'))
    except KeyError:
        print("[ERROR] Missing 'r', 'g', 'b' attributes in group %d spawn." % group_id)
        return False
    except ValueError:
        print("[ERROR] Invalid type for 'r', 'g', 'b' attributes in group %d spawn." % group_id)
        return False


    locations = []
    try:
        max_x = 0
        max_y = 0
        min_x = 255
        min_y = 255
        for spawn_id, location in enumerate(COLOR_DICTIONARY[rgb]):
            if(max_x<location[0]):
                max_x = location[0]
            if(max_y<location[1]):
                max_y = location[1]
            if(min_x>location[0]):
                min_x = location[0]
            if(min_y>location[1]):
                min_y = location[1]

        name = 'Spawn_%d' % (group_id)
        spawn_node = xml_generator.make_state_teleport(name, min_x, min_y, max_x, max_y)
        chance = group_node.find('Spawn').find('Transition').attrib['chance']
        SPAWNS.append([name, chance])
        BEHAVIOR_XML.append(spawn_node)
        add_agents(group_id, group_node, min_x, min_y, max_x, max_y,SCENE_XML)

    except KeyError:
        print(
            "[ERROR] Could not find pixels with an RGB value of %s in %s.png when trying to create group %d spawn." %
            (rgb, SCENARIO_NAME, group_id))
        return False

    return True

def add_spawn_transition(BEHAVIOR_XML):
    node_respawn = xml_generator.make_state_final('ReSpawn')
    respawn_trans = xml_generator.make_transition_random('ReSpawn', SPAWNS)
    BEHAVIOR_XML.append(node_respawn)
    BEHAVIOR_XML.append(respawn_trans)


def add_goals(group_id, group_node, total_goalsets, BEHAVIOR_XML):

    for goal_set_id, goal_set_node in enumerate(group_node.findall('GoalSet')):
        
        rgb = None
        try:
            rgb = get_node_rgb(goal_set_node.find('Color'))
        except KeyError:
            print("[ERROR] Missing 'r', 'g', 'b' attributes in group %d goal set %d color." %
                  (group_id, goal_set_id))
            return False
        except ValueError:
            print("[ERROR] Invalid type for 'r', 'g', 'b' attributes in group %d goal set %d." %
                  (group_id, goal_set_id))
            return False

        destinations = None

        try:
            destinations = COLOR_DICTIONARY[rgb]
        except KeyError:
            print("[ERROR] Could not find pixels with an RGB value of %s in %s.png when trying to create group %d goal set %d." %
                  (rgb, SCENARIO_NAME, group_id, goal_set_id))
            return False


        state_travel_name = 'Walk_%d' % group_id
        travel_node = xml_generator.make_state_travel(state_travel_name, goal_set_id + total_goalsets, SCENARIO_NAME)
        BEHAVIOR_XML.append(travel_node)

        max_x = 0
        max_y = 0
        min_x = 255
        min_y = 255
        for location in destinations:
            if(max_x<location[0]):
                max_x = location[0]
            if(max_y<location[1]):
                max_y = location[1]
            if(min_x>location[0]):
                min_x = location[0]
            if(min_y>location[1]):
                min_y = location[1]
        travel_arrive_tran = xml_generator.make_transition_goal_reached(state_travel_name, 'ReSpawn',[min_x,min_y,max_x,max_y])
        BEHAVIOR_XML.append(travel_arrive_tran)

        min = 0
        try:
            min = int(goal_set_node.attrib['min'])
        except KeyError:
            print("[WARNING] Missing 'min' attribute in group %d goal set %d. Using default value %d." %
                  (group_id, goal_set_id, min))
        except ValueError:
            print("[WARNING] Invalid type for 'min' attribute in group %d goal set %d. Using default value %d." %
                  (group_id, goal_set_id, min))

        max = 0
        try:
            max = int(goal_set_node.attrib['max'])
        except KeyError:
            print("[WARNING] Missing 'max' attribute in group %d goal set %d. Using default value %d." %
                  (group_id, goal_set_id, max))
        except ValueError:
            print("[WARNING] Invalid type for 'max' attribute in group %d goal set %d. Using default value %d." %
                  (group_id, goal_set_id, max))

        timer_tran = xml_generator.make_transition_timer(state_travel_name, 'ReSpawn', min, max)
        BEHAVIOR_XML.append(timer_tran)
        spawn_name = 'Spawn_%d' % group_id
        destination_tran = xml_generator.make_transition_random(spawn_name, [[state_travel_name, 1]])
        BEHAVIOR_XML.append(destination_tran)


def create_XML_link():
    root = et.Element('Project')
    root.set('scene', '%sS.xml' % SCENARIO_NAME)
    root.set('behavior', '%sB.xml' % SCENARIO_NAME)
    root.set('view', '%sV.xml' % SCENARIO_NAME)
    root.set('model', 'orca')
    root.set('dumpPath', 'images/%s' % SCENARIO_NAME)
    return root


def create_XML_scene_behavior(MAIN_XML,BEHAVIOR_XML, SCENE_XML):

    total_goalsets = 0
    total_spawn = 0
    for group_id, group_node in enumerate(MAIN_XML.findall('Group')):

        if not add_goal_sets(group_id, group_node, total_goalsets, BEHAVIOR_XML):
            return False

        if not add_spawn(group_id, group_node, BEHAVIOR_XML, SCENE_XML):
            return False

        
        add_goals(group_id, group_node, total_goalsets,BEHAVIOR_XML)
        total_goalsets += len(group_node.findall('GoalSet'))
        total_spawn += len(group_node.findall('Spawn'))
    
    add_spawn_transition(BEHAVIOR_XML)

    return True


def create_XML_viewer(VIEWER_XML ):

    x = BEHAVIOR_IMAGE.shape[1] / 2 +50
    y = BEHAVIOR_IMAGE.shape[0] / 2 +50
    xtgt = 0
    ytgt = 0
    scale = 0.5

    camera = VIEWER_XML.find('Camera')
    camera.set('xpos', str(x))
    camera.set('ypos', str(y))
    camera.set('xtgt', str(xtgt))
    camera.set('ytgt', str(ytgt))
    camera.set('orthoScale', str(scale))


def write_to_XML(node, fileName):
    data = et.tostring(node)
    data = xdm.parseString(data)
    data = data.toprettyxml(indent="\t")
    outfile = open('%s.xml' % fileName, 'w')
    outfile.write(data)
    outfile.close()


'''
######################## Main Program ######################## 
'''

def menge_main(behavior_map, wall_map, xml_path, scene_name, output_path):

    global WALL_IMAGE, COLOR_DICTIONARY, SPAWNS, SCENARIO_NAME, BEHAVIOR_IMAGE
    SCENE_XML = et.parse('MengeFileGenerator/base_scene.xml').getroot()
    BEHAVIOR_XML = et.Element('BFSM')
    VIEWER_XML = et.parse('MengeFileGenerator/base_viewer.xml').getroot()
    SCENARIO_NAME = scene_name
    XML_PATH = xml_path
    OUTPUT_PATH = os.path.join(output_path, SCENARIO_NAME)
    MAIN_XML = et.parse(XML_PATH).getroot()
    BEHAVIOR_IMAGE = behavior_map
    WALL_IMAGE = wall_map

    if not os.path.exists("%s/" % OUTPUT_PATH):
        print("Creating output directory './%s/'" % OUTPUT_PATH, end='\r', flush=True)
        os.makedirs("%s/" % OUTPUT_PATH)

    print("Creating link file '%s/%s.xml'..." % (OUTPUT_PATH, SCENARIO_NAME), end='\r', flush=True)
    link_xml = create_XML_link()
    write_to_XML(link_xml, '%s/%s' % (OUTPUT_PATH, SCENARIO_NAME))

    print("Creating viewer file '%s/%sV.xml'..." % (OUTPUT_PATH, SCENARIO_NAME), end='\r', flush=True)
    create_XML_viewer(VIEWER_XML)
    write_to_XML(VIEWER_XML, '%s/%sV' % (OUTPUT_PATH, SCENARIO_NAME))

    print("Creating behavior file '%s/%sB.xml..." % (SCENARIO_NAME, SCENARIO_NAME), end='\r', flush=True)
    COLOR_DICTIONARY = create_color_dictionary(BEHAVIOR_IMAGE)
    if not create_XML_scene_behavior(MAIN_XML, BEHAVIOR_XML, SCENE_XML):
        return
    write_to_XML(BEHAVIOR_XML, '%s/%sB' % (OUTPUT_PATH, SCENARIO_NAME))

    print("Creating scene file '%s/%sS.xml..." % (SCENARIO_NAME, SCENARIO_NAME), end='\r', flush=True)
    wall_points = square_generator.build_point_dict(WALL_IMAGE, 255)
    wall_squares = square_generator.build_square_list(WALL_IMAGE, wall_points)
    data = {
        'width': WALL_IMAGE.shape[1],
        'height': WALL_IMAGE.shape[0],
        'squares': wall_squares
    }
    obstacle_set_node = wall_generator.create_obstacle_set(data)
    SCENE_XML.append(obstacle_set_node)
    write_to_XML(SCENE_XML, '%s/%sS' % (OUTPUT_PATH, SCENARIO_NAME))

    print("Creating road map file %s/%s.txt..." % (OUTPUT_PATH, SCENARIO_NAME), end='\r', flush=True)
    walkable_points = square_generator.build_point_dict(WALL_IMAGE, 0)
    walkable_squares = square_generator.build_square_list(WALL_IMAGE, walkable_points)
    data = {
        'width': WALL_IMAGE.shape[1],
        'height': WALL_IMAGE.shape[0],
        'squares': walkable_squares,
        'graph': square_generator.build_border_dict(walkable_squares),
    }
    graph_generator.build("%s/%s" % (OUTPUT_PATH, SCENARIO_NAME), data)

    print("Completed! Use the following command to run the scenario in menge:")
    print("./menge -d 2000 -p %s/%s/%s.xml" % (os.getcwd(), SCENARIO_NAME, SCENARIO_NAME))
