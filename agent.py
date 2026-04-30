import requests
import json
import pymysql
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ==================== 配置区 ====================
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "deepseek-r1:1.5b"

# ⚠️ MySQL 连接配置（改成你能连上的真实信息）
DB_CONFIG = {
    "host": "localhost",        # 你的MySQL主机地址
    "port": 3306,                   # 端口
    "user": "root",                 # 用户名
    "password": "Ms329830",         # 密码
    "database": "chinook",          # 数据库名
    "charset": "utf8mb4",
    "connect_timeout": 10,
    "autocommit": True
}

# ==================== 数据库连接 ====================

def get_connection():
    """创建数据库连接"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        raise Exception(f"数据库连接失败: {str(e)}")

# ==================== 工具函数 ====================

def get_table_schema() -> str:
    """获取数据库所有表的结构"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        if not tables:
            return "数据库中未找到任何表。"
        result = ""
        for table in tables:
            table_name = table[0]
            result += f"\n=== 表: {table_name} ===\n"
            cursor.execute(f"SHOW COLUMNS FROM `{table_name}`;")
            for col in cursor.fetchall():
                result += f"  - {col[0]} ({col[1]})\n"
        return result.strip()
    except Exception as e:
        return f"获取表结构时出错: {str(e)}"
    finally:
        if conn:
            conn.close()

def execute_query(sql: str) -> str:
    """执行一条 SQL 查询并返回结果"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(sql)
        if sql.strip().upper().startswith('SELECT'):
            results = cursor.fetchall()
            if not results:
                return "查询成功，但没有返回任何数据。"
            return str(results[:50])
        else:
            conn.commit()
            return "语句执行成功。"
    except Exception as e:
        return f"SQL执行出错: {str(e)}"
    finally:
        if conn:
            conn.close()

def visualize_query(sql: str, chart_type: str = "bar") -> str:
    """执行查询并生成图表"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
        if not results:
            return "查询没有返回任何数据，无法绘图。"
        results = results[:10]
        labels = [str(row[0]) for row in results]
        values = [row[1] if len(row) > 1 else 1 for row in results]
        plt.clf()
        plt.figure(figsize=(10, 6))
        if chart_type == "pie":
            plt.pie(values, labels=labels, autopct='%1.1f%%')
            plt.title("查询结果 - 饼图")
        else:
            plt.bar(labels, values)
            plt.title("查询结果 - 柱状图")
            plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        chart_path = "query_chart.png"
        plt.savefig(chart_path, dpi=100)
        plt.close('all')
        return f"图表已保存为 {chart_path}"
    except Exception as e:
        return f"生成图表时出错: {str(e)}"
    finally:
        if conn:
            conn.close()

# ==================== 调模型 ====================

def ask_brain(messages: list) -> str:
    """把 messages 发给 Ollama，返回模型回复"""
    try:
        data = {
            "model": MODEL_NAME,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.1}
        }
        response = requests.post(OLLAMA_URL, json=data, timeout=60)
        if response.status_code != 200:
            return f"Ollama 返回错误: HTTP {response.status_code}"
        return response.json()["message"]["content"]
    except Exception as e:
        return f"调用模型出错: {str(e)}"

# ==================== 系统提示词 ====================

SYSTEM_PROMPT = """你是数据库查询助手。你可以使用以下三个工具：

工具1：get_table_schema
  作用：获取数据库中所有表的结构
  不需要参数

工具2：execute_query
  作用：执行一条 SQL 查询
  参数：sql（SQL语句，注意这是 MySQL 语法）

工具3：visualize_query
  作用：执行查询并生成图表
  参数：sql（SQL语句），chart_type（图表类型，可选 "bar" 或 "pie"）

规则：
1. 当需要查询数据库时，严格只返回以下 JSON 格式，不要包含任何其他文字：
   {"tool": "工具名", "args": {"参数名": "参数值"}}
2. 拿到工具返回的结果后，用中文回答用户问题。
3. 如果问题不需要数据库，直接回答。
4. 用户要求画图时，使用 visualize_query 工具。"""

# ==================== 主程序 ====================

def main():
    # 启动前测试数据库连接
    try:
        conn = get_connection()
        conn.close()
        print("✅ 数据库连接成功")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    print("=" * 50)
    print("🤖 你的数据库助手已上线！")
    print("   - 可以问我数据库里的任何问题")
    print("   - 可以让我画图（柱状图/饼图）")
    print("   - 输入 exit 退出")
    print("=" * 50)

    while True:
        try:
            user_input = input("\n你：")
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if user_input.lower() == "exit":
            print("再见！")
            break

        if not user_input.strip():
            continue

        messages.append({"role": "user", "content": user_input})
        print("[思考中...]")
        reply = ask_brain(messages)

        if '{"tool":' in reply:
            try:
                start = reply.find('{"tool":')
                end = reply.rfind('}') + 1
                tool_json = reply[start:end]
                tool_call = json.loads(tool_json)

                tool_name = tool_call.get("tool")
                tool_args = tool_call.get("args", {})
                print(f"[Agent 调用工具: {tool_name}]")

                if tool_name == "get_table_schema":
                    tool_result = get_table_schema()
                elif tool_name == "execute_query":
                    tool_result = execute_query(tool_args.get("sql", ""))
                elif tool_name == "visualize_query":
                    tool_result = visualize_query(
                        tool_args.get("sql", ""),
                        tool_args.get("chart_type", "bar")
                    )
                else:
                    tool_result = f"未知工具: {tool_name}"

                messages.append({
                    "role": "system",
                    "content": f"工具 {tool_name} 返回结果：{tool_result}"
                })

                print("[正在组织回答...]")
                final_reply = ask_brain(messages)
                messages.append({"role": "assistant", "content": final_reply})
                print(f"Agent：{final_reply}")

            except json.JSONDecodeError:
                messages.append({"role": "assistant", "content": reply})
                print(f"Agent：{reply}")
            except Exception as e:
                print(f"[调试] 工具调用出错: {str(e)}")
        else:
            messages.append({"role": "assistant", "content": reply})
            print(f"Agent：{reply}")

if __name__ == "__main__":
    main()