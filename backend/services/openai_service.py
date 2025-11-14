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

    async def analyze_menu_image(self, image_bytes: bytes) -> List[Dict]:
        """
        使用GPT-4 Vision分析菜单图片，提取菜品名称和描述
        返回包含 name 和 menu_description 的字典列表
        """
        start_time = time.time()
        print(f"🖼️  原始图片大小: {len(image_bytes)} bytes")
        
        # 压缩图片
        print("🗜️  开始压缩图片...")
        try:
            # 打开图片
            image = Image.open(io.BytesIO(image_bytes))
            original_size = image.size
            print(f"📐 原始尺寸: {original_size[0]}x{original_size[1]}")
            
            # 设置最大尺寸（OpenAI Vision API推荐最大2048x2048）
            max_size = 2048
            max_dimension = max(original_size)
            
            # 如果图片太大，进行缩放
            if max_dimension > max_size:
                scale = max_size / max_dimension
                new_size = (int(original_size[0] * scale), int(original_size[1] * scale))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
                print(f"📐 压缩后尺寸: {new_size[0]}x{new_size[1]}")
            else:
                print(f"📐 图片尺寸合适，无需缩放")
            
            # 转换为RGB模式（如果不是的话）
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 保存为JPEG格式（压缩率更高）
            compressed_buffer = io.BytesIO()
            image.save(compressed_buffer, format='JPEG', quality=85, optimize=True)
            compressed_bytes = compressed_buffer.getvalue()
            compressed_size = len(compressed_bytes)
            
            compression_ratio = (1 - compressed_size / len(image_bytes)) * 100
            print(f"✅ 图片压缩完成: {len(image_bytes)} bytes → {compressed_size} bytes (压缩率: {compression_ratio:.1f}%)")
            
            image_bytes = compressed_bytes
            image_format = "jpeg"
        except Exception as e:
            print(f"⚠️  图片压缩失败，使用原图: {e}")
            # 如果压缩失败，使用原图
            # 检测图片格式
            if len(image_bytes) >= 4:
                if image_bytes[:4] == b'\x89PNG':
                    image_format = "png"
                elif image_bytes[:3] == b'GIF':
                    image_format = "gif"
                elif len(image_bytes) >= 12 and image_bytes[8:12] == b'WEBP':
                    image_format = "webp"
                elif image_bytes[:2] == b'\xff\xd8':  # JPEG文件头
                    image_format = "jpeg"
                else:
                    image_format = "jpeg"
            else:
                image_format = "jpeg"
        
        # 将图片转换为base64
        print("🔄 开始转换图片为base64...")
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        print(f"✅ Base64转换完成，长度: {len(base64_image)} 字符")
        
        try:
            api_start_time = time.time()
            print("🚀 开始调用OpenAI GPT-4o-mini API...")
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """请仔细分析这张餐厅菜单图片，提取出所有菜品的完整信息。

重要要求：
1. 注意菜单的类别（section），比如在"Salad"类别下的"Caesar"应该识别为"Caesar Salad"
2. 提取完整的菜品名称，包括类别信息
3. 如果菜单中有菜品描述/介绍，也要一起提取
4. 返回JSON格式，每个菜品包含name（完整名称）和menu_description（菜单中的描述，如果没有则为null）

返回格式：
{
  "dishes": [
    {
      "name": "完整菜品名称",
      "menu_description": "菜单中的描述文字，如果没有则为null"
    }
  ]
}

只返回JSON，不要其他文字。如果图片不是菜单或无法识别，返回 {"dishes": []}。"""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/{image_format};base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000  # 增加token限制以支持描述
            )
            
            api_elapsed = time.time() - api_start_time
            print(f"✅ OpenAI API调用成功，耗时: {api_elapsed:.2f}秒")
            
            if not response.choices or not response.choices[0].message.content:
                print("⚠️  API返回空内容")
                return []
            
            content = response.choices[0].message.content
            print(f"📝 API返回内容: {content[:500]}...")
            
            # 解析JSON响应
            import json
            import re
            
            # 尝试从文本中提取JSON
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group(0)
            
            try:
                result = json.loads(content)
                if isinstance(result, dict) and "dishes" in result:
                    dishes = result["dishes"]
                    total_elapsed = time.time() - start_time
                    print(f"🍽️  解析到 {len(dishes)} 个菜品，总耗时: {total_elapsed:.2f}秒")
                    return dishes
                else:
                    print("⚠️  返回格式不正确，尝试解析为列表")
                    # 兼容旧格式：如果返回的是纯文本列表
                    dish_names = [line.strip() for line in content.split('\n') if line.strip()]
                    return [{"name": name, "menu_description": None} for name in dish_names]
            except json.JSONDecodeError as json_err:
                print(f"⚠️  JSON解析失败: {json_err}")
                # 如果JSON解析失败，尝试提取菜品名称
                dish_names = [line.strip() for line in content.split('\n') if line.strip() and not line.strip().startswith('{')]
                if dish_names:
                    print(f"🍽️  使用备用解析方法，找到 {len(dish_names)} 个菜品")
                    return [{"name": name, "menu_description": None} for name in dish_names]
                else:
                    print("❌ 无法解析返回内容")
                    return []
        except Exception as e:
            error_msg = str(e)
            print(f"❌ OpenAI API错误详情: {error_msg}")
            import traceback
            print(traceback.format_exc())
            raise Exception(f"OpenAI API调用失败: {error_msg}")

    async def translate_only(self, dishes: List[Dict]) -> List[Dict]:
        """
        只翻译菜品名称，不生成描述
        接收包含 name 和 menu_description 的字典列表
        """
        start_time = time.time()
        if not dishes:
            return []
        
        # 提取菜品名称列表
        dish_names = [dish.get("name", dish) if isinstance(dish, dict) else dish for dish in dishes]
        
        # 构建提示词
        dishes_text = "\n".join([f"- {name}" for name in dish_names])
        
        prompt = f"""请为以下菜品提供中文翻译：
{dishes_text}

返回JSON对象，格式为：
{{
  "dishes": [
    {{
      "name": "原始英文名称",
      "translation": "中文翻译"
    }}
  ]
}}

只返回JSON，不要其他文字。"""

        try:
            api_start_time = time.time()
            print(f"🌐 开始调用GPT-4o-mini翻译API，菜品数量: {len(dish_names)}")
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=2000
            )
            
            api_elapsed = time.time() - api_start_time
            print(f"✅ GPT-4o-mini API调用成功，耗时: {api_elapsed:.2f}秒")
            
            if not response.choices or not response.choices[0].message.content:
                print("⚠️  API返回空内容")
                return []
            
            # 解析JSON响应
            import json
            import re
            content = response.choices[0].message.content.strip()
            print(f"📝 API返回内容长度: {len(content)} 字符")
            
            # 尝试从文本中提取JSON
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group(0)
            
            try:
                result = json.loads(content)
            except json.JSONDecodeError as json_err:
                print(f"⚠️  JSON解析失败: {json_err}")
                # 使用正则表达式提取
                extracted_dishes = []
                dish_pattern = r'\{\s*"name"\s*:\s*"([^"]+)"\s*,\s*"translation"\s*:\s*"([^"]+)"'
                matches = re.findall(dish_pattern, content)
                for match in matches:
                    if len(match) == 2:
                        extracted_dishes.append({
                            "name": match[0],
                            "translation": match[1]
                        })
                
                if extracted_dishes:
                    print(f"✅ 使用正则表达式提取到 {len(extracted_dishes)} 个菜品")
                    # 合并菜单描述信息
                    menu_descriptions = {}
                    for dish in dishes:
                        if isinstance(dish, dict) and "name" in dish:
                            menu_descriptions[dish["name"]] = dish.get("menu_description")
                    
                    # 将菜单描述添加到翻译结果中
                    for translated_dish in extracted_dishes:
                        original_name = translated_dish.get("name")
                        if original_name in menu_descriptions:
                            translated_dish["menu_description"] = menu_descriptions[original_name]
                    
                    return extracted_dishes
                else:
                    raise Exception(f"JSON解析失败: {str(json_err)}")
            
            # 提取dishes数组
            if isinstance(result, dict) and "dishes" in result:
                translated_dishes = result["dishes"]
                print(f"✅ 成功解析，找到 {len(translated_dishes)} 个菜品")
                
                # 合并菜单描述信息
                menu_descriptions = {}
                for dish in dishes:
                    if isinstance(dish, dict) and "name" in dish:
                        menu_descriptions[dish["name"]] = dish.get("menu_description")
                
                # 将菜单描述添加到翻译结果中
                for translated_dish in translated_dishes:
                    original_name = translated_dish.get("name")
                    if original_name in menu_descriptions:
                        translated_dish["menu_description"] = menu_descriptions[original_name]
                
                total_elapsed = time.time() - start_time
                print(f"✅ 翻译完成，总耗时: {total_elapsed:.2f}秒")
                return translated_dishes
            
            return []
        except Exception as e:
            error_msg = str(e)
            print(f"❌ 翻译失败: {error_msg}")
            raise Exception(f"翻译失败: {error_msg}")

    async def get_dish_description(self, dish_name: str, translation: str = None) -> str:
        """
        获取单个菜品的描述
        """
        start_time = time.time()
        prompt = f"""请为以下菜品提供详细描述（50-100字）：
菜品名称：{dish_name}"""
        
        if translation:
            prompt += f"\n中文名称：{translation}"
        
        prompt += "\n\n请提供菜品的详细描述，包括主要食材、口味特点、制作方式等信息。描述长度在50-100字之间。"

        try:
            api_start_time = time.time()
            print(f"📝 开始生成菜品描述: {dish_name}")
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=200
            )
            
            api_elapsed = time.time() - api_start_time
            print(f"✅ GPT-4 API调用成功，耗时: {api_elapsed:.2f}秒")
            
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

    async def translate_and_describe(self, dish_names: List[str]) -> List[Dict]:
        """
        翻译菜品名称并生成描述
        """
        if not dish_names:
            return []
        
        # 构建提示词
        dishes_text = "\n".join([f"- {name}" for name in dish_names])
        
        prompt = f"""请为以下菜品提供中文翻译和简短描述（50-100字）：
{dishes_text}

返回JSON对象，格式为：
{{
  "dishes": [
    {{
      "name": "原始英文名称",
      "translation": "中文翻译",
      "description": "菜品描述（50-100字）"
    }}
  ]
}}

只返回JSON，不要其他文字。"""

        try:
            print(f"🌐 开始调用GPT-4翻译和描述API，菜品数量: {len(dish_names)}")
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=4000  # 增加token限制，避免JSON被截断
            )
            
            print("✅ GPT-4 API调用成功")
            
            if not response.choices or not response.choices[0].message.content:
                print("⚠️  API返回空内容")
                return []
            
            # 解析JSON响应
            import json
            import re
            content = response.choices[0].message.content.strip()
            print(f"📝 API返回内容长度: {len(content)} 字符")
            print(f"📝 内容预览: {content[:300]}...")
            
            # 尝试从文本中提取JSON（处理可能的markdown代码块或其他格式）
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group(0)
            
            # 尝试修复不完整的JSON（处理被截断的情况）
            try:
                result = json.loads(content)
            except json.JSONDecodeError as json_err:
                print(f"⚠️  JSON解析失败，尝试修复...")
                print(f"错误位置: {json_err.msg} at line {json_err.lineno}, column {json_err.colno}")
                
                # 尝试修复常见的JSON截断问题
                # 1. 如果缺少闭合引号，尝试添加
                # 2. 如果缺少闭合括号，尝试添加
                fixed_content = content
                
                # 检查是否缺少闭合引号（在最后一个字段）
                if '"name"' in fixed_content and fixed_content.count('"') % 2 != 0:
                    # 找到最后一个未闭合的引号位置
                    last_quote_pos = fixed_content.rfind('"')
                    if last_quote_pos > 0:
                        # 检查是否需要添加闭合引号
                        after_quote = fixed_content[last_quote_pos+1:].strip()
                        if after_quote and not after_quote.startswith(('"', ',', '}', ']')):
                            # 在适当位置添加闭合引号
                            fixed_content = fixed_content[:last_quote_pos+1] + '"' + fixed_content[last_quote_pos+1:]
                
                # 尝试补全缺失的闭合括号
                open_braces = fixed_content.count('{')
                close_braces = fixed_content.count('}')
                if open_braces > close_braces:
                    fixed_content += '}' * (open_braces - close_braces)
                
                open_brackets = fixed_content.count('[')
                close_brackets = fixed_content.count(']')
                if open_brackets > close_brackets:
                    fixed_content += ']' * (open_brackets - close_brackets)
                
                print(f"🔧 修复后的内容预览: {fixed_content[:300]}...")
                
                try:
                    result = json.loads(fixed_content)
                    print("✅ JSON修复成功")
                except json.JSONDecodeError as fix_err:
                    print(f"❌ JSON修复失败: {fix_err}")
                    print(f"原始内容（前500字符）: {content[:500]}")
                    # 如果修复失败，尝试只提取能解析的部分
                    # 使用更宽松的方式：尝试提取每个dish对象
                    dishes = []
                    dish_pattern = r'\{\s*"name"\s*:\s*"([^"]+)"\s*,\s*"translation"\s*:\s*"([^"]+)"\s*,\s*"description"\s*:\s*"([^"]*)"'
                    matches = re.findall(dish_pattern, content)
                    for match in matches:
                        if len(match) == 3:
                            dishes.append({
                                "name": match[0],
                                "translation": match[1],
                                "description": match[2] if match[2] else "描述生成中..."
                            })
                    
                    if dishes:
                        print(f"✅ 使用正则表达式提取到 {len(dishes)} 个菜品")
                        return dishes
                    else:
                        raise Exception(f"JSON解析失败且无法修复: {str(json_err)}")
            
            # 提取dishes数组
            if isinstance(result, dict) and "dishes" in result:
                print(f"✅ 成功解析，找到 {len(result['dishes'])} 个菜品")
                return result["dishes"]
            
            print("⚠️  返回结果中没有dishes字段")
            return []
        except Exception as e:
            error_msg = str(e)
            print(f"❌ 翻译和描述生成失败: {error_msg}")
            import traceback
            print(traceback.format_exc())
            raise Exception(f"翻译和描述生成失败: {error_msg}")

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

