import streamlit as it
from openai import OpenAI
import os
import json
from datetime import datetime
from config import Config
from database import Database
from rich.markdown import Markdown



from streamlit import session_state
#构建数据库表结构：
def build_schema_info(db) -> str:
    """构建数据库schema信息"""
    schemas = db.get_all_schemas()
    info_lines = ["数据库表结构信息：\n"]

    for table_name, columns in schemas.items():
        info_lines.append(f"表名: {table_name}")
        for col in columns:
            field = col.get("Field", "")
            type_info = col.get("Type", "")
            null = col.get("Null", "")
            key = col.get("Key", "")
            default = col.get("Default", "")
            extra = col.get("Extra", "")
            info_lines.append(
                f"  - {field}: {type_info} | Null: {null} | Key: {key} | Default: {default} | {extra}"
            )
        info_lines.append("")

    return "\n".join(info_lines)
#加载会话信息：
def load_session(session_name):
    if os.path.exists(f"session/{session_name}.json"):
        with open(f"session/{session_name}.json","r",encoding="utf-8") as f:
            session_data = json.load(f)
            it.session_state.message=session_data["message"]
            it.session_state.nature=session_data["nature"]
            it.session_state.nick_name=session_data["nick_name"]
            it.session_state.current_session=session_data["current_session"]
def judge_select(text):
    return "我是查询数据指令" in text

#调用函数连接数据库：
def connect_database():
    try:
        return Database()
    except Exception as e:
        print(f"[red]初始化失败: {e}[/red]")
        return None

    console.print(f"[green]已连接数据库: {Config.MYSQL_DATABASE}[/green]")
    console.print(f"[green]可用表数量: {len(db.get_tables())}[/green]\n")
#关闭数据库
def close_database():
    db.close()
#写函数调用用来保存对话：
def save_chat_message():
    if not hasattr(it.session_state, 'current_session') or not it.session_state.current_session:
        return
    current_data={
             "current_session":it.session_state.current_session,
             "message":it.session_state.message,
             "nature":it.session_state.nature,
             "nick_name":it.session_state.nick_name
    }
    if not os.path.exists("session"):
         os.mkdir("session")
    session_name = it.session_state.current_session.replace(":", "-").replace(" ", "_")
    with open( f"session/{session_name}.json","w",encoding="utf-8") as i:
         json.dump(current_data,i,ensure_ascii=False,indent=2)
         i.close()
def load_chat_message():
    chat_session=[]
    if os.path.exists("session"):
        for file in os.listdir("session"):
            if file.endswith(".json"):
                chat_session.append(file[:-5])
    return chat_session

def _process_response(db, response: str) -> str:
        """处理AI响应，提取并执行SQL"""
        import re

        # 查找SQL代码块
        sql_pattern = r"```sql\s*(.*?)\s*```"
        sql_matches = re.findall(sql_pattern, response, re.DOTALL | re.IGNORECASE)

        results_text = ""

        for sql in sql_matches:
            try:
                results, columns = db.execute_query(sql.strip())
                #results_text += f"\n\n执行SQL: {sql.strip()}\n"
                if results:
                    # 格式化结果
                    results_text += "表数据查询结果:\n\n"
                    for row in results[:20]:  # 限制显示20条
                        row_dict = dict(zip(columns, row))
                        results_text += f"  {row_dict}\n\n"
                    if len(results) > 20:
                        results_text += f"  ... 还有 {len(results) - 20} 条记录\n\n"
                else:
                    results_text += "查询结果为空\n\n"
            except ValueError as e:
                results_text += f"[red]安全限制: {e}[/red]\n\n"
            except Exception as e:
                results_text += f"[red]执行错误: {e}[/red]\n\n"

        # 移除SQL代码块，保留解释
        clean_response = re.sub(sql_pattern, "", response, flags=re.DOTALL | re.IGNORECASE)

        # 组合结果
        if results_text:
            return f"{results_text}\n{clean_response.strip()}"
        return clean_response.strip()

def display_response(self, response: str) -> None:
        """美化显示响应"""
        md = Markdown(response)
        console.print(md)

#get help中要你自己模型的链接
#  建立一个空容器。
#chunk.choices.delta.content:
#拼接容器
#会话记忆：it.session_state;+message

#初始话页面设置
db=connect_database()
table_str=build_schema_info(db)

it.set_page_config(page_title="AI-agent",
                   page_icon="🤖",
                   layout="wide",
                   initial_sidebar_state="expanded",
                   menu_items={'Get Help': 'https://github.com/deepseek-ai/ai-agent',
                               'Report a bug': 'https://github.com/deepseek-ai/ai-agent/issues',
                               'About': 'This is an AI-agent demo.'
                               }
                   )
it.title("聊天小助手")
nature="可爱"
nick_name="小可爱"
if "current_session" not in it.session_state:
    it.session_state.current_session=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
it.text(f"当前会话 :{session_state.current_session}")
if "message" not in it.session_state:
    it.session_state.message = []
for message in it.session_state.message:
    it.chat_message(message["role"]).write(message["content"])

prompt=it.chat_input("请输入你的问题")
if prompt:
   with it.chat_message("user"):
       it.write(prompt)
       it.session_state.message.append({"role": "user", "content": prompt})
with it.sidebar:
    it.subheader("会话设置")
    if it.button("新建会话", width="stretch", icon="✏"):
        if session_state.message:
            save_chat_message()
        it.session_state.current_session=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        it.session_state.message = []
        nature = "可爱"
        nick_name = "小可爱"
        it.rerun()
    it.text("会话历史")
    col1,col2=it.columns([4,1])
    chat_session=load_chat_message()
    for data in chat_session:
        if col1.button(data, width="stretch",key=f"load_{data}",type="primary" if data==session_state.current_session else"secondary"):
            load_session(data)
            it.rerun()
        if col2.button("",icon="❌",key=f"delete_{data}"):
            if os.path.exists(f"session/{data}.json"):
                os.remove(f"session/{data}.json")
                if data==session_state.current_session:
                    it.session_state.message=[]
                it.rerun()
    it.subheader("参数信息")
    nick_name=it.text_input("请输入你的名称",value="小可爱",placeholder="请输入名字")
    nature=it.text_input("请输入你的性格",value="可爱",placeholder="请输入性格")
#if nick_name  not in it.session_state:
#    it.session_state.nick_name="小可爱"
#if nature  not in it.session_state:
#    it.session_state.nature="可爱"
#调用AI大模型生成回复
if prompt:
  client = OpenAI(
    api_key= "sk-54eb9eef21944ac3af76046758ed9fe4" ,
    base_url="https://api.deepseek.com"
  )
  table_str_escaped = table_str.replace('%', '%%')
  c="你是一个%s女生，你的名字叫%s，不能在回答中有删除线，同时你也是数据分析师，如果是查询表数据，生成‘我是查询数据指令’，帮我生成1条查询的SQL语句。如果是查询或列出表结构，则不认为是查询数据指令；其他情况，都不生成SELECT查询sql语句。我现在数据库的表结构有:"+table_str_escaped
  response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                        {"role": "system", "content": c%(nature,nick_name)},
                        {"role": "user", "content": str(prompt)},
                    ],
            stream=True
                )

  response_message=it.empty()
  full_response=" "
  for chunk in response:
    if chunk.choices[0].delta.content is not None:
      text=chunk.choices[0].delta.content
      full_response+=text
      response_message.markdown(full_response)
  response_message.chat_message("assistant").write(full_response)
  it.session_state.message.append({"role": "assistant", "content": full_response})

  if judge_select(full_response):
    outputStr = _process_response(db,full_response)
    response_message.chat_message("assistant").write(outputStr)
    it.session_state.message.append({"role": "assistant", "content": outputStr})
#加载完要更新最新的信息保存起来
#加载数据库