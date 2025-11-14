import { useState, useRef } from 'react'
import { Dish } from '../App'

interface MenuUploadProps {
  onDishesLoaded: (dishes: Dish[]) => void
  loading: boolean
  setLoading: (loading: boolean) => void
}

const MenuUpload = ({ onDishesLoaded, loading, setLoading }: MenuUploadProps) => {
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // 显示预览
    const reader = new FileReader()
    reader.onloadend = () => {
      setImagePreview(reader.result as string)
    }
    reader.readAsDataURL(file)

    // 上传并分析
    handleUpload(file)
  }

  const handleUpload = async (file: File) => {
    setLoading(true)
    try {
      console.log('📤 开始上传图片...')
      const formData = new FormData()
      formData.append('file', file)

      // 1. 分析菜单
      console.log('🔍 步骤1: 调用菜单识别API...')
      const analyzeResponse = await fetch('/api/analyze-menu', {
        method: 'POST',
        body: formData,
      })

      console.log('📥 识别API响应状态:', analyzeResponse.status)
      
      if (!analyzeResponse.ok) {
        const errorText = await analyzeResponse.text()
        console.error('❌ 识别API错误:', errorText)
        throw new Error(`菜单分析失败: ${analyzeResponse.status} - ${errorText}`)
      }

      const analyzeData = await analyzeResponse.json()
      console.log('✅ 识别结果:', analyzeData)
      const dishesFromAnalysis = analyzeData.dishes || []

      if (!dishesFromAnalysis || dishesFromAnalysis.length === 0) {
        alert('未能识别到菜品，请确保上传的是清晰的菜单图片')
        setLoading(false)
        return
      }

      console.log(`📋 识别到 ${dishesFromAnalysis.length} 个菜品:`, dishesFromAnalysis)

      // 直接使用分析结果（已包含翻译和类别信息）
      const dishes: Dish[] = dishesFromAnalysis.map((dish: any) => ({
        name: dish.name,
        translation: dish.translation || undefined,
        category: dish.category || undefined,
        categoryTranslation: dish.category_translation || undefined,
        menuDescription: dish.menu_description || undefined, // 菜单中的原始描述（英文）
        translationDescription: dish.translation_description || undefined, // 菜单描述的中文翻译
        description: undefined, // AI生成的详细描述，初始不加载
        selected: false,
        loadingDetail: false,
      }))

      console.log('🎉 处理完成，加载菜品列表（包含翻译和类别）')
      onDishesLoaded(dishes)
    } catch (error) {
      console.error('❌ 完整错误信息:', error)
      const errorMessage = error instanceof Error ? error.message : '处理失败，请重试'
      alert(`处理失败: ${errorMessage}\n\n请查看浏览器控制台（F12）获取详细信息`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mb-8">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4 text-gray-700">
          上传菜单照片
        </h2>
        
        {imagePreview ? (
          <div className="mb-4">
            <img
              src={imagePreview}
              alt="菜单预览"
              className="w-full rounded-lg border border-gray-200"
            />
          </div>
        ) : (
          <div
            className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-blue-400 transition-colors"
            onClick={() => fileInputRef.current?.click()}
          >
            <div className="text-4xl mb-2">📷</div>
            <p className="text-gray-600">点击或拖拽上传菜单照片</p>
          </div>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileSelect}
          className="hidden"
          disabled={loading}
        />

        {imagePreview && (
          <button
            onClick={() => {
              setImagePreview(null)
              onDishesLoaded([])
              if (fileInputRef.current) {
                fileInputRef.current.value = ''
              }
            }}
            className="mt-4 w-full bg-gray-200 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-300 transition-colors"
            disabled={loading}
          >
            重新选择
          </button>
        )}

        {loading && (
          <div className="mt-4 text-center text-blue-600">
            <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
            <p className="mt-2">正在分析菜单...</p>
            <p className="mt-1 text-xs text-gray-500">请查看浏览器控制台（F12）查看详细进度</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default MenuUpload

