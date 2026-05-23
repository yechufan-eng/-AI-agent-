"""配置管理模块"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """应用配置"""

    # Claude API
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # MySQL配置
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "schoolclass")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "1234")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "mysql")

    # 排除的表
    EXCLUDED_TABLES: list[str] = [
        t.strip() for t in os.getenv("EXCLUDED_TABLES", "").split(",") if t.strip()
    ]

    @classmethod
    def validate(cls) -> bool:
        """验证必要配置是否存在"""
        if not cls.ANTHROPIC_API_KEY:
            print("错误: 未设置 ANTHROPIC_API_KEY")
            return False
        if not cls.MYSQL_DATABASE:
            print("错误: 未设置 MYSQL_DATABASE")
            return False
        return True
