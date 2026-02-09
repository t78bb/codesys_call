# -*- coding: utf-8 -*-
"""
Project POU compilation script generator
单独提取的项目 POU 编译脚本生成器
"""

import logging

logger = logging.getLogger(__name__)


def project_generate_pou_create_set_compile_script(path, params):
    """Generate script to create, set, and compile a pou."""
    pou_infos = []
    for param in params:
        pou_name = param.get("pou_name", "TestBlock")
        pou_type = param.get("pou_type", "FUNCTION_BLOCK")
        code_decl, code_impl = param.get("pou_code", ("", ""))
        ret_type = param.get("return_type", "")
        # Escape code for string literal
        code_decl = code_decl.replace("\\", "\\\\").replace("\n", "\\n")
        code_impl = code_impl.replace("\\", "\\\\").replace("\n", "\\n")
        pou_info = """
{{
"pou_name": "{0}",
"pou_type": "{1}",
"code_decl": "{2}",
"code_impl": "{3}",
"ret_type": "{4}"
}}
""".format(pou_name, pou_type, code_decl, code_impl, ret_type).strip()
        logger.info("POU name: %s", pou_name)
        pou_infos.append(pou_info)
        logger.info("POU info: %s", pou_info)
    pou_infos_str = "["+ ",\n".join(pou_infos) + "]"
    
    return """# -*- coding: utf-8 -*-
import scriptengine
import traceback
import time
import re
import json
import sys
import os


try:
    print("Starting project close script")
    # Check if we have an active project
    if not hasattr(session, 'active_project') or session.active_project is None:
        print("No active project in session")
        result = {{"success": False, "error": "No active project in session"}}
    else:
        # Get active project
        project = session.active_project
        print("Got active project")
        
        if hasattr(project, 'close'):
            try:
                print("Closing project using project.close() method")
                project.close()
                print("Project closed via close() method")
            except Exception as close_error:
                print("Error closing project via close() method: " + str(close_error))
                print("Will still try to clear session.active_project")
        else:
            print("Project has no close() method, will just clear session.active_project")
        
        # Clear session active project
        session.active_project = None
        
        print("Project close completed successfully")
except Exception as e:
    error_type, error_value, error_traceback = sys.exc_info()
    print("Error in project close script: " + str(error_value))
    print(traceback.format_exc())


try:
    print("Starting project open script")
    # Check if global instances are available
    if not hasattr(scriptengine, 'projects'):
        print("Global scriptengine.projects instance not found")
    else:
        try:
            # Open project using the global projects instance
            print("Using global scriptengine.projects instance to open project")
            project = scriptengine.projects.open("{0}")
            
            if project is None:
                print("Project open returned None")
                result = {{"success": False, "error": "Project open operation returned None"}}
            else:
                print("Project opened successfully, Storing project as active project in session")
                session.active_project = project
                
                # Get project info for result, with careful attribute checking
                project_info = {{"path": "{0}"}}  # Always include the path that was requested
                
                # Get actual path from project object if available
                if hasattr(project, 'path'):
                    project_info['path'] = project.path
                    print("Project path: " + project.path)
                    
                    # Try to extract name from path if name attribute is missing
                    if not hasattr(project, 'name'):
                        try:
                            project_info['name'] = os.path.basename(project.path)
                            print("Extracted name from path: " + project_info['name'])
                        except Exception as name_error:
                            project_info['name'] = os.path.basename("{0}")
                            print("Error extracting name from path, using request path basename instead")
                else:
                    print("Project has no path attribute, using request path")
                
                # Check for name attribute (if not already set above)
                if 'name' not in project_info and hasattr(project, 'name'):
                    project_info['name'] = project.name
                    print("Project name: " + project.name)
                elif 'name' not in project_info:
                    # Last resort - extract from the requested path
                    project_info['name'] = os.path.basename("{0}")
                    print("Using name from request path: " + project_info['name'])
                
                # Check for dirty attribute
                if hasattr(project, 'dirty'):
                    project_info['dirty'] = project.dirty
                    print("Project dirty flag: " + str(project.dirty))
                else:
                    project_info['dirty'] = False
                    print("Project has no dirty attribute, assuming False")
                
                # Return project info
                result = {{
                    "success": True,
                    "project": project_info
                }}
                print("Project open completed successfully")
        except Exception as e:
            print("Error opening project: " + str(e))
            print(traceback.format_exc())
            result = {{"success": False, "error": "Error opening project: " + str(e)}}
except Exception as e:
    error_type, error_value, error_traceback = sys.exc_info()
    print("Error in project open script: " + str(error_value))
    print(traceback.format_exc())
    result = {{"success": False, "error": str(error_value)}}

debug_info = "DEBUGGING INFO:\\n"

if not hasattr(session, 'active_project') or session.active_project is None:
    print("No active project in session")
    result = {{"success": False, "error": "No active project in session"}}
    raise Exception("No active project in session")


pou_infos = {1}
result = {{}}
pou_objs = []

pou_mapping = {{
    info["pou_name"]: info["pou_type"] for info in pou_infos
}}

# Try to get application
project = session.active_project
print("Got active project")
if not hasattr(project, 'active_application') or project.active_application is None:
    print("Project has no active application")
    result = {{"success": False, "error": "Project has no active application"}}
    raise Exception("Project has no active application")

application = project.active_application
print("Got active application")

def update_variable_type(program_code, new_types):
    pattern = re.compile(r"(VAR)(.*?)(END_VAR)", re.DOTALL)

    match = pattern.search(program_code)
    if not match:
        raise ValueError("No valid VAR ... END_VAR block found.")

    var_block_start = match.group(1)
    var_block_end = match.group(3)

    new_vars = ["test_{{}}: {{}};".format(i, new_type)
        for i, new_type in enumerate(new_types)
    ]
    new_var_block = "VAR\\n" + "\\n".join(new_vars) + "\\nEND_VAR"

    updated_code = program_code[:match.start()] + new_var_block + program_code[match.end():]
    return updated_code


def get_program(application):
    program_name = "PLC_PRG"
    programs = application.find(program_name)
    if len(programs):
        return programs[0]
    try:
        program = application.create_pou(
            name=program_name,
            type=scriptengine.PouType.Program
        )
        return program
    except Exception, e:
        print("Error creating program: " + str(e))
        result = {{"success": False, "error": "Error creating program: " + str(e)}}
        raise Exception("Error creating program: " + str(e))

# def get_and_replace_pou(project, pou_info):
#     try:
#         pou_name = pou_info.get('pou_name')

#         application = project.active_application
#         pous = application.find(pou_name, True)

#         #pous = projects.find(pou_name, True)
#         for pou in pous:
#             pou.textual_declaration.replace(pou_info.get('code_decl'))
#             pou.textual_implementation.replace(pou_info.get('code_impl'))
#             res = {{
#                 "success": True,
#                 "pou": {{
#                     "name": name,
#                     "type": pou_type
#                 }}
#             }}
#             return pou, res
#     except Exception, e:
#         print("Error getting and replacing POU: " + str(e))
#         result = {{"success": False, "error": "Error getting and replacing POU: " + str(e)}}
#         return None, result


def get_and_replace_pou(project, pou_info):
    try:
        pou_name = pou_info.get('pou_name')

        application = project.active_application
        if application is None:
            print("get Application failed")
            result = {{"success": False, "error": "Project has no active application"}}
            return None, result
        pous = application.find(pou_name, True)

        # pous = projects.find(pou_name, True)
        print("start replace pous")
        for pou in pous:
            print("enter for pou in pous")
            # Ensure code strings are not None to avoid "Value cannot be null" error
            code_decl = pou_info.get('code_decl') or "jk"
            code_impl = pou_info.get('code_impl') or "jk"
            pou.textual_declaration.replace(code_decl)
            pou.textual_implementation.replace(code_impl)
            res = {{
                "success": True,
                "pou": {{
                    "name": pou_name
                }}
            }}
            print("replace pous success")
            return pou, res
        
        # If no POU was found in the loop
        print("nothing matched - POU not found: " + pou_name)
        result = {{"success": False, "error": "POU not found: " + pou_name}}
        return None, result
    except Exception, e:
        print("Error getting and replacing POU: " + str(e))
        result = {{"success": False, "error": "Error getting and replacing POU: " + str(e)}}
        return None, result

def create_new_pou(project, pou_info):
    name = pou_info.get('pou_name')
    pou_type = pou_info.get('pou_type')
    declaration_text = pou_info.get('code_decl')
    implementation_text = pou_info.get('code_impl')
    ret_type = pou_info.get('ret_type')

    print("Starting POU creation script for %s" % name)
    application = project.active_application
    print("Got active application")

    container = application
    print("Using application object directly for POU creation")
    
    # Use the properly defined POU types and implementation languages
    try:
        # Map the string name to the actual PouType enum value
        print("Determining POU type for: %s" % pou_type)
        
        # Define POU type map according to the working example code
        pou_type_map = {{
            "PROGRAM": scriptengine.PouType.Program,
            "FUNCTION_BLOCK": scriptengine.PouType.FunctionBlock,
            "FUNCTION": scriptengine.PouType.Function
        }}
        
        # Get the POU type from the map
        if pou_type in pou_type_map:
            pou_type_value = pou_type_map[pou_type]
            print("Set POU type to %s" % pou_type)
        else:
            print("Unknown POU type: %s" % pou_type)
            result = {{"success": False, "error": "Unknown POU type: %s" % pou_type}}
            raise Exception("Unknown POU type: %s" % pou_type)
        
        print("Using default language: ST (None)")
        
    except Exception, e:
        print("Error resolving type values: " + str(e))
        result = {{"success": False, "error": "Error resolving type values: " + str(e)}}
        return None, result
    
    # Create POU with the correct parameters
    try:
        print("Creating POU: " + name)
        
        # Call with keyword arguments as shown in the example
        if pou_type == "FUNCTION":
            # For functions, return_type is required
            if not ret_type or ret_type.strip() == "":
                print("Error: return_type is required for FUNCTION but is empty")
                result = {{"success": False, "error": "return_type is required for FUNCTION type POU. Please specify a valid return type (e.g., BOOL, INT, REAL) in the function declaration."}}
                return None, result
            
            pou = container.create_pou(
                name=name,
                type=pou_type_value,
                return_type=ret_type
            )
            print("Created function with return type: " + ret_type)
        else:
            # For programs and function blocks, return_type should not be specified
            pou = container.create_pou(
                name=name,
                type=pou_type_value
            )
            print("Created POU without return type")
        
        if pou is not None:
            print("POU created successfully")

            pou.textual_declaration.replace(declaration_text)
            pou.textual_implementation.replace(implementation_text)

            print("POU updated successfully")

            result = {{
                "success": True,
                "pou": {{
                    "name": name,
                    "type": pou_type
                }}
            }}
            return pou, result
        else:
            print("POU creation failed - returned None")
            result = {{"success": False, "error": "POU creation failed - returned None"}}
    except Exception, e:
        print("Error creating POU: " + str(e))
        result = {{"success": False, "error": "Error creating POU: " + str(e)}}
    
    return None, result


def clean_app(application):
    try:
        print("Performing clean build")
        application.clean()
        print("Clean operation completed")
    except Exception, clean_error:
        print("Error during clean operation: " + str(clean_error))
        print("Will attempt to continue with build anyway")
    

def compile_pou(application, pou_objs, pou_mapping):
    start_time = time.time()
    print("Starting compile process...")

    compile_msgs = []

    def extract_line_number(text):
        match = re.search(r'(?:Line|行)[\\s:]*(\\d+)', text)
        if match:
            return int(match.group(1))
        else:
            return -1

    try:
        print("Compiling application...")
        application.build()
        print("Compiling operation completed")
        compilation_time = time.time() - start_time
        
        cates = system.get_message_categories(bActive=False)
        
        for cate in cates:
            if cate is None:
                continue
            desc = system.get_message_category_description(cate)
            build_desc_diff_lang = set(["Build", "编译"])  # supplyment by yourself if need language change
            levels = set([scriptengine.Severity.FatalError, scriptengine.Severity.Error]) # we only consider fatal errors and normal errors
            obj_names = set([obj.get_name() for obj in pou_objs])
            if desc in build_desc_diff_lang:
                print("Found compile message category, msgs:")
                msg_objs = system.get_message_objects(category=cate)
                for obj in msg_objs:
                    print("Obj pos: {{}}, desc: {{}}, ser: {{}}".format(obj.position_text, obj.text, obj.severity))
                compile_msgs = [
                    {{
                        "Path": extract_line_number(obj.position_text) if obj.position_text else -1,
                        "ErrorDesc": obj.text,
                        "IsDef": True if obj.position_text and "Decl" in obj.position_text else False,
                        "PouName": obj.object.get_name() if obj.object else "",
                        "ID": obj.prefix + "{{:0>4d}}".format(int(obj.number))
                    }}
                    for obj in msg_objs if obj.severity in levels and \\
                        obj.object and obj.object.get_name() in obj_names
                ]
                print(compile_msgs)

        result = {{
            "success": True,
            "message": "Build operation completed",
            "pous": [{{
                "name": pou.get_name(),
                "type": pou_mapping[pou.get_name()]
            }} for pou in pou_objs],
            "time": compilation_time,
            "Errors": compile_msgs
        }}
    except Exception, precompile_error:
        print("Error during precompile operation: " + str(precompile_error))
        print(traceback.format_exc())
        result = {{"success": False, "error": "Error during precompile operation: " + str(precompile_error)}}

    return result

try:
    for pou_info in pou_infos:
        pou_obj, result = get_and_replace_pou(project, pou_info)
        if not result["success"]:
            result["error"] += " POU creation failed"
            raise Exception("")
        pou_objs.append(pou_obj)
    
    # We'll try to make a reference of this pou in a default program to ensure pou be compiled in application.build()
    # program_obj = get_program(application)
    # new_textual_declaration = update_variable_type(
    #     program_obj.textual_declaration.text, [pou.get_name() for pou in pou_objs])
    # program_obj.textual_declaration.replace(new_textual_declaration)
    

    result = compile_pou(application, pou_objs, pou_mapping)
   # result["new_textual_declaration"] = new_textual_declaration
    if not result["success"]:
        result["error"] += " POU compilation failed"
        raise Exception("")
    
except Exception, err:
    print("Error during workflow: " + str(err))
    print(traceback.format_exc())
    if not result:
        result = {{"success": False, "error": "Error during workflow: " + str(err)}}

""".format(path, pou_infos_str)

