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


