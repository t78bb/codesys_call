# 示例：如何获取 POU 的定义部分和实现部分的代码内容

def get_pou_code_content(project, pou_name):
    """获取指定 POU 的声明和实现代码内容"""
    try:
        application = project.active_application
        pous = application.find(pou_name)

        for pou in pous:
            # 获取声明部分的代码
            declaration_code = pou.textual_declaration.text
            print("Declaration code for {}:".format(pou_name))
            print(declaration_code)
            print("-" * 50)

            # 获取实现部分的代码
            implementation_code = pou.textual_implementation.text
            print("Implementation code for {}:".format(pou_name))
            print(implementation_code)
            print("-" * 50)

            # 返回代码内容
            return {
                "pou_name": pou_name,
                "declaration": declaration_code,
                "implementation": implementation_code
            }

        # 如果没找到 POU
        return None

    except Exception, e:
        print("Error getting POU code: " + str(e))
        return None

# 使用示例
# pou_code = get_pou_code_content(session.active_project, "MyFunctionBlock")
# if pou_code:
#     print("Declaration:", pou_code["declaration"])
#     print("Implementation:", pou_code["implementation"])









