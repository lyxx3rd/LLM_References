
import fitz  # PyMuPDF
from tqdm import tqdm
import requests
import json
import re
import os
import random
import tkinter as tk
from tkinter import scrolledtext,ttk
from scholarly import scholarly
import time
import arxiv
import numpy as np
from tkinter import messagebox

global_qianfan_api_key = ""
global_qianfan_se_key = ""
global_volces_key = ""

def get_global_api_keys():
    """获取全局变量"""
    global global_volces_key, global_qianfan_api_key, global_qianfan_se_key
    return global_volces_key, global_qianfan_api_key, global_qianfan_se_key
def set_global_api_keys(volces_key="", api_key="", secret_key=""):
    """设置全局变量"""
    global global_volces_key, global_qianfan_api_key, global_qianfan_se_key

    if len(volces_key) > 5:
        global_volces_key = volces_key
    if len(api_key) > 5 and len(secret_key) > 5:
        global_qianfan_api_key = api_key
        global_qianfan_se_key = secret_key
    

def volces_api_test(volces_api):
    content = "你好"
    url = 'https://ark.cn-beijing.volces.com/api/v3/chat/completions'
    headers = {
        'Authorization': volces_api,
        'Content-Type': 'application/json'  # 添加这个header确保服务器知道我们发送的是JSON数据。
    }
    data = {
        "model": "ep-20250119174343-k5t6p",
        "messages": [
            {
                "role": "user",
                "content": content
            }
        ],
        "stream": False,
        "temperature":0.6,

    }

    response = requests.post(url, headers=headers, json=data)
    ans = response.status_code
    if response.status_code == 200:
        set_global_api_keys(volces_key=volces_api)
        return "测试通过"
    else: 
        return "api_code异常或网络异常"


def qianfan_api_test(API_Key, Secret_Key):
    url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={API_Key}&client_secret={Secret_Key}"

    payload = json.dumps("")
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    if response.status_code == 200:
        set_global_api_keys(volces_key="", api_key=API_Key, secret_key=Secret_Key)
        return "测试通过"
    else: 
        return "api_code异常或网络异常"
    
def volces_chat(content,system_messages="你是一个有用的助手"):
    volces_api,_,_ = get_global_api_keys()
    url = 'https://ark.cn-beijing.volces.com/api/v3/chat/completions'
    headers = {
        'Authorization': volces_api,
        'Content-Type': 'application/json'  # 添加这个header确保服务器知道我们发送的是JSON数据。
    }
    data = {
        "model": "ep-20250119174343-k5t6p",
        "messages": [
            {
                "role": "system",
                "content": system_messages
            },
            {
                "role": "user",
                "content": content
            }
        ],
        "stream": False,
        "temperature":0.4,
    
    }

    response = requests.post(url, headers=headers, json=data)
    ans = response.json()['choices'][0]['message']['content']
    return ans

def extract_text_with_pymupdf(pdf_path):
    document = fitz.open(pdf_path)
    text = ""
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        text += page.get_text("text")
    return text

def modify_ref(input_content):
    input_str = f"""我正在整理一个论文的引用的内容, 但是在提取引用时产生了大量的干扰和错误字符, 请为我整理成标准的引用格式,剔除干扰信息, 提取标准格式。如输入内容已经是标准格式, 则输出原内容。
格式说明:包含在一个括号内部, 由一个人名开头, 由一个年份结尾, 参考格式为(人名 et al., 年份), 如果因为缺人名或缺时间或其他任何原因导致无法生成, 则回复'格式错误'
<正确的引用格式>:(Trivedi et al., 2022)<正确的引用格式>

<错误的引用格式>:(Trivedietal.,
1 Introduction
2022)<错误的引用格式>

待提取内容:{input_content}"""
    ans = volces_chat(input_str)
    return ans

def find_years_in_string(input_str):
    # 定义正则表达式模式，匹配四位数字，通常年份范围为 1000 到 2999
    pattern = r'\b(1[0-9]{3}|2[0-9]{3})\b'
    
    # 使用 re.findall 查找所有匹配的年份
    matches = re.findall(pattern, input_str)
    
    if matches:
        #print("Found years:", matches)
        return True
    else:
        #print("No years found.")
        return False

def process_parentheses_APA(text_output):
    stack = []
    last_location = 0
    i = True
    original_list = []
    index_list = []

    while i:
        start_location = text_output.find("(", last_location)
        if start_location == -1:  # 如果找不到左括号，退出循环
            break
        
        end_location = text_output.find(")", start_location + 1)
        if end_location == -1:  # 如果找不到右括号，也退出循环
            print("Error: No closing parenthesis found.")
            break
        
        # 将当前左括号位置压入栈中
        stack.append(start_location)
        
        # 查找是否有更多的左括号在当前左括号和右括号之间
        next_location = text_output.find("(", start_location + 1)
        while next_location != -1 and next_location < end_location:
            # 弹出栈顶元素，因为我们找到了一个更深的左括号
            stack.pop()
            stack.append(next_location)
            next_location = text_output.find("(", next_location + 1)
        
        # 找到最内层的括号对并打印
        real_start_location = stack.pop()
        content = text_output[real_start_location:end_location + 1]
        #print(find_years_in_string(content))
        if find_years_in_string(content):
            original_list.append(content)
            index_list.append([real_start_location,end_location + 1])
        #else:
            #print(content, find_years_in_string(content))
        
        # 更新 last_location 到当前右括号之后的位置
        last_location = end_location + 1
    
    ## 返回列表
    return original_list,index_list

def process_square_IEEE(text_output):
    stack = []
    last_location = 0
    original_list = []
    index_list = []

    while True:
        start_location = text_output.find("[", last_location)
        if start_location == -1:  # 如果找不到左方括号，退出循环
            break
        
        end_location = text_output.find("]", start_location + 1)
        if end_location == -1:  # 如果找不到右方括号，也退出循环
            print("Error: No closing square bracket found.")
            break
        
        # 查找是否有更多的左方括号在当前左方括号和右方括号之间
        next_location = text_output.find("[", start_location + 1)
        while next_location != -1 and next_location < end_location:
            # 这里我们不使用栈来处理嵌套情况，因为对于[numbers]格式，
            # 我们只关心最内层的匹配，即直接配对的[]。
            # 所以，如果找到更深一层的左方括号，则忽略之前的匹配。
            start_location = next_location
            end_location = text_output.find("]", start_location + 1)
            next_location = text_output.find("[", start_location + 1)
        
        # 确保我们找到了一个有效的[number]格式
        content = text_output[start_location:end_location + 1]
        lab_temp = content[1:-1].strip()
        lab_temp = lab_temp.replace(" ", "")
        lab_temp = lab_temp.replace(",", "")
        lab_temp = lab_temp.replace(".", "")
        if lab_temp.isdigit():  # 检查是否为纯数字（去除首尾的方括号后）
            original_list.append(content)
            index_list.append([start_location, end_location + 1])
        
        # 更新last_location到当前右方括号之后的位置
        last_location = end_location + 1
    
    return original_list, index_list


def list_pdf_files(folder_path):
    """
    列出指定文件夹中所有PDF文件的名称（不递归进入子文件夹）。
    
    参数:
        folder_path (str): 要检查的文件夹路径。
        
    返回:
        list: 文件夹中所有PDF文件的名称列表。
    """
    pdf_files = []
    # 获取文件夹中的所有文件名
    if not os.path.isdir(folder_path):  # 如果不是文件夹，则返回空列表
        return []
    for file_name in os.listdir(folder_path):
        # 构建完整路径
        full_path = os.path.join(folder_path, file_name)
        # 检查是否是文件且扩展名为.pdf
        if os.path.isfile(full_path) and file_name.lower().endswith('.pdf'):
            pdf_files.append(file_name)
    return pdf_files


def start_project(file_path):
    if not os.path.isdir(f"{file_path}/project"):
        os.mkdir(f"{file_path}/project")

    ## 创建项目
    user_input = get_bibtex_name()
    if not os.path.isdir(f"{file_path}//project/{user_input}"):
        print(f"未检测到项目, 自动创建项目:{user_input}")
        os.mkdir(f"{file_path}//project/{user_input}")
    else:
        print(f"已启动项目:{user_input}")

    ## 创建pdf文件夹
    if not os.path.isdir(f"{file_path}//project/{user_input}/pdf"):
        os.mkdir(f"{file_path}//project/{user_input}/pdf")
    else:
        pdf_num = len(list_pdf_files(f"{file_path}//project/{user_input}/pdf"))
        print(f"当前项目中论文数量为:{pdf_num}")

    ## 创建data文件夹
    if not os.path.isdir(f"{file_path}//project/{user_input}/data"):
        os.mkdir(f"{file_path}//project/{user_input}/data")

    ## 创建extract_dict.json
    if not os.path.isfile(f"{file_path}/project/{user_input}/data/ref_extract_info_dict.json"):
        #print("创建extract_dict.json")
        with open(f"{file_path}/project/{user_input}/data/ref_extract_info_dict.json", "w") as f:
            json.dump({}, f)
    
    ## 创建ref_appendix_dictences.json
    if not os.path.isfile(f"{file_path}//project/{user_input}/data/ref_extract_appendix_dict.json"):
        #print("创建ref_appendix_dictences.json")
        with open(f"{file_path}/project/{user_input}/data/ref_extract_appendix_dict.json", "w") as f:
            json.dump({}, f)
    
    return(user_input)

def refine_refname(ref):
    ref = ref.replace('etal', 'et al')
    ref = ref.replace(' et al', 'et al')
    ref = ref.replace('et al', ' et al')
    ref = ref.replace('-', '')
    ref = ref.replace('\n', '').strip()

    if not ref.startswith('('):
        ref = '(' + ref
    if not ref.endswith(')'):
        ref += ')'

    ref = ref.replace('( ', '(')
    ref = ref.replace(' )', ')')
    ref = ref.replace(',2', ', 2')
    ref = ref.replace(',1', ', 1')
    ans = modify_ref(ref)
    return ans

def split_references(reference_dict):
    output_dict = reference_dict.copy()

    ref_set_list = []
    for i in tqdm(reference_dict.keys()):
        result = []
        ref = reference_dict[i]["original_ref"]
        # 如果没有分号，直接添加到结果列表中
        parts = ref.split(';')
        for part in parts:
            ans = refine_refname(part)
            result.append(ans)
            ref_set_list.append(ans)
        
        output_dict[i]["sub_list"] = result

    
    return output_dict,ref_set_list

def create_popup_window(output_text):
    """
    创建一个带有滚动条的文本框窗口来显示长输出。
    
    参数:
        output_text (str): 要显示的长输出文本。
    """
    # 创建主窗口
    root = tk.Tk()
    root.title("输出窗口")
    root.geometry("600x400")  # 设置窗口大小

    # 创建滚动文本框
    text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=70, height=20)
    text_area.pack(expand=True, fill='both')

    # 插入文本
    text_area.insert(tk.INSERT, output_text)

    # 禁用编辑
    text_area.configure(state='disabled')

    # 运行主循环
    root.mainloop()

def process_newlines(input_str):
    # 第一步：查找所有句号后面紧跟换行符的情况，并用特殊标记替换它们
    # 这里我们用一个临时的特殊标记来保存这些位置，以便后续恢复
    special_marker = "SPECIAL_MARKER"
    pattern = r'\.\n'
    temp_str, num_subs = re.subn(pattern, f'.{special_marker}', input_str)
    
    # 第二步：删除所有剩余的换行符
    temp_str = temp_str.replace('\n', '')
    
    # 第三步：恢复特殊标记为原始的句号+换行符
    final_str = temp_str.replace(special_marker, '\n')
    
    return final_str

def modify_references_content(ref_list):
    new_ref_list = []
    new_ref = ""
    for ref in tqdm(ref_list):
        point = ref.find(",")
        if point != -1:
            #print(ref[0:point])
            ans = volces_chat(f"判断给出内容是否是人名, 回答为是或否, 内容为:{ref[0:point]}")
            #print(ans)
            if ans == "是":
                if new_ref != "":
                    new_ref_list.append(new_ref)
                new_ref = ref
            else:
                new_ref = new_ref + ref
        else:
            new_ref = new_ref + ref
    new_ref_list.append(new_ref)
    return new_ref_list

def is_four_digit_number(s):
    return s.isdigit() and len(s) == 4

        
def is_year_str(s):
    """
    判断字符串是否为有效年份格式：4位数字后面紧跟一个且仅一个小写字母。
    """
    return bool(re.match(r'^\d{4}[a-z]$', s))

def is_four_digit_number(s):
    s = s.strip()
    return s.isdigit() and len(s) == 4

def review_ref(ref_list):
    print("正在检测文献信息是否正确..., 原始列表数量为:",len(ref_list))
    new_list = []
    for ref_temp in ref_list:
        i = 0
        for temp_str in ref_temp.split("."):
            if is_four_digit_number(temp_str.strip()):
                i = i+1
            elif is_year_str(temp_str.strip()):
                i = i+1
        if i >= 2:
            #print(f"有{i}个年份")
            #print(ref_temp)
            ans = volces_chat(f"我正在整理我的文献附录, 我怀疑我的引用信息里包含{i}个论文, 如果是我判断错误, 即包含一个论文的话, 请返回原内容, 如果确实包含多个论文, 请用分号';'进行切分!\n我提供的文献信息:\n{ref_temp}")
            temp_list = ans.split(";")
            new_list.extend(temp_list)
            #return False
        elif i == 0:
            print("没有年份")
            print(ref_temp)
            #return False
        elif i == 1:
            new_list.append(ref_temp)
    print("检测成功! 纠正后数量为:",len(new_list))
    return new_list

def search_ref(author_name, year, ref_list):
    for ref in ref_list:
        ref_name_list = ref.split('.')[0]
        ref_chief_name = ref_name_list.split(',')[0]
        tag1 = ref.find(author_name)
        tag2 = ref.find(year)
        if tag1 != -1 and tag2 != -1:
            return ref
        
    for ref in ref_list:
        tag1 = ref.find(author_name[0])
        tag2 = ref.find(year)
        if tag1 != -1 and tag2 != -1:
            return ref

def extract_name_and_year(test_str):
    list_temp = test_str.split(' ')
    year = str(list_temp[-1][:-1])
    list_temp = list_temp[0].split('and')[0]
    name = list_temp[1:]
    name = name.replace(',','')
        
    return name,year

def remove_symbols(text):
    # 使用正则表达式只保留文字和数字，\w匹配任何单词字符(等价于[a-zA-Z0-9_])
    # 为了支持Unicode字符，使用re.U标志，并且修改模式为匹配Unicode中的Letter和Number类别
    return re.sub(r'[^\w\u4e00-\u9fff]', '', text, flags=re.U)

def get_bibtex_from_dblp(title):
    #print("Dblp:",title)
    # 替换空格为加号，并对特殊字符进行URL编码
    search_query = requests.utils.quote(title.replace(' ', '+'))

    # 构建DBLP搜索API的URL
    url = f"https://dblp.org/search/publ/api/?q={search_query}&format=json&h=150"

    # 发送请求
    response = requests.get(url)
    data = response.json()
    return data

def remove_non_word_chars(s):
    # 使用正则表达式匹配字符串开头和结尾的非文字字符
    s = re.sub(r'^\W+', '', s)  # 去掉开头的非文字字符
    s = re.sub(r'\W+$', '', s)  # 去掉结尾的非文字字符
    return s

def check_paper_and_author_name(paper_name, title_searched,author, author_seached):
    ans = volces_chat(f"我正在进行论文检索, 但是检索的内容经常会出现异常字符, 我需要你通过论文名称和作者名称判断是否为同一篇论文! \n我提供的论文:\n[论文名称]:{paper_name}\n[作者名称]:{author}\n\n检索出的论文:\n[论文名称]:{title_searched}\n[作者名称]:{author_seached}\n\n判断这是否是我检索的对象论文? 只回复是或否")
    return ans

def search_paper_from_dblp(title,author):

    try:
        data = get_bibtex_from_dblp(title)
        if data['result']['completions']['@total'] == '0':
            return False,"未检索到论文,论文检索反馈数量为0"
    except:
        return False,"检索失败"

    try:
        dict = data["result"]['hits']['hit']
    except:
        return False,f"key值信息错误错误"


    for i in range(len(data["result"]['hits']['hit'])):
        title_searched = data["result"]['hits']['hit'][i]['info']["title"]
        title_searched = remove_non_word_chars(title_searched)
        if remove_symbols(title) == remove_symbols(title_searched):
            if type(data["result"]['hits']['hit'][i]['info']['authors']["author"]) == list:
                author_seached = data["result"]['hits']['hit'][i]['info']['authors']["author"][0]["text"]
            elif type(data["result"]['hits']['hit'][i]['info']['authors']["author"]) == dict:
                author_seached = data["result"]['hits']['hit'][i]['info']['authors']["author"]["text"]
            ans = check_paper_and_author_name(title,title_searched,author,author_seached)
            if ans == "是":
                paper_info_dict = (data["result"]['hits']['hit'][i]['info'])
                author_name_list = []
                for author in paper_info_dict['authors']['author']:
                    #print(author)
                    try:
                        author_name_list.append(author['text'])
                    except:
                        print("dblp author error, info:",author)
                        return False,f"作者信息错误"
                paper_info_dict['authors'] = clean_name_list(author_name_list)
                return True,paper_info_dict,
        #else:
            #print("作者不匹配",author,data["result"]['hits']['hit'][i]['info']['authors']["author"][0]["text"])

    
    return False,f"返回{data['result']['completions']['@total']}个论文,未完全匹配"


def get_bibtex_from_semanticscholar(title):
    # 设置你的查询参数
    fields = "title,authors,venue,year,abstract"  # 返回的字段
    limit = 1  # 返回的结果数量

    # 构造请求URL
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={title}&fields={fields}&limit={limit}"

    # 发送GET请求
    response = requests.get(url)

    # 检查请求是否成功
    if response.status_code == 200:
        # 解析响应数据
        data = response.json()
        # 打印结果
        return data
    else:
        print(f"请求失败，状态码：{response.status_code}")
        return False

def search_paper_from_semanticscholar(title,author):
    data = get_bibtex_from_semanticscholar(title)
    if data == False:
        return False,"检索异常! 过于频繁或网络问题!",""
    title_searched = data['data'][0]['title']
    try:
        abstract_searched = data['data'][0]['abstract']
    except:
        abstract_searched = ""
    if abstract_searched == None:
        abstract_searched = ""
    author_searched = data['data'][0]['authors'][0]['name']
    ans = check_paper_and_author_name(title, title_searched, author, author_searched)
    if ans == "是":
        paper_info_dict = data['data'][0]
        author_name_list = []
        for author in paper_info_dict['authors']:
            #print(author)
            author_name_list.append(author['name'])
        paper_info_dict['authors'] = clean_name_list(author_name_list)
        del(paper_info_dict['abstract'])
        return True,paper_info_dict,abstract_searched
    else:
        return False,"返回1个论文,未完全匹配",""
    
def check_papertitle_from_google(title,author):
    # 论文名称
    #paper_title = "Deep Residual Learning for Image Recognition"
    abstract_searched = ""
    # 开始搜索
    try:
        search_query = scholarly.search_pubs(title)
        
    # 获取第一个结果
    
        first_result = next(search_query)
        title_searched =  first_result['bib']['title']
        author_searched = first_result['bib']['author']
        abstract_searched = first_result['bib']['abstract']
        ans = check_paper_and_author_name(title, title_searched,author, author_searched)
        if ans == "是":
            #if title_searched.lower() == title.lower():
                #print("论文名称验证成功")
            #else:
                #print(f"已经纠正论文名称, 原名称{title}, 修正名称{title_searched}")
            modified_title = title_searched
        else:
            #print("论文名称不匹配")
            #print(f"检索的论文名称:{title_searched}\n检索的论文的作者名称:{author_searched}")
            modified_title = title
        
    except StopIteration:
        modified_title = title
        abstract_searched = ""
        print("Google Scholar未找到论文")
    except Exception as e:
        # 捕获所有其他类型的异常
        print(f"发生未知错误: {e}")
        modified_title = title
        abstract_searched = ""
    
    # 执行休眠, 随机休眠0.5~0.8秒
    time.sleep(random.uniform(0.5, 0.8))
    #print("Googlel title:",modified_title)

    return modified_title,abstract_searched

def generate_bibtex(paper_info_dict,source):
    bibtex_dict = {}
    ans = volces_chat(f"将下面给出的论文的信息生成为标准的bibtex格式, 只返回bibtex的引用内容! 返回禁止任何说明及备注! 如果含有多篇论文信息, 只生成顺位第一篇!\n<论文信息>:\n{str(paper_info_dict)}")
    ans = ans.replace("```bibtex\n","")
    ans = ans.replace("\n```","")
    list_temp = ans.split("\n")
    bibtex_name = list_temp[0][list_temp[0].find("{")+1:-1].strip()
    bibtex_dict['bibtex_name'] = bibtex_name
    bibtex_dict['source'] = source
    bibtex_dict['bibtex_content'] = ans
    return bibtex_dict

def clean_name_list(authors):

    # 定义一个正则表达式模式来匹配名字中的数字部分
    pattern = re.compile(r'\s\d{4}$')

    # 清理作者名单
    cleaned_authors = [pattern.sub('', author) for author in authors]

    return cleaned_authors

def check_connectivity(url="https://scholar.google.com.hk/?hl=zh-CN", timeout=2):
    try:
        response = requests.get(url, timeout=timeout)
        # 如果状态码为200，则认为连通性测试成功
        if response.status_code == 200:
            return '网络正常'
    except requests.RequestException as e:
        # 捕获所有可能的请求异常，包括超时
        pass
    
    return '网络异常'

def find_common_index(k_list, v_list, source_list=None, dk=None, dv=None, fix_source=False):
    """
    查找两个值在各自列表中的索引，确保这些索引相同。
    
    :param k_list: 包含键值的列表
    :param v_list: 包含数值的列表
    :param source_list: 包含来源信息的列表（可选）
    :param dk: 要查找的键值
    :param dv: 要查找的数值
    :param fix_source: 是否需要检查来源信息，默认为 False
    :return: 如果找到相同的索引，则返回 (True, index)；否则返回 (False, None)。
    """

    if fix_source and source_list is None:
        raise ValueError("当 fix_source 为 True 时，必须提供 source_list 参数")

    for index, (key, value) in enumerate(zip(k_list, v_list)):
        if key == dk and value == dv:
            if fix_source:
                if source_list[index] != "Generation":
                    return True, index
            else:
                return True, index

    # 如果没有找到匹配项
    return False, None

def search_arxiv(query, max_results=5):
    client = arxiv.Client()

    # 创建搜索查询对象
    search = arxiv.Search(
        query=query,  # 搜索关键词
        max_results=max_results,  # 返回结果的最大数量
        #sort_by=arxiv.SortCriterion.SubmittedDate,  # 排序依据（可选）
        #sort_order=arxiv.SortOrder.Descending  # 降序排序（可选）
    )

    # 将结果转换为列表以确保可以多次访问
    results = list(client.results(search))

    return results

def preprocess_arxiv(text):
    """预处理函数：转换为小写并移除标点符号"""
    text = text.lower()
    # 保留字母、数字和空格，去除其他字符
    return ''.join(char for char in text if char.isalnum() or char.isspace())

def calculate_similarity(str1, str2):
    """计算两个字符串的相似度，基于顺序的单词重复度"""
    # 预处理输入字符串
    str1 = preprocess_arxiv(str1)
    str2 = preprocess_arxiv(str2)

    # 将字符串拆分成单词列表
    words1 = str1.split()
    words2 = str2.split()

    # 初始化计数器
    match_count = 0
    i, j = 0, 0

    # 双指针遍历两个单词列表
    while i < len(words1) and j < len(words2):
        if words1[i] == words2[j]:
            match_count += 1
            i += 1
            j += 1
        else:
            # 如果当前单词不匹配，移动指向较短单词序列的指针
            if i >= len(words1) or (j < len(words2) and words1[i] != words2[j]):
                j += 1
            elif j >= len(words2) or (i < len(words1) and words1[i] != words2[j]):
                i += 1

    # 计算最大可能匹配数，用于归一化
    max_possible_matches = min(len(words1), len(words2))
    
    # 返回相似度分数，范围从0到1
    similarity_score = match_count / max_possible_matches if max_possible_matches > 0 else 0
    return similarity_score


def get_arxiv_bibtex(paper):
  
    authors = " and ".join([f"{author.name}" for author in paper.authors])
    title = paper.title
    year = paper.published.year
    eprint = paper.entry_id.split('/')[-1]

    bibtex = f"""@article{{{authors.split(" ")[1]}{year}{title.split(" ")[0] + title.split(" ")[1]},
author={{{authors}}},
title={{{title}}},
journal={{arXiv preprint arXiv:{eprint}}},
year={{{year}}},
eprint={{{eprint}}},
archivePrefix={{arXiv}},
primaryClass={{{paper.primary_category}}},
url={{{paper.entry_id}}},
}}
"""
    return bibtex

def search_paper_from_arxiv(query, author):
    data = search_arxiv(query, 6)

    title_list = []
    for result in data:
        #print(f"Title: {result.title}")
        title_list.append(result.title)
    #print(title_list)
    try:
        most_similar = max(title_list, key=lambda x: calculate_similarity(query, x))
        similarity_score = calculate_similarity(query, most_similar)
        target_index = title_list.index(most_similar)
        title = str(data[target_index].title)
        author_seached = str(data[target_index].authors[0])
        abstract = str(data[target_index].summary)
        #print(f"Most similar title: {most_similar}")
        #print(f"Similarity authors: {author_seached}")
        ans = check_paper_and_author_name(query, most_similar,author, author_seached)
        if ans == "是":
            bibtex_entry = get_arxiv_bibtex(data[target_index])
            list_temp = bibtex_entry.split("\n")
            bibtex_name = list_temp[0][list_temp[0].find("{")+1:-1].strip()
            return True, most_similar, author_seached, abstract, bibtex_name, bibtex_entry
        else:
            return False, most_similar, author_seached, abstract, "", ""
    except:
        return False, "", "", "", "", ""
    
def find_references(text_output):
    start_str = "\nReferences\n"
    start_str_location = text_output.find(start_str)

    if start_str_location == -1:
        start_str = "\nREFERENCES\n"
        start_str_location = text_output.find(start_str)
    
    if start_str_location == -1:
        start_str = "\nBibliography\n"
        start_str_location = text_output.find(start_str)
    
    if start_str_location == -1:
        print("没有找到参考文献标识, 请手动输入!")
        start_str = input("请输入引用标识的起始字符:")
        end_str = input("请输入引用标识的结束字符, 如果没有请输入'0':")
        
        if end_str == '0':
            references = text_output[text_output.find(start_str):]
        else:
            references = text_output[text_output.find(start_str):text_output.find(end_str)]
    else:
        # 查找结束标识
        possible_end_locations = [
            text_output.find("\nA\n", start_str_location + len(start_str)),
            text_output.find("\nA ", start_str_location + len(start_str)),
            text_output.find("\nAppendix", start_str_location + len(start_str))
        ]
        
        end_str_location = min([loc for loc in possible_end_locations if loc != -1], default=-1)
        
        if end_str_location != -1:
            references = text_output[start_str_location + len(start_str):end_str_location]
        else:
            references = text_output[start_str_location + len(start_str):]
        
        # 检查提取的参考文献长度是否合理
        if len(references.strip()) < 100:  # 假设参考文献至少有100个字符
            print("没有找到参考文献标识, 请手动输入!")
            start_str = input("请输入引用标识的起始字符:")
            end_str = input("请输入引用标识的结束字符, 如果没有请输入'0':")
            
            if end_str == '0':
                references = text_output[text_output.find(start_str):]
            else:
                references = text_output[text_output.find(start_str):text_output.find(end_str)]

    return references.strip()

def load_config():
            # 获取当前工作目录
    current_path = os.getcwd()

    # 打印当前工作目录
    print("当前工作路径:", current_path)
    config_template = {"project_space": "", "volces_api": "", "qianfan_api": {"API_Key": "","Secret_Key":""}}  # 默认模板
    
    if not os.path.isdir("./config"):
        os.makedirs("./config")
        print(f"创建了config文件夹")
    
    if os.path.isfile("./config/config.json"):
        print(f"config.json文件已存在")
        try:
            print("尝试加载")
            with open("./config/config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
            
            #print(config)
            # 使用字典的get方法，如果键不存在，则使用默认值（这里为空字符串）
            project_space = config.get("project_space", "")
            volces_api = config.get("volces_api", "")
            qianfan_api = config.get("qianfan_api", {})
            
            # 更新默认模板中的值
            config_template.update({
                "project_space": project_space,
                "volces_api": volces_api,
                "qianfan_api": qianfan_api
            })
            if project_space == "":
                print("请选择文件路径")
                return True, "请选择文件路径", config_template
            if volces_api == "":
                print("请填入Volces API")
                return True, "填入Volces API", config_template
            if qianfan_api['API_Key'] == "":
                print("请填入Qwen API")
                return True, "请填入Qianfan API_Key", config_template
            if qianfan_api['Secret_Key'] == "":
                print("请填入Qwen Secret")
                return True, "请填入Qianfan Secret_Key", config_template
            else:
                print("文件正常")
                return False, "配置文件正常", config_template
        except Exception as e:
            print(f"读取配置文件时出错: {str(e)}")
            with open("./config/config.json", "w", encoding="utf-8") as f:
                    json.dump(config_template, f, ensure_ascii=False, indent=4)
            return True, f"读取配置文件时出错: {str(e)}", config_template
    else:
        with open("./config/config.json", "w", encoding="utf-8") as f:
                json.dump(config_template, f, ensure_ascii=False, indent=4)
        # 如果目录或文件不存在，返回默认模板
        print("配置文件不存在")
        return True,"配置文件不存在" ,config_template
def get_volces_api():
    while True:
        volces_api = get_volces_api_inputs()
        ans = volces_api_test(volces_api)
        print("volces_api:",ans)
        if  ans != "测试通过":
            volces_api = get_volces_api_inputs()
        else:
            return volces_api
        
def get_qianfan_api():
    while True:
        api_key, secret_key = get_qianfan_api_inputs()
        ans = qianfan_api_test(api_key, secret_key)
        print("qianfan_api:", ans)
        if ans != "测试通过":
            api_key, secret_key = get_qianfan_api_inputs()
        else:
            return api_key, secret_key

def get_qianfan_api_inputs():
    """创建一个小的输入窗口，获取用户输入的API Key和Secret Key"""
    root_temp = tk.Tk()
    root_temp.withdraw()

    def on_confirm(event=None):  # 添加 event 参数，并设置默认值为 None
        nonlocal api_key, secret_key
        api_key = api_key_entry.get()
        secret_key = secret_key_entry.get()
        popup.destroy()

    api_key = ""
    secret_key = ""
    popup = tk.Toplevel(root_temp)
    popup.title("输入Qianfan API:")

    # 设置窗口大小
    popup.geometry("300x200")
    popup.configure(bg='#f0f0f0')

    # 使用ttk风格化组件
    style = ttk.Style(popup)
    style.configure('.', font=('Microsoft YaHei', 12), background='#f0f0f0')
    style.configure('TButton', foreground='black', background='#4CAF50', borderwidth=1, focusthickness=3, focuscolor='none')
    style.map('TButton', background=[('active', '#45a049')])
    style.configure('TLabel', foreground='#333333', background='#f0f0f0', font=('Microsoft YaHei', 12))

    # 创建API Key标签和输入框
    api_key_label = ttk.Label(popup, text="API Key:")
    api_key_label.pack(pady=5)

    api_key_entry = ttk.Entry(popup, width=30)
    api_key_entry.pack(pady=5)

    # 创建Secret Key标签和输入框
    secret_key_label = ttk.Label(popup, text="Secret Key:")
    secret_key_label.pack(pady=5)

    secret_key_entry = ttk.Entry(popup, width=30)
    secret_key_entry.pack(pady=5)

    # 绑定回车键到确认函数
    api_key_entry.bind('<Return>', on_confirm)
    secret_key_entry.bind('<Return>', on_confirm)

    # 创建确认按钮
    confirm_button = ttk.Button(popup, text="确认", command=on_confirm)
    confirm_button.pack(pady=10)

    # 等待用户关闭弹出窗口
    popup.wait_window()

    return api_key, secret_key
def get_volces_api_inputs():
    """创建一个小的输入窗口，获取用户输入的BibTeX项目名称"""
    root_temp = tk.Tk()
    root_temp.withdraw() 
    def on_confirm(event=None):  # 添加 event 参数，并设置默认值为 None
        nonlocal volces_api
        volces_api = entry.get()
        popup.destroy()

    volces_api = ""
    popup = tk.Toplevel(root_temp)
    popup.title("输入Volces API:")
    
    # 设置窗口大小
    popup.geometry("300x150")
    popup.configure(bg='#f0f0f0')

    # 使用ttk风格化组件
    style = ttk.Style(popup)
    style.configure('.', font=('Microsoft YaHei', 12), background='#f0f0f0')
    style.configure('TButton', foreground='black', background='#4CAF50', borderwidth=1, focusthickness=3, focuscolor='none')
    style.map('TButton', background=[('active', '#45a049')])
    style.configure('TLabel', foreground='#333333', background='#f0f0f0', font=('Microsoft YaHei', 12))

    # 创建标签和输入框
    label = ttk.Label(popup, text="Volces API:")
    label.pack(pady=10)

    entry = ttk.Entry(popup, width=30)
    entry.pack(pady=10)

    # 绑定回车键到确认函数
    entry.bind('<Return>', on_confirm)

    # 创建确认按钮
    confirm_button = ttk.Button(popup, text="确认", command=on_confirm)
    confirm_button.pack(pady=10)

    # 等待用户关闭弹出窗口
    popup.wait_window()

    return volces_api

def get_bibtex_name_inputs():
    """创建一个小的输入窗口，获取用户输入的BibTeX项目名称"""
    root_temp = tk.Tk()
    root_temp.withdraw() 
    def on_confirm(event=None):  # 添加 event 参数，并设置默认值为 None
        nonlocal bibtex_name
        bibtex_name = entry.get()
        popup.destroy()

    bibtex_name = ""
    popup = tk.Toplevel(root_temp)
    popup.title("输入BibTeX项目名称")
    
    # 设置窗口大小
    popup.geometry("300x150")
    popup.configure(bg='#f0f0f0')

    # 使用ttk风格化组件
    style = ttk.Style(popup)
    style.configure('.', font=('Microsoft YaHei', 12), background='#f0f0f0')
    style.configure('TButton', foreground='black', background='#4CAF50', borderwidth=1, focusthickness=3, focuscolor='none')
    style.map('TButton', background=[('active', '#45a049')])
    style.configure('TLabel', foreground='#333333', background='#f0f0f0', font=('Microsoft YaHei', 12))

    # 创建标签和输入框
    label = ttk.Label(popup, text="请输入BibTeX项目名称:")
    label.pack(pady=10)

    entry = ttk.Entry(popup, width=30)
    entry.pack(pady=10)

    # 绑定回车键到确认函数
    entry.bind('<Return>', on_confirm)

    # 创建确认按钮
    confirm_button = ttk.Button(popup, text="确认", command=on_confirm)
    confirm_button.pack(pady=10)

    # 等待用户关闭弹出窗口
    popup.wait_window()

    return bibtex_name
def get_bibtex_name(folder_selected):
    def get_folders(folder_selected):
        """获取指定目录下的所有文件夹"""
        folders = [name for name in os.listdir(folder_selected) if os.path.isdir(os.path.join(folder_selected, name))]
        return folders
    
    # 获取文件夹列表
    folders = get_folders(folder_selected)
    print("检测到目录:",folders)
    if folders:
        bibtex_name = get_bibtex_name_choose(folders)
    else:
        bibtex_name = get_bibtex_name_inputs()

    return bibtex_name
def get_bibtex_name_choose(folders):
    """创建一个小的输入窗口，获取用户输入的BibTeX项目名称"""
    root_temp = tk.Toplevel()  # 使用Toplevel而不是Tk
    root_temp.title("选择需要启动的数据库")
    
    bibtex_name = ""  # 初始化bibtex_name

    def on_confirm():
        nonlocal bibtex_name
        bibtex_name = combo_box.get()
        root_temp.destroy()  # 关闭窗口

    def on_create_new():
        nonlocal bibtex_name
        bibtex_name = get_bibtex_name_inputs()
        root_temp.destroy()  # 关闭窗口

    # 创建下拉选择框
    combo_box = ttk.Combobox(root_temp, values=folders)
    combo_box.pack(padx=10, pady=10)
    if folders:  # 确保有文件夹可选
        combo_box.set(folders[0])  # 设置默认值到下拉菜单

    # 设置窗口大小
    root_temp.geometry("300x150")

    # 使用ttk风格化组件
    style = ttk.Style(root_temp)
    style.configure('.', font=('Microsoft YaHei', 12), background='#f0f0f0')
    style.configure('TButton', foreground='black', background='#4CAF50', borderwidth=1, focusthickness=3, focuscolor='none')
    style.map('TButton', background=[('active', '#45a049')])
    style.configure('TLabel', foreground='#333333', background='#f0f0f0', font=('Microsoft YaHei', 12))

    # 创建确认按钮
    confirm_button = ttk.Button(root_temp, text="确认", command=on_confirm)
    confirm_button.pack(pady=10)

    # 创建“创建新数据集”按钮
    new_button = ttk.Button(root_temp, text="创建新数据集", command=on_create_new)
    new_button.pack(pady=10)

    # 等待用户关闭弹出窗口
    root_temp.wait_window()

    return bibtex_name
def strat_programme(file_path):
    if os.path.isdir(file_path):
        print("开始, 项目目录为:",file_path)
        project_name = start_project(file_path)
        pdf_file_list = list_pdf_files(f"{file_path}/project/{project_name}/pdf")
        with open(f"{file_path}/project/{project_name}/data/ref_extract_info_dict.json", "r", encoding = "utf-8") as f:
            ref_extract_info_dict = json.load(f)
        with open(f"{file_path}/project/{project_name}/data/ref_extract_appendix_dict.json", "r", encoding = "utf-8") as f:
            ref_extract_appendix_dict = json.load(f)
    
    return project_name,pdf_file_list,ref_extract_info_dict,ref_extract_appendix_dict
def start_project(file_path):
    if not os.path.isdir(f"{file_path}/project"):
        os.mkdir(f"{file_path}/project")

    ## 创建项目
    user_input = get_bibtex_name(f"{file_path}/project")
    if not os.path.isdir(f"{file_path}/project/{user_input}"):
        print(f"未检测到项目, 自动创建项目:{user_input}")
        os.mkdir(f"{file_path}/project/{user_input}")
    else:
        print(f"已启动项目:{user_input}")

    ## 读取api
    with open("./config/config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    volces_api = config["volces_api"]
    qianfan_API_Key = config["qianfan_api"]['API_Key']
    qianfan_Secret_Key = config["qianfan_api"]['Secret_Key']
    set_global_api_keys(volces_api, qianfan_API_Key, qianfan_Secret_Key)
    _1,_2,_3 = get_global_api_keys()
    print("api读取长度:", len(_1),len(_2),len(_3))

    if user_input:
        ## 创建pdf文件夹
        if not os.path.isdir(f"{file_path}/project/{user_input}/pdf"):
            os.mkdir(f"{file_path}/project/{user_input}/pdf")
        else:
            pdf_num = len(list_pdf_files(f"{file_path}/project/{user_input}/pdf"))
            print(f"当前项目中论文数量为:{pdf_num}")

        ## 创建data文件夹
        if not os.path.isdir(f"{file_path}/project/{user_input}/data"):
            os.mkdir(f"{file_path}/project/{user_input}/data")

        ## 创建extract_dict.json
        if not os.path.isfile(f"{file_path}/project/{user_input}/data/ref_extract_info_dict.json"):
            #print("创建extract_dict.json")
            with open(f"{file_path}/project/{user_input}/data/ref_extract_info_dict.json", "w") as f:
                json.dump({}, f)
        
        ## 创建ref_appendix_dictences.json
        if not os.path.isfile(f"{file_path}/project/{user_input}/data/ref_extract_appendix_dict.json"):
            #print("创建ref_appendix_dictences.json")
            with open(f"{file_path}/project/{user_input}/data/ref_extract_appendix_dict.json", "w") as f:
                json.dump({}, f)
    
    return(user_input)

def detect_citation_style(pdf_path):
    """检测引用风格"""
    # 定义正则表达式模式
    #print(pdf_path)
    text = extract_text_with_pymupdf(pdf_path)
    #print(len(text))
    if len(text) < 10000:
        text = text[0:int(len(text)*0.6)]
    else:
        text = text[0:10000]
    numeric_pattern = r'\[\d+\]' + r'|\[\d+,?\s\d+\]'  # 匹配 [1], [2], ...
    author_year_pattern = r'et al.,?\s\d{4}'  # 匹配 (Author, 2020) 或 (Author et al., 2020)

    # 查找匹配项
    numeric_matches = re.findall(numeric_pattern, text)
    author_year_matches = re.findall(author_year_pattern, text)
    if numeric_matches:
        #print(numeric_matches)
        return 'IEEE'
    elif author_year_matches:
        #print(author_year_matches)
        return 'APA'
    else:
        print(len(text))
        return 'Unknown_Citation_Style'

def process_newlines_IEEE(text):
    # 第一步：移除所有换行符
    text_no_newlines = text.replace('\n', '')
    
    # 第二步：找到所有匹配的 [数字] 格式
    matches = list(re.finditer(r'\[\d+\]', text_no_newlines))
    
    # 第三步：构建新的字符串，在每个 [数字] 格式的前面插入一个换行符
    result = []
    last_end = 0
    for match in matches:
        start, end = match.span()
        
        # 添加从上一个结束位置到当前 [数字] 格式前的部分
        result.append(text_no_newlines[last_end:start])
        
        # 在 [数字] 格式前插入换行符
        result.append('\n')
        result.append(text_no_newlines[start:end])
        
        # 更新最后一个结束位置
        last_end = end
    
    # 添加剩余的部分
    result.append(text_no_newlines[last_end:])
    
    # 将列表合并成最终的字符串
    processed_text = ''.join(result)
    
    return processed_text

def extract_reference_numbers(reference_texts):
    # 定义一个正则表达式模式来匹配 [数字]
    pattern = r'^\[\d+\]'
    
    reference_numbers = []

    match = re.search(pattern, reference_texts)
    if match:
        num = (match.group())
    else:
        num = (None)  # 如果没有找到匹配项，则添加 None 或其他标识符
    content = reference_texts.replace(num, '').strip()
    
    return num, content

def process_newlines_IEEE(text):
    # 第一步：移除所有换行符
    text_no_newlines = text.replace('\n', '')
    
    # 第二步：找到所有匹配的 [数字] 格式
    matches = list(re.finditer(r'\[\d+\]', text_no_newlines))
    
    # 第三步：构建新的字符串，在每个 [数字] 格式的前面插入一个换行符
    result = []
    last_end = 0
    for match in matches:
        k = match.group()
        start, end = match.span()
        
        # 添加从上一个结束位置到当前 [数字] 格式前的部分
        result.append(text_no_newlines[last_end:start])
        
        # 在 [数字] 格式前插入换行符
        result.append('\n')
        result.append(text_no_newlines[start:end])
        
        # 更新最后一个结束位置
        last_end = end
    
    # 添加剩余的部分
    result.append(text_no_newlines[last_end:])
    
    # 将列表合并成最终的字符串
    processed_text = ''.join(result)
    
    return processed_text

def refine_refname_IEEE(ref):
    ref = ref.replace('-', '')
    ref = ref.replace('\n', '').strip()

    if not ref.startswith('['):
        ref = '[' + ref
    if not ref.endswith(']'):
        ref += ']'

    ref = ref.replace(' ', '')
    return ref

def split_references_IEEE(reference_dict):
    output_dict = reference_dict.copy()

    ref_set_list = []
    for i in tqdm(reference_dict.keys()):
        result = []
        ref = reference_dict[i]["original_ref"]
        #print(ref)
        # 如果没有分号，直接添加到结果列表中
        parts = ref.split(',')
        for part in parts:
            ans = refine_refname_IEEE(part)
            result.append(ans)
            ref_set_list.append(ans)
        
        output_dict[i]["sub_list"] = result

    return output_dict,ref_set_list

def get_access_token():
    """
    使用 API Key，Secret Key 获取access_token，替换下列示例中的应用API Key、应用Secret Key
    """
    _,API_Key,Secret_Key = get_global_api_keys()
        
    url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={API_Key}&client_secret={Secret_Key}"
    
    payload = json.dumps("")
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json().get("access_token")

def embedding_qianfan_limited_length(content_list):
    url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/embeddings/bge_large_zh?access_token=" + get_access_token()
    headers = {
        'Content-Type': 'application/json'
    }

    def split_content(content_list, max_batch_size=16, max_length_per_item=4096):
        batches = []
        current_batch = []

        for content in content_list:
            if len(content) > max_length_per_item:
                content = content[0:4096]

            if len(current_batch) >= max_batch_size:
                # 如果当前批次已满，则开始一个新的批次
                batches.append(current_batch)
                current_batch = []

            current_batch.append(content)

        if current_batch:
            batches.append(current_batch)

        return batches

    batches = split_content(content_list)

    all_embeddings = []

    for batch in batches:
        payload = json.dumps({
            "input": batch
        })
        response = requests.request("POST", url, headers=headers, data=payload)
        temp_dict = json.loads(response.text)
        
        if 'data' not in temp_dict:
            print(f"API 错误: {temp_dict}")
            continue
        
        embeddings = [item['embedding'] for item in temp_dict['data']]
        all_embeddings.extend(embeddings)

    # 将提取的 embeddings 转换为 numpy 矩阵
    embedding_matrix = np.array(all_embeddings)
    
    return embedding_matrix

def retriever_top(similarity, text_list, num_top):
    retrieve_dict = {}
    arr = np.array(similarity).flatten()
    
    # 找到排序后的索引，基于调整后的相似度
    sorted_indices = np.array(arr).argsort()
    # 因为argsort()返回的是从小到大排序的索引，所以我们需要从末尾开始取
    top_indices = sorted_indices[-num_top:][::-1]  # 反转切片以获得最大的几个索引
    # 获取对应的值
    top_values = np.array(arr)[top_indices]
    
    # 输出结果
    for n, (i, v) in enumerate(zip(top_indices, top_values)):
        retrieve_dict[n] = {
            'Index': i,
            'score': v,
            'content': text_list[i]
        }
        
    return retrieve_dict

def retriever(question, Index, text_list, num_top=1):
    question_embeddings = embedding_qianfan_limited_length([question])
    similarity = Index @ question_embeddings.T
    retrieve_dict = retriever_top(
        similarity, 
        text_list, 
        num_top
    )
    
    return retrieve_dict


def rerank_qianfan(query, retrieve_dict):

    url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/reranker/bce_reranker_base?access_token=" + get_access_token()

    # 构建 rerank_list 和对应的 index_list
    rerank_list = []
    index_list = []
    for item in retrieve_dict.values():
        rerank_list.append(item['content'])
        index_list.append(item['Index'])

    payload = json.dumps({
        "query": query,
        "documents": rerank_list
    })
    headers = {
        'Content-Type': 'application/json'
    }

    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        response.raise_for_status()  # 检查 HTTP 错误
        temp_dict = response.json()
        print("API Response:", temp_dict)  # 调试输出

        # 将 index 信息与重新排序后的文档关联起来
        results_with_index = []
        full_info_dicts = []
        for result in temp_dict.get('results', []):
            original_index = index_list[result['index']]
            result_with_index = {
                'content': result['document']
            }
            full_info_dict = {
                'content': result['document'],
                'relevance_score': result['relevance_score'],
                'original_index': original_index
            }
            results_with_index.append(result_with_index)
            full_info_dicts.append(full_info_dict)

        return {'results': results_with_index, 'full_info_dict': full_info_dicts}
    except requests.exceptions.RequestException as e:
        print(f"API 请求失败: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON 解码失败: {e}")
        return None
    
def process_input_RAG(query, Index_list,content_list, document_list, location_list, ref_extract_info_dict, ref_extract_appendix_dict, bibtex_dict, latex_form = True):
    """处理输入文本的函数"""
    # 这里可以替换为你自己的处理逻辑

    #print("2, 长度为:",len(Index_list),len(content_list))
    Index = np.array(Index_list)
    retrieve_dict = retriever(query, Index,content_list, 15)
    rerank_dict = rerank_qianfan(query, retrieve_dict)
    output_str = ""
    i = 0
    for v in rerank_dict['results']:
        output_str =  output_str + f"[第{i+1}条]:\n" +  v['content'] + "\n\n"
        i = i + 1
        if i >= 5:
            break
    
    #print("Rerank 结果:",str(rerank_dict))   

    sample_message = """
<示例1>:
检索增强生成（RAG）是检索模型与语言模型集成产生的一种在模型推理中利用外部知识的方法，是解决大语言模型固有知识局限性的重要技术[1]，在自然语言处理领域的生成任务中整合外部数据源信息为输入查询或生成输出提 供补充参考或指令[2]，也是在传统和基于大语言模型的检索增强生成（RAG）模型中被应用的方法，现有研究主要考虑顺序推理结构[3]。
"""
#<示例2>:
#在检索阶段，常用的数据集包括像维基百科这样的大型文本库，它为模型提供了广泛的知识基础，使其能够针对特定问题找到最相关的信息片段。对于生成阶段，常用的数据集则可能包括问答对、对话记录或是特定任务的文本样本，例如新闻文章或技术文档等。这些数据集帮助模型学习如何基于检索到的信息生成准确且连贯的回答[7,8,9,22]。


    ans = volces_chat(f"根据我给出的资料, 以一句话回答我的问题! 回答的信息需要严格来源于我给出的资料! 写作风格为学术论文风格! 对于每一个引用的信息都以[数字]的形式表明引用的资料的Index! 禁止以括号的形式添加说明, 尤其是被引用的作者和年份信息!\n引用尽量以资料内容为单位, 尽量标在句中每一个准确的位置, 而不是句末统一标注! 如遇到多条标记必须合并, 如[1,2,3], 而不是[1][2][3]! 请参考示例 \n\n问题:{query}\n\n资料:{str(output_str)}\n\n 如果相关资料无法回答该问题, 则回复'无相关资料'", system_messages= sample_message)
    
    print(ans)
    output1_rag_info = f"[论文库检索结果]: \n{str(output_str.strip())}"
    output_volces = f"[输入的问题]: \n{query} \n\n [AI回复结果]: \n{ans}"

    ## search_bibtex
    def search_bibtex(text,rerank_dict, document_list, location_list, ref_extract_info_dict, ref_extract_appendix_dict, bibtex_dict):
        bibtex_name_list = []
        bibtex_content_list = []
        bibtex_sublist_list = []
        # 使用正则表达式查找所有中括号内的数字
        numbers = re.findall(r'\[.*?\]', text)

        # 将找到的数字字符串转换为整数
        temp_list = []
        for k in numbers:
            temp_text = k[1:-1]
            temp_list.append(temp_text.split(","))

        original_index_list = []
        for i in temp_list:
            for n in i:
                temp_id = rerank_dict['full_info_dict'][int(n)-1]['original_index']
                original_index_list.append(temp_id)
                temp_document = document_list[temp_id]
                temp_location = location_list[temp_id]
                try:
                    ref_extract_info_dict_info = ref_extract_info_dict[temp_document]['references'][str(temp_location)]
                    bibtex_sublist_list.append(ref_extract_info_dict_info['sub_list'])
                    temp_name_list = []
                    temp_content_list = []
                    for k in ref_extract_info_dict_info['sub_list']:

                        temp_label = 0
                        temp_str = ref_extract_appendix_dict[temp_document]['references'][k]
                        for kk,vv in bibtex_dict.items():
                            for dk,dv in vv.items():
                                if str(temp_document) == kk and str(k) == dv['k']:
                                    temp_label = 1
                                    if temp_str == dv['v']:
                                        temp_name_list.append(dv['bibtex_name'])
                                        temp_content_list.append(dv['bibtex_content'])
                                        #print("Bibtex Info OK:", dv['bibtex_name'], "\n", dv['bibtex_content'])
                                        
                                    else:
                                        print("人工判断:")
                                        print("temp_str:",temp_str)
                                        print("dv['v']:",dv['v'])
                        if temp_label == 0:
                            print("Bibtex Info search ERROR, Check:", temp_document, k, temp_str)
                    bibtex_name_list.append(temp_name_list)
                    bibtex_content_list.append(temp_content_list)
                except:
                    print("Bibtex Info ERROR, Check:", temp_document, temp_location, len(document_list), len(location_list), document_list[0], location_list[0])

        #print("bibtex_sublist_list:", bibtex_sublist_list)
        #print("bibtex_name_list:", bibtex_name_list)
        #print("bibtex_content_list:", bibtex_content_list)
        latex_bib_list = []
        latex_content_str = ""
        for i in range(len(bibtex_name_list)):
            temp_str = ""
            for n in range(len(bibtex_name_list[i])):
                temp_str += " " + bibtex_name_list[i][n] + ","
                clearn_str = bibtex_content_list[i][n].strip()
                latex_content_str += clearn_str + "\n\n"
            latex_bib = "\\cite{"+ temp_str[0:-1].strip() + "}"
            latex_bib_list.append(latex_bib)
        
        print("latex_bib_list:", latex_bib_list)

        return latex_bib_list, latex_content_str

    if ans != "无相关资料":
        latex_bib_list, latex_content_str = search_bibtex(ans,rerank_dict, document_list, location_list, ref_extract_info_dict, ref_extract_appendix_dict, bibtex_dict)

        if latex_form:
            output1_rag_info = latex_content_str

            numbers = re.findall(r'\[.*?\]', ans)
            ans2 = ans

            for i in range(len(numbers)):
                        # 将找到的数字字符串转换为整数
                temp_list = []
                for k in numbers:
                    temp_text = k[1:-1]
                    temp_list.append(temp_text.split(","))
                    temp_str = ""

            x_n = 0
            temp_str_list = []
            for temp_list_sub in temp_list:
                length = len(temp_list_sub)
                print(length)
                for nn in range(length):
                    temp_str += " " + latex_bib_list[x_n + nn] + ","
                x_n = x_n + length
                temp_str = temp_str.replace("}, \\cite{", " ,")
                temp_str_list.append(temp_str)

            for i in range(len(numbers)):
                ans2 = ans2.replace(numbers[i],temp_str_list[i])

            output_volces = ans2


    return output_volces, output1_rag_info


def on_confirm_LLM(input_entry, index_list, content_list, document_list, location_list, ref_extract_info_dict, ref_extract_appendix_dict, bibtex_dict, latex_form, event=None):
    """确认按钮点击或回车键按下时的回调函数"""
    input_text = input_entry.get().strip()
    link_button.grid_remove()  # 初始隐藏按钮
    if not input_text:
        messagebox.showwarning("警告", "请输入一些内容！")
        return
    
    output_volces, output_rag_info = process_input_RAG(input_text, index_list, content_list, document_list, location_list, ref_extract_info_dict, ref_extract_appendix_dict, bibtex_dict, latex_form)
    output_text_LLM.set(output_volces)
    output_text_RAG.set(output_rag_info)
    output_text_RAG_widget.grid_forget()  # 隐藏 RAG 输出文本框
    link_button.grid(row=3, column=0, columnspan=2, pady=10)  # 使用 grid 放置按钮

def click_link_button():
    output_text_RAG_widget.grid(row=2, column=0, columnspan=2, padx=10, pady=10)  # 显示 RAG 输出文本框
    link_button.grid_forget()

def click_link_button():
    """显示RAG检索内容按钮点击事件处理函数"""
    if output_text_RAG_widget.winfo_ismapped():
        output_text_RAG_widget.grid_remove()
        link_button.config(text="显示Latex格式")
    else:
        output_text_RAG_widget.grid(row=2, column=0, columnspan=2, padx=10, pady=10)
        link_button.config(text="隐藏RAG检索内容")

def create_LLM_window(folder_selected, project_name):
    global root_temp, input_entry, output_text_LLM, output_text_RAG, output_text_RAG_widget, link_button
    """创建并显示一个新的顶层窗口"""
    root_temp = tk.Toplevel()
    root_temp.title("输入与处理窗口")

    # 输入栏和确认按钮
    global input_entry

    with open(f"{folder_selected}/project/{project_name}/data/ref_extract_info_dict.json", "r", encoding="utf-8") as f:
        ref_extract_info_dict = json.load(f)
    with open(f"{folder_selected}/project/{project_name}/data/ref_extract_appendix_dict.json", "r", encoding="utf-8") as f:
        ref_extract_appendix_dict = json.load(f)
    with open(f"{folder_selected}/project/{project_name}/data/bibtex_dict.json", "r", encoding="utf-8") as f:
        bibtex_dict = json.load(f)
    with open(f"{folder_selected}/project/{project_name}/data/Index.json", "r", encoding="utf-8") as f:
        index_dict = json.load(f)
        
    content_list = []
    Index_list = []
    document_list = []
    location_list = []
    for k, v in index_dict.items():
        content_list.extend(v['content_list'])
        Index_list.extend(v['Index'])
        location_list.extend(range(len(v['content_list'])))
        document_list.extend([k] * len(v['content_list']))

    input_entry = tk.Entry(root_temp, width=70)
    input_entry.grid(row=0, column=0, padx=10, pady=10)

    checkbox_state = tk.BooleanVar()  # 创建一个布尔变量来存储复选框的状态
    checkbox = tk.Checkbutton(root_temp, text="显示Latex格式", variable=checkbox_state)
    checkbox.grid(row=0, column=2, padx=10, pady=10)

    #print("数据库加载完成, 长度为:", len(Index_list), len(content_list))
    input_entry.bind("<Return>", lambda event: on_confirm_LLM(input_entry, Index_list, content_list, document_list, location_list, ref_extract_info_dict, ref_extract_appendix_dict, bibtex_dict, checkbox_state.get()))  # 绑定回车键


    confirm_button = tk.Button(root_temp, text="确认", command=lambda: on_confirm_LLM(input_entry, Index_list, content_list, document_list, location_list, ref_extract_info_dict, ref_extract_appendix_dict, bibtex_dict, checkbox_state.get()))
    confirm_button.grid(row=0, column=1, padx=10, pady=10)

    link_button = tk.Button(
        root_temp,
        text="显示RAG检索内容",
        fg="blue",  # 设置文字颜色为蓝色
        cursor="hand2",  # 设置鼠标悬停时的光标为手型
        borderwidth=0,  # 去掉边框
        highlightthickness=0,  # 去掉高亮边框
        activeforeground="red",  # 设置点击时的文字颜色为红色
        command=click_link_button  # 设置按钮点击事件
    )
    link_button.grid(row=3, column=0, columnspan=2, pady=10)  # 使用 grid 放置按钮
    link_button.grid_remove()  # 初始隐藏按钮

    # 输出栏
    global output_text_LLM, output_text_RAG
    output_text_LLM = tk.StringVar()
    output_text_RAG = tk.StringVar()

    # LLM 输出文本框
    output_text_LLM_widget = tk.Text(root_temp, wrap=tk.WORD, width=80, height=20, state=tk.DISABLED)
    output_text_LLM_widget.grid(row=1, column=0, columnspan=2, padx=10, pady=10)

    # RAG 输出文本框
    output_text_RAG_widget = tk.Text(root_temp, wrap=tk.WORD, width=80, height=20, state=tk.DISABLED)
    output_text_RAG_widget.grid(row=2, column=0, columnspan=2, padx=10, pady=10)
    output_text_RAG_widget.grid_remove()  # 初始隐藏 RAG 输出文本框

    # 更新文本框内容的函数
    def update_text_widget(widget, text):
        widget.config(state=tk.NORMAL)
        widget.delete(1.0, tk.END)
        widget.insert(tk.END, text)
        widget.config(state=tk.DISABLED)

    # 绑定 StringVar 到文本框
    output_text_LLM.trace_add("write", lambda *args: update_text_widget(output_text_LLM_widget, output_text_LLM.get()))
    output_text_RAG.trace_add("write", lambda *args: update_text_widget(output_text_RAG_widget, output_text_RAG.get()))

    root_temp.mainloop()

