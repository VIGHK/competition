import asyncio
import sys
from typing import Optional
from contextlib import AsyncExitStack #异步上下文管理器，用于管理多个异步资源

from mcp import ClientSession, StdioServerParameters #ClientSession为MCP框架的客户端会话类，stdio_client为通过标准输入输出与服务器通信
from mcp.client.stdio import stdio_client

from anthropic import Anthropic #Anthropic为Claude模型的官方SDK
from dotenv import load_dotenv
from openai import OpenAI
import json


#load_dotenv()  # 从 .env 加载环境变量

class MCPClient:
    def __init__(self):
        # 初始化会话和客户端对象
        self.session: Optional[ClientSession] = None #MCP服务器连接会话
        self.exit_stack = AsyncExitStack() #异步资源清理栈
        self.client = OpenAI(api_key="sk-4d765424d2a44527a9d7f6193623343a", base_url="https://api.deepseek.com/v1") #

    async def connect_to_server(self, server_script_path: str):
        """连接到 MCP 服务器

        参数：
            server_script_path: 服务器脚本路径 (.py 或 .js)
        """
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("服务器脚本必须是 .py 或 .js 文件")

        command = "python" if is_python else "node"
        #配置StdioServerParameters（启动命令/参数）
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )

        #通过stdio_client建立连接
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        #初始化会话并列出可用工具
        await self.session.initialize()

        #列出可用工具
        response = await self.session.list_tools()
        tools = response.tools
        print("\n已连接到服务器，可用工具:", [tool.name for tool in tools])

    async def process_query(self, query: str) -> str:
        """使用DeepSeek 和可用工具处理查询"""
        messages = [{"role": "user", "content": query}]

        # 获取可用工具列表
        response = await self.session.list_tools()
        available_tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            } for tool in response.tools
        ]

        # 初始API调用
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            tools=available_tools
        )
        print(f"大模型第一次回应：{response.choices[0].message}")  # 打印完整消息对象

        assistant_message = response.choices[0].message
        # 保留完整的assistant消息对象
        messages.append(dict(assistant_message))  # 转换为字典确保可序列化

        # 检查是否需要调用工具
        if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                try:
                    tool_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    tool_args = {}

                # 执行工具调用
                result = await self.session.call_tool(tool_name, tool_args)

                # 准备工具响应
                tool_response = {
                    "role": "tool",
                    "content": str(result.content) if result.content else "",
                    "tool_call_id": tool_call.id,
                    "name": tool_name
                }
                print("准备添加工具响应:", tool_response)
                messages.append(tool_response)

                # 获取包含工具结果的响应
                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=messages,
                    tools=available_tools
                )
                print(f"大模型第二次回应：{response.choices[0].message}")

        return str(response.choices[0].message.content)

    async def chat_loop(self):
        """运行交互式聊天循环"""
        print("\nMCP 客户端已启动！")
        print("输入你的查询或 'quit' 退出。")

        while True:
            try:
                query = input("\n查询: ").strip()

                if query.lower() == 'quit':
                    break

                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                print(f"\n错误: {str(e)}")

    async def cleanup(self):
        """清理资源"""
        await self.exit_stack.aclose()

async def main():
    if len(sys.argv) < 2:
        print("用法: python client.py <服务器脚本路径>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())