# 导入数据库检查工具，用来读取表结构
from sqlalchemy import inspect
# 导入pandas，接收、存储数据库查询结果
import pandas as pd
# 导入绘图库，实现数据可视化
import matplotlib.pyplot as plt

# 定义AI智能体的数据库工具类
class DatabaseTool:

    # 工具1：通用检索表结构（静态方法，直接类名调用）
    @staticmethod
    def get_table_schema(engine, table_name: str) -> str:
        # 创建通用数据库检查器，适配MySQL/SQLite/PostgreSQL
        inspector = inspect(engine)
        # 获取目标表的所有字段信息（字段名、类型、约束）
        columns = inspector.get_columns(table_name)
        # 获取该表的主键字段
        primary_keys = inspector.get_primary_keys(table_name)

        # 定义空列表，用来存放拼接好的表结构文本
        schema_info = []
        # 遍历每一个字段
        for col in columns:
            # 拼接每个字段的详细信息：名字、类型、是否主键、是否可空
            info = (
                f"字段名：{col['name']}，"
                f"类型：{str(col['type'])}，"
                f"主键：{col['name'] in primary_keys}，"
                f"可空：{col['nullable']}"
            )
            # 把当前字段信息加入列表
            schema_info.append(info)
        # 将所有字段信息换行拼接成一段字符串，方便AI读取
        return "\n".join(schema_info)


    # 工具2：通用执行SQL查询
    @staticmethod
    def execute_query(engine, sql: str):
        # 建立临时数据库连接，执行完自动关闭
        with engine.connect() as conn:
            # 执行sql语句，查询结果转为DataFrame表格格式
            df = pd.read_sql(sql, conn)
        # 返回查询到的结构化数据
        return df


    # 工具3：查询结果数据可视化（柱状图）
    @staticmethod
    def visualize_data(df, x_col: str, y_col: str):
        # 创建画布，设置图片大小
        plt.figure(figsize=(8, 5))
        # 绘制柱状图：x轴字段、y轴字段
        plt.bar(df[x_col], df[y_col])
        # 设置x轴名称
        plt.xlabel(x_col)
        # 设置y轴名称
        plt.ylabel(y_col)
        # 设置图表标题
        plt.title("数据可视化")
        # 自动调整布局，防止文字重叠
        plt.tight_layout()
        # 弹出显示图表
        plt.show()