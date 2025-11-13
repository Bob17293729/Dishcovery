# Dishcovery 🍽️

一个智能菜单识别与翻译应用，用户可以上传餐厅菜单照片，AI自动识别菜品名称并生成中文翻译和描述，还可以为感兴趣的菜品生成AI图片。

## 功能特性

- 📸 **菜单识别**: 使用GPT-4 Vision自动识别菜单中的菜品名称
- 🌐 **智能翻译**: 自动将英文菜品名称翻译成中文
- 📝 **菜品描述**: AI生成每个菜品的详细描述（50-100字）
- 🎨 **图片生成**: 使用DALL-E为选中的菜品生成精美图片
- 📱 **移动端优化**: 专为移动设备设计的响应式界面

## 技术栈

### 后端
- Python 3.8+
- FastAPI
- OpenAI API (GPT-4 Vision, GPT-4, DALL-E)

### 前端
- React 18
- TypeScript
- Tailwind CSS
- Vite

## 项目结构

```
Dishcovery/
├── backend/              # 后端API服务
│   ├── main.py          # FastAPI主文件
│   ├── services/        # 服务层
│   │   └── openai_service.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/            # 前端应用
│   ├── src/
│   │   ├── components/  # React组件
│   │   │   ├── MenuUpload.tsx
│   │   │   ├── DishList.tsx
│   │   │   └── DishCard.tsx
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
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
cp .env.example .env
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
分析菜单图片，提取菜品名称

**请求**: `multipart/form-data` with `file` field

**响应**:
```json
{
  "dish_names": ["Dish 1", "Dish 2", ...]
}
```

### POST /api/translate-describe
翻译菜品名称并生成描述

**请求**:
```json
{
  "dish_names": ["Dish 1", "Dish 2"]
}
```

**响应**:
```json
{
  "dishes": [
    {
      "name": "Dish 1",
      "translation": "菜品1",
      "description": "菜品描述..."
    }
  ]
}
```

### POST /api/generate-image
为菜品生成AI图片

**请求**:
```json
{
  "dish_name": "Dish 1",
  "translation": "菜品1"
}
```

**响应**:
```json
{
  "image_url": "https://..."
}
```

## 使用说明

1. **上传菜单**: 点击上传区域，选择餐厅菜单照片
2. **等待识别**: AI会自动识别菜单中的菜品名称
3. **查看翻译**: 系统会自动为每个菜品生成中文翻译和描述
4. **选择菜品**: 点击"选择"按钮选择感兴趣的菜品
5. **生成图片**: 选中的菜品会自动生成AI图片

## 开发计划

- [x] 阶段1: 项目基础搭建
- [x] 阶段2: 后端核心功能开发
- [x] 阶段3: 前端基础界面开发
- [x] 阶段4: 前后端集成和完整流程
- [ ] 阶段5: 优化和测试

## 注意事项

- 需要有效的OpenAI API Key
- 图片识别和生成会消耗OpenAI API额度
- 建议使用清晰的菜单照片以获得最佳识别效果
- 图片生成可能需要10-30秒

## 许可证

MIT License

