# routers/text2sql_router.py
import re
import traceback
import logging
from typing import Optional
import time

from fastapi import status,Request
from pydantic import BaseModel

from routers.base_router import BaseRouter
from services.text2sql_service import Text2SqlService


logger = logging.getLogger(__name__)



# 数据模型
class QueryRequest(BaseModel):
    question: str
    user_id: Optional[str] = None
    chat_id: Optional[str] = None
    limit: Optional[int] = 10
    auto_execute: Optional[bool] = True


class QueryResponse(BaseModel):
    success: bool
    question: str
    result: dict = None
    error: Optional[str] = None
    execution_time: float


class Text2SqlRouter(BaseRouter):
    def __init__(self):
        logger.info("Initializing Text2SqlRouter")
        super().__init__()
        self.router = self._register_routes()
        self._initialized = False
        self.text2service = Text2SqlService()

    def _register_routes(self):
        self.router.post(
            "/query",
            response_model=QueryResponse,
            status_code=status.HTTP_200_OK,
            summary="查询问题",
            description="模型转换sql",
            tags=["vanna系统"]
        )(self.natural_language_query)

        return self.router
    async def natural_language_query(self, request: QueryRequest):
        """自然语言查询接口 - 异步版本"""
        start_time = time.time()
        execution_time = 0
        try:
            # 输入端确保只生成查询问题
            logger.info(f"收到查询请求：{request.question}")
            
            # 异步调用服务层
            result = await self.text2service.probe_wenshu(request.question, request.user_id, request.chat_id)
            execution_time = time.time() - start_time

            return QueryResponse(
                success=True,
                question=request.question,
                result=result,
                execution_time=execution_time
            )

        except Exception as e:
            logger.error(f"查询处理失败：{str(e)}")
            execution_time = time.time() - start_time
            traceback.print_exc()
            return QueryResponse(
                success=False,
                question=request.question,
                error=str(e),
                execution_time=execution_time
            )
