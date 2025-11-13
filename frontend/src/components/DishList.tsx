import { Dish } from '../App'
import DishCard from './DishCard'

interface DishListProps {
  dishes: Dish[]
  setDishes: (dishes: Dish[]) => void
  loading: boolean
  setLoading: (loading: boolean) => void
}

const DishList = ({ dishes, setDishes, loading, setLoading }: DishListProps) => {
  const handleToggleSelect = (index: number) => {
    const newDishes = [...dishes]
    newDishes[index].selected = !newDishes[index].selected
    setDishes(newDishes)
  }

  const handleDetailLoaded = (index: number, description: string, imageUrl: string) => {
    const newDishes = [...dishes]
    newDishes[index].description = description
    newDishes[index].imageUrl = imageUrl
    newDishes[index].selected = true
    setDishes(newDishes)
  }

  const handleLoadingChange = (index: number, loading: boolean) => {
    const newDishes = [...dishes]
    newDishes[index].loadingDetail = loading
    setDishes(newDishes)
  }

  const selectedCount = dishes.filter((d) => d.selected).length

  return (
    <div className="mt-8">
      <div className="bg-white rounded-lg shadow-md p-6 mb-4">
        <h2 className="text-xl font-semibold mb-4 text-gray-700">
          识别到的菜品 ({dishes.length})
        </h2>
        {selectedCount > 0 && (
          <p className="text-sm text-gray-600 mb-4">
            已查看 {selectedCount} 个菜品详情
          </p>
        )}
        <p className="text-xs text-gray-500">
          点击任意菜品卡片查看详情和图片
        </p>
      </div>

      <div>
        {dishes.map((dish, index) => (
          <DishCard
            key={index}
            dish={dish}
            onToggleSelect={() => handleToggleSelect(index)}
            onDetailLoaded={(description, imageUrl) => 
              handleDetailLoaded(index, description, imageUrl)
            }
            onLoadingChange={(loading) => 
              handleLoadingChange(index, loading)
            }
          />
        ))}
      </div>
    </div>
  )
}

export default DishList

