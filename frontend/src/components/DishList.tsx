/**
 * 菜品列表组件
 * 管理菜品列表的显示和状态
 */
import { Dish } from '../App'
import DishCard from './DishCard'

interface DishListProps {
  dishes: Dish[]
  setDishes: (dishes: Dish[]) => void
  loading: boolean
  setLoading: (loading: boolean) => void
}

const DishList = ({ dishes, setDishes, loading, setLoading }: DishListProps) => {
  const handleToggleExpand = (index: number) => {
    const newDishes = [...dishes]
    newDishes[index].expanded = !newDishes[index].expanded
    setDishes(newDishes)
  }

  const handleImageGenerated = (index: number, imageUrl: string) => {
    const newDishes = [...dishes]
    newDishes[index].imageUrl = imageUrl
    setDishes(newDishes)
  }

  const handleLoadingImageChange = (index: number, loading: boolean) => {
    const newDishes = [...dishes]
    newDishes[index].loadingImage = loading
    setDishes(newDishes)
  }

  return (
    <div className="mt-8">
      <div className="bg-white rounded-lg shadow-md p-6 mb-4">
        <h2 className="text-xl font-semibold mb-4 text-gray-700">
          识别到的菜品 ({dishes.length})
        </h2>
        <p className="text-xs text-gray-500">
          点击"展开详情"查看完整描述，点击"生成参考图片"生成菜品图片
        </p>
      </div>

      <div>
        {dishes.map((dish, index) => (
          <DishCard
            key={index}
            dish={dish}
            onToggleExpand={() => handleToggleExpand(index)}
            onImageGenerated={(imageUrl) => 
              handleImageGenerated(index, imageUrl)
            }
            onLoadingImageChange={(loading) => 
              handleLoadingImageChange(index, loading)
            }
          />
        ))}
      </div>
    </div>
  )
}

export default DishList
