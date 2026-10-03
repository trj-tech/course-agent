from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置，可通过 .env 覆盖。"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "course-agent"
    debug: bool = True

    # 开发默认使用本地 SQLite，后续可切换 MySQL
    database_url: str = "sqlite:///./course_agent.db"

    # JWT 认证（生产环境务必通过 .env 覆盖）
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    # DeepSeek 大模型（OpenAI 兼容接口）
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"


settings = Settings()
