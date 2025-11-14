"""
OpenAI 服务模块
提供图片压缩、Markdown提取、NDJSON解析等核心功能
支持两阶段流式处理：图片→Markdown→NDJSON
"""
import openai
import os
import base64
import time
import io
import json
import asyncio
from typing import AsyncGenerator, Dict, Any, Tuple
from queue import Queue, Empty
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

# ============================================================================
# 常量定义
# ============================================================================

# 第一阶段：图片 → Markdown 的 System Prompt
MARKDOWN_EXTRACTION_SYSTEM_PROMPT = """你是一名专业的菜单文本提取专家。

你的任务是将菜单图片中的所有文本内容完整、准确地提取为 Markdown 格式。

【核心要求】
1. 完整提取所有文本，包括：
   - 菜品名称（英文）
   - 菜品描述（英文）
   - 分类标题（如 Salads, Pizzas, Desserts 等）
   - 价格信息
   - 小字说明、备注等

2. 保持原始排版结构：
   - 使用 Markdown 标题（# ## ###）表示分类
   - 使用列表或段落表示菜品
   - 保留缩进和两列排版信息
   - 使用适当的 Markdown 格式（**粗体**、*斜体*等）

3. 输出要求：
   - 直接输出 Markdown，不要添加解释文字
   - 不要使用代码块包裹
   - 确保所有文本都被提取，不要遗漏任何内容

4. 格式示例：
   # Menu
   
   ## Salads
   - **Caesar Salad** - Fresh romaine lettuce with Caesar dressing
   - **Chop Salad** - Mixed greens with vegetables
   
   ## Pizzas
   - **Margherita Pizza** - Classic tomato, mozzarella, and basil
   - **Pepperoni Pizza** - Spicy pepperoni with mozzarella
"""

# 第二阶段：Markdown → NDJSON 的 System Prompt
NDJSON_GENERATION_SYSTEM_PROMPT = """你是一名菜单结构化解析专家。

你必须严格按"NDJSON（一行一个 JSON）"格式输出菜品信息。

【核心要求】
每识别到一道菜，就立即输出一行 JSON，格式如下：
{"section": "...", "name_en": "...", "name_zh": "...", "ingredients_en": "...", "ingredients_zh": "...", "description_zh": "...", "image_prompt": "..."}

不等待全部菜识别完成。

【字段说明】
- section: 菜品所属分类（如 "Salads", "Pizzas", "Desserts"）
- name_en: 完整的英文菜名（必须补全）
- name_zh: 自然的中文翻译
- ingredients_en: 主要食材列表（英文，用逗号分隔，如 "tomato, mozzarella, basil"）
- ingredients_zh: 主要食材列表（中文，用逗号分隔，如 "番茄, 马苏里拉奶酪, 罗勒"）
- description_zh: 菜品的中文详细描述（80-120字，包含口感、特色、制作方式等）
- image_prompt: 用于生成菜品图片的英文提示词（简洁描述菜品外观，如 "A beautiful Margherita pizza with fresh mozzarella, tomato sauce, and basil leaves on a wooden board"）

【结构补全规则】
- 如果菜名不完整，根据 section 自动补全：
  - "Salads" 区域中的 "Chop" → "Chop Salad"
  - "Pizzas" 区域中的 "Margherita" → "Margherita Pizza"
  - "Desserts" 区域中的 "Cheesecake" → "Cheesecake"
- 如果菜名已包含类别词（如 "Caesar Salad"），不要重复补全
- 确保 name_en 是完整、规范的菜名

【字段生成要求】
- ingredients_en 和 ingredients_zh：从菜单中提取主要食材，如果没有明确列出，根据菜名推断
- description_zh：基于菜单中的描述信息，生成专业、自然的中文菜品介绍，包含口感、特色、制作方式等
- image_prompt：生成简洁的英文提示词，描述菜品的外观特征，用于 AI 图片生成

【输出规则】
- 绝对禁止输出数组、包裹的大 JSON
- 绝对禁止输出 markdown 格式、注释、解释文字
- 绝对禁止使用 ```json 代码块
- 每一行必须是合法的 JSON 对象
- 一行 = 一道菜
- 立即输出，不要等待
- 所有字段都必须有值（即使是空字符串）
"""

# ============================================================================
# 工具函数
# ============================================================================

def compress_image(image_bytes: bytes) -> Tuple[bytes, str]:
    """
    压缩图片为 JPEG 格式
    
    Args:
        image_bytes: 原始图片字节
        
    Returns:
        (压缩后的字节, 图片格式)
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        original_size = img.size
        
        # 如果最长边超过 2000px，进行缩放
        if max(img.size) > 2000:
            scale = 2000 / max(img.size)
            new_size = (int(img.size[0] * scale), int(img.size[1] * scale))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            print(f"📐 图片缩放: {original_size} → {new_size}")
        
        # 转换为 RGB 模式（JPEG 不支持透明通道）
        if img.mode != "RGB":
            img = img.convert("RGB")
        
        # 保存为 JPEG，质量 85
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85, optimize=True)
        compressed_bytes = buf.getvalue()
        
        print(f"📐 图片压缩: {len(image_bytes)} bytes → {len(compressed_bytes)} bytes")
        return compressed_bytes, "jpeg"
    except Exception as e:
        print(f"⚠️ 图片压缩失败，使用原图: {e}")
        return image_bytes, "jpeg"


def extract_text_from_delta(delta) -> str:
    """
    从 OpenAI delta 对象中提取文本内容
    兼容多种 delta.content 类型：str、list、dict
    
    Args:
        delta: OpenAI 响应中的 delta 对象
        
    Returns:
        提取的文本字符串
    """
    if not hasattr(delta, "content"):
        return ""
    
    data = delta.content
    if isinstance(data, str):
        return data
    elif isinstance(data, list):
        texts = []
        for item in data:
            if isinstance(item, str):
                texts.append(item)
            elif isinstance(item, dict) and "text" in item:
                texts.append(item["text"])
        return "".join(texts)
    return ""


# ============================================================================
# OpenAI 服务类
# ============================================================================

class OpenAIService:
    """OpenAI API 服务封装类"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.client = openai.OpenAI(api_key=api_key)

    async def analyze_menu_image_stream(
        self, 
        image_bytes: bytes
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        两阶段流式处理：图片 → Markdown → NDJSON
        
        第一阶段：流式输出 Markdown（yield {"type": "markdown", "content": "..."}）
        第二阶段：流式输出 NDJSON 菜品（yield {"type": "dish", "dish": {...}}）
        
        Args:
            image_bytes: 菜单图片的字节数据
            
        Yields:
            - {"type": "markdown", "content": "..."} - Markdown 文本片段
            - {"type": "markdown_done"} - Markdown 阶段完成
            - {"type": "dish", "dish": {...}} - 菜品 JSON 对象
            - {"type": "done"} - 全部完成
        """
        start_time = time.time()
        print(f"🖼 开始处理图片: {len(image_bytes)} bytes")
        
        # 1. 压缩图片
        compressed_bytes, image_format = compress_image(image_bytes)
        base64_image = base64.b64encode(compressed_bytes).decode("utf-8")
        
        # 2. 第一阶段：图片 → Markdown（流式）
        print("📝 阶段1: 开始提取 Markdown...")
        markdown_content = ""
        
        async for chunk in self._stream_markdown_extraction(base64_image, image_format):
            if chunk["type"] == "markdown":
                markdown_content += chunk["content"]
                yield chunk  # 实时输出 Markdown 片段
            elif chunk["type"] == "error":
                yield chunk
                return
        
        yield {"type": "markdown_done"}
        print(f"✅ Markdown 提取完成，长度: {len(markdown_content)} 字符")
        
        # 3. 第二阶段：Markdown → NDJSON（流式）
        if not markdown_content.strip():
            yield {"type": "error", "error": "未能提取到 Markdown 内容"}
            return
        
        print("🍽 阶段2: 开始解析 NDJSON...")
        dish_count = 0
        
        async for chunk in self._stream_ndjson_generation(markdown_content):
            if chunk["type"] == "dish":
                dish_count += 1
                print(f"   → 收到菜品 {dish_count}: {chunk['dish']['name_en']}")
                yield chunk
            elif chunk["type"] == "error":
                yield chunk
                return
        
        yield {"type": "done"}
        elapsed = time.time() - start_time
        print(f"🎉 处理完成：{dish_count} 道菜，总耗时 {elapsed:.2f}s")

    async def _stream_markdown_extraction(
        self, 
        base64_image: str, 
        image_format: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        第一阶段：流式提取 Markdown
        
        Args:
            base64_image: Base64 编码的图片
            image_format: 图片格式
            
        Yields:
            {"type": "markdown", "content": "..."} 或 {"type": "error", "error": "..."}
        """
        loop = asyncio.get_event_loop()
        chunk_queue = Queue()
        
        def create_stream(queue):
            """在后台线程中创建流"""
            try:
                stream = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": MARKDOWN_EXTRACTION_SYSTEM_PROMPT},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "请完整提取这张菜单图片中的所有文本内容，输出为 Markdown 格式。"},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/{image_format};base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    stream=True,
                    max_tokens=4096
                )
                
                for chunk in stream:
                    queue.put(chunk)
                queue.put(None)  # 结束标记
            except Exception as e:
                queue.put(e)  # 错误标记
        
        executor = loop.run_in_executor(None, create_stream, chunk_queue)
        
        try:
            while True:
                def get_chunk():
                    try:
                        return chunk_queue.get(timeout=0.1)
                    except Empty:
                        return None
                
                chunk = await loop.run_in_executor(None, get_chunk)
                
                if chunk is None:
                    if executor.done():
                        try:
                            executor.result()
                        except Exception as e:
                            yield {"type": "error", "error": str(e)}
                            return
                        if chunk_queue.empty():
                            break
                    await asyncio.sleep(0.01)
                    continue
                
                if isinstance(chunk, Exception):
                    yield {"type": "error", "error": str(chunk)}
                    return
                
                if not chunk.choices:
                    continue
                
                delta = chunk.choices[0].delta
                if not delta:
                    continue
                
                text = extract_text_from_delta(delta)
                if text:
                    yield {"type": "markdown", "content": text}
                
                await asyncio.sleep(0)
        except Exception as e:
            yield {"type": "error", "error": f"Markdown 提取失败: {str(e)}"}

    async def _stream_ndjson_generation(
        self, 
        markdown_content: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        第二阶段：流式生成 NDJSON
        
        Args:
            markdown_content: 完整的 Markdown 内容
            
        Yields:
            {"type": "dish", "dish": {...}} 或 {"type": "error", "error": "..."}
        """
        loop = asyncio.get_event_loop()
        chunk_queue = Queue()
        
        def create_stream(queue):
            """在后台线程中创建流"""
            try:
                stream = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": NDJSON_GENERATION_SYSTEM_PROMPT},
                        {
                            "role": "user",
                            "content": f"请分析以下菜单 Markdown，按 NDJSON 格式逐条输出菜品信息：\n\n{markdown_content}"
                        }
                    ],
                    stream=True,
                    max_tokens=4096
                )
                
                for chunk in stream:
                    queue.put(chunk)
                queue.put(None)  # 结束标记
            except Exception as e:
                queue.put(e)  # 错误标记
        
        executor = loop.run_in_executor(None, create_stream, chunk_queue)
        
        buffer = ""
        
        try:
            while True:
                def get_chunk():
                    try:
                        return chunk_queue.get(timeout=0.1)
                    except Empty:
                        return None
                
                chunk = await loop.run_in_executor(None, get_chunk)
                
                if chunk is None:
                    if executor.done():
                        try:
                            executor.result()
                        except Exception as e:
                            yield {"type": "error", "error": str(e)}
                            return
                        if chunk_queue.empty():
                            break
                    await asyncio.sleep(0.01)
                    continue
                
                if isinstance(chunk, Exception):
                    yield {"type": "error", "error": str(chunk)}
                    return
                
                if not chunk.choices:
                    continue
                
                delta = chunk.choices[0].delta
                if not delta:
                    continue
                
                text = extract_text_from_delta(delta)
                if not text:
                    continue
                
                buffer += text
                
                # 按行拆分并解析 JSON
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    
                    # 跳过空行和非 JSON 行
                    if not line or not line.startswith("{") or not line.endswith("}"):
                        continue
                    
                    try:
                        data = json.loads(line)
                        
                        # 格式化菜品结构（新字段结构）
                        dish = {
                            "section": data.get("section", ""),
                            "name_en": data.get("name_en", ""),
                            "name_zh": data.get("name_zh", ""),
                            "ingredients_en": data.get("ingredients_en", ""),
                            "ingredients_zh": data.get("ingredients_zh", ""),
                            "description_zh": data.get("description_zh", ""),
                            "image_prompt": data.get("image_prompt", ""),
                        }
                        
                        yield {"type": "dish", "dish": dish}
                    except json.JSONDecodeError:
                        # 忽略解析失败的 JSON
                        continue
                
                await asyncio.sleep(0)
            
            # 处理 buffer 中最后可能残留的一行
            if buffer.strip().startswith("{") and buffer.strip().endswith("}"):
                try:
                    data = json.loads(buffer.strip())
                    dish = {
                        "section": data.get("section", ""),
                        "name_en": data.get("name_en", ""),
                        "name_zh": data.get("name_zh", ""),
                        "ingredients_en": data.get("ingredients_en", ""),
                        "ingredients_zh": data.get("ingredients_zh", ""),
                        "description_zh": data.get("description_zh", ""),
                        "image_prompt": data.get("image_prompt", ""),
                    }
                    yield {"type": "dish", "dish": dish}
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            yield {"type": "error", "error": f"NDJSON 生成失败: {str(e)}"}

    async def get_dish_description_stream(
        self, 
        dish_name: str, 
        translation: str = None, 
        menu_description: str = None, 
        translation_description: str = None
    ) -> AsyncGenerator[str, None]:
        """
        流式获取单个菜品的详细描述
        
        Args:
            dish_name: 英文菜名
            translation: 中文翻译
            menu_description: 菜单中的英文描述
            translation_description: 菜单中的中文描述
            
        Yields:
            描述文本片段（逐个 token）
        """
        start_time = time.time()
        prompt = f"""请为以下菜品提供详细描述（80-120字）：
菜品名称：{dish_name}"""
        
        if translation:
            prompt += f"\n中文名称：{translation}"
        
        if translation_description:
            prompt += f"\n菜单描述（中文）：{translation_description}"
        elif menu_description:
            prompt += f"\n菜单描述（英文）：{menu_description}"
        
        prompt += "\n\n要求："
        prompt += "\n1. 基于菜单中的描述信息，生成专业、自然的中文菜品介绍"
        prompt += "\n2. 不要逐字翻译，要理解菜品特点后重新组织语言"
        prompt += "\n3. 可以适当补充菜品的特色、口感、制作方式等信息"
        prompt += "\n4. 语言要流畅，让中文读者能够理解并产生食欲"
        prompt += "\n5. 描述长度在80-120字之间"

        try:
            print(f"📝 开始流式生成菜品描述: {dish_name}")
            loop = asyncio.get_event_loop()
            chunk_queue = Queue()
            
            def create_stream(queue):
                """在后台线程中创建流"""
                try:
                    stream = self.client.chat.completions.create(
                model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}],
                        stream=True,
                max_tokens=300
            )
            
                    for chunk in stream:
                        queue.put(chunk)
                    queue.put(None)  # 结束标记
                except Exception as e:
                    queue.put(e)  # 错误标记
            
            executor = loop.run_in_executor(None, create_stream, chunk_queue)
            
            try:
                while True:
                    def get_chunk():
                        try:
                            return chunk_queue.get(timeout=0.1)
                        except Empty:
                            return None
                    
                    chunk = await loop.run_in_executor(None, get_chunk)
                    
                    if chunk is None:
                        if executor.done():
                            try:
                                executor.result()
                            except Exception as e:
                                print(f"❌ 描述生成失败: {e}")
                                yield f"描述生成失败: {str(e)}"
                                return
                            if chunk_queue.empty():
                                break
                        await asyncio.sleep(0.01)
                        continue
                    
                    if isinstance(chunk, Exception):
                        print(f"❌ 描述生成失败: {chunk}")
                        yield f"描述生成失败: {str(chunk)}"
                        return
                    
                    if not chunk.choices:
                        continue
                    
                    delta = chunk.choices[0].delta
                    if not delta:
                        continue
                    
                    text = extract_text_from_delta(delta)
                    if text:
                        yield text
                    
                    await asyncio.sleep(0)
                
                elapsed = time.time() - start_time
                print(f"✅ 描述生成完成，耗时 {elapsed:.2f}s")
            except Exception as e:
                print(f"❌ 描述生成失败: {e}")
                yield f"描述生成失败: {str(e)}"
        except Exception as e:
            print(f"❌ 描述生成失败: {e}")
            yield f"描述生成失败: {str(e)}"

    async def generate_dish_image(self, image_prompt: str) -> str:
        """
        使用 DALL-E 生成菜品图片
        
        Args:
            image_prompt: 图片生成提示词（英文）
            
        Returns:
            生成的图片 URL
        """
        start_time = time.time()
        
        # 使用传入的 image_prompt，并添加通用修饰词
        prompt = f"{image_prompt}, professional food photography, high quality, restaurant style"
        
        try:
            print(f"🎨 开始生成图片，提示词: {image_prompt[:50]}...")
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            
            if not response.data or len(response.data) == 0:
                raise Exception("图片生成失败：未返回图片URL")
            
            elapsed = time.time() - start_time
            print(f"✅ 图片生成完成，耗时 {elapsed:.2f}s")
            return response.data[0].url
        except Exception as e:
            raise Exception(f"DALL-E图片生成失败: {str(e)}")
