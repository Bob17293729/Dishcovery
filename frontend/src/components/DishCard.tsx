/**
 * 菜品卡片组件
 * 显示菜品信息，支持展开详情和生成参考图片
 */
import { Dish } from '../App'

interface DishCardProps {
  dish: Dish
  onToggleExpand: () => void
  onImageGenerated: (imageUrl: string) => void
  onLoadingImageChange: (loading: boolean) => void
}

const DishCard = ({ dish, onToggleExpand, onImageGenerated, onLoadingImageChange }: DishCardProps) => {
  const handleGenerateImage = async (e: React.MouseEvent) => {
    e.stopPropagation() // 阻止触发卡片的展开/收起
    
    if (!dish.image_prompt) {
      alert('缺少图片生成提示词')
      return
    }

    if (dish.loadingImage) {
      return
    }

    onLoadingImageChange(true)

    try {
      console.log(`🎨 开始生成图片: ${dish.name_en}`)
      const response = await fetch('/api/generate-image', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          image_prompt: dish.image_prompt,
        }),
      })

      if (!response.ok) {
        throw new Error('图片生成失败')
      }

      const data = await response.json()
      console.log(`✅ 图片生成成功: ${dish.name_en}`)
      onImageGenerated(data.image_url)
    } catch (error) {
      console.error('Error generating image:', error)
      alert('生成图片失败，请重试')
    } finally {
      onLoadingImageChange(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-4 mb-4 border-2 border-gray-200 hover:border-blue-300 hover:shadow-lg transition-all">
      {/* 分类标签 */}
      {dish.section && (
        <span className="inline-block px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs font-medium mb-2">
          {dish.section}
        </span>
      )}

      {/* 默认显示内容 */}
      <div className="mb-3">
        {/* 英文菜名 - 必须显示，即使为空也显示占位符 */}
        <h3 className="text-lg font-semibold text-gray-800">
          {dish.name_en || '未命名菜品'}
        </h3>
        
        {/* 中文菜名 */}
        {dish.name_zh && dish.name_zh.trim() && (
          <p className="text-base text-blue-600 font-medium mt-1">
            {dish.name_zh}
          </p>
        )}

        {/* 食材（英文） */}
        {dish.ingredients_en && dish.ingredients_en.trim() && (
          <p className="text-sm text-gray-600 mt-2">
            <span className="font-medium">Ingredients:</span> {dish.ingredients_en}
          </p>
        )}

        {/* 食材（中文） */}
        {dish.ingredients_zh && dish.ingredients_zh.trim() && (
          <p className="text-sm text-gray-600 mt-1">
            <span className="font-medium">主要食材:</span> {dish.ingredients_zh}
          </p>
        )}

        {/* 如果所有字段都为空，显示提示 */}
        {!dish.name_en && !dish.name_zh && !dish.ingredients_en && !dish.ingredients_zh && (
          <p className="text-sm text-gray-400 italic mt-2">
            菜品信息加载中...
          </p>
        )}
      </div>

      {/* 展开的详情 */}
      {dish.expanded && dish.description_zh && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <p className="text-sm text-gray-700 leading-relaxed">
            {dish.description_zh}
          </p>
        </div>
      )}

      {/* 生成的图片 */}
      {dish.imageUrl && (
        <div className="mt-4">
          <img
            src={dish.imageUrl}
            alt={dish.name_zh || dish.name_en}
            className="w-full rounded-lg border border-gray-200"
          />
        </div>
      )}

      {/* 底部操作按钮 */}
      <div className="mt-4 flex justify-between items-center">
        {/* 展开/收起按钮 */}
        {dish.description_zh && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              onToggleExpand()
            }}
            className="text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            {dish.expanded ? '收起详情' : '展开详情'}
          </button>
        )}

        {/* 生成参考图片按钮 */}
        <button
          onClick={handleGenerateImage}
          disabled={dish.loadingImage || !dish.image_prompt}
          className={`ml-auto px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            dish.loadingImage
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-blue-500 text-white hover:bg-blue-600'
          }`}
        >
          {dish.loadingImage ? (
            <span className="flex items-center">
              <span className="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></span>
              生成中...
            </span>
          ) : (
            '生成参考图片'
          )}
        </button>
      </div>
    </div>
  )
}

export default DishCard
