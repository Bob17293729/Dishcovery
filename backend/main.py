from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
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


class DishInfo(BaseModel):
    name: str
    translation: Optional[str] = None
    description: Optional[str] = None


class TranslateRequest(BaseModel):
    dishes: List[dict]  # 包含 name 和 menu_description 的字典列表


class GenerateImageRequest(BaseModel):
    dish_name: str
    translation: Optional[str] = None
    menu_description: Optional[str] = None


class GetDishDetailRequest(BaseModel):
    dish_name: str
    translation: Optional[str] = None
    menu_description: Optional[str] = None
    translation_description: Optional[str] = None


@app.get("/")
async def root():
    return {"message": "Dishcovery API is running"}


@app.post("/api/analyze-menu")
async def analyze_menu(file: UploadFile = File(...)):
    """
    分析菜单图片，提取菜品名称和描述
    """
    try:
        print(f"📥 收到图片上传请求: {file.filename}, 类型: {file.content_type}")
        
        # 读取文件内容
        print("📖 开始读取文件内容...")
        contents = await file.read()
        print(f"✅ 文件读取完成，大小: {len(contents)} bytes")
        
        # 验证文件大小（限制为10MB）
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="图片文件过大，请上传小于10MB的图片")
        
        # 调用OpenAI服务识别菜品
        print("🤖 开始调用OpenAI API识别菜品...")
        dishes = await openai_service.analyze_menu_image(contents)
        print(f"✅ 识别完成，找到 {len(dishes)} 个菜品")
        
        return {"dishes": dishes}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = str(e)
        print(f"❌ 分析菜单错误: {error_detail}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"分析菜单失败: {error_detail}")


@app.post("/api/translate")
async def translate(request: TranslateRequest):
    """
    只翻译菜品名称，不生成描述
    """
    try:
        dishes = await openai_service.translate_only(request.dishes)
        return {"dishes": dishes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"翻译失败: {str(e)}")


@app.post("/api/get-dish-detail")
async def get_dish_detail(request: GetDishDetailRequest):
    """
    获取单个菜品的描述和图片
    """
    try:
        # 生成描述
        description = await openai_service.get_dish_description(
            request.dish_name,
            request.translation,
            request.menu_description,
            request.translation_description
        )
        
        # 生成图片
        image_url = await openai_service.generate_dish_image(
            request.dish_name,
            request.translation,
            request.menu_description
        )
        
        return {
            "description": description,
            "image_url": image_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取菜品详情失败: {str(e)}")


@app.post("/api/generate-image")
async def generate_image(request: GenerateImageRequest):
    """
    为选中的菜品生成AI图片
    """
    try:
        image_url = await openai_service.generate_dish_image(
            request.dish_name, 
            request.translation,
            request.menu_description
        )
        return {"image_url": image_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图片生成失败: {str(e)}")

