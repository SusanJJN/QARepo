该repository是一个针对本地代码仓业务功能生成问答对以微调Qwen模型的工具。支持python/java/cpp三种语言。主要代码位于utils.py以及main.py中。

# 使用方法：
1. 安装依赖库：pip install -r requirements.txt
2. 在main.py中修改DeepSeek的密钥，第17行"api_key"="your_deepseek_key"
3. 运行main.py，如： python main.py repo_dir=D:\test2 output_file=example.json repo_des="当前代码仓是一个Python项目，实现了对分割模型的训练。"

repo_dir是本地代码仓的路径，output_file是生成json文件的路径，repo_des是代码仓的描述。
4. 等待生成完成，生成的问答对会以存储在output_file中，每一个问答对的格式如下：（覆盖两个场景）
{
    'instruction':生成的问题,
    'input'：{
        'function_list':[func_dict1,func_dict2,...], #代码仓中所有函数信息的字典列表
        'repository_description':输入的代码仓描述

    }，# 该字段会以字符串形式存储，这里为了方便展示，用字典表示
    'output':生成的答案
}

其中func_dict的格式如下：
{
    'name':函数名
    'code':函数代码段，
    'file':函数所在的文件路径，
    'metadata':{
        'description':函数描述，
        'logic_steps':函数逻辑步骤，
    }
}

# Qwen模型微调
Qwen模型的微调是在AutoDL平台上完成，使用官方镜像https://www.codewithgpu.com/i/datawhalechina/self-llm/Qwen2.5-self-llm，相关代码存在Qwen2-7B-Lora.ipynb中

由于算力有限，微调使用的训练数据中删除了'input'字段中的'function_list'字段的'code'字段。notebook中保留了对两种场景提问的推理答案。

