/**
 * Markdown 显示组件
 * 用于实时显示从菜单图片提取的 Markdown 内容
 */
import ReactMarkdown from 'react-markdown'

interface MarkdownDisplayProps {
  markdown: string
}

const MarkdownDisplay = ({ markdown }: MarkdownDisplayProps) => {
  if (!markdown) {
    return null
  }

  return (
    <div className="mb-8">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4 text-gray-700">
          提取的菜单内容 (Markdown)
        </h2>
        <div className="border border-gray-200 rounded-lg p-4 bg-gray-50 max-h-96 overflow-y-auto text-sm">
          <div className="markdown-content">
            <ReactMarkdown
              components={{
                h1: ({ children }) => <h1 className="text-xl font-bold mt-4 mb-2">{children}</h1>,
                h2: ({ children }) => <h2 className="text-lg font-bold mt-3 mb-2">{children}</h2>,
                h3: ({ children }) => <h3 className="text-base font-semibold mt-2 mb-1">{children}</h3>,
                p: ({ children }) => <p className="mb-2 text-gray-700">{children}</p>,
                ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
                li: ({ children }) => <li className="text-gray-700">{children}</li>,
                strong: ({ children }) => <strong className="font-semibold text-gray-900">{children}</strong>,
                em: ({ children }) => <em className="italic">{children}</em>,
              }}
            >
              {markdown}
            </ReactMarkdown>
          </div>
        </div>
        {markdown && (
          <p className="mt-2 text-xs text-gray-500">
            共 {markdown.length} 字符
          </p>
        )}
      </div>
    </div>
  )
}

export default MarkdownDisplay

