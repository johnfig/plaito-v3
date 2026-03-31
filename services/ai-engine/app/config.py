from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    supabase_url: str = "http://localhost:54321"
    supabase_service_key: str = ""
    deepseek_api_key: str = ""
    environment: str = "development"
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
