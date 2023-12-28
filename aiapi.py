import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
# 请将这里的字符串替换为你的实际API密钥
api_key = "sk-XGrhLsiPQJy53ExWbD83b6eDxxxxx023644d0bBd0364F302F8600e"
base_url = "https://api.aiaiapi.com/v1"


# 定义一个函数，用于读取文件内容
def read_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        return f'读取文件 {file_path} 时发生错误: {e}'

# 定义一个函数，用于读取指定目录下所有Python文件的内容
def read_project_files(root_dir):
    contents = {}
    for root, dirs, files in os.walk(root_dir):
        for filename in files:
            # 检查文件扩展名是否是我们感兴趣的语言
            if filename.endswith('.py') or filename.endswith('.c') or \
                    filename.endswith('.ts') or filename.endswith('.tsx') or \
                    filename.endswith('.cpp') or filename.endswith('.cxx') or \
               filename.endswith('.cc') or filename.endswith('.java'):
                file_path = os.path.join(root, filename)
                file_content = read_file(file_path)  # 调用read_file函数获取内容
                contents[file_path] = file_content  # 将内容存储在字典中
    return contents


# 定义一个函数，用于向API发送代码内容并获取处理结果
def get_completion(file_path, code_content):
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    data = {
        "model": "gpt-4-1106-preview",
        "messages": [
            {"role": "system", "content": f"请对来自 {file_path} 的代码每一行都使用中文注释，只输出代码相关的注释，其他一概不要."},
            {"role": "user", "content": code_content}
        ],
    }
    max_retries = 3  # 设置最大重试次数
    retries = 0  # 初始化重试计数器

    while retries < max_retries:  # 循环直到达到最大重试次数
        response = requests.post(f"{base_url}/chat/completions", headers=headers, json=data)
        print(f"文件 {file_path} 的API响应: {response.status_code}")
        if response.status_code == 200:  # 如果响应状态码是200（成功）
            response_data = response.json()
            content_list = response_data['choices'][0]['message']['content']
            completion_content = "".join(content_list)  # 返回所有消息内容的拼接字符串
            # 去除Markdown代码块标识
            completion_content = completion_content.replace("```python\n", "").replace("```\n", "").replace("```", "")
            return completion_content
        else:
            retries += 1  # 增加重试计数器
            print(f"请求失败，正在重试... ({retries}/{max_retries})")
            if retries == max_retries:  # 如果达到最大重试次数
                return f"错误: {response.status_code}, {response.text}"  # 返回错误信息
            # 可以在这里添加延时等待，例如：time.sleep(1)

# 注意：如果你要使用time.sleep，请确保在文件顶部导入time模块

# 定义一个函数，用于将内容写入指定的输出目录文件
def write_output_to_file(output_dir, file_path, content):
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)  # 创建输出目录，如果不存在

        relative_path = os.path.relpath(file_path, project_root)  # 获取文件相对于项目根目录的路径
        output_file_path = os.path.join(output_dir, relative_path)  # 创建输出文件的完整路径
        output_file_dir = os.path.dirname(output_file_path)  # 获取输出文件的目录路径

        if not os.path.exists(output_file_dir):
            os.makedirs(output_file_dir)  # 创建输出文件的目录，如果不存在

        with open(output_file_path, 'w', encoding='utf-8') as file:
            file.write(content)  # 将内容写入文件
            file.flush()  # 强制刷新文件缓冲区

        # 为了调试，检查文件是否真的有内容
        with open(output_file_path, 'r', encoding='utf-8') as file:
            written_content = file.read()
            if written_content:
                print(f"文件已成功写入，并且内容不为空：{output_file_path}")
            else:
                print(f"文件已成功写入，但内容为空：{output_file_path}")

    except Exception as e:
        print(f"写入文件时出现错误：{e}")

# 修改后的程序的主执行逻辑
if __name__ == "__main__":
    project_root = r'D:\chatgpt\chatbox'  # 项目根目录路径
    output_root = r'D:\chatgpt\chatbox-oo'  # 输出根目录路径
    file_contents = read_project_files(project_root)  # 获取项目文件内容

    # 创建线程池执行器，指定最大工作线程数，例如10
    with ThreadPoolExecutor(max_workers=100) as executor:
        # 创建一个future到文件路径的映射
        future_to_file_path = {executor.submit(get_completion, file_path, content): file_path for file_path, content in file_contents.items()}

        # 遍历完成的future
        for future in as_completed(future_to_file_path):
            file_path = future_to_file_path[future]
            try:
                completion_response = future.result()
                if completion_response.startswith("错误: "):  # 如果返回错误消息
                    print(completion_response)  # 打印错误消息
                else:
                    write_output_to_file(output_root, file_path, completion_response)  # 将响应写入文件
                    print(f'文件 {file_path} 的输出已写入')
                    print('-' * 80)
            except Exception as exc:
                print(f'文件 {file_path} 生成异常: {exc}')