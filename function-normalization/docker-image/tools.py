# Libraries 
from pymongo import MongoClient
import os

""" Environment Variables """
# Mongo database Host and Port
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))

# Mongo database and collection names
DATABASE = os.getenv("DATABASE", "UIDB")
COLLECTION = os.getenv("COLLECTION", "functions")

# Connect with mongo DB
mongo_host = MONGO_HOST+":"+str(MONGO_PORT)
mongo_client = MongoClient("mongodb://"+mongo_host+"/")

# Connect with Database
mongo_db = mongo_client[DATABASE]
mongo_collection = mongo_db[COLLECTION]

""" Normalization Startup """
def normalize(complex_function_json):
    # Search for each function node
    ## Until there is no any other function for one full loop
    nodes = complex_function_json["expression"]

    # Start with the purpose of finding something to fix
    ready_nodes = False
    
    # Stop only when there are no functions left in the nodes
    while not ready_nodes:
        ready_nodes = True
        for node in nodes:
            # If you find a function then normalize it and start a new loop
            if node["info"]["kind"] == "function": 
                single_function_normalization(node, nodes)
                ready_nodes = False
                break

    # Change the "expression" field to match the normalized one
    complex_function_json["expression"] = nodes

    # Return the "complex" graph that is now simple
    return complex_function_json

""" Single Function Normalization """
def single_function_normalization(node, nodes):
    # Get the function's nodes and args
    library_function = mongo_collection.find_one({"name" : node["info"]["name"]})
    library_expression = library_function["expression"]
    library_args = library_function["args"]

    # Find the max step of the nodes
    max_step = find_max_step_of_nodes(nodes)
    
    # Add (max_step + 2) to all the steps of the library's expression
    ## But do not change an 0 value (this valus are needed to find the starting and ending nodes)
    library_expression_lifted = lift_values(library_expression, max_step)
    
    # Fix lifted output and get the output step
    output_step, output_next_step = fix_output(library_expression_lifted, node)
    # Fix the next node's "from" of the lifted output
    fix_output_next(nodes, node["step"], output_step, output_next_step)

    # Fix lifted inputs
    # Start by counting the 0 position
    arg_position = 0
    for library_arg in library_args:
        # Get the next arg_id
        arg_id = library_arg["arg_id"]

        # Make the "from" nodes to look at the "next" node of the argument node with the given ID
        step_from, step_current, step_next =  make_from_look_at_next_node(arg_id, arg_position, node, nodes, library_expression_lifted)
        arg_position += 1   # Add one to the postion of the arguments

        # Make the argument's "next" node come from the argument's "from" node with the given ID
        make_next_look_at_from_node(step_from, step_current, step_next, library_expression_lifted)

    # Remove the arguments of the lifted expression
    remove_args(library_expression_lifted)

    # Add the lifted expression in the nodes
    nodes.extend(library_expression_lifted)

    # Remove the function from the nodes
    nodes.remove(node)
    return

""" Function to find the max step from a list of nodes """
def find_max_step_of_nodes(nodes):
    # Assume that the first next step is the max
    max_step = nodes[0]["next"]

    # Find the max step of all the nodes
    for node in nodes:
        steps = get_from_steps(node)
        for step in steps:
            if step > max_step: max_step = step
    
    # Return the max_step
    return max_step

""" Function to get all the from steps from a node, as a list """
def get_from_steps(node):
    # Assume the list is empty
    list_of_steps = []

    # Get the list or make the list based on the node["from"] type
    if type(node["from"]) == list:
        list_of_steps = node["from"]
    else:
        list_of_steps = [node["from"]]
    
    # Return the list of steps
    return list_of_steps

""" Function to add (number + 2) to all the non zero steps of the given nodes """
def lift_values(nodes, number):
    # Start with zero nodes
    lifted_nodes = []

    # Make the number to be added
    addition_number = number + 2

    # For each node append the new node as lifted
    for node in nodes:
        # Break the node from nodes so the value will not be changed by reference
        broken_node = node.copy()

        # Change the from values
        from_steps = get_from_steps(broken_node)
        if from_steps != [0]:
            if len(from_steps) == 1 : broken_node["from"] = broken_node["from"] + addition_number
            else: broken_node["from"] = [from_step + addition_number for from_step in broken_node["from"]]
        
        # Change the next values
        if broken_node["next"] != 0 : broken_node["next"] = broken_node["next"] + addition_number

        # Change the step values
        broken_node["step"] = broken_node["step"] + addition_number

        # Append the broken node in the new list
        lifted_nodes.append(broken_node)

    # Return the lifted nodes
    return lifted_nodes

""" Function that is removing all the arguments from a list of nodes """
def remove_args(nodes):
    # Assume that there is a removed node to start the while loop
    removed = True
    while removed == True:
        # Assume that there will not be any removed node
        removed = False

        # Search all nodes, if you find one to remove then remove and try again
        for node in nodes:
            if node["info"]["kind"] == "arg": 
                nodes.remove(node)
                removed = True
                break
    return

""" Function to fix the only next with the value zero """
def fix_output(nodes, node_model):
    for node in nodes:
        if node["next"] == 0 : 
            node["next"] = node_model["next"]
            return node["step"], node["next"]

""" Function to connect a node with a given "from" node """
def fix_output_next(nodes, current_from_step, needed_from_step, node_step):
    # Do nothing if the next node is the value zero.
    if node_step == 0 : return

    # Search all the nodes
    for node in nodes:
        # Node found
        if node["step"] == node_step:
            # get all the "from" steps
            from_steps = get_from_steps(node)
            # If there is only one "from" step, then make it the needed "from" step
            # Else, give the same "from" steps but change the current "from" with the needed "from"
            if len(from_steps) == 1 :
                node["from"] = needed_from_step
            else:
                new_from_steps = []
                for step in from_steps:
                    if step == current_from_step :  new_from_steps.append(needed_from_step)
                    else: new_from_steps.append(step)
                node["from"] = new_from_steps
    return

""" Function to fix the nodes before the argument given """
def make_from_look_at_next_node(arg_id, arg_position, func_node, nodes, lifted_nodes):
    # Get the step of the original node to change
    from_node_step = get_from_steps(func_node)[arg_position]

    # Find the next step to give to the node before the argument
    next_step = None        # Assume None as it will find value in the for loop
    argument_step = None    # Assume None as it will find value in the for loop
    for node in lifted_nodes:
        # Filter out the non argument nodes
        if not ("arg_id" in node["info"]):
            continue
        
        # Find the argument and hold the next step
        if node["info"]["arg_id"] == arg_id:
            next_step = node["next"]
            argument_step = node["step"]

    # Find the from node
    for node in nodes:
        # Change the next step of the from node to the next step of the argument given
        if node["step"] == from_node_step:
            node["next"] = next_step

    # Return the from and next steps of the argument, with the current step as well
    return from_node_step, argument_step, next_step

""" Function to fix the nodes after the argument given """
def make_next_look_at_from_node(step_from, arg_step, next_step, lifted_nodes):
    # Find the next step of the argument
    for node in lifted_nodes:
        if node["step"] == next_step:
            # If from is number then change it as a number
            if len(get_from_steps(node)) == 1 :
                node["from"] = step_from
            else:   # Else change only the element that is the argument
                for i in range(len(get_from_steps(node))):
                    if node["from"][i] == arg_step : node["from"][i] = step_from
            break

    return