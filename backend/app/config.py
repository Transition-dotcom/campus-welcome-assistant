"""
应用配置。所有配置通过环境变量或 .env 文件设置，有默认值适合本地开发。
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 数据库
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = "root"
    db_name: str = "campus_nav"

    # JWT — 生产环境必须通过环境变量 JWT_SECRET 设置强随机密钥
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 120        # 2 小时
    refresh_token_expire_days: int = 7             # 7 天

    # 服务
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
            f"?charset=utf8mb4"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
