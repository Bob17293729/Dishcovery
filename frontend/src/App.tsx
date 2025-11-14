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
  name: string
  translation?: string
  category?: string  // 类别（英文，如 salad, soup）
  categoryTranslation?: string  // 类别翻译（中文，如 沙拉, 汤品）
  description?: string
  menuDescription?: string  // 菜单中的原始描述（英文）
  translationDescription?: string  // 菜单描述的中文翻译
  imageUrl?: string
  selected?: boolean
  loadingDetail?: boolean
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

