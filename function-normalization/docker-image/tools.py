# Libraries 
from pymongo import MongoClient
import os

""" Environment Variables """
# Mongo database Host and Port
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))

# Mongo database and collection names
DATABASE = os.getenv("DATABASE", "TEST")
COLLECTION = os.getenv("COLLECTION", "library")

""" Function to allign the changes with the complex graph """
def make_changes(node, nodes):
    # Connect with mongo DB
    mongo_host = MONGO_HOST+":"+str(MONGO_PORT)
    mongo_client = MongoClient("mongodb://"+mongo_host+"/")

    # Connect with Database
    mydb = mongo_client[DATABASE]
    mycol = mydb[COLLECTION]

    """ Configuring max step to get new steps """
    # Get max step of nodes in the complex function
    max_step = -1
    for current_node in nodes:
        if(current_node["next"] > max_step):
            max_step = current_node["next"]
        if(current_node["step"] > max_step):
            max_step = current_node["step"]
        if type(current_node["from"]) == list:
            for i in range(len(current_node["from"])):
                if(current_node["from"][i] > max_step):
                    max_step = current_node["from"][i]
        else:
            if(current_node["from"] > max_step):
                max_step = current_node["from"]

    # Initialise the max_step as k 
    k = max_step

    """ Getting needed function from MongoDB library """
    # Get the function from library
    library_function = mycol.find_one({"name" : node["info"]["name"]})
  
    # Clear Mongo _id field
    del library_function["_id"]
  
    """ Give the new steps to the function from the library """
    # shift up all steps by k-1
    for obj in library_function["expression"]:
        obj["step"] += k-1
        if obj["next"] != 0:
            obj["next"] += k-1
        if obj["from"] != 0:
            if type(obj["from"]) == list:
                for i in range(len(obj["from"])):
                    obj["from"][i] += k-1
            else:
                obj["from"] += k-1
  
    # Fix arg steps
    arg_steps = node["from"]
    for i in range(len(arg_steps)):
        next_step = 0
        current_step = 0
        for obj in library_function["expression"]:
            if obj["info"]["kind"] == "arg":
                if obj["info"]["arg_id"] == (i+1):
                    next_step = obj["next"]
                    current_step = obj["step"]
                    break
        for obj in library_function["expression"]:
            if obj["step"] == next_step:
                for j in range(len(obj["from"])):
                    if obj["from"][j] == current_step:
                        obj["from"][j] = arg_steps[i]
                        break
  
    # Keep only the expression
    library_expression = library_function["expression"]
  
    # Remove not usable nodes (args)
    for i in range(len(library_expression)-1,-1,-1):
        if library_expression[i]["info"]["kind"] == "arg":
            del library_expression[i]
  
    # Fix the next with the value 0 (zero) from the library
    # Give it the output next from the complex function
    ## Do that ONLY if there is non-zero value in the node variable
    # Start from the end because the zero value will be last most of the times
    if(node["next"] != 0):
        # Fix next step
        for i in range(len(library_expression)-1,-1,-1):
            from_step = -1
            if(library_expression[i]["next"] == 0):
                library_expression[i]["next"] = node["next"]
                from_step = library_expression[i]["step"]
                break
        # Fix from steps of the next step from the complex function
        for i in range(len(nodes)):
            if(nodes[i]["step"] == node["next"]):
                if type(nodes[i]["from"]) == list:
                    for j in range(len(nodes[i]["from"])):
                        if(nodes[i]["from"][j] == node["step"]):
                            nodes[i]["from"][j] = from_step
                else:
                    nodes[i]["from"] = from_step
  
    # Start changing the given "next" attributes of the JSON 
    # to match with the new ids
    for i in range(len(nodes)):
        if(nodes[i]["next"] == node["step"]):
            for current_lib_node in library_expression:
                if(type(current_lib_node["from"]) == list):
                    for current_step in current_lib_node["from"]:
                        if(current_step == nodes[i]["step"]):
                            nodes[i]["next"] = current_lib_node["step"]
                else:
                    if(current_lib_node["from"] == nodes[i]["step"]):
                        nodes[i]["next"] = current_lib_node["step"] 

    # Add in the end of all the nodes the normalized expression from the library function
    for current_node in library_expression:
        nodes.append(current_node)

""" Function to delete the function nodes that are now imported in the Complex JSON """
def clear_functions(nodes):
    for i in range(len(nodes)-1,-1,-1):
        if nodes[i]["info"]["kind"] == "function":
            del nodes[i]

""" Normalization function """
def normalize(complex_function_json):
    # Search for each function node
    nodes = complex_function_json["expression"]
    for node in nodes:
        if node["info"]["kind"] == "function":
            # For every function, make changes in the complex JSON
            make_changes(node, nodes)
    # Finally, clean up not needed nodes
    clear_functions(nodes)

    # Change the "expression" field to match the normalized one
    complex_function_json["expression"] = nodes

    # Return the "complex" graph that is now simple
    return complex_function_json