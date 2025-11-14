import { Dish } from '../App'

interface DishCardProps {
  dish: Dish
  onToggleSelect: () => void
  onDetailLoaded: (description: string, imageUrl: string) => void
  onLoadingChange: (loading: boolean) => void
}

const DishCard = ({ dish, onToggleSelect, onDetailLoaded, onLoadingChange }: DishCardProps) => {
  const handleClick = async () => {
    // 如果已经有描述和图片，就不需要再次加载
    if (dish.description && dish.imageUrl) {
      onToggleSelect()
      return
    }

    // 如果正在加载，不重复请求
    if (dish.loadingDetail) {
      return
    }

    // 开始加载详情
    onLoadingChange(true)
    
    try {
      console.log(`📥 开始加载菜品详情: ${dish.name}`)
      const response = await fetch('/api/get-dish-detail', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          dish_name: dish.name,
          translation: dish.translation,
          menu_description: dish.menuDescription,
        }),
      })

      if (!response.ok) {
        throw new Error('获取菜品详情失败')
      }

      const data = await response.json()
      console.log(`✅ 菜品详情加载成功: ${dish.name}`)
      
      onDetailLoaded(data.description, data.image_url)
      onToggleSelect() // 加载完成后自动选择
    } catch (error) {
      console.error('Error loading dish detail:', error)
      alert('加载菜品详情失败，请重试')
    } finally {
      onLoadingChange(false)
    }
  }

  return (
    <div
      className={`bg-white rounded-lg shadow-md p-4 mb-4 border-2 transition-all cursor-pointer ${
        dish.selected
          ? 'border-blue-500 bg-blue-50'
          : 'border-gray-200 hover:border-blue-300 hover:shadow-lg'
      }`}
      onClick={handleClick}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1">
          {dish.categoryTranslation && (
            <span className="inline-block px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs font-medium mb-2">
              {dish.categoryTranslation}
            </span>
          )}
          <h3 className="text-lg font-semibold text-gray-800">{dish.name}</h3>
          {dish.translation && (
            <p className="text-base text-blue-600 font-medium mt-1">
              {dish.translation}
            </p>
          )}
          {dish.translationDescription && (
            <p className="text-sm text-gray-600 mt-2 leading-relaxed">
              {dish.translationDescription}
            </p>
          )}
          {!dish.translationDescription && dish.menuDescription && (
            <p className="text-xs text-gray-500 mt-2 leading-relaxed italic">
              {dish.menuDescription}
            </p>
          )}
        </div>
        {dish.selected && (
          <div className="ml-4 px-3 py-1 bg-blue-500 text-white rounded-lg text-sm">
            已查看
          </div>
        )}
      </div>

      {dish.loadingDetail && (
        <div className="mt-4 text-center text-blue-600">
          <div className="inline-block animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-sm">正在加载详情和图片...</p>
        </div>
      )}

      {dish.description && !dish.loadingDetail && (
        <p className="text-sm text-gray-600 mt-2 leading-relaxed">
          {dish.description}
        </p>
      )}

      {dish.imageUrl && !dish.loadingDetail && (
        <div className="mt-4">
          <img
            src={dish.imageUrl}
            alt={dish.translation || dish.name}
            className="w-full rounded-lg border border-gray-200"
          />
        </div>
      )}

      {!dish.description && !dish.loadingDetail && (
        <p className="text-xs text-gray-400 mt-2">点击查看详情和图片</p>
      )}
    </div>
  )
}

export default DishCard

