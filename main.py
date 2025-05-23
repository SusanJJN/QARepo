from utils import *
import sys

def parse_cli_args(args):
    """解析命令行参数并提取关键配置
    Args:
        args: sys.argv列表，包含命令行参数
    Returns:
        dict: 包含以下键的配置字典：
            repo_dir: 代码仓路径
            output_file: 输出文件路径
            repo_des: 仓库描述信息
    """
    params = {
        'repo_dir': '',
        'output_file': '',
        'repo_des': ''
    }
    
    for arg in args[1:]:  # 跳过第一个参数（脚本名称）
        if '=' in arg:
            key, value = arg.split('=', 1)
            if key in params:
                params[key] = value
    return params

if __name__ == "__main__":
    # 解析命令行参数
    cli_params = parse_cli_args(sys.argv)
    
    # 执行生成流程
    data_count = generate_training_data(
        repo_dir=cli_params['repo_dir'],
        output_file=cli_params['output_file'],
        repository_description=cli_params['repo_des']
    )
    print(f"成功生成 {data_count} 条训练数据")


# if __name__ == "__main__":
#     # 配置参数
#     repo_dir = 'D:/test2'
#     output_file = 'example.json'
#     repository_description = '当前代码仓是一个Python项目，实现了对分割模型的训练。'
    
#     # 执行生成流程
#     data_count = generate_training_data(repo_dir, output_file, repository_description)
#     print(f"成功生成 {data_count} 条训练数据")

# if __name__ == "__main__":
#     repo_dir = 'D:/test2'
#     output_file = 'example.json'
#     repository_description = '当前代码仓是一个Python项目，实现了对分割模型的训练。'

#     qa_data = []
#     func_dicts = []
#     for root, _, files in os.walk(repo_dir):
#         for file in files:
#             print(file)
#             # 修改点：支持多语言文件后缀
#             file_path = os.path.join(root, file)
#             ext = Path(file_path).suffix.lower()
#             # 允许的文件类型
#             if ext not in VALID_EXTENSIONS:
#                 continue
                
#             # 修改点：直接遍历所有支持的文件
#             for func in parse_functions(file_path, repo_dir):
#                 filtered_func = {
#                     **func,
#                     "metadata": {
#                         k: v for k, v in func["metadata"].items() 
#                         if k != "questions"
#                     }
#                 }
#                 func_dicts.append(filtered_func)

#                 qa_pairs = generate_qa_pair(func)
#                 for pair in qa_pairs:  # 优化循环变量名
#                     qa_data.append(pair)
                
#                 requirements = generate_requirement_metadata(func)
#                 for req in requirements:  # 优化循环变量名
#                     qa_data.append(generate_qa_pair2(req))

#     # print(qa_data)
#     for qa in qa_data:
#         qa['input'] = f"""{repository_description}包含以下函数：{str(func_dicts)}"""

#     # 保存训练数据
#     with open(output_file, "w", encoding="utf-8") as f:
#         json.dump(qa_data, f, indent=2, ensure_ascii=False)
#     print(f"成功生成 {len(qa_data)} 条训练数据")


# from utils import *

# if __name__ == "__main__":
    
#     repo_dir = 'D:/test'
#     output_file = 'result.json'

#     # 遍历所有Python文件
#     qa_data = []
#     for root, _, files in os.walk(repo_dir):
#         for file in files:
#             # if file.endswith(".py") and not file.startswith("test"):
#             file_path = os.path.join(root, file)
#             for func in parse_functions(file_path, repo_dir):
#                 # questions.append(generate_questions(func))
#                 qa_pairs = generate_qa_pair(func)
#                 for i in range(len(qa_pairs)):
#                     qa_data.append(qa_pairs[i])
#                 # qa_data.append(generate_qa_pair(func))

#                 requirements = generate_requirement_metadata(func)
#                 for i in range(len(requirements)):
#                     qa_data.append(generate_qa_pair2(requirements[i]))

#     # print(qa_data)
#     # 保存训练数据
#     with open(output_file, "w", encoding="utf-8") as f:
#         json.dump(qa_data, f, indent=2, ensure_ascii=False)
#     print(f"成功生成 {len(qa_data)} 条训练数据")

