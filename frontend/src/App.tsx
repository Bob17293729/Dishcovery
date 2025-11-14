/**
 * 主应用组件
 * 支持两阶段流式处理：
 * 1. 图片 → Markdown（实时显示）
 * 2. Markdown → NDJSON（实时显示菜品卡片）
 */
import { useState } from 'react'
import MenuUpload from './components/MenuUpload'
import DishList from './components/DishList'
import MarkdownDisplay from './components/MarkdownDisplay'

export interface Dish {
  section: string  // 菜品所属分类
  name_en: string  // 英文菜名
  name_zh: string  // 中文菜名
  ingredients_en: string  // 主要食材（英文）
  ingredients_zh: string  // 主要食材（中文）
  description_zh: string  // 中文详细描述
  image_prompt: string  // 图片生成提示词
  imageUrl?: string  // 生成的图片URL
  expanded?: boolean  // 是否展开详情
  loadingImage?: boolean  // 是否正在生成图片
}

function App() {
  const [dishes, setDishes] = useState<Dish[]>([])
  const [markdown, setMarkdown] = useState<string>('')
  const [loading, setLoading] = useState(false)

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100">
      <div className="container mx-auto px-4 py-8 max-w-md">
        <h1 className="text-3xl font-bold text-center mb-8 text-gray-800">
          🍽️ Dishcovery
        </h1>
        <MenuUpload 
          onDishesLoaded={setDishes}
          onMarkdownUpdate={setMarkdown}
          loading={loading}
          setLoading={setLoading}
        />
        <MarkdownDisplay markdown={markdown} />
        {dishes.length > 0 && (
          <DishList 
            dishes={dishes}
            setDishes={setDishes}
            loading={loading}
            setLoading={setLoading}
          />
        )}
      </div>
    </div>
  )
}

export default App

