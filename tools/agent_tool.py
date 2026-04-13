import logging
import types
import pandas as pd
import requests
from langchain_core.tools import tool

nw_rag_url = "http://localhost:8000"

def _get_similar_ddl(question: str) -> dict:
    """
    根据用户问题，获取可能需要的数据库表结构（DDL）
    """
    try:
        response = requests.post(
            nw_rag_url + "/api/v1/rag/wenshu_query",
            json={
                "question": question,
                "collection": "nw_wenshu_ddl",
                "top_k": 5,
                "query_mode": "vector"
            },
            timeout=120
        )
        if response.status_code == 200:
            data = response.json()
            return {"ddl": data.get("data")}
        else:
            logging.error(f"nw_rag服务错误, ERROR: HTTP {response.status_code}")
    except Exception as e:
        logging.error(f"ERROR: {str(e)}")
    return {"ddl": []}

def _get_similar_sql(question: str) -> dict:
    """
    根据用户问题，获取相关的问答对示例（问题-sql）
    """
    try:
        response = requests.post(
            nw_rag_url + "/api/v1/rag/wenshu_query",
            json={
                "question": question,
                "collection": "nw_wenshu_qa_pair",
                "top_k": 10,
                "query_mode": "hybrid",
                "output_fields": "qa_pair"
            },
            timeout=120
        )
        if response.status_code == 200:
            data = response.json()
            return {"sql_examples": data.get("data")}
        else:
            logging.error(f"nw_rag服务错误, ERROR: HTTP {response.status_code}")
    except Exception as e:
        logging.error(f"ERROR: {str(e)}")
    return {"sql_examples": []}

def _execute_sql(sql: str):
    """
    连接达梦数据库并执行 SQL 查询语句

    Args:
        sql: 要执行的 SQL 语句（仅支持 SELECT）

    Returns:
        DataFrame: 查询结果
    """
    try:
        import dmPython
        conn = dmPython.connect(
            user='DB_GXAI',
            password='Gxaidmm@123',
            server='LOCALHOST',
            port=5236,
            autoCommit=True
        )
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=[desc[0] for desc in cursor.description])
        cursor.close()
        conn.close()
        return {
            'success': True,
            'data': df,
            'rows': len(df)
        }
    except Exception as e:
        logging.error(f"数据库执行失败: {str(e)}")
        return {
            'success': False,
            'error': f'数据库执行失败: {str(e)}',
            'error_code': 'DATABASE_ERROR'
        }

def _get_ddl_table_info(ddls: list) -> dict:
    """
    获取表的结构信息和注释
    """
    try:
        response = requests.post(
            nw_rag_url + "/api/v1/rag/field_query",
            json={
                "expr": f"ddl_name in {ddls}",
                "collection": "nw_wenshu_ddl",
                "top_k": 5,
                "output_fields": "text"
            },
            timeout=120
        )
        if response.status_code == 200:
            data = response.json()
            return {"table_info": data.get("data")}
        else:
            logging.error(f"nw_rag服务错误, ERROR: HTTP {response.status_code}")
    except Exception as e:
        logging.error(f"ERROR: {str(e)}")
    return {"table_info": []}

def _get_similar_docs(question: str) -> dict:
    """
    根据用户问题，获取可能需要的文档内容
    """
    try:
        response = requests.post(
            nw_rag_url + "/api/v1/rag/wenshu_query",
            json={
                "question": question,
                "collection": "nw_wenshu_doc",
                "top_k": 8
            },
            timeout=120
        )
        if response.status_code == 200:
            data = response.json()
            return {"docs": data.get("data")}
        else:
            logging.error(f"nw_rag服务错误, ERROR: HTTP {response.status_code}")
    except Exception as e:
        logging.error(f"ERROR: {str(e)}")
    return {"docs": []}

class WenShuTools:
    def __init__(self):
        pass

    def get_tools(self):
        return [
            tool(_get_similar_ddl),
            tool(_get_similar_sql),
            tool(_get_similar_docs),
            tool(_execute_sql),
            tool(_get_ddl_table_info)
        ]