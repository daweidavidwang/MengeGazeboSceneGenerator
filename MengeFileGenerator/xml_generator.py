import xml.etree.ElementTree as et
import random
'''
######################## Behavior XML ######################## 
'''


''' ----------- Goals ----------- '''


def make_goal_set(id, capacity, locations):
    node = et.Element('GoalSet')
    node.set('id', str(id))
    for i, location in enumerate(locations):
        goal = et.SubElement(node, 'Goal')
        goal.set('type', 'point')
        goal.set('id', str(i))
        #goal.set('capacity', str(capacity))
        goal.set('x', str(location[0]))
        goal.set('y', str(location[1]))
        #goal.set('radius', '.5')
        #goal.set('weight', '1')
    return node


''' ----------- States ----------- '''


def make_state_static(name, persistent, velocity):
    node = et.Element('State')
    node.set('name', name)
    node.set('final', '0')
    goal_selector = et.SubElement(node, 'GoalSelector')
    goal_selector.set('type', 'identity')
    goal_selector.set('persistent', persistent)
    vel_component = et.SubElement(node, 'VelComponent')
    vel_component.set('type', velocity)
    return node


def make_state_teleport(name, min_x, min_y, max_x, max_y):
    node = make_state_static(name, '0', 'zero')
    action = et.SubElement(node, 'Action')
    action.set('type', 'teleport')
    action.set('dist', 'u')
    action.set('min_x', str(min_x))
    action.set('min_y', str(min_y))
    action.set('max_x', str(max_x))
    action.set('max_y', str(max_y))
    #action.set('exit_reset', 'true')
    return node


def make_state_travel(name, goal_set_id, map_name):
    node = et.Element('State')
    node.set('name', name)
    node.set('final', '0')
    goal_selector = et.SubElement(node, 'GoalSelector')
    goal_selector.set('type', 'random')
    goal_selector.set('goal_set', str(goal_set_id))
    goal_selector.set('persistent', '1')
    vel_component = et.SubElement(node, 'VelComponent')
    vel_component.set('type', 'road_map')
    vel_component.set('file_name', '%s.txt' % map_name)
    return node

def make_state_final(name):
    node = et.Element('State')
    node.set('name',name)
    node.set('final','0')
    vel_component = et.SubElement(node, 'VelComponent')
    vel_component.set('type', 'zero')
    return node 


''' ----------- Transitions  ----------- '''


def make_transition_timer(fro, to, min, max):
    node = et.Element('Transition')
    node.set('from', fro)
    node.set('to', to)
    condition = et.SubElement(node, 'Condition')
    condition.set('type', 'timer')
    condition.set('dist', 'u')
    condition.set('min', str(min))
    condition.set('max', str(max))
    condition.set('per_agent', '1')
    return node


def make_transition_goal_reached(fro, to, goal_area):
    node = et.Element('Transition')
    node.set('from', fro)
    node.set('to', to)
    condition = et.SubElement(node, 'Condition')
    condition.set('type', 'AABB')
    condition.set('inside', '1')
    condition.set('min_x', str(goal_area[0]))
    condition.set('min_y', str(goal_area[1]))
    condition.set('max_x', str(goal_area[2]))
    condition.set('max_y', str(goal_area[3]))
    return node


def make_transition_random(fro, destinations):
    node = et.Element('Transition')
    node.set('from', fro)
    condition = et.SubElement(node, 'Condition')
    condition.set('type', 'auto')
    target = et.SubElement(node, 'Target')
    target.set('type', 'prob')
    for destination in destinations:
        state = et.SubElement(target, 'State')
        state.set('name', destination[0])
        state.set('weight', str(destination[1]))
    return node


'''
######################## Scene XML ######################## 
'''


def make_agent_profile(id, speed):
    node = et.Element('AgentProfile')
    node.set('name', 'group_%d' % id)
    node.set('inherits', 'base')
    properties = et.SubElement(node, 'Common')
    properties.set('class', str(id))
    properties.set('pref_speed', str(speed))
    return node


def make_agent_group(id, amount, min_x, min_y, max_x, max_y):
    node = et.Element('AgentGroup')
    profile_selector = et.SubElement(node, 'ProfileSelector')
    profile_selector.set('type', 'const')
    profile_selector.set('name', 'group_%d' % id)
    state_selector = et.SubElement(node, 'StateSelector')
    state_selector.set('type', 'const')
    state_selector.set('name', 'Walk_%d' % id)
    generator = et.SubElement(node, 'Generator')
    generator.set('type', 'explicit')
    if(min_x==max_x and min_y==max_y):
        print("No space for generating %d agents" % amount)
        amount = 1
    for agent_id in range(amount):
        agent = et.SubElement(generator, 'Agent')
        agent.set('p_x', str(random.uniform(min_x, max_x)))
        agent.set('p_y', str(random.uniform(min_y, max_y)))
    
    return node