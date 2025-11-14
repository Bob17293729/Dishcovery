# Dishcovery 🍽️

An intelligent menu recognition and translation application. Users can upload restaurant menu photos, and AI automatically recognizes dish information, generates Chinese translations and descriptions, and can also generate AI images for dishes of interest.

## Features

- 📸 **Intelligent Menu Recognition**: Automatically recognizes all text content in menu images using GPT-4o-mini Vision
- 🔄 **Two-Stage Streaming Processing**: 
  - Stage 1: Image → Markdown (real-time text extraction display)
  - Stage 2: Markdown → NDJSON (real-time structured dish information display)
- 🌐 **Smart Translation**: Automatically translates English dish names to Chinese
- 📝 **Dish Descriptions**: AI generates detailed descriptions for each dish (80-120 characters, including taste, features, preparation methods, etc.)
- 🥗 **Ingredient Extraction**: Automatically extracts and translates main ingredient lists
- 🎨 **Image Generation**: Uses DALL-E 3 to generate beautiful images for selected dishes
- 📱 **Mobile Optimized**: Responsive interface designed specifically for mobile devices
- ⚡ **Real-time Feedback**: Streaming processing with real-time display of recognition progress and results

## Tech Stack

### Backend
- Python 3.8+
- FastAPI
- OpenAI API (GPT-4o-mini Vision, GPT-4o-mini, DALL-E 3)
- Pillow (image compression processing)
- Server-Sent Events (SSE) streaming

### Frontend
- React 18
- TypeScript
- Tailwind CSS
- Vite
- react-markdown (Markdown rendering)

## Project Structure

```
Dishcovery/
├── backend/              # Backend API service
│   ├── main.py          # FastAPI main file
│   ├── services/        # Service layer
│   │   └── openai_service.py  # OpenAI service (two-stage streaming)
│   ├── requirements.txt
│   └── env.example
├── frontend/            # Frontend application
│   ├── src/
│   │   ├── components/  # React components
│   │   │   ├── MenuUpload.tsx    # Menu upload component
│   │   │   ├── DishList.tsx      # Dish list component
│   │   │   ├── DishCard.tsx      # Dish card component
│   │   │   └── MarkdownDisplay.tsx  # Markdown display component
│   │   ├── App.tsx      # Main application component
│   │   └── main.tsx     # Entry file
│   ├── package.json
│   └── vite.config.ts
├── menu/                # Sample menu files
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 18+
- OpenAI API Key

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp env.example .env
# Edit .env file and add your OPENAI_API_KEY
```

5. Start backend service:
```bash
uvicorn main:app --reload
```

Backend service will start at `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start development server:
```bash
npm run dev
```

Frontend application will start at `http://localhost:5173`

## API Endpoints

### POST /api/analyze-menu
Analyze menu image with two-stage streaming processing and return dish information

**Request**: 
- Content-Type: `multipart/form-data`
- Parameter: `file` (image file, max 10MB)

**Response**: 
Server-Sent Events (SSE) streaming response with the following message types:

1. **Markdown Stage** (Stage 1):
```json
{"type": "markdown", "content": "Extracted text snippet..."}
{"type": "markdown_done"}
```

2. **NDJSON Stage** (Stage 2):
```json
{"type": "dish", "dish": {
  "section": "Salads",
  "name_en": "Caesar Salad",
  "name_zh": "凯撒沙拉",
  "ingredients_en": "romaine lettuce, caesar dressing, parmesan",
  "ingredients_zh": "长叶生菜, 凯撒酱, 帕尔马干酪",
  "description_zh": "经典凯撒沙拉，选用新鲜的长叶生菜...",
  "image_prompt": "A beautiful Caesar salad with fresh romaine lettuce..."
}}
```

3. **Done/Error**:
```json
{"type": "done"}
{"type": "error", "error": "Error message"}
```

**Processing Flow**:
1. Image compression (max edge ≤2000px, JPEG quality 85)
2. Stage 1: Extract text as Markdown using GPT-4o-mini Vision
3. Stage 2: Parse Markdown into structured NDJSON format using GPT-4o-mini
4. Real-time streaming return, frontend can display results immediately

### POST /api/generate-image
Generate AI image for dish (DALL-E 3)

**Request**:
```json
{
  "image_prompt": "A beautiful Margherita pizza with fresh mozzarella..."
}
```

**Response**:
```json
{
  "image_url": "https://oaidalleapiprodscus..."
}
```

### GET /
Health check endpoint

**Response**:
```json
{
  "message": "Dishcovery API is running"
}
```

## Usage Instructions

1. **Upload Menu**: Click upload area and select restaurant menu photo (supports common image formats, max 10MB)
2. **View Extraction Process in Real-time**: 
   - Stage 1: Real-time display of Markdown text extracted from image
   - Stage 2: Real-time display of parsed dish cards
3. **View Dish Information**: Each dish card contains:
   - English name and Chinese translation
   - Main ingredients (English and Chinese)
   - Detailed description (80-120 characters)
4. **Expand Details**: Click dish card to expand and view full information
5. **Generate Image**: Click "Generate Image" button to use DALL-E 3 to generate beautiful image for the dish
6. **View Original Text**: Page bottom displays complete Markdown extraction results

## Core Features Explained

### Two-Stage Streaming Architecture

This project adopts an innovative two-stage streaming architecture to improve user experience and system efficiency:

**Stage 1: Image → Markdown**
- Uses GPT-4o-mini Vision model to recognize menu images
- Extracts all text content while maintaining original layout structure
- Outputs standard Markdown format
- Real-time streaming return, users can immediately see extraction progress

**Stage 2: Markdown → NDJSON**
- Uses GPT-4o-mini to parse Markdown content
- Automatically completes incomplete dish names (e.g., "Chop" → "Chop Salad")
- Generates structured data: category, dish name, ingredients, description, image prompt
- Streams output item by item, frontend displays dish cards in real-time

### Image Processing Optimization

- Automatic compression: Automatically scales when longest edge exceeds 2000px
- Format conversion: Uniformly converts to JPEG format (quality 85)
- Size limit: Maximum upload file size 10MB

### Data Structure

Each dish contains the following fields:
- `section`: Dish category (e.g., "Salads", "Pizzas")
- `name_en`: Complete English dish name
- `name_zh`: Chinese translation
- `ingredients_en`: Main ingredients (English, comma-separated)
- `ingredients_zh`: Main ingredients (Chinese, comma-separated)
- `description_zh`: Detailed description (80-120 characters)
- `image_prompt`: Image generation prompt (English)

## Development Roadmap

- [x] Stage 1: Project foundation setup
- [x] Stage 2: Backend core functionality development (two-stage streaming)
- [x] Stage 3: Frontend basic interface development
- [x] Stage 4: Frontend-backend integration and complete workflow
- [x] Stage 5: Streaming optimization and real-time feedback
- [ ] Stage 6: Performance optimization and enhanced error handling

## Notes

- **API Key**: Requires valid OpenAI API Key supporting GPT-4o-mini and DALL-E 3
- **API Costs**: 
  - Image recognition uses GPT-4o-mini Vision (lower cost)
  - Text parsing uses GPT-4o-mini (lower cost)
  - Image generation uses DALL-E 3 (per-request pricing)
- **Image Requirements**: 
  - Recommended to use clear menu photos for best recognition results
  - Supports common image formats (JPEG, PNG, WebP, etc.)
  - Maximum file size: 10MB
- **Processing Time**: 
  - Markdown extraction: Usually 5-15 seconds (depends on menu complexity)
  - NDJSON parsing: Usually 3-10 seconds (depends on number of dishes)
  - Image generation: Usually 10-30 seconds
- **Mobile Access**: Backend configured with CORS, supports mobile access (development environment allows all origins)

## Technical Highlights

- ✨ **Streaming Processing**: Uses SSE to implement real-time data streaming, improving user experience
- 🎯 **Two-Stage Architecture**: Separates text extraction and structured parsing, improving accuracy and maintainability
- 🖼️ **Smart Image Processing**: Automatic compression and format conversion, optimizing API calls
- 📱 **Responsive Design**: Interface layout optimized specifically for mobile devices
- 🔄 **Real-time Feedback**: Users can view processing progress and intermediate results in real-time

## License

MIT License

---

# Dishcovery 🍽️

一个智能菜单识别与翻译应用，用户可以上传餐厅菜单照片，AI自动识别菜品信息并生成中文翻译和描述，还可以为感兴趣的菜品生成AI图片。

## 功能特性

- 📸 **智能菜单识别**: 使用 GPT-4o-mini Vision 自动识别菜单图片中的所有文本内容
- 🔄 **两阶段流式处理**: 
  - 阶段1：图片 → Markdown（实时显示文本提取过程）
  - 阶段2：Markdown → NDJSON（实时显示结构化菜品信息）
- 🌐 **智能翻译**: 自动将英文菜品名称翻译成中文
- 📝 **菜品描述**: AI生成每个菜品的详细描述（80-120字，包含口感、特色、制作方式等）
- 🥗 **食材提取**: 自动提取并翻译主要食材列表
- 🎨 **图片生成**: 使用 DALL-E 3 为选中的菜品生成精美图片
- 📱 **移动端优化**: 专为移动设备设计的响应式界面
- ⚡ **实时反馈**: 流式处理，实时显示识别进度和结果

## 技术栈

### 后端
- Python 3.8+
- FastAPI
- OpenAI API (GPT-4o-mini Vision, GPT-4o-mini, DALL-E 3)
- Pillow (图片压缩处理)
- Server-Sent Events (SSE) 流式传输

### 前端
- React 18
- TypeScript
- Tailwind CSS
- Vite
- react-markdown (Markdown 渲染)

## 项目结构

```
Dishcovery/
├── backend/              # 后端API服务
│   ├── main.py          # FastAPI主文件
│   ├── services/        # 服务层
│   │   └── openai_service.py  # OpenAI服务（两阶段流式处理）
│   ├── requirements.txt
│   └── env.example
├── frontend/            # 前端应用
│   ├── src/
│   │   ├── components/  # React组件
│   │   │   ├── MenuUpload.tsx    # 菜单上传组件
│   │   │   ├── DishList.tsx      # 菜品列表组件
│   │   │   ├── DishCard.tsx      # 菜品卡片组件
│   │   │   └── MarkdownDisplay.tsx  # Markdown显示组件
│   │   ├── App.tsx      # 主应用组件
│   │   └── main.tsx     # 入口文件
│   ├── package.json
│   └── vite.config.ts
├── menu/                # 示例菜单文件
└── README.md
```

## 快速开始

### 前置要求

- Python 3.8+
- Node.js 18+
- OpenAI API Key

### 后端设置

1. 进入后端目录：
```bash
cd backend
```

2. 创建虚拟环境（推荐）：
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 配置环境变量：
```bash
cp env.example .env
# 编辑 .env 文件，填入你的 OPENAI_API_KEY
```

5. 启动后端服务：
```bash
uvicorn main:app --reload
```

后端服务将在 `http://localhost:8000` 启动

### 前端设置

1. 进入前端目录：
```bash
cd frontend
```

2. 安装依赖：
```bash
npm install
```

3. 启动开发服务器：
```bash
npm run dev
```

前端应用将在 `http://localhost:5173` 启动

## API端点

### POST /api/analyze-menu
分析菜单图片，两阶段流式处理并返回菜品信息

**请求**: 
- Content-Type: `multipart/form-data`
- 参数: `file` (图片文件，最大 10MB)

**响应**: 
Server-Sent Events (SSE) 流式响应，包含以下消息类型：

1. **Markdown 阶段**（阶段1）:
```json
{"type": "markdown", "content": "提取的文本片段..."}
{"type": "markdown_done"}
```

2. **NDJSON 阶段**（阶段2）:
```json
{"type": "dish", "dish": {
  "section": "Salads",
  "name_en": "Caesar Salad",
  "name_zh": "凯撒沙拉",
  "ingredients_en": "romaine lettuce, caesar dressing, parmesan",
  "ingredients_zh": "长叶生菜, 凯撒酱, 帕尔马干酪",
  "description_zh": "经典凯撒沙拉，选用新鲜的长叶生菜...",
  "image_prompt": "A beautiful Caesar salad with fresh romaine lettuce..."
}}
```

3. **完成/错误**:
```json
{"type": "done"}
{"type": "error", "error": "错误信息"}
```

**处理流程**:
1. 图片压缩（最长边≤2000px，JPEG质量85）
2. 阶段1：使用 GPT-4o-mini Vision 提取文本为 Markdown
3. 阶段2：使用 GPT-4o-mini 解析 Markdown 为结构化 NDJSON 格式
4. 实时流式返回，前端可立即显示结果

### POST /api/generate-image
为菜品生成AI图片（DALL-E 3）

**请求**:
```json
{
  "image_prompt": "A beautiful Margherita pizza with fresh mozzarella..."
}
```

**响应**:
```json
{
  "image_url": "https://oaidalleapiprodscus..."
}
```

### GET /
健康检查端点

**响应**:
```json
{
  "message": "Dishcovery API is running"
}
```

## 使用说明

1. **上传菜单**: 点击上传区域，选择餐厅菜单照片（支持常见图片格式，最大 10MB）
2. **实时查看提取过程**: 
   - 阶段1：实时显示从图片中提取的 Markdown 文本
   - 阶段2：实时显示解析出的菜品卡片
3. **查看菜品信息**: 每个菜品卡片包含：
   - 英文名称和中文翻译
   - 主要食材（中英文）
   - 详细描述（80-120字）
4. **展开详情**: 点击菜品卡片可展开查看完整信息
5. **生成图片**: 点击"生成图片"按钮，使用 DALL-E 3 为菜品生成精美图片
6. **查看原始文本**: 页面底部显示完整的 Markdown 提取结果

## 核心特性详解

### 两阶段流式处理架构

本项目采用创新的两阶段流式处理架构，提升用户体验和系统效率：

**阶段1：图片 → Markdown**
- 使用 GPT-4o-mini Vision 模型识别菜单图片
- 提取所有文本内容并保持原始排版结构
- 输出标准 Markdown 格式
- 实时流式返回，用户可立即看到提取进度

**阶段2：Markdown → NDJSON**
- 使用 GPT-4o-mini 解析 Markdown 内容
- 自动补全不完整的菜名（如 "Chop" → "Chop Salad"）
- 生成结构化数据：分类、菜名、食材、描述、图片提示词
- 逐条流式输出，前端实时显示菜品卡片

### 图片处理优化

- 自动压缩：最长边超过 2000px 时自动缩放
- 格式转换：统一转换为 JPEG 格式（质量 85）
- 大小限制：上传文件最大 10MB

### 数据结构

每个菜品包含以下字段：
- `section`: 菜品分类（如 "Salads", "Pizzas"）
- `name_en`: 完整英文菜名
- `name_zh`: 中文翻译
- `ingredients_en`: 主要食材（英文，逗号分隔）
- `ingredients_zh`: 主要食材（中文，逗号分隔）
- `description_zh`: 详细描述（80-120字）
- `image_prompt`: 图片生成提示词（英文）

## 开发计划

- [x] 阶段1: 项目基础搭建
- [x] 阶段2: 后端核心功能开发（两阶段流式处理）
- [x] 阶段3: 前端基础界面开发
- [x] 阶段4: 前后端集成和完整流程
- [x] 阶段5: 流式处理优化和实时反馈
- [ ] 阶段6: 性能优化和错误处理增强

## 注意事项

- **API Key**: 需要有效的 OpenAI API Key，支持 GPT-4o-mini 和 DALL-E 3
- **API 费用**: 
  - 图片识别使用 GPT-4o-mini Vision（成本较低）
  - 文本解析使用 GPT-4o-mini（成本较低）
  - 图片生成使用 DALL-E 3（按次收费）
- **图片要求**: 
  - 建议使用清晰的菜单照片以获得最佳识别效果
  - 支持常见图片格式（JPEG, PNG, WebP 等）
  - 最大文件大小：10MB
- **处理时间**: 
  - Markdown 提取：通常 5-15 秒（取决于菜单复杂度）
  - NDJSON 解析：通常 3-10 秒（取决于菜品数量）
  - 图片生成：通常 10-30 秒
- **移动端访问**: 后端已配置 CORS，支持移动端访问（开发环境允许所有来源）

## 技术亮点

- ✨ **流式处理**: 使用 SSE 实现实时数据流，提升用户体验
- 🎯 **两阶段架构**: 分离文本提取和结构化解析，提高准确性和可维护性
- 🖼️ **智能图片处理**: 自动压缩和格式转换，优化 API 调用
- 📱 **响应式设计**: 专为移动端优化的界面布局
- 🔄 **实时反馈**: 用户可实时查看处理进度和中间结果

## 许可证

MIT License

