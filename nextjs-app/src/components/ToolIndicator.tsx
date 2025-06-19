'use client'

import { useState, useEffect } from 'react'

interface ToolIndicatorProps {
  tools_used?: string[]
  tool_execution_info?: Array<{
    name: string
    args: Record<string, any>
    id: string
  }>
}

// Tool icon mapping
const getToolIcon = (toolName: string): string => {
  switch (toolName) {
    case 'datetime':
      return '🕐'
    case 'calculator':
      return '🧮'
    case 'web_search':
      return '🔍'
    case 'file_reader':
      return '📄'
    case 'one_on_one_scheduler':
      return '📅'
    default:
      return '🔧'
  }
}

// Tool display name mapping
const getToolDisplayName = (toolName: string): string => {
  switch (toolName) {
    case 'datetime':
      return 'DateTime'
    case 'calculator':
      return 'Calculator'
    case 'web_search':
      return 'Web Search'
    case 'file_reader':
      return 'File Reader'
    case 'one_on_one_scheduler':
      return 'Meeting Scheduler'
    default:
      return toolName
  }
}

export default function ToolIndicator({ tools_used, tool_execution_info }: ToolIndicatorProps) {
  const [showDetails, setShowDetails] = useState(false)

  if (!tools_used || tools_used.length === 0) {
    return null
  }

  return (
    <div className="mt-2 mb-2">
      {/* Tool badges */}
      <div className="flex flex-wrap items-center gap-2 mb-2">
        <span className="text-xs text-gray-400 font-mono">Tools used:</span>
        {tools_used.map((tool, index) => (
          <div
            key={`${tool}-${index}`}
            className="inline-flex items-center space-x-1 bg-blue-900/30 border border-blue-700/50 rounded-md px-2 py-1 text-xs font-mono text-blue-300"
          >
            <span>{getToolIcon(tool)}</span>
            <span>{getToolDisplayName(tool)}</span>
          </div>
        ))}
        {tool_execution_info && tool_execution_info.length > 0 && (
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="text-xs text-gray-400 hover:text-gray-300 font-mono underline"
          >
            {showDetails ? 'Hide details' : 'Show details'}
          </button>
        )}
      </div>

      {/* Tool execution details */}
      {showDetails && tool_execution_info && (
        <div className="bg-gray-800/50 border border-gray-700 rounded-md p-3 text-xs font-mono">
          <div className="text-gray-400 mb-2">Tool Execution Details:</div>
          {tool_execution_info.map((tool, index) => (
            <div key={`${tool.id}-${index}`} className="mb-2 last:mb-0">
              <div className="text-blue-300 font-semibold">
                {getToolIcon(tool.name)} {getToolDisplayName(tool.name)}
              </div>
              {Object.keys(tool.args).length > 0 && (
                <div className="text-gray-400 ml-4 mt-1">
                  <div className="text-gray-500">Arguments:</div>
                  <div className="ml-2 text-gray-300">
                    {Object.entries(tool.args).map(([key, value]) => (
                      <div key={key}>
                        <span className="text-gray-400">{key}:</span>{' '}
                        <span className="text-gray-200">
                          {typeof value === 'string' ? `"${value}"` : JSON.stringify(value)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
} 