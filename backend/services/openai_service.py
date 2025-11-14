import openai
import os
import base64
import time
import io
from typing import List, Dict
from dotenv import load_dotenv
from PIL import Image

load_dotenv()


class OpenAIService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.client = openai.OpenAI(api_key=api_key)

    async def analyze_menu_image_stream(self, image_bytes: bytes):
        """
        流式版本：使用 GPT-4o-mini 从图片中直接逐条输出 NDJSON 的菜品信息。
        每识别到一条菜品 JSON，就 yield 一条。
        """
        import time
        import json
        import base64
        import io
        from PIL import Image
        
        start_time = time.time()
        print(f"🖼 原始图片: {len(image_bytes)} bytes")
        
        # ---------------------------------------------------------------------
        #  1) 图片压缩（安全、鲁棒、可处理任意图片格式）
        # ---------------------------------------------------------------------
        #
        try:
            img = Image.open(io.BytesIO(image_bytes))
            if max(img.size) > 2000:
                scale = 2000 / max(img.size)
                new_size = (int(img.size[0] * scale), int(img.size[1] * scale))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            if img.mode != "RGB":
                img = img.convert("RGB")
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=85, optimize=True)
            image_bytes = buf.getvalue()
            image_format = "jpeg"
            print(f"📐 压缩后: {len(image_bytes)} bytes")
        except Exception as e:
            print(f"⚠ 图片压缩失败：{e}")
            image_format = "jpeg"
        
        # ---------------------------------------------------------------------
        #  2) Base64 转换
        # ---------------------------------------------------------------------
        #
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        
        # ---------------------------------------------------------------------
        #  3) Streaming Prompt（绝对能触发 NDJSON per line）
        # ---------------------------------------------------------------------
        #
        system_prompt = """
你是一名菜单结构解析专家。

你必须严格按"NDJSON（一行一个 JSON）"格式输出。

切记：绝对不能输出数组、绝对不能输出包裹的大 JSON。

【核心要求】

每识别到一道菜，就立即输出一行 JSON，格式如下：

{"section": "...", "name_en": "...", "description_en": "...", "name_zh": "...", "description_zh": "..."}

不等待全部菜识别完成。

【结构补全】

- SALADS 区域中的 "Chop" → "Chop Salad"

- PIZZAS 区域中的 "Margherita" → "Margherita Pizza"

- 如果已包含类别词，例如 Caesar Salad，不要重复补全

【规则】

- 不输出 markdown/注释/解释

- 不输出 ```json

- 每一行必须是合法 JSON

- 一行 = 一道菜

"""
        
        user_prompt = "请分析这张菜单（图片已给出），并按 NDJSON 格式逐条输出菜品。"
        
        # ---------------------------------------------------------------------
        #  4) 启动 Streaming
        # ---------------------------------------------------------------------
        #
        print("🌐 开始 GPT-4o-mini 流式识别...")
        
        # 使用队列在后台线程中处理同步流，避免阻塞事件循环
        import asyncio
        from queue import Queue, Empty
        
        def create_and_iterate_stream(queue):
            """在后台线程中创建流并迭代chunks"""
            try:
                stream = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": user_prompt},
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
        
        # 创建队列和后台任务
        chunk_queue = Queue()
        loop = asyncio.get_event_loop()
        # 在后台线程中运行流式处理（不等待，立即返回）
        executor = loop.run_in_executor(None, create_and_iterate_stream, chunk_queue)
        # 不等待executor完成，让它后台运行
        
        # ---------------------------------------------------------------------
        #  5) Chunk 拼接处理（极强鲁棒性版本）
        # ---------------------------------------------------------------------
        #
        buffer = ""
        dish_count = 0
        
        def extract_text(delta):
            """
            兼容多种 delta.content 类型：str、list、dict。
            """
            out = []
            if hasattr(delta, "content"):
                data = delta.content
                if isinstance(data, str):
                    out.append(data)
                elif isinstance(data, list):
                    for x in data:
                        if isinstance(x, str):
                            out.append(x)
                        elif isinstance(x, dict):
                            # openai sometimes returns {"text": "..."}
                            if "text" in x:
                                out.append(x["text"])
            return "".join(out)
        
        # ---------------------------------------------------------------------
        #  6) 流式读取 + 行级 NDJSON 解析（异步版本）
        # ---------------------------------------------------------------------
        #
        try:
            while True:
                # 从队列中异步获取chunk（非阻塞）
                def get_chunk():
                    try:
                        return chunk_queue.get(timeout=0.1)  # 0.1秒超时
                    except Empty:
                        return None
                
                chunk = await loop.run_in_executor(None, get_chunk)
                if chunk is None:
                    # 检查executor是否还在运行
                    if executor.done():
                        # executor已完成，检查是否有错误
                        try:
                            executor.result()
                        except Exception as e:
                            raise e
                        # 如果队列为空且executor完成，退出循环
                        if chunk_queue.empty():
                            break
                    await asyncio.sleep(0.01)  # 短暂等待后重试
                    continue
                
                # 检查结束标记和错误
                if chunk is None:  # 结束标记（从队列中获取的None）
                    break
                if isinstance(chunk, Exception):  # 错误
                    raise chunk
                
                # 处理chunk
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if not delta:
                    continue
                text = extract_text(delta)
                if not text:
                    continue
                buffer += text
                
                # 按行拆分并处理
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    # 跳过空行 / 非 JSON 开头
                    if not line or not line.startswith("{") or not line.endswith("}"):
                        continue
                    try:
                        data = json.loads(line)
                    except:
                        continue
                    
                    # 格式化内部菜品结构
                    dish = {
                        "name": data.get("name_en", ""),
                        "translation": data.get("name_zh", ""),
                        "category": (data.get("section") or "").lower().replace(" ", "_"),
                        "category_translation": data.get("section", ""),
                        "menu_description": data.get("description_en") or None,
                        "translation_description": data.get("description_zh") or None,
                    }
                    dish_count += 1
                    print(f"   → 收到菜品 {dish_count}: {dish['name']}")
                    yield dish  # 立即yield，不等待
                
                # 让出控制权，允许其他协程运行
                await asyncio.sleep(0)
            
            # 处理 buffer 中最后可能残留的一行
            if buffer.strip().startswith("{") and buffer.strip().endswith("}"):
                try:
                    data = json.loads(buffer.strip())
                    dish = {
                        "name": data.get("name_en", ""),
                        "translation": data.get("name_zh", ""),
                        "category": (data.get("section") or "").lower().replace(" ", "_"),
                        "category_translation": data.get("section", ""),
                        "menu_description": data.get("description_en") or None,
                        "translation_description": data.get("description_zh") or None,
                    }
                    dish_count += 1
                    print(f"   → 收到菜品 {dish_count}: {dish['name']}")
                    yield dish
                except:
                    pass
        except Exception as e:
            print("❌ Streaming error:", str(e))
            raise
        
        print(f"🍽 流式识别完成：{dish_count} 道菜，耗时 {time.time()-start_time:.2f}s")

    async def get_dish_description(self, dish_name: str, translation: str = None, 
                                   menu_description: str = None, translation_description: str = None) -> str:
        """
        获取单个菜品的描述
        包含菜单中的原始描述信息
        """
        start_time = time.time()
        prompt = f"""请为以下菜品提供详细描述（80-120字）：
菜品名称：{dish_name}"""
        
        if translation:
            prompt += f"\n中文名称：{translation}"
        
        # 如果菜单中有描述，将其加入prompt
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
            api_start_time = time.time()
            print(f"📝 开始生成菜品描述: {dish_name}")
            if menu_description or translation_description:
                print(f"   包含菜单描述: {translation_description or menu_description}")
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=300
            )
            
            api_elapsed = time.time() - api_start_time
            print(f"✅ GPT-4o-mini API调用成功，耗时: {api_elapsed:.2f}秒")
            
            if not response.choices or not response.choices[0].message.content:
                return "描述生成中..."
            
            description = response.choices[0].message.content.strip()
            total_elapsed = time.time() - start_time
            print(f"✅ 描述生成成功，长度: {len(description)} 字符，总耗时: {total_elapsed:.2f}秒")
            return description
        except Exception as e:
            error_msg = str(e)
            print(f"❌ 描述生成失败: {error_msg}")
            return "描述生成失败，请重试"

    async def generate_dish_image(self, dish_name: str, translation: str = None, menu_description: str = None) -> str:
        """
        使用DALL-E生成菜品图片
        """
        start_time = time.time()
        # 构建图片生成提示词
        prompt = f"A beautiful, appetizing photo of {dish_name}"
        if translation:
            prompt += f" ({translation})"
        
        # 如果菜单中有描述，将其加入prompt以生成更准确的图片
        if menu_description:
            prompt += f". The dish is described as: {menu_description}"
        
        prompt += ", professional food photography, high quality, restaurant style"
        
        try:
            api_start_time = time.time()
            print(f"🎨 开始生成图片: {dish_name}")
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            
            api_elapsed = time.time() - api_start_time
            print(f"✅ DALL-E API调用成功，耗时: {api_elapsed:.2f}秒")
            
            if not response.data or len(response.data) == 0:
                raise Exception("图片生成失败：未返回图片URL")
            
            total_elapsed = time.time() - start_time
            print(f"✅ 图片生成完成，总耗时: {total_elapsed:.2f}秒")
            return response.data[0].url
        except Exception as e:
            raise Exception(f"DALL-E图片生成失败: {str(e)}")

