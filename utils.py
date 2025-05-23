import ast
import astunparse
import os
import re
import json
from openai import OpenAI
from time import sleep
from pathlib import Path
from tree_sitter import Parser, Language

VALID_EXTENSIONS = {
    '.py', '.java', '.cpp', '.cc', '.cxx', '.h', '.hpp'
}

# 新增配置常量
API_CONFIG = {
    "api_key": "your-deepseek-key",
    "base_url": "https://api.deepseek.com",
    "model": "deepseek-chat",
}

# 修改现有client初始化
client = OpenAI(
    api_key=API_CONFIG["api_key"], 
    base_url=API_CONFIG["base_url"]
)

# 初始化多语言解析器
def init_parser(language):
    """初始化tree-sitter语言解析器
    Args:
        language: 目标编程语言 (python/java/cpp等)
    Returns:
        tuple: (解析器对象, 语言对象)
    Raises:
        Exception: 语言库加载失败时抛出异常
    """
    parser = Parser()
    try:
        print(f"正在加载{language}语言库，路径：{os.path.abspath('build/my-languages.so')}")
        # 返回语言对象和解析器
        LANGUAGE = Language('build/my-languages.so', language)
        print(f"语言对象加载成功：{LANGUAGE}")
        parser.set_language(LANGUAGE)
        return parser, LANGUAGE  # 返回解析器和语言对象
    except Exception as e:
        print(f"加载{language}语言失败：{str(e)}")
        raise

# 修改后的parse_functions函数
def parse_functions(file_path, repo_path, question_num=10):
    """解析文件并提取函数信息（支持多语言）
    Args:
        file_path: 绝对文件路径
        repo_path: 代码仓根目录路径
    Returns:
        list: 包含函数字典的列表，结构如下：
            [{
                "name": 函数名,
                "code": 完整代码,
                "file": 相对路径,
                "metadata": 元数据
            }]
    """
    functions = []
    try:
        ext = Path(file_path).suffix.lower()
        lang = ''
        if ext == '.py':
            lang = 'python'
        elif ext == '.java':
            lang = 'java'
        elif ext in VALID_EXTENSIONS:
            lang = 'cpp'
        print('lang: ', lang)
        if not lang:
            return functions
            
        # 根据不同语言使用不同解析方式
        if lang == 'python':
            return parse_python_functions(file_path, repo_path, question_num)
        else:
            return parse_tree_sitter_functions(file_path, repo_path, lang, question_num)
    except Exception as e:
        print(f"解析文件 {file_path} 失败：{str(e)}")
    return functions

# 新增通用解析函数
def parse_tree_sitter_functions(file_path, repo_path, lang, question_num=10):
    """使用Tree-sitter解析非Python语言文件提取函数信息
    Args:
        file_path: 绝对文件路径
        repo_path: 代码仓根目录路径
        lang: 目标语言 (java/cpp)
    Returns:
        list: 包含函数字典的列表，结构如下：
            [{
                "name": 函数名,
                "code": 完整代码,
                "file": 相对路径,
                "metadata": 元数据
            }]
    """
    functions = []
    try:
        parser, language = init_parser(lang)
        with open(file_path, "r", encoding='utf-8') as f:
            code = f.read()
        
        tree = parser.parse(bytes(code, "utf-8"))
        root_node = tree.root_node
        
        # 通用查询语句
        query_str = {
            'java': """
(class_declaration
  (class_body
    (method_declaration
      name: (identifier) @method_name)))""",
            'cpp': """
(function_definition
  declarator: (function_declarator
    declarator: (identifier) @function_name))"""
        }[lang]
        
        # 创建查询的正确方式
        query = language.query(query_str)
        captures = query.captures(root_node)
        
        # 提取函数信息
        for node, _ in captures:
            func_name = code[node.start_byte:node.end_byte]
            func_code = code[node.start_byte:node.end_byte]
            
            func_info = {
                "name": func_name,
                "code": func_code,
                "file": str(Path(file_path).relative_to(repo_path)),
                "metadata": None
            }
            
            print(f"正在处理函数：{func_name}")
            func_info["metadata"] = generate_function_metadata(func_name, func_code, question_num)
            sleep(1.5)
            
            functions.append(func_info)
            
    except Exception as e:
        print(f"解析{lang.upper()}文件失败：{str(e)}")
    return functions

def generate_function_metadata(func_name, func_code, question_num=10):
    """调用DeepSeek生成函数元数据（功能描述、逻辑步骤、相关问题）
    Args:
        func_name: 函数名称
        func_code: 函数完整代码
        question_num: 需要生成的问题数量
    Returns:
        dict: 包含以下键的字典：
            description: 功能描述
            logic_steps: 实现步骤列表
            questions: 相关问题文本
    """
    try:
        response = client.chat.completions.create(
            model=API_CONFIG["model"],
            messages=[{
                "role": "user",
                "content": f"""请分析以下Python函数的功能和实现逻辑：
                \n```python
                {func_code}
                ```\n
                按以下JSON格式回复：
                {{
                    "function_description": "函数主要功能的自然语言描述（不要出现'函数'字样）",
                    "logic_steps": ["步骤1", "步骤2", "步骤n"]
                }}
                说明要求：
                1. logic_steps用简洁中文描述，不要代码术语
                2. 直接返回json内容，不要以“json”这个词开头
                3. 对logic_steps里面的每个步骤以步骤的编号开头
                4. function_description只概括函数的最主要功能，以最简洁的语言描述
                """
            }],
            temperature=0.3,
            max_tokens=300
        )

        result = json.loads(response.choices[0].message.content.strip())
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{
                "role": "user",
                "content": f"""请生成{str(question_num)}种与『{result["function_description"].strip("。")}是如何实现的？』句式结构完全相同、仅替换疑问词（如如何→怎样/什么）和动词（实现→运作/达成）的提问方式，保持简短且不涉及具体细节
                说明要求：
                1. 用简洁中文
                2. 目的是对该功能的实现流程进行提问，不要对具体细节进行提问
                3. 生成的是结构相似、用词不同的提问句式
                4. 每个提问句以编号开头
                """
            }],
            temperature=0.3,
            max_tokens=300
        )

        return {
            "description": result["function_description"].strip("。"),
            "logic_steps": result["logic_steps"],
            "questions": response.choices[0].message.content.strip()
        }
    except Exception as e:
        print(f"GPT生成失败：{str(e)}")
        return {
            "description": f"{func_name}的实现流程",
            "logic_steps": ["自动生成逻辑步骤（详见代码实现）"],
            "questions": ""
        }

    
def generate_requirement_metadata(func_info, requirement_num=3):
    """调用DeepSeek生成扩展需求及实现方案
    Args:
        func_info: 包含函数元数据的字典
        requirement_num: 需要生成的需求数量
    Returns:
        list: 需求字典列表，结构如下：
            [{
                "requirement_description": 需求描述,
                "explanation": 实现方案,
                "logic_steps": 步骤列表
            }]
    """
    try:
        response = client.chat.completions.create(
            model=API_CONFIG["model"],
            messages=[{
                "role": "user",
                "content": f"""请根据以下对当前代码仓中函数的描述，生成{str(requirement_num)}种可实现的新增功能需求描述以及对应的解决方案以及逻辑步骤：
                \n```python
                {func_info['metadata']['description']}
                ```\n
                按以下JSON格式回复：
                {{
                    "requirement_description": "新增功能需求的自然语言描述",
                    "explanation": "对应的解决方案的描述",
                    "logic_steps": ["步骤1", "步骤2", "步骤n"]
                }}
                说明要求：
                1. logic_steps用简洁中文描述，不要代码术语
                2. 直接返回json内容，不要以“json”这个词开头
                3. 对logic_steps里面的每个步骤以步骤的编号开头
                4. explanation是要用简洁的语言对如何实现这个需求的解决方案进行描述，而不是对需求的进一步描述
                """
            }],
            temperature=0.3,
            max_tokens=5000
        )

        raw_content = response.choices[0].message.content.strip()
        json_blocks = re.findall(r'\{.*?\}(?=\s*\{|\Z)', raw_content, re.DOTALL)
        
        requirements = []
        for block in json_blocks:
            try:

                cleaned_block = re.sub(r',\s*$', '', block)
                requirement = json.loads(cleaned_block)
                requirements.append({
                    "requirement_description": requirement.get("requirement_description", ""),
                    "explanation": requirement.get("explanation", ""),
                    "logic_steps": requirement.get("logic_steps", [])
                })
            except json.JSONDecodeError as e:
                print(f"解析失败：{str(e)}\n内容片段：{block[:50]}...")

        return requirements
    except Exception as e:
        print(f"GPT生成失败：{str(e)}")
        return {
            "description": f"{func_name}的实现流程",
            "logic_steps": ["自动生成逻辑步骤（详见代码实现）"]
        }

def parse_python_functions(file_path, repo_path, question_num=10):
    """解析Python文件并提取函数元数据
    Args:
        file_path: 待解析文件的绝对路径
        repo_path: 代码仓根目录路径
    Returns:
        list: 包含函数信息的字典列表，结构如下：
            [{
                "name": 函数名,
                "code": 完整代码,
                "file": 相对路径,
                "metadata": 元数据字典
            }]
    """
    functions = []
    try:
        with open(file_path, "r",encoding='utf-8') as f:
            code = f.read()
        tree = ast.parse(code)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # 提取函数基本信息
                func_code = astunparse.unparse(node).strip()
                func_info = {
                    "name": node.name,
                    "code": func_code,
                    "file": str(Path(file_path).relative_to(repo_path)),
                    "metadata": None
                }
                
                # 调用GPT生成元数据
                print(f"正在处理函数：{node.name}")
                func_info["metadata"] = generate_function_metadata(node.name, func_code, question_num)
                sleep(1.5)  # 控制请求频率
                
                functions.append(func_info)
    except Exception as e:
        print(f"解析文件 {file_path} 失败：{str(e)}")
    return functions
    
def generate_qa_pair(func_info):
    """将函数信息转换为结构化QA训练数据
    Args:
        func_info: 包含函数信息的字典
    Returns:
        list: QA字典列表，结构如下：
            [{
                "instruction": 问题描述,
                "input": 补充上下文,
                "output": 包含实现细节的格式化回答
            }]
    """
    raw_questions = func_info['metadata']['questions'].split('\n')
    cleaned_questions = [
        q.split('. ', 1)[1].strip()  # 去除行首编号
        for q in raw_questions 
        if q.strip() and '. ' in q
    ]
    return [{
        "instruction": cleaned_questions[i],
        "input": '',
        "output": f"""{func_info['metadata']['description']}的实现方式：
• 实现函数：{func_info['name']}
• 文件位置：{func_info['file']}
• 实现步骤：
{chr(10).join(['  - ' + step for step in func_info['metadata']['logic_steps']])}
• 完整代码：
```python
{func_info['code']}
```"""
    } for i in range(len(cleaned_questions))]

def generate_qa_pair2(requirements):
    """将需求元数据转换为结构化QA训练数据
    Args:
        requirements: 包含需求信息的字典，结构为：
            {
                "requirement_description": 需求描述,
                "explanation": 实现方案,
                "logic_steps": 步骤列表
            }
    Returns:
        dict: 单个QA对字典，结构如下：
            {
                "instruction": 需求提问,
                "input": 补充上下文,
                "output": 包含实现方案的格式化回答
            }
    """

    return {
        "instruction": f"""如何{requirements['requirement_description']}""",
        "input": '',
        "output": f"""{requirements['requirement_description']}的实现方式：{requirements['explanation']};
实现步骤：
{chr(10).join(['  - ' + step for step in requirements['logic_steps']])}"""


    }

def generate_training_data(repo_dir, output_file, repository_description='', question_num=10, requirement_num=3):
    """生成代码仓训练数据集的主流程
    Args:
        repo_dir: 代码仓根目录路径
        output_file: 输出文件路径
        repository_description: 仓库描述信息
    Returns:
        int: 生成的QA对总数
    功能说明：
        1. 遍历代码仓所有有效文件
        2. 解析每个文件中的函数信息
        3. 生成实现原理QA对和需求扩展QA对
        4. 聚合数据并保存为JSON格式
    """
    qa_data = []
    func_dicts = []
    
    for root, _, files in os.walk(repo_dir):
        for file in files:
            file_path = os.path.join(root, file)
            ext = Path(file_path).suffix.lower()
            if ext not in VALID_EXTENSIONS:
                continue
                
            for func in parse_functions(file_path, repo_dir, question_num):
                filtered_func = {
                    **func,
                    "code": "",
                    "metadata": {
                        k: v for k, v in func["metadata"].items() 
                        if k != "questions"
                    }
                }
                func_dicts.append(filtered_func)
                
                # 生成QA数据
                qa_pairs = generate_qa_pair(func)
                qa_data.extend(qa_pairs)
                
                requirements = generate_requirement_metadata(func, requirement_num)
                for req in requirements:
                    qa_data.append(generate_qa_pair2(req))

    # 添加元数据
    for qa in qa_data:
        qa['input'] = f"""{repository_description}包含以下函数：{str(func_dicts)}"""

    # 保存结果
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(qa_data, f, indent=2, ensure_ascii=False)
    return len(qa_data)
