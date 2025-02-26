import tkinter as tk
from tkinter import ttk, filedialog
import threading
import os
from utils import *
import hashlib

lock = threading.Lock()
def update_step_status(step_index, status):
    """更新步骤的状态"""
    step_labels[step_index].config(text=f"{steps[step_index]} {status}")
def main_programme():
    global button, button_LLM, label
        # 创建标签，用于显示选择的目录路径
    label = ttk.Label(main_frame, text="还未选择任何目录")
    label.pack(expand=True)

    # 创建一个线程来执行主程序
    print("选择工作环境")
    status_temp, message_temp, config_template = load_config()
    if status_temp:
        root.after(0, lambda: label.config(text=message_temp))
    if os.path.isdir(config_template["project_space"]):
        print(f'已读取{config_template["project_space"]}')
        folder_selected = config_template["project_space"]
    else:
        folder_selected = filedialog.askdirectory()
        config_template["project_space"] = folder_selected
        with open("./config/config.json", "w", encoding="utf-8") as f:
            json.dump(config_template, f, ensure_ascii=False, indent=4)
    print(f"选择目录:{folder_selected}")

    if config_template["volces_api"] == "":
        volces_api = get_volces_api()
        config_template["volces_api"] = volces_api
        with open("./config/config.json", "w", encoding="utf-8") as f:
            json.dump(config_template, f, ensure_ascii=False, indent=4)

    if config_template["qianfan_api"]['API_Key'] == "":
        #print(config_template)
        api_key, secret_key = get_qianfan_api()
        config_template["qianfan_api"]['API_Key'] = api_key
        config_template["qianfan_api"]['Secret_Key'] = secret_key
        with open("./config/config.json", "w", encoding="utf-8") as f:
            json.dump(config_template, f, ensure_ascii=False, indent=4)
    update_step_status(0, "✔")  # 第一步完成
    root.after(0, lambda: label.config(text="配置文件验证成功!\n选择需要启动的bibtex数据库"))
    
    ## 
    project_name,pdf_file_list,ref_extract_info_dict,ref_extract_appendix_dict = strat_programme(folder_selected)
    print(project_name)
    root.after(0, lambda: label.config(text=f"{project_name}数据库启动成功!"))

    ## 读取pdf
    update_step_status(1, project_name)  # 第二步完成
    num_ref = 0

    num_document = len(ref_extract_info_dict)
    if num_document > 0:
        root.after(0, lambda: button_LLM.config(text="开始问答", command=lambda: Index_tk(folder_selected, project_name), state='normal'))
        root.after(0, lambda: button_LLM.pack(expand=False))
        for v in ref_extract_info_dict.values():
            num_ref = num_ref + len(v['references'])
    if len(pdf_file_list) > 0:
        root.after(0, lambda: label.config(text=f"{project_name} 数据库启动成功, 检测到 {len(pdf_file_list)} 个 PDF 文件.\n数据库中包含 {num_document} 个文献, 共计 {num_ref} 条引用。"))
        root.after(0, lambda: button.config(text="开始处理提取PDF", command=lambda: extract_from_pdf_tk(folder_selected, project_name), state='normal'))
    else:
        root.after(0, lambda: label.config(text=f"当前数据库里无 PDF 文件，请在下述地址中:\n{folder_selected}/project/{project_name}/pdf\n中存放待分析的PDF"))

def Index_tk(folder_selected, project_name):
    global button_LLM, label, button
    root.after(0, lambda: button_LLM.config(state='disabled'))
    root.after(0, lambda: button.config(state='disabled'))
    
    print("生成数据库索引")
    Index(folder_selected,project_name)
    print("数据库索引检测完成, 开始retrieval")

    create_LLM_window(folder_selected,project_name)
def Index(folder_selected, project_name):
    with open(f"{folder_selected}/project/{project_name}/data/ref_extract_info_dict.json", "r", encoding = "utf-8") as f:
        ref_extract_info_dict = json.load(f)

    if os.path.isfile(f"E:/Project/LLM_reference/test/project/RAG/data/Index.json"):
        with open(f"E:/Project/LLM_reference/test/project/RAG/data/Index.json", "r", encoding = "utf-8") as f:
            index_dict = json.load(f)
    else:
        index_dict = {}

    
    for k,v in ref_extract_info_dict.items():
        if k not in index_dict:
            index_dict[k] = {}
            print("创建新数据库")

        content_list = []
        for dk,dv in v['references'].items():
            content = dv['object'] + "被用于" + dv['Mode_of_use'] + "\n它的描述为:" + dv['Description']
            content_list.append(content)
            #print(content_list)
            content_str = str(content_list).encode('utf-8')
            hash_object = hashlib.sha256(content_str)
            hash_hex = hash_object.hexdigest()
            #break
        print("检测数据库哈希")
        try:
            if hash_hex == index_dict[k]['Hash']:
                print("数据库未更新, 跳过更新")
                continue
            else:
                print("数据库已更新, 重新计算Index")
                print(hash_hex)
                print(index_dict[k]['Hash'])
        except:
            print("数据库读取失败, 重新计算Index")
        
        # 获取十六进制表示的哈希值
        
        Index = embedding_qianfan_limited_length(content_list)
        if isinstance(Index, np.ndarray):
            Index = Index.tolist()  # 将 ndarray 转换为 list

        index_dict[k]['Index'] = Index
        index_dict[k]['Hash'] = hash_hex
        index_dict[k]['content_list'] = content_list

        with open(f"{folder_selected}/project/{project_name}/data/Index.json", 'w', encoding='utf-8') as f:
            json.dump(index_dict, f, ensure_ascii=False, indent=4)
        print("Index已保存")
    
def retrieve_tk(query, Index_list,content_list):
    query = "RAG是什么?"
    Index = np.array(Index_list)
    retrieve_dict = retriever(query, Index,content_list, 5)
    rerank_dict = rerank_qianfan(query, retrieve_dict)
    print(rerank_dict)

def extract_from_pdf_tk(folder_selected, project_name):
    global button, label

    button.config(state='disabled')
    pdf_file_list = list_pdf_files(f"{folder_selected}/project/{project_name}/pdf")
    def deal_pdf_file_list(folder_selected, pdf_file_list):
        for pdf_file_path in pdf_file_list:
            pdf_file_path = f"{folder_selected}/project/{project_name}/pdf/{pdf_file_path}"
            # 示例调用
            print("开始读取:",pdf_file_path)

            pdf_file_list = list_pdf_files(f"{folder_selected}/project/{project_name}/pdf")
            with open(f"{folder_selected}/project/{project_name}/data/ref_extract_info_dict.json", "r", encoding = "utf-8") as f:
                ref_extract_info_dict = json.load(f)
            with open(f"{folder_selected}/project/{project_name}/data/ref_extract_appendix_dict.json", "r", encoding = "utf-8") as f:
                ref_extract_appendix_dict = json.load(f)
            
            print("开始读取:",pdf_file_path)

            # 示例调用
            text_output = extract_text_with_pymupdf(pdf_file_path)
            file_name = text_output.split("\n")[0]

            if file_name in ref_extract_info_dict.keys():
                print(f"该文件{file_name}已经提取过, 跳过")
                continue
            else:
                citation_style = detect_citation_style(pdf_file_path)
                print(citation_style)
                root.after(0, lambda: label.config(text=f"开始建立{pdf_file_path}索引, 格式为{citation_style}"))
                if citation_style == "APA":
                    extract_from_pdf_APA(folder_selected,project_name,pdf_file_path)
                    root.after(0, lambda: label.config(text=f"{pdf_file_path}索引已建立完成"))
                elif citation_style == "IEEE":
                    extract_from_pdf_IEEE(folder_selected,project_name,pdf_file_path)
                root.after(0, lambda: label.config(text=f"{pdf_file_path}索引已建立完成"))
        return False

    deal_pdf_file_list_thread = threading.Thread(target=lambda: deal_pdf_file_list(folder_selected,pdf_file_list))
    deal_pdf_file_list_thread.start()
    
    update_step_status(2, "✔")  # 第一步完成
    root.after(0, lambda: label.config(text="pdf信息提取完成!") )
    root.after(0, lambda: button.config(text="建立BibTex索引", command=lambda: construct_bibtex_tk(folder_selected, project_name), state='normal') )

def extract_from_pdf_IEEE(folder_selected,project_name,pdf_file_path):
    with open(f"{folder_selected}/project/{project_name}/data/ref_extract_info_dict.json", "r", encoding = "utf-8") as f:
        ref_extract_info_dict = json.load(f)
    with open(f"{folder_selected}/project/{project_name}/data/ref_extract_appendix_dict.json", "r", encoding = "utf-8") as f:
        ref_extract_appendix_dict = json.load(f)
    print("当前运行IEEE处理程序")
    text_output = extract_text_with_pymupdf(pdf_file_path)
    file_name = text_output.split("\n")[0]
    label.config(text=f"开始提取{file_name}信息,字数为{len(text_output)}...\n当前文件进度为(0/4)")

    original_list,index_list = process_square_IEEE(text_output)

    extracted_dict = {}
    for i in range(len(original_list)):
        extracted_dict[i] = {}
        extracted_dict[i]['original_ref'] = original_list[i]
        extracted_dict[i]['original_index'] = index_list[i]

    for i in tqdm(range(len(index_list))):
        #print(original_list[i])
        text_temp = text_output[index_list[i][0]-500:index_list[i][1]+100]
        system_message = f"""
        你正在做一个论文的引用信息提取的工作, 即从一个论文里逐条提取每一个引用, 主要内容是这个文章到底引用了这个参考文献的什么内容.
        我会我需要提取内容的文献原文, 以及这个引用标识本身, 以及这个表示的前几个字符以用于定位.
        只允许返回一个标准格式的json, 如有多个内容必须合并到一个统一切固定的格式里!
        <输出格式>:
        {{
            "object": "被标注引用的结论或内容等, 去除(name et al., year)等引用标识",
            "type": "结论/数据库/方法/性能/其他",
            "Mode_of_use":"如何被该论文使用的"
            "Description": "整理后对这个事物的描述(中文), 去除引用标识!"
        }}

        <输出示例>:
        <示例1>:
        {{
            "object": "HotpotQA",
            "type": "数据库",
            "Mode_of_use":"论文使用了该数据库"
            "Description": "HotpotQA是一种被广泛引用的多跳检索问题的数据库"
        }}

        <示例2>:
        {{
            "object": "As one of the most fundamental data mining techniques, retrieval aims to understand the input query and extract relevant information from external data sources",
            "type": "结论",
            "Mode_of_use":"论文使用了该结论作为背景的依据"
            "Description": "检索作为最基本的数据挖掘技术之一,目的是理解输入查询并提取相关信息来自外部数据源."
        }}

        <示例3>:
        {{
            "object": "EEs",
            "type": "性能",
            "Mode_of_use":"论文使用了该方法的实验性能作为对比"
            "Description": "EEs在HotpotQA的数据库中进行多跳实验, 其MAE为0.18, MSE为0.36, ACC为0.98"
        }}
        """

        input_str = f"""
        [原文]:{text_temp}

        [引用标识]:{original_list[i]}

        [辅助定位的前几个字符]:{text_output[index_list[i][0]-50:index_list[i][1]]}
        """
        i_n = 0
        while True:
            try:
                ans = volces_chat(input_str,system_message)
                temp_dict = json.loads(ans)
                break
            except:
                print(ans)
                i_n = i_n+1
            if i_n>3:
                break

        extracted_dict[i].update(temp_dict)
        #print(temp_dict)
        #print(extracted_dict[i])
        #print("_"*60)

    ref_dict,ref_set_list = split_references_IEEE(extracted_dict)
    label.config(text=f"开始提取{file_name}信息,字数为{len(text_output)}...\n当前文件进度为(1/4)")
    label.update_idletasks()
    ref_set = set(ref_set_list)
    ref_set_list = list(ref_set)


    ## 提取附录引用部分标识
    #start_str = input("请输入引用标识的起始字符:")
    
    #end_str = input("请输入引用标识的结束字符, 如果没有请输入'0':")
    #if str(end_str) == '0':
    #    references = text_output[text_output.find(start_str)+11:]
    #else:
    #    references = text_output[text_output.find(start_str)+11:text_output.find(end_str)]
    references = find_references(text_output)
    ref_text = process_newlines_IEEE(references)
    dict_ref_to_appendix = {}
    ref_text_list = ref_text.strip().split('\n')
    for ref in ref_text_list:
        ref = ref.strip()
        if ref:
            num, content = extract_reference_numbers(ref)
            dict_ref_to_appendix[num] = content
            
    ref_extract_info_dict[file_name] = {}
    ref_extract_appendix_dict[file_name] = {}
    ref_extract_info_dict[file_name]["type"] = "IEEE"
    ref_extract_appendix_dict[file_name]["type"] = "IEEE"
    ref_extract_info_dict[file_name]["references"] = extracted_dict
    ref_extract_appendix_dict[file_name]["references"] = dict_ref_to_appendix
            #break

    with open(f"{folder_selected}/project/{project_name}/data/ref_extract_info_dict.json", 'w', encoding='utf-8') as f:
        json.dump(ref_extract_info_dict, f, ensure_ascii=False, indent=4)

    with open(f"{folder_selected}/project/{project_name}/data/ref_extract_appendix_dict.json", 'w', encoding='utf-8') as f:
        json.dump(ref_extract_appendix_dict, f, ensure_ascii=False, indent=4)
    print("保存成功!")
    label.config(text=f"{file_name}处理完成, 已保存!")
    label.update_idletasks()

def extract_from_pdf_APA(folder_selected,project_name,pdf_file_path):
    with open(f"{folder_selected}/project/{project_name}/data/ref_extract_info_dict.json", "r", encoding = "utf-8") as f:
        ref_extract_info_dict = json.load(f)
    with open(f"{folder_selected}/project/{project_name}/data/ref_extract_appendix_dict.json", "r", encoding = "utf-8") as f:
        ref_extract_appendix_dict = json.load(f)
    print("当前运行APA处理程序")
    text_output = extract_text_with_pymupdf(pdf_file_path)
    file_name = text_output.split("\n")[0]
    label.config(text=f"开始提取{file_name}信息,字数为{len(text_output)}...\n当前文件进度为(0/4)")

    original_list,index_list = process_parentheses_APA(text_output)

    extracted_dict = {}
    for i in range(len(original_list)):
        extracted_dict[i] = {}
        extracted_dict[i]['original_ref'] = original_list[i]
        extracted_dict[i]['original_index'] = index_list[i]

    for i in tqdm(range(len(index_list))):
        #print(original_list[i])
        text_temp = text_output[index_list[i][0]-500:index_list[i][1]+100]
        system_message = f"""
        你正在做一个论文的引用信息提取的工作, 即从一个论文里逐条提取每一个引用, 主要内容是这个文章到底引用了这个参考文献的什么内容.
        我会我需要提取内容的文献原文, 以及这个引用标识本身, 以及这个表示的前几个字符以用于定位.
        只允许返回一个标准格式的json, 如有多个内容必须合并到一个统一切固定的格式里!
        <输出格式>:
        {{
            "object": "被标注引用的结论或内容等, 去除(name et al., year)等引用标识",
            "type": "结论/数据库/方法/性能/其他",
            "Mode_of_use":"如何被该论文使用的"
            "Description": "整理后对这个事物的描述(中文), 去除引用标识!"
        }}

        <输出示例>:
        <示例1>:
        {{
            "object": "HotpotQA",
            "type": "数据库",
            "Mode_of_use":"论文使用了该数据库"
            "Description": "HotpotQA是一种被广泛引用的多跳检索问题的数据库"
        }}

        <示例2>:
        {{
            "object": "As one of the most fundamental data mining techniques, retrieval aims to understand the input query and extract relevant information from external data sources",
            "type": "结论",
            "Mode_of_use":"论文使用了该结论作为背景的依据"
            "Description": "检索作为最基本的数据挖掘技术之一,目的是理解输入查询并提取相关信息来自外部数据源."
        }}

        <示例3>:
        {{
            "object": "EEs",
            "type": "性能",
            "Mode_of_use":"论文使用了该方法的实验性能作为对比"
            "Description": "EEs在HotpotQA的数据库中进行多跳实验, 其MAE为0.18, MSE为0.36, ACC为0.98"
        }}
        """

        input_str = f"""
        [原文]:{text_temp}

        [引用标识]:{original_list[i]}

        [辅助定位的前几个字符]:{text_output[index_list[i][0]-50:index_list[i][1]]}
        """
        i_n = 0
        while True:
            try:
                ans = volces_chat(input_str,system_message)
                temp_dict = json.loads(ans)
                break
            except:
                print(ans)
                i_n = i_n+1
            if i_n>3:
                break
        extracted_dict[i].update(temp_dict)
        #print(temp_dict)
    ref_dict,ref_set_list = split_references(extracted_dict)

    label.config(text=f"开始提取{file_name}信息,字数为{len(text_output)}...\n当前文件进度为(1/4)")
    label.update_idletasks()
    ref_set = set(ref_set_list)
    ref_set_list = list(ref_set)


    ## 提取附录引用部分标识
    #start_str = input("请输入引用标识的起始字符:")
    
    #end_str = input("请输入引用标识的结束字符, 如果没有请输入'0':")
    #if str(end_str) == '0':
    #    references = text_output[text_output.find(start_str)+11:]
    #else:
    #    references = text_output[text_output.find(start_str)+11:text_output.find(end_str)]
    references = find_references(text_output)
    
    ## 调整附录引用部分
    ref_text = process_newlines(references)
    ref_list = ref_text.split("\n")
    ref_list = modify_references_content(ref_list)
    checked_ref_list = review_ref(ref_list)
    label.config(text=f"开始提取{file_name}信息,字数为{len(text_output)}...\n当前文件进度为(2/4)")
    label.update_idletasks()


    ## 开始匹配
    rest_ref_set_list = ref_set_list.copy()
    rest_checked_ref_list = checked_ref_list.copy()

    dict_ref_to_appendix = {}
    for ref_temp in ref_set_list:
        
        i = 0
        #ref_temp = ref_set_list[6]
        #print(ref_temp)
        autnor, year = extract_name_and_year(ref_temp)
        
        for ref_appendix_temp in checked_ref_list:
            author_name = ref_appendix_temp.split(".")[0].split(",")[0]
            author_name_list = author_name.split(" ")
            whether_name = autnor in author_name_list
            if whether_name and year in ref_appendix_temp:
                #print(ref_appendix_temp)
                i = i+1
                rest_ref_set_list = [x for x in rest_ref_set_list if x != ref_temp]
                rest_checked_ref_list = [x for x in rest_checked_ref_list if x != ref_appendix_temp]
                dict_ref_to_appendix[ref_temp] = ref_appendix_temp
        if i == 0:
            print(ref_temp)
            #print(autnor,year)
            print("not match")
        elif i > 1:
            print(ref_temp)
            print("more than one match")

    label.config(text=f"开始提取{file_name}信息,字数为{len(text_output)}...\n当前文件进度为(3/4)")
    label.update_idletasks()
    ## 开始二次补充匹配
    for rest_ref_set in rest_ref_set_list:
        bib_append = ""
        for i in range(len(rest_checked_ref_list)):
            bib_append += f"{str(i)}" + ":" + rest_checked_ref_list[i] + "\n"
        input_str = f"""
        请你从下面的引用列表中, 匹配我给出的引用的附录文本, 只返回附录文本的索引号, 如果没有非常匹配的引用, 请直接返回"没有匹配的引用".
        <待匹配的引用>:{rest_ref_set}
        <引用列表>:{bib_append}"""
        ans = deepseek_chat(input_str)
        try:
            ans = int(ans)
        except:
            ans = "没有匹配的引用"

        if ans == "没有匹配的引用":
            print(rest_ref_set)
            print("AI二次匹配引用失败")
        else:
            dict_ref_to_appendix[rest_ref_set] = rest_checked_ref_list[int(ans)]
            rest_ref_set_list = [x for x in rest_ref_set_list if x != rest_ref_set]
            rest_checked_ref_list.pop(int(ans))
            print("AI二次匹配引用成功!")
    
    ref_extract_info_dict[file_name] = {}
    ref_extract_appendix_dict[file_name] = {}
    ref_extract_info_dict[file_name]["type"] = "APA"
    ref_extract_appendix_dict[file_name]["type"] = "APA"
    ref_extract_info_dict[file_name]["references"] = extracted_dict
    ref_extract_appendix_dict[file_name]["references"] = dict_ref_to_appendix
    #break

    with open(f"{folder_selected}/project/{project_name}/data/ref_extract_info_dict.json", 'w', encoding='utf-8') as f:
        json.dump(ref_extract_info_dict, f, ensure_ascii=False, indent=4)

    with open(f"{folder_selected}/project/{project_name}/data/ref_extract_appendix_dict.json", 'w', encoding='utf-8') as f:
        json.dump(ref_extract_appendix_dict, f, ensure_ascii=False, indent=4)
    label.config(text=f"{file_name}处理完成, 已保存!")
    label.update_idletasks()

def construct_bibtex_tk(folder_selected, project_name):
    global button, label
    def update_ui_after_thread_completion():
        if construct_bibtex_thread.is_alive():
            root.after(100, update_ui_after_thread_completion)  # 每100ms检查一次
        else:
            root.after(0, lambda: label.config(text="BibTex索引建立完成!"))
            root.after(0, lambda: button.config(text="BibTex索引建立完成", state='disabled'))
            update_step_status(3, "✔")  # 第一步完成
    root.after(0, lambda: button.config(text="BibTex索引建立中...",state='disabled'))
    root.after(0, lambda: label.config(text="BibTex索引建立中...") )

    construct_bibtex_thread = threading.Thread(target=lambda: construct_bibtex(folder_selected,project_name))
    construct_bibtex_thread.start()

    root.after(0, update_ui_after_thread_completion)

def construct_bibtex(folder_selected, project_name):
    check_result = check_connectivity()
    print("google连接性测试:",check_result)

    with open(f"{folder_selected}/project/{project_name}/data/ref_extract_appendix_dict.json", encoding='utf-8') as f:
        ref_extract_appendix_dict = json.load(f)

    if os.path.exists(f"{folder_selected}/project/{project_name}/data/bibtex_dict.json"):
        with open(f"{folder_selected}/project/{project_name}/data/bibtex_dict.json",encoding="utf-8") as f:
            bibtex_dict = json.load(f)
    else:
        bibtex_dict = {}
        #print("空bibtex")

    for k,v in ref_extract_appendix_dict.items():
        print("title:",k)
        paper_type = v['type']
        if k in bibtex_dict.keys():
            bibtex_dict_k = bibtex_dict[k]
            k_list = []
            v_list = []
            source_list = []
            for bib_k,bib_v in bibtex_dict[k].items():
                k_list.append(bib_v['k'])
                v_list.append(bib_v['v'])
                source_list.append(bib_v['source'])
            i=len(bibtex_dict[k])
        else:
            bibtex_dict[k] = {}
            bibtex_dict_k = {}
            k_list = []
            v_list = []
            source_list = []
            i = 0    

        for dk,dv in tqdm(v['references'].items()):
            #check_result = check_connectivity()
            if len(k_list) > 0:
                statue_temp,index_num = find_common_index(k_list, v_list, source_list, dk, dv, fix_source=False)
                if statue_temp:
                    #print("已存在,skip")
                    #i+=1
                    continue
            #print("现有bibtex数量:",i)
            temp_dict = {}
            temp_dict['k'] = dk
            temp_dict['v'] = dv
            #print(k,v)
            if paper_type == "IEEE":
                authors = dv.split(",")[0]
                author = authors.split(" ")[-1]
            elif paper_type == "APA":
                author_name = dk.split(".")[0].split(",")[0]
                author = author_name.split(" ")[0][1:]
            else:
                print("论文类型错误")
            #print(author)
            title = volces_chat(f"提取下列论文信息的title! 只返回title的字符串, 不返回其他信息!\n{dv}")
            #print(title)
            
            abstract = ""
            ##测试
            #print(author_name)
            #print("等待谷歌反馈")
            #title,abstract = check_papertitle_from_google(title,author)
            #print(title,author,abstract)
            #print(title, author)
            statue_temp, title, first_Author, abstract, bibtex_name, bibtex_entry = search_paper_from_arxiv(title, author)

            if statue_temp:
                #print("arxiv有内容")
                temp_dict["title"] = title
                temp_dict["first_Author"] = first_Author
                temp_dict["abstract"] = abstract
                temp_dict["bibtex_name"] = bibtex_name
                temp_dict["source"] = "arxiv"
                temp_dict["bibtex_content"] = bibtex_entry
                bibtex_dict_k[i] = temp_dict
                i+=1
            else:
                bibtex_info = dv
                source = "Generation"
                ## arxiv无内容
                if check_result == '网络正常':
                    title,abstract = check_papertitle_from_google(title,author)
                    #print(title,author)
                    #print("等待Dblp反馈")
                statue_temp,paper_info_dict = search_paper_from_dblp(title,author)
            
                if statue_temp:
                    bibtex_info = paper_info_dict
                    source = "Dblp"
                else:
                    #print("等待semanticscholar反馈")
                    statue_temp,paper_info_dict,abstract_2 = search_paper_from_semanticscholar(title,author)
                    if len(abstract_2) > len(abstract):
                        abstract = abstract_2
                    source = "Semanticscholar"
                    if statue_temp:
                        for k_temp in ["ee","key","url","paperId"]:
                            if k in paper_info_dict:
                                del paper_info_dict[k_temp]
                            #print(paper_info_dict)
                        bibtex_info = paper_info_dict
                    else:
                        #print("未找到论文")
                        source = "Generation"
                        bibtex_info = dv
                #elif check_result == '网络异常':
                #    source = "Generation"
                #    bibtex_info = dv

                temp_dict.update(generate_bibtex(bibtex_info,source))
                temp_dict["title"] = title
                temp_dict["first_Author"] = author
                temp_dict["abstract"] = abstract
                #print(temp_dict)
                bibtex_dict_k[i] = temp_dict
                i+=1
                #print("结束——————————————————————————————")
            #print("i:",i)
            #if i >=2:
            #    break
            bibtex_dict[k].update(bibtex_dict_k)
            with open(f"{folder_selected}/project/{project_name}/data/bibtex_dict.json", 'w', encoding='utf-8') as f:
                        json.dump(bibtex_dict, f, ensure_ascii=False, indent=4)
    print("bibtex_dict.json文件已保存")

# 创建主窗口
root = tk.Tk()
root.title("选择目录示例")

# 设置窗口大小
window_width = 600
window_height = 300
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
position_top = int(screen_height / 2 - window_height / 2)
position_right = int(screen_width / 2 - window_width / 2)
root.geometry(f'{window_width}x{window_height}+{position_right}+{position_top}')

# 设置窗口最小尺寸
root.minsize(500, 250)

# 设置背景颜色
root.configure(bg='#f0f0f0')

# 使用ttk风格化组件
style = ttk.Style()

# 设置全局字体
style.configure('.', font=('Microsoft YaHei', 12), background='#f0f0f0')

# 设置按钮样式
style.configure('TButton', foreground='black', background='#4CAF50', borderwidth=1, focusthickness=3, focuscolor='none')
style.map('TButton', background=[('active', '#45a049')])

# 设置标签样式
style.configure('TLabel', foreground='#333333', background='#f0f0f0', font=('Microsoft YaHei', 12))

# 创建左侧步骤列表
steps_frame = ttk.Frame(root)
steps_frame.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=20)

# 步骤名称
steps = ["启动项目", "启动数据库", "提取PDF信息", "生成BibTeX"]
step_labels = []

# 为每个步骤创建标签
for i, step in enumerate(steps):
    step_label = ttk.Label(steps_frame, text=f"{step} ✖")  # 初始状态为未完成
    step_label.grid(row=i, column=0, sticky=tk.W, pady=5)
    step_labels.append(step_label)

# 创建右侧主功能区
main_frame = ttk.Frame(root)
main_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=20, pady=20)

# 创建按钮，点击后弹出选择目录的对话框
button = ttk.Button(main_frame, text="选择目录", command=main_programme())
button.pack(pady=20)

# 创建按钮，点击后弹出选择目录的对话框
button_LLM = ttk.Button(main_frame, text="开始问答", state="DISABLED")
button_LLM.pack(pady=20)
button_LLM.pack_forget()

def on_closing():
    """当用户点击关闭按钮时调用"""
    root.quit()

root.protocol("WM_DELETE_WINDOW", on_closing)
# 进入消息循环
root.mainloop()