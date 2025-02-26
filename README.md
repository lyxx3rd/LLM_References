# LLM_Referencs

通过LLM模型生成参考文献, 并实现直接检索调用!

## 1. 快速开始

安装基础环境
```bash
pip install -r requirements.txt
```

运行
```python
python app.py
```

## 2. 使用方法

### 1. 选择一级目录

在一级目录下可以存在多个数据库, 以不同数据库为单位可以实现分类管理不同类型或不同领域的文献

### 2. 配置基础API

api需要包括volces(字节)的api, 以及qianfan(baidu)的api.


volces官网: http://console.volcengine.com/auth/login?redirectURI=%2Fark%2Fregion%3Aark%2Bcn-beijing%2Fmodel%3Fvendor%3DBytedance%26view%3DLIST_VIEW


qianfan官网: https://cloud.baidu.com/doc/WENXINWORKSHOP/index.html


2.1 API示例


volces api 格式为: Bearer 23afde61-....-.... (参考长度:43)


qianfan API_Key 格式为: 23afde61.... (参考长度:24)


qianfan Secret_Key 格式为: 23afde61.... (参考长度:32)


### 3. 配置数据库

"创建新数据库"按钮可以创建新的数据库

也可以选择现有数据库

### 4. 提取pdf信息

在将论文文献以pdf的格式放如数据库路径下的pdf文件夹后, 点击"提取pdf信息"按钮即可

路径如:"{folder_selected}/project/{project_name}/pdf"

### 5. 生成Bibtex

自动从包括arxiv, google, dblp, semanticscholar四个路径搜索引用文献, 并自动生成Bibtex文件.

当所有路径都找不到时, 会使用LLM自动生成Bibtex, 但此时需注意是否存在信息提取错误或者原论文瞎编引用的情况

所有Bibtex的生成来源都会标注在 {folder_selected}/project/{project_name}/data/bibtex_dict.json 的resource中.

### 6. 检索调用

点击"开始问答"进入检索环节!

!! 注意 !!

这是在pdf的论文库里检索引用的内容, 并抓取其附录, 且核对Bibtex的功能!

并不是检索问答类的LLM!

因此不会(大概不会)存在知识推理或解读, 一切内容基于原文!

如原文没有的信息, 会直接返回"未找到相关引用"!

6.1 Latex格式

为方便Latex写作, 可以选择"Latex格式"

输出的内容可直接复制进Latex中, 并将Latex的Bibtex复制进入Latex文件的bib中, 然后即可直接引用!

Latex编辑软件推荐使用Overleaf!

## 结尾

有问题私聊我吧!
