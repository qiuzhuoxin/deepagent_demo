# ==================== 模型配置 ====================
# 选择模型模式："server" 使用服务器模型，"local" 使用本地 Ollama 模型
import os
from pathlib import Path

MODEL_MODE = "local"  # 可选值: "server" | "local"

# ------------------ 服务器模型配置 ------------------
# 当 MODEL_MODE = "server" 时生效
SERVER_LLM_BASE_URL = "http://172.16.49.54:9080/v1"
SERVER_LLM_MODEL = "qwen3-30b-a3b-instruct"
SERVER_LLM_API_KEY = "sk-no-key-required"

# ------------------ 本地模型配置 ------------------
# 当 MODEL_MODE = "local" 时生效
LOCAL_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
LOCAL_LLM_MODEL = "qwen3-32b"
# LOCAL_BASE_URL = "http://127.0.0.1:11434/v1"
# LOCAL_LLM_MODEL = "qwen3:1.7b"
LOCAL_LLM_API_KEY = os.getenv("MODEL_API_KEY")


# RAG服务路径
nw_rag_url = "http://127.0.0.1:8000"
# 达梦数据库
DM_DATABASE_URL = "127.0.0.1"
DM_DATABASE_PORT = 5236
DM_DATABASE_USER = "DB_GXAI"
DM_DATABASE_PWD = "Gxaidmm@123"

# Redis
REDIS_URL = "redis://:123456@127.0.0.1:6379/0"
MEMORY_KEY_PREFIX = "mem:text2sql"
MEMORY_MAX_TURNS = 3
MEMORY_TTL_SECONDS = 604800

CURRENT_ROOT = Path(__file__).parent.resolve()
SKILLS_DIR = (CURRENT_ROOT / "skills").as_posix() # 统一为正斜杠 /

def get_model_config():
    """
    获取统一的模型配置
    根据 MODEL_MODE 返回对应的模型配置
    """
    if MODEL_MODE == "server":
        return {
            "mode": "server",
            # LLM 配置
            "llm_base_url": SERVER_LLM_BASE_URL,
            "llm_model": SERVER_LLM_MODEL,
            "llm_api_key": SERVER_LLM_API_KEY,
        }
    elif MODEL_MODE == "local":
        return {
            "mode": "local",
            # LLM 配置
            "llm_base_url": LOCAL_BASE_URL,
            "llm_model": LOCAL_LLM_MODEL,
            "llm_api_key": LOCAL_LLM_API_KEY,  # Ollama 不需要 API key
        }
    else:
        raise ValueError(f"无效的 MODEL_MODE: {MODEL_MODE}，可选值为 'server' 或 'local'")

