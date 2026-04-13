
import os
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend, LocalShellBackend
from dotenv import load_dotenv
from langchain_core.tracers import LangChainTracer
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver

from rich.console import Console

from tools.agent_tool import WenShuTools

load_dotenv()

tracer = LangChainTracer()
console = Console()

# 1. 路径标准化处理
current_root = Path(__file__).parent.resolve()
skills_dir = (current_root / "skills").as_posix() # 统一为正斜杠 /
checkpointer = MemorySaver()

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
   
"""

def create_sql_deep_agent():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    print(base_dir)

    llm = ChatOpenAI(
        model_name="qwen3-32b",
        openai_api_key="sk-861647c7debd4fe7a8e424928e356d0b",
        openai_api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
        temperature=0.2,
        timeout=600,
        streaming=False,
        extra_body={"enable_thinking": False}
    )

    wenshu_tool = WenShuTools()


    # 组装 Deep Agent
    agent = create_deep_agent(
        model=llm,
        system_prompt=system_prompt,
        skills=[skills_dir],
        memory=["./AGENTS.md"],
        tools=wenshu_tool.get_tools(),
        backend=FilesystemBackend(root_dir=str(current_root), virtual_mode=True),
        checkpointer=checkpointer,  # Required!
    )

    return agent


content = "统计公司处分，违规对象分别为单位和员工，各有多少违规数量？"
content = "四维度九类型（或问题整改维度、整改措施类型）分别是指什么？"
# content = "统计系统风险探针总数有多少个？已上线多少个?本单位最近一个月触发次数最多的探针规则是？"
def main():
    agent = create_sql_deep_agent()

    # for step in agent.stream(
    #     {"messages": [{"role": "user", "content": content}]},
    #     config={"configurable": {"thread_id": "12345"},
    #             "callbacks": [tracer]}
    # ):
        # # 监控：是否加载成功
        # if 'SkillsMiddleware.before_agent' in step:
        #     count = len(step['SkillsMiddleware.before_agent'].get('skills_metadata', []))
        #     print(f"📊 状态: 已加载 {count} 个技能")
        #
        # # 监控：正在做什么
        # if 'model' in step:
        #     msg = step['model']['messages'][0]
        #     if msg.tool_calls:
        #         # 只打印动作名称，不打印那一长串内容
        #         print(f"🤔 动作: 正在调用 [{msg.tool_calls[0]['name']}]...")
        #
        # # 结果：最终回答
        # if 'agent' in step:
        #     print(f"\n🎯 结果:\n{step['agent']['messages'][-1].content}")
    for step in agent.stream(
            {"messages": [{"role": "user", "content": content}]},
            config={"configurable": {"thread_id": "12345"},
                    "callbacks": [tracer]},
            stream_mode="values"
    ):
        step["messages"][-1].pretty_print()



if __name__ == "__main__":
    main()