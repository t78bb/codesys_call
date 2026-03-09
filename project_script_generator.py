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

def setup_prompt_answers_for_storage_upgrade():
    #Try to auto-answer storage format upgrade prompt with No.
    try:
        sys_obj = None
        try:
            sys_obj = scriptengine.system
        except Exception:
            try:
                sys_obj = system
            except Exception:
                sys_obj = None

        if sys_obj is None:
            print("system object unavailable, skip prompt setup")
            return

        # Keep normal prompt behavior and log message keys for diagnosis.
        if hasattr(scriptengine, 'PromptHandling'):
            try:
                sys_obj.prompt_handling = (
                    scriptengine.PromptHandling.ForwardSimplePrompts |
                    scriptengine.PromptHandling.LogMessageKeys
                )
            except Exception, e:
                print("Failed setting prompt_handling: " + str(e))

        if not hasattr(sys_obj, 'prompt_answers') or not hasattr(scriptengine, 'PromptResult'):
            print("prompt_answers or PromptResult unavailable, skip prompt auto-answer")
            return

        no_result = scriptengine.PromptResult.No
        # Exact key captured from runtime log.
        sys_obj.prompt_answers["LossOfDataWarning2"] = no_result
        # Candidate keys for storage format / upgrade prompts.
        candidate_keys = [
            "StorageFormatUpgrade",
            "UpgradeStorageFormat",
            "ProjectStorageFormatUpgrade",
            "ProjectFormatUpgrade",
            "AskUpgradeProjectStorageFormat",
            "UpgradeProjectFormat",
            "ProjectUpgrade"
        ]
        for key in candidate_keys:
            sys_obj.prompt_answers[key] = no_result
        print("Configured prompt_answers=No for storage upgrade candidates")
    except Exception, e:
        print("setup_prompt_answers_for_storage_upgrade failed: " + str(e))

setup_prompt_answers_for_storage_upgrade()


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
        print("pout_name: " + pou_name)
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
            # code_impl += "qwdqwe"

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
    max_compile_msgs = 2000

    def extract_line_number(text):
        match = re.search(r'(?:Line|行)[\\s:]*(\\d+)', text)
        if match:
            return int(match.group(1))
        else:
            return -1

    def safe_get_message_object_name(msg_obj):
        try:
            if not hasattr(msg_obj, 'object') or msg_obj.object is None:
                return ""
            return msg_obj.object.get_name()
        except Exception, e:
            print("Failed to get message object name: " + str(e))
            return ""

    def safe_get_message_id(msg_obj):
        try:
            if hasattr(msg_obj, 'prefix') and hasattr(msg_obj, 'number') and msg_obj.prefix is not None and msg_obj.number is not None:
                return msg_obj.prefix + "{{:0>4d}}".format(int(str(msg_obj.number)))
            return ""
        except Exception, e:
            print("Failed to build message id: " + str(e))
            return ""

    def safe_get_message_full_info(msg_obj):
        info = {{}}
        try:
            info["__type__"] = str(type(msg_obj))
        except Exception:
            info["__type__"] = ""
        try:
            info["__repr__"] = str(msg_obj)
        except Exception:
            info["__repr__"] = ""

        try:
            attr_names = dir(msg_obj)
        except Exception, e:
            info["__dir_error__"] = str(e)
            return info

        for attr in attr_names:
            if attr.startswith("__") and attr.endswith("__"):
                continue
            try:
                value = getattr(msg_obj, attr)
                if callable(value):
                    info[attr] = "<callable>"
                else:
                    try:
                        info[attr] = str(value)
                    except Exception:
                        info[attr] = "<unprintable>"
            except Exception, e:
                info[attr] = "<access_error: " + str(e) + ">"

        # Provide explicit nested object snapshot if present.
        try:
            if hasattr(msg_obj, 'object') and msg_obj.object is not None:
                nested = msg_obj.object
                nested_info = {{}}
                try:
                    nested_info["__type__"] = str(type(nested))
                except Exception:
                    nested_info["__type__"] = ""
                try:
                    nested_info["__repr__"] = str(nested)
                except Exception:
                    nested_info["__repr__"] = ""
                try:
                    nested_info["name"] = nested.get_name()
                except Exception, e:
                    nested_info["name"] = "<access_error: " + str(e) + ">"
                info["object_snapshot"] = nested_info
        except Exception, e:
            info["object_snapshot"] = "<access_error: " + str(e) + ">"

        return info

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
            precompile_desc_diff_lang = set(["Precompile", "Compile Information", "编译信息", "预编译"])  # precompile category
            levels = set([scriptengine.Severity.FatalError, scriptengine.Severity.Error]) # we only consider fatal errors and normal errors
            obj_names = set()
            for pou in pou_objs:
                try:
                    obj_names.add(pou.get_name())
                except Exception, e:
                    print("Skip invalid pou object while collecting names: " + str(e))

            # if desc in precompile_desc_diff_lang:
            #     print("Found precompile message category, msgs:")
            #     try:
            #         msg_objs = system.get_message_objects(category=cate)
            #     except Exception, e:
            #         print("Skip precompile category due to get_message_objects error: " + str(e))
            #         continue
            #     for obj in msg_objs:
            #         try:
            #             print("Obj pos: {{}}, desc: {{}}, ser: {{}}".format(obj.position_text, obj.text, obj.severity))
            #         except Exception, e:
            #             print("Failed to print precompile message object: " + str(e))

            #     for obj in msg_objs:
            #         try:
            #             if obj.severity not in levels:
            #                 continue

            #             pou_name = safe_get_message_object_name(obj)
            #             if pou_name and pou_name not in obj_names:
            #                 continue

            #             compile_msgs.append({{
            #                 "Path": extract_line_number(obj.position_text) if obj.position_text else -1,
            #                 "ErrorDesc": obj.text if hasattr(obj, 'text') else "",
            #                 "IsDef": True if obj.position_text and "Decl" in obj.position_text else False,
            #                 "PouName": pou_name,
            #                 "ID": safe_get_message_id(obj),
            #                 "ObjFull": safe_get_message_full_info(obj)
            #             }})

            #             if len(compile_msgs) >= max_compile_msgs:
            #                 compile_msgs.append({{
            #                     "Path": -1,
            #                     "ErrorDesc": "Compile message list truncated at limit: " + str(max_compile_msgs),
            #                     "IsDef": False,
            #                     "PouName": "",
            #                     "ID": ""
            #                 }})
            #                 break
            #         except Exception, e:
            #             print("Skip invalid precompile message object during collection: " + str(e))

            #     if len(compile_msgs) >= max_compile_msgs:
            #         break

            if desc in build_desc_diff_lang:
                print("Found compile message category, msgs:")
                try:
                    msg_objs = system.get_message_objects(category=cate)
                except Exception, e:
                    print("Skip build category due to get_message_objects error: " + str(e))
                    continue
                for obj in msg_objs:
                    try:
                        print("Obj pos: {{}}, desc: {{}}, ser: {{}}".format(obj.position_text, obj.text, obj.severity))
                    except Exception, e:
                        print("Failed to print compile message object: " + str(e))

                for obj in msg_objs:
                    try:
                        if obj.severity not in levels:
                            continue

                        pou_name = safe_get_message_object_name(obj)
                        # If message is bound to a specific object, keep project scope filtering.
                        if pou_name is None or (pou_name and pou_name not in obj_names):
                            continue

                        compile_msgs.append({{
                            "Path": extract_line_number(obj.position_text) if obj.position_text else -1,
                            "ErrorDesc": obj.text if hasattr(obj, 'text') else "",
                            "IsDef": True if obj.position_text and "Decl" in obj.position_text else False,
                            "PouName": pou_name,
                            "ID": safe_get_message_id(obj),
                            "ObjFull": safe_get_message_full_info(obj)
                        }})

                        if len(compile_msgs) >= max_compile_msgs:
                            compile_msgs.append({{
                                "Path": -1,
                                "ErrorDesc": "Compile message list truncated at limit: " + str(max_compile_msgs),
                                "IsDef": False,
                                "PouName": "",
                                "ID": ""
                            }})
                            break
                    except Exception, e:
                        print("Skip invalid compile message object during collection: " + str(e))

                if len(compile_msgs) >= max_compile_msgs:
                    break
                print(compile_msgs)

        safe_pous = []
        for pou in pou_objs:
            try:
                pou_name = pou.get_name()
                safe_pous.append({{
                    "name": pou_name,
                    "type": pou_mapping.get(pou_name, "UNKNOWN")
                }})
            except Exception, e:
                print("Skip invalid pou object while building result: " + str(e))

        result = {{
            "success": True,
            "message": "Build operation completed",
            "pous": safe_pous,
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

