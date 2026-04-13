# main.py
from fastapi import FastAPI, Request

import logging.config
from contextlib import asynccontextmanager
import uvicorn


# 配置logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 移除所有现有的handler
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# 创建新的格式化器和handler
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)




# 创建 FastAPI 实例并绑定生命周期
app = FastAPI()


from routers.text2sql_router import Text2SqlRouter
text2sql_router = Text2SqlRouter()
# 挂载路由（确保每个路由模块中定义了 router 实例）
app.include_router(text2sql_router.router, prefix="/api/v1/text2sql")



# 健康检查端点

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/api/v1/stats")
async def get_stats(request: Request):
    """获取系统状态统计"""
    stats = {}

    request_tracker = getattr(request.app.state, 'request_tracker', None)
    if request_tracker:
        stats["requests"] = await request_tracker.get_stats()

    rate_limiter = getattr(request.app.state, 'rate_limiter', None)
    if rate_limiter:
        stats["rate_limiter"] = rate_limiter.get_stats()

    vn = getattr(request.app.state, 'vn', None)
    if vn and hasattr(vn, 'executor'):
        stats["thread_pool"] = vn.executor.get_stats()

    return stats



if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8018,
        workers=1,
        timeout_keep_alive=600,
        reload=False,
        limit_concurrency=1000,
        backlog=2048
    )
