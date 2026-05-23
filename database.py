"""MySQL数据库操作模块"""
import re
from typing import Any

import mysql.connector
from mysql.connector import Error
from rich.table import Table

from config import Config




class Database:
    """MySQL数据库操作类"""

    def __init__(self) -> None:
        self.connection = None
        self.connect()

    def connect(self) -> None:
        """连接数据库"""
        try:
            self.connection = mysql.connector.connect(
                host=Config.MYSQL_HOST,
                port=Config.MYSQL_PORT,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                database=Config.MYSQL_DATABASE,
            )
        except Error as e:
            console.print(f"[red]数据库连接失败: {e}[/red]")
            raise

    def close(self) -> None:
        """关闭连接"""
        if self.connection and self.connection.is_connected():
            self.connection.close()

    def get_tables(self) -> list[str]:
        """获取所有表名"""
        cursor = self.connection.cursor()
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        # 过滤排除的表
        return [t for t in tables if t not in Config.EXCLUDED_TABLES]

    def get_table_schema(self, table_name: str) -> list[dict[str, Any]]:
        """获取表结构"""
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(f"DESCRIBE `{table_name}`")
        schema = cursor.fetchall()
        cursor.close()
        return schema

    def get_all_schemas(self) -> dict[str, list[dict[str, Any]]]:
        """获取所有表的schema"""
        schemas = {}
        for table in self.get_tables():
            schemas[table] = self.get_table_schema(table)
        return schemas

    def is_safe_query(self, sql: str) -> bool:
        """检查是否为安全的SELECT查询"""
        sql_upper = sql.strip().upper()
        # 只允许SELECT语句
        if not sql_upper.startswith("SELECT"):
            return False
        # 禁止危险操作
        dangerous_keywords = [
            "INSERT",
            "UPDATE",
            "DELETE",
            "DROP",
            "ALTER",
            "CREATE",
            "TRUNCATE",
            "GRANT",
            "REVOKE",
        ]
        for keyword in dangerous_keywords:
            if re.search(rf"\b{keyword}\b", sql_upper):
                return False
        return True

    def execute_query(self, sql: str) -> tuple[list[tuple], list[str]]:
        """执行查询，返回结果和列名"""
        if not self.is_safe_query(sql):
            raise ValueError("只允许执行SELECT查询")

        cursor = self.connection.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        cursor.close()
        return results, columns

    def display_results(self, results: list[tuple], columns: list[str]) -> None:
        """美化显示查询结果"""
        if not results:
            console.print("[yellow]查询结果为空[/yellow]")
            return

        table = Table(show_header=True, header_style="bold cyan")
        for col in columns:
            table.add_column(col)

        for row in results:
            table.add_row(*[str(cell) if cell is not None else "NULL" for cell in row])

        console.print(table)
        console.print(f"[green]共 {len(results)} 条记录[/green]")
