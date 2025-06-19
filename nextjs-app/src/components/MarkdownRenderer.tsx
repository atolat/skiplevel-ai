'use client'

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { ComponentProps } from 'react'

interface MarkdownRendererProps {
  content: string
  className?: string
}

export default function MarkdownRenderer({ content, className = '' }: MarkdownRendererProps) {
  return (
    <div className={`markdown-content ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Headings
          h1: ({ children }) => (
            <h1 className="text-xl font-bold text-green-400 font-mono mb-3 border-b border-gray-700 pb-2">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-lg font-bold text-blue-400 font-mono mb-2 mt-4">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-md font-bold text-yellow-400 font-mono mb-2 mt-3">
              {children}
            </h3>
          ),
          
          // Paragraphs
          p: ({ children }) => (
            <p className="text-gray-200 font-mono mb-3 leading-relaxed">
              {children}
            </p>
          ),
          
          // Lists
          ul: ({ children }) => (
            <ul className="text-gray-200 font-mono mb-3 ml-4 space-y-1">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="text-gray-200 font-mono mb-3 ml-4 space-y-1 list-decimal">
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li className="text-gray-200 font-mono">
              <span className="text-green-400 mr-2">•</span>
              {children}
            </li>
          ),
          
          // Code blocks
          code: ({ inline, children, ...props }: ComponentProps<'code'> & { inline?: boolean }) => {
            if (inline) {
              return (
                <code 
                  className="bg-gray-800 text-green-400 px-1 py-0.5 rounded font-mono text-sm border border-gray-700"
                  {...props}
                >
                  {children}
                </code>
              )
            }
            
            return (
              <div className="bg-gray-900 border border-gray-700 rounded-lg p-4 mb-3 overflow-x-auto">
                <code className="text-green-300 font-mono text-sm whitespace-pre" {...props}>
                  {children}
                </code>
              </div>
            )
          },
          
          // Pre blocks (for code blocks)
          pre: ({ children }) => (
            <div className="bg-gray-900 border border-gray-700 rounded-lg p-4 mb-3 overflow-x-auto">
              {children}
            </div>
          ),
          
          // Blockquotes
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-blue-500 pl-4 py-2 my-3 bg-gray-800/50 text-gray-300 font-mono italic">
              {children}
            </blockquote>
          ),
          
          // Links
          a: ({ href, children }) => (
            <a 
              href={href} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-blue-400 hover:text-blue-300 underline font-mono"
            >
              {children}
            </a>
          ),
          
          // Tables
          table: ({ children }) => (
            <div className="overflow-x-auto mb-3">
              <table className="min-w-full border border-gray-700 font-mono text-sm">
                {children}
              </table>
            </div>
          ),
          th: ({ children }) => (
            <th className="border border-gray-700 px-3 py-2 bg-gray-800 text-green-400 font-bold text-left">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="border border-gray-700 px-3 py-2 text-gray-200">
              {children}
            </td>
          ),
          
          // Horizontal rule
          hr: () => (
            <hr className="border-gray-700 my-4" />
          ),
          
          // Strong/Bold
          strong: ({ children }) => (
            <strong className="text-white font-bold">
              {children}
            </strong>
          ),
          
          // Emphasis/Italic
          em: ({ children }) => (
            <em className="text-gray-300 italic">
              {children}
            </em>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
} 