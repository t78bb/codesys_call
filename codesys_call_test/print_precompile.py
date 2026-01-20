# -*- coding: utf-8 -*-
import scriptengine
import traceback
import time
import re

def compile_pou(application, pou_objs):
    """
    Compile POUs and get precompile messages
    
    :param application: CODESYS application object
    :param pou_objs: List of POU objects to compile
    """
    start_time = time.time()
    print("Starting compile process...")
    application.clean()
    compile_msgs = []
    precompile_msgs = []

    def extract_line_number(text):
        match = re.search(r'(?:Line|行)[\s:]*(\d+)', text)
        if match:
            return int(match.group(1))
        else:
            return -1

    # Precompile step - get precompile messages before build
    try:
        print("Starting precompile...")
        precompile_start_time = time.time()

        # Get message categories
        cates_pre = system.get_message_categories(bActive=True)
        if not cates_pre:
            print("No message categories found")
            return []

        print("Got {0} message categories".format(len(cates_pre)))

        # Define constants outside loop
        precompile_desc_diff_lang = set(["Precompile", "预编译"])
        
        # Find precompile category
        for cate in cates_pre:
            if cate is None:
                continue
            
            desc = system.get_message_category_description(cate)
            if desc not in precompile_desc_diff_lang:
                continue
            
            # Found precompile category
            print("Found precompile message category: " + desc)
            msg_objs = system.get_message_objects(category=cate)
            
            if not msg_objs:
                print("No precompile messages found")
                break
            
            print("Got {0} message objects".format(len(msg_objs)))
            
            # Build message list
            precompile_msgs = [
                {
                    "Path": extract_line_number(obj.position_text) if obj.position_text else -1,
                    "ErrorDesc": obj.text if obj.text else "",
                    "IsDef": True if obj.position_text and "Decl" in obj.position_text else False,
                    "PouName": obj.object.get_name() if obj.object else "",
                    "ID": (obj.prefix + "{0:04d}".format(int(obj.number))) if hasattr(obj, 'prefix') and hasattr(obj, 'number') and obj.prefix is not None and obj.number is not None else ""
                }
                for obj in msg_objs
            ]
            
            print("Found {0} precompile messages".format(len(precompile_msgs)))
            for msg in precompile_msgs:
                print("  - {0}".format(msg.get("ErrorDesc", "")))
            
            break  # Found and processed, exit loop

        precompile_time = time.time() - precompile_start_time
        print("Precompile operation completed in {0:.2f} seconds".format(precompile_time))

    except Exception, precompile_error:
        print("Error during precompile operation: " + str(precompile_error))
        print(traceback.format_exc())

    return precompile_msgs


# Main execution
try:
    print("===== Starting CODESYS Precompile Test =====")
    
    # Get system instance
    system = scriptengine.system
    session.system = system
    print("Got system instance")
    
    # Get active project
    if not hasattr(scriptengine, 'session') or not scriptengine.session:
        print("Error: No active session")
    else:
        project = scriptengine.session.active_project
        if not project:
            print("Error: No active project")
        else:
            print("Got active project: " + project.get_name())
            
            # Get active application
            application = project.active_application
            if not application:
                print("Error: No active application")
            else:
                print("Got active application")
                
                # Get all POUs from application
                pou_objs = []
                try:
                    # Try to find all POUs in the application
                    all_objects = application.find("*", True)
                    for obj in all_objects:
                        if hasattr(obj, 'type'):
                            # Check if it's a POU (Program, Function, FunctionBlock)
                            obj_type_str = str(obj.type) if hasattr(obj, 'type') else ""
                            if "Pou" in obj_type_str or "Program" in obj_type_str or "Function" in obj_type_str:
                                pou_objs.append(obj)
                                print("Found POU: " + obj.get_name())
                except Exception, find_error:
                    print("Error finding POUs: " + str(find_error))
                
                if len(pou_objs) == 0:
                    print("Warning: No POUs found, using empty list")
                
                # Call compile_pou function
                result = compile_pou(application, pou_objs)
                print("===== Test Completed =====")
                print("Result: " + str(result))
                
except Exception, main_error:
    print("Error in main execution: " + str(main_error))
    print(traceback.format_exc())