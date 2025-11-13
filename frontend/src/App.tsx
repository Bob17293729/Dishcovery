import { useState } from 'react'
import MenuUpload from './components/MenuUpload'
import DishList from './components/DishList'

export interface Dish {
  name: string
  translation?: string
  description?: string
  menuDescription?: string  // 菜单中的原始描述
  imageUrl?: string
  selected?: boolean
  loadingDetail?: boolean
}

function App() {
  const [dishes, setDishes] = useState<Dish[]>([])
  const [loading, setLoading] = useState(false)

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100">
      <div className="container mx-auto px-4 py-8 max-w-md">
        <h1 className="text-3xl font-bold text-center mb-8 text-gray-800">
          🍽️ Dishcovery
        </h1>
        <MenuUpload 
          onDishesLoaded={setDishes}
          loading={loading}
          setLoading={setLoading}
        />
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

