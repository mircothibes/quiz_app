from dataclasses import dataclass
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class DatabaseConfig:
    host: str
    port: int
    name: str
    user: str
    password: str


def load_config() -> DatabaseConfig:
    load_dotenv()

    host = os.getenv("DB_HOST", "localhost")
    port_str = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")

    if not name or not user or not password:
        raise ValueError("Missing required database environment variables: DB_NAME, DB_USER, DB_PASSWORD")

    return DatabaseConfig(
        host=host,
        port=int(port_str),
        name=name,
        user=user,
        password=password,
    )
