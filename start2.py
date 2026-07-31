import asyncio
import json
import httpx
from wecom_aibot_sdk import WeComAIBot

# ================= 配置区域 =================
# 1. 企微智能机器人凭证 (长连接模式)
BOT_ID = "你的_Bot_ID"
BOT_SECRET = "你的_Bot_Secret"

# 2. 内网 Dify Workflow 配置
DIFY_BASE_URL = "http://你的内网IP/v1"  # 例如 http://192.168.1.100/v1
DIFY_API_KEY = "app-你的Dify密钥"
DIFY_INPUT_VARIABLE = "query"  # 你的 Dify Workflow "开始"节点里的输入变量名，通常是 query 或 text

# ============================================

# 初始化 httpx 异步客户端 (用于调用内网 Dify)
http_client = httpx.AsyncClient(timeout=60.0)

async def call_dify_workflow(user_query: str, user_id: str) -> str:
    """
    调用内网 Dify Workflow 并获取结果
    """
    url = f"{DIFY_BASE_URL}/workflows/run"
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": {
            DIFY_INPUT_VARIABLE: user_query  # 将用户输入传给 Dify 的变量
        },
        "response_mode": "blocking",  # 阻塞模式，等待完整结果返回
        "user": user_id
    }

    try:
        print(f"[*] 正在调用 Dify，用户: {user_id}, 问题: {user_query}")
        response = await http_client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        # Dify Workflow 的输出在 data['data']['outputs'] 中
        # 假设你的 Workflow 最终输出节点有一个叫 'text' 或 'result' 的变量
        outputs = data.get("data", {}).get("outputs", {})
        
        # 尝试获取常见的输出变量名，或者直接返回整个 outputs 的 JSON 字符串
        ai_answer = outputs.get("text") or outputs.get("result") or json.dumps(outputs, ensure_ascii=False)
        return str(ai_answer)
        
    except Exception as e:
        print(f"[!] 调用 Dify 失败: {e}")
        return "抱歉，AI 大脑正在开小差，请稍后再试。"

# ================= 企微机器人事件处理 =================

bot = WeComAIBot(BOT_ID, BOT_SECRET)

@bot.on_text_message
async def handle_text_message(event):
    """
    处理用户发送的文本消息
    """
    # 获取消息内容、发送者 ID 和用于回复的 msgid
    content = event.content
    user_id = event.from_user
    msgid = event.msgid
    
    print(f"[收到消息] 用户 {user_id}: {content}")

    # 1. 调用 Dify Workflow (异步执行，不阻塞 WebSocket 接收)
    ai_answer = await call_dify_workflow(content, user_id)
    
    print(f"[AI 回复] {ai_answer}")

    # 2. 将结果回复给企微用户
    # 使用 SDK 提供的回复方法，传入 msgid 确保回复到正确的会话
    await bot.reply_text(msgid, ai_answer)

# ================= 启动服务 =================

async def main():
    print("🚀 企微 Dify 转发服务启动中...")
    print("💡 提示：请确保你的本地电脑能访问内网 Dify 服务器")
    
    # 启动 WebSocket 长连接 (SDK 会自动处理心跳和断线重连)
    await bot.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n服务已停止")