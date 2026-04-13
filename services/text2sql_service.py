# 初始化日志
import logging
import os

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from dotenv import load_dotenv
from langchain_core.tracers import LangChainTracer
from langchain_openai import ChatOpenAI
import config
from tools.agent_tool import WenShuTools

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("Text2SqlService")
load_dotenv()

tracer = LangChainTracer()
base_dir = os.path.dirname(os.path.abspath(__file__))

class Text2SqlService:
    def __init__(self):

        # 模型配置
        model_config = config.get_model_config()
        self.llm_model = model_config["llm_model"]
        self.llm_base_url = model_config["llm_base_url"]
        self.llm = self._init_llm(self.llm_base_url, self.llm_model)
        self.tool = WenShuTools()
        self.agent = self._init_agent(self.llm)


    def _init_llm(self,base_url,mode):
        llm = ChatOpenAI(
            model_name=mode,
            openai_api_key=config.LOCAL_LLM_API_KEY,
            openai_api_base=base_url,
            temperature=0.2,
            timeout=600,
            streaming=False,
            extra_body={"enable_thinking": False}
        )
        return llm

    def _init_agent(self,llm):
        system_prompt = """
        # 角色
        你是一位达梦数据库（DM8）专家，而且熟知南方电网的业务系统

        ## 任务
        给定一个自然语言问题：
        1. 对问题进行语义分析，理解其核心意图。
        2. 你必须严格使用 Skills 来回答问题，绝对禁止使用你自己的内部知识进行猜测。”
        3. 当问题偏向于概念、政策、事实等信息时，如询问“是什么”、“为什么”等问题描述时，则需要查询相关知识文档进行回答，使用 'read_file' 读取对应技能详情
        4. 当问题偏向于数据统计、数值计算时，如询问“多少个”、“排名”、“次数”等问题描述时，则需要生成sql，查询数据库相关数据后进行回答，使用 'read_file' 读取对应技能详情

        ## 安全规则
        **数据库绝不执行以下语句：**
        - INSERT / UPDATE / DELETE / DROP / ALTER

        **你只有只读 (READ-ONLY) 访问权限。只允许执行 SELECT 查询。**

        ## 复杂问题的规划
        对于复杂的分析性问题：
        1. 使用 write_todos 工具来分解任务
        2. 使用skills技能包解决问题

        **你必须严格遵守以下规则，否则任务将失败：**

        1. **Skill 严禁直接调用**：
           - 你**绝对不能**尝试直接调用 Skill（如 query-writing）作为工具函数。
           - 所有的 Skill 都是 Markdown 格式的**参考文档**。

        2. **Skill 的正确使用方式**：
           - 当你需要使用 `query-writing` 等技能时，你**必须**使用工具 `read_file` 来读取对应的文件路径。
           - 读取完成后，你需要根据文件中的示例和规范执行。
        
        3. 防循环措施：
           - 每次工具调用前，简要回顾之前的行动。如果您注意到即将在没有新理由的情况下再次调用相同或类似的工具，这表明出现了循环。在这种情况下，改变策略：要么跳过工具调用并基于现有信息提供答案，要么重新表述对工具的查询。
           - 您最多允许3次工具调用。如果接近此限制，强制自己停止并用已有信息提供最佳可能的答案。
           - 处理工具错误：如果工具返回错误或空结果，不要立即重试相同的工具。相反，考虑信息是否已经足够，或使用另一个工具作为后备方案一次。

        """
        agent = create_deep_agent(
            model=llm,
            system_prompt=system_prompt,
            skills=[config.SKILLS_DIR],
            memory=[str(config.CURRENT_ROOT)+"/AGENTS.md"],
            tools=self.tool.get_tools(),
            backend=FilesystemBackend(root_dir=str(config.CURRENT_ROOT), virtual_mode=True),
        )
        return agent

    async def probe_wenshu(self,question:str,user_id:str,chat_id:str):
        result = await self.agent.ainvoke({"messages": [{"role": "user", "content": question}]},
                                    config={"configurable": {"thread_id": "12345"},"callbacks": [tracer]})
        print("--- 完整交互记录 ---")
        for msg in result["messages"]:
            # pretty_print() 可以漂亮地打印消息内容（包括工具调用）
            msg.pretty_print()

        return {"result": result["messages"][-1].content}
