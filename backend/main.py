from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import os
import json
import asyncio
from dotenv import load_dotenv

from services.openai_service import OpenAIService

load_dotenv()

app = FastAPI(title="Dishcovery API")

# CORS配置 - 允许所有来源（开发环境）
# 生产环境建议限制为特定域名
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，方便移动端访问
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化OpenAI服务
openai_service = OpenAIService()


class GenerateImageRequest(BaseModel):
    image_prompt: str


@app.get("/")
async def root():
    return {"message": "Dishcovery API is running"}


@app.post("/api/analyze-menu")
async def analyze_menu(file: UploadFile = File(...)):
    """
    分析菜单图片，两阶段流式返回：
    1. 第一阶段：Markdown 流式输出
    2. 第二阶段：NDJSON 菜品流式输出
    使用 Server-Sent Events (SSE) 格式
    """
    async def generate():
        try:
            print(f"📥 收到图片上传请求: {file.filename}, 类型: {file.content_type}")
            
            # 读取文件内容
            print("📖 开始读取文件内容...")
            contents = await file.read()
            print(f"✅ 文件读取完成，大小: {len(contents)} bytes")
            
            # 验证文件大小（限制为10MB）
            if len(contents) > 10 * 1024 * 1024:
                yield f"data: {json.dumps({'type': 'error', 'error': '图片文件过大，请上传小于10MB的图片'})}\n\n"
                return
            
            # 调用OpenAI服务进行两阶段流式处理
            print("🤖 开始调用OpenAI API（两阶段流式）...")
            
            async for chunk in openai_service.analyze_menu_image_stream(contents):
                # 转发所有类型的消息
                yield f"data: {json.dumps(chunk)}\n\n"
            
            print("✅ 流式处理完成")
            
        except Exception as e:
            import traceback
            error_detail = str(e)
            print(f"❌ 分析菜单错误: {error_detail}")
            print(traceback.format_exc())
            yield f"data: {json.dumps({'type': 'error', 'error': f'分析菜单失败: {error_detail}'})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用 nginx 缓冲
        }
    )


@app.post("/api/generate-image")
async def generate_image(request: GenerateImageRequest):
    """
    根据 image_prompt 生成菜品参考图片
    """
    try:
        image_url = await openai_service.generate_dish_image(request.image_prompt)
        return {"image_url": image_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图片生成失败: {str(e)}")

