"""
Agent 核心框架（LangChain 版本）
使用 LangChain + Qwen (DashScope) 实现 function calling
支持多轮对话、工具调用、会话管理、agentic loop
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import os

from langchain_openai import ChatOpenAI
from langchain_core.messages import (
    HumanMessage, AIMessage, ToolMessage, SystemMessage, BaseMessage
)
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from service.agent_tools import get_default_tools  # 引入修改后的工具模块
from dotenv import load_dotenv  # 新增：加载 .env 文件
load_dotenv()  # 加载项目根目录的 .env 文件

class ConversationHistory:
    """会话历史管理（LangChain messages 格式）"""

    def __init__(self, system_prompt: str = "", max_turns: int = 30):
        self.system_prompt = system_prompt
        self.max_turns = max_turns
        # 存储 LangChain BaseMessage 列表
        self.messages: List[BaseMessage] = []

    def add_user(self, content: str):
        """添加用户消息"""
        self.messages.append(HumanMessage(content=content, id=f"user_{datetime.now().isoformat()}"))
        self._trim()

    def add_assistant(self, content: str, tool_calls: Optional[List[Dict]] = None):
        """添加助手消息（支持 tool_calls 元数据）"""
        extra = {"tool_calls": tool_calls} if tool_calls else {}
        self.messages.append(AIMessage(content=content, id=f"assistant_{datetime.now().isoformat()}", **extra))
        self._trim()

    def add_tool_result(self, tool_call_id: str, content: str):
        """添加工具执行结果"""
        self.messages.append(ToolMessage(content=content, tool_call_id=tool_call_id))
        self._trim()

    def _trim(self):
        """保留最近 max_turns 轮对话（user+assistant 各算1轮）"""
        # 过滤出非 system 消息进行计数
        non_system = [m for m in self.messages if not isinstance(m, SystemMessage)]
        if len(non_system) > self.max_turns * 2:
            # 保留最后 max_turns*2 条非 system 消息 + 所有 system 消息
            system_msgs = [m for m in self.messages if isinstance(m, SystemMessage)]
            self.messages = system_msgs + non_system[-(self.max_turns * 2):]

    def get(self) -> List[BaseMessage]:
        """获取完整消息列表（含 system prompt）"""
        if self.system_prompt:
            has_system = any(isinstance(m, SystemMessage) for m in self.messages)
            if not has_system:
                return [SystemMessage(content=self.system_prompt)] + self.messages
        return self.messages

    def clear(self):
        self.messages.clear()

    def to_dict(self) -> List[Dict]:
        """导出为字典格式（便于调试/日志）"""
        return [self._message_to_dict(m) for m in self.messages]

    @staticmethod
    def _message_to_dict(msg: BaseMessage) -> Dict:
        """BaseMessage → dict 转换"""
        base = {"role": msg.type, "content": msg.content}
        if isinstance(msg, AIMessage) and msg.tool_calls:
            base["tool_calls"] = msg.tool_calls
        elif isinstance(msg, ToolMessage):
            base["tool_call_id"] = msg.tool_call_id
        return base


class Agent:
    """
    Agent 核心类（LangChain 实现，使用 Qwen 模型）

    特性：
    - 使用 ChatOpenAI + bind_tools 实现原生 function calling
    - 手动实现 agentic loop，支持连续工具调用
    - 工具注册表 + 会话历史隔离，便于测试和扩展
    """

    def __init__(
            self,
            db,
            system_prompt: Optional[str] = None,
            model: str = "qwen3.5-plus",
            temperature: float = 0.1,
            max_tokens: int = 2048
    ):
        self.db = db
        self.model_name = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # 初始化 LangChain Chat Model
        self.chat_model = ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key=os.getenv("DASHSCOPE_API_KEY"),  # 从.env读取
        )

        # 工具注册表：name → Tool 对象
        self._tools: Dict[str, tool] = {}

        # 会话管理
        self.system_prompt = system_prompt or self._default_system_prompt()
        self.conversation = ConversationHistory(system_prompt=self.system_prompt)

        # 绑定工具 schema 到 model（懒加载）
        self._bound_model = None

    def _default_system_prompt(self) -> str:
        return """你是一个专业的实验室面试助手 Agent。

你的能力：
1. **姓名匹配**：用户可以说"分析张三的表现"，你需要先通过 lookup_interviewees_by_name 工具模糊查找到对应的面试者 ID，再调用分析工具。
2. **批处理**：用户可以说"统计所有面试者"或"分析张三和李四"，你需要对多个面试者批量调用工具并汇总结果。
3. **发送邮件**：分析完成后，可以将报告通过邮件发送给对应面试者。
4. **综合分析**：你可以连续调用多个工具完成复杂任务。

工作原则：
- 当用户提到人名时，始终先查找确认 ID，再进行操作
- 批量操作时，为每个人单独调用工具并整合结果
- 发邮件前，确认已获取到报告内容和正确邮箱
- 用中文回复，语言简洁专业"""

    def register_tool(self, tool_obj: tool):
        """注册单个 LangChain Tool（用 @tool 装饰器创建的对象）"""
        self._tools[tool_obj.name] = tool_obj
        self._bound_model = None  # 重置绑定，使新工具生效
        print(f"[ToolRegistry] 注册工具: {tool_obj.name}")

    def register_tools(self, tools: List[tool]):
        """批量注册工具"""
        for t in tools:
            self.register_tool(t)

    def _get_bound_model(self):
        """获取已绑定工具 schema 的 model（懒加载）"""
        if self._bound_model is None:
            tool_list = list(self._tools.values())
            self._bound_model = self.chat_model.bind_tools(tool_list)
        return self._bound_model

    def chat(self, user_input: str, config: Optional[RunnableConfig] = None) -> str:
        """
        主对话接口（LangChain + agentic loop）

        流程：
        1. 用户输入 → 加入历史
        2. 调用 bind_tools 的 model，可能返回 tool_calls
        3. 执行工具 → 结果作为 ToolMessage 返回给 model
        4. 循环直到 model 输出纯文本回复
        """
        # 1. 添加用户消息
        self.conversation.add_user(user_input)

        # 2. Agentic loop
        max_tool_iterations = 10  # 防止无限循环
        iteration = 0

        while iteration < max_tool_iterations:
            iteration += 1

            # 调用模型（已绑定 tools）
            model = self._get_bound_model()
            response = model.invoke(self.conversation.get(), config=config)

            # 3. 检查是否有工具调用
            if hasattr(response, "tool_calls") and response.tool_calls:
                # 记录 assistant 消息（含 tool_calls 元数据）
                self.conversation.add_assistant(
                    content=response.content,
                    tool_calls=response.tool_calls
                )

                # 4. 执行所有工具调用
                for tool_call in response.tool_calls:
                    result = self._execute_tool_call(tool_call)
                    self.conversation.add_tool_result(
                        tool_call_id=tool_call["id"],
                        content=result
                    )
                    print(f"[Agent] 工具调用: {tool_call['name']} → {result[:100]}...")

                # 继续循环，将工具结果反馈给 model
                continue
            else:
                # 5. 纯文本回复，结束循环
                self.conversation.add_assistant(content=response.content)
                return response.content

        # 达到最大迭代次数，返回中断信息
        return "[Agent] 达到最大工具调用次数，任务未完成"

    def _execute_tool_call(self, tool_call: Dict[str, Any]) -> str:
        """执行单个工具调用（LangChain Tool 标准接口）"""
        tool_name = tool_call["name"]
        tool_args = tool_call.get("args", {})

        tool_obj = self._tools.get(tool_name)
        if not tool_obj:
            return f"❌ 错误：未找到工具 [{tool_name}]"

        try:
            # LangChain Tool 支持 .invoke(args) 或直接调用
            result = tool_obj.invoke(tool_args)
            return str(result) if not isinstance(result, str) else result
        except Exception as e:
            return f"❌ 工具执行失败 [{tool_name}]: {str(e)}"

    def stream_chat(self, user_input: str, config: Optional[RunnableConfig] = None):
        """
        流式对话接口（生成式回复流）
        注意：工具调用阶段仍为同步执行，仅最终文本回复支持流式
        """
        self.conversation.add_user(user_input)

        max_tool_iterations = 10
        iteration = 0

        while iteration < max_tool_iterations:
            iteration += 1
            model = self._get_bound_model()

            # 先收集完整 response 以判断是否有 tool_calls
            chunks = []
            full_content = ""
            has_tool_calls = False

            for chunk in model.stream(self.conversation.get(), config=config):
                chunks.append(chunk)
                if hasattr(chunk, "content") and chunk.content:
                    full_content += chunk.content
                    yield chunk.content  # 流式输出文本
                if hasattr(chunk, "tool_calls") and chunk.tool_calls:
                    has_tool_calls = True

            # 合并 chunk 为完整 message
            response = chunks[0].concat(chunks[1:]) if len(chunks) > 1 else chunks[0]

            if has_tool_calls and response.tool_calls:
                self.conversation.add_assistant(content=full_content, tool_calls=response.tool_calls)

                for tool_call in response.tool_calls:
                    result = self._execute_tool_call(tool_call)
                    self.conversation.add_tool_result(tool_call["id"], result)
                    print(f"[Agent] 工具调用: {tool_call['name']} → {result[:100]}...")
                continue
            else:
                self.conversation.add_assistant(content=full_content)
                return

        yield "[Agent] 达到最大工具调用次数"

    # ───────── 管理接口 ─────────

    def get_conversation_history(self) -> List[Dict]:
        return self.conversation.to_dict()

    def clear_conversation(self):
        self.conversation.clear()

    def get_registered_tools(self) -> List[str]:
        return list(self._tools.keys())
    def get_tools(self):
        """返回所有注册的工具对象列表"""
        return list(self._tools.values())


# ───────── 快捷工厂函数 ─────────

def create_agent(db, **kwargs) -> Agent:
    """
    快速创建 Agent 实例并注册默认工具

    用法：
        agent = create_agent(db, model="qwen-plus")
        response = agent.chat("分析张三的面试表现")
    """
    agent = Agent(db=db, **kwargs)
    tools = get_default_tools(db)
    agent.register_tools(tools)
    return agent