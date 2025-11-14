/**
 * 菜单上传组件
 * 支持两阶段流式处理：
 * 1. 图片 → Markdown（流式显示）
 * 2. Markdown → NDJSON（流式解析并显示菜品卡片）
 */
import { useState, useRef } from 'react'
import { Dish } from '../App'

interface MenuUploadProps {
  onDishesLoaded: (dishes: Dish[]) => void
  onMarkdownUpdate: (markdown: string) => void
  loading: boolean
  setLoading: (loading: boolean) => void
}

const MenuUpload = ({ onDishesLoaded, onMarkdownUpdate, loading, setLoading }: MenuUploadProps) => {
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
    const dishes: Dish[] = [] // 用于累积接收到的菜品
    let markdownBuffer = '' // 用于累积 Markdown 内容
    
    try {
      console.log('📤 开始上传图片...')
      const formData = new FormData()
      formData.append('file', file)

      // 流式分析菜单
      console.log('🔍 开始两阶段流式处理...')
      const analyzeResponse = await fetch('/api/analyze-menu', {
        method: 'POST',
        body: formData,
      })

      console.log('📥 识别API响应状态:', analyzeResponse.status)
      
      // 先检查响应状态
      if (!analyzeResponse.ok) {
        const errorText = await analyzeResponse.text()
        console.error('❌ 识别API错误:', errorText)
        throw new Error(`菜单分析失败: ${analyzeResponse.status} - ${errorText}`)
      }

      // 检查响应是否为流式
      if (!analyzeResponse.body) {
        throw new Error('响应体为空')
      }

      const reader = analyzeResponse.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      console.log('📡 开始流式读取数据...')

      while (true) {
        const { done, value } = await reader.read()
        
        if (done) {
          console.log('✅ 流式读取完成')
          break
        }

        // 解码数据并添加到缓冲区
        buffer += decoder.decode(value, { stream: true })
        
        // 处理缓冲区中的完整消息（SSE格式：data: {...}\n\n）
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // 保留最后不完整的行

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6)) // 移除 "data: " 前缀
              
              // 处理错误
              if (data.type === 'error') {
                console.error('❌ 服务器错误:', data.error)
                throw new Error(data.error)
              }
              
              // 第一阶段：Markdown 流式输出
              if (data.type === 'markdown') {
                markdownBuffer += data.content
                // 实时更新 Markdown 显示
                onMarkdownUpdate(markdownBuffer)
                console.log(`📝 Markdown 更新，当前长度: ${markdownBuffer.length} 字符`)
              }
              
              // Markdown 阶段完成
              if (data.type === 'markdown_done') {
                console.log('✅ Markdown 提取完成')
                onMarkdownUpdate(markdownBuffer) // 确保最终更新
              }
              
              // 第二阶段：NDJSON 菜品流式输出
              if (data.type === 'dish' && data.dish) {
                const dish: Dish = {
                  section: data.dish.section || '',
                  name_en: data.dish.name_en || '',
                  name_zh: data.dish.name_zh || '',
                  ingredients_en: data.dish.ingredients_en || '',
                  ingredients_zh: data.dish.ingredients_zh || '',
                  description_zh: data.dish.description_zh || '',
                  image_prompt: data.dish.image_prompt || '',
                  expanded: false,
                  loadingImage: false,
                }
                
                dishes.push(dish)
                console.log(`📋 收到菜品 ${dishes.length}: ${dish.name_en || '未命名'}`)
                
                // 立即更新UI，显示已收到的菜品
                onDishesLoaded([...dishes])
              }
              
              // 全部完成
              if (data.type === 'done') {
                console.log('✅ 所有菜品已接收完成')
                setLoading(false)
                return
              }
            } catch (parseError) {
              console.warn('⚠️ 解析消息失败:', parseError, '原始数据:', line)
            }
          }
        }
      }

      if (dishes.length === 0) {
        alert('未能识别到菜品，请确保上传的是清晰的菜单图片')
        setLoading(false)
        return
      }

      console.log(`🎉 处理完成，共收到 ${dishes.length} 个菜品`)
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
              onMarkdownUpdate('')
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
