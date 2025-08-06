'use client'

import { useState, useRef, useEffect } from 'react'
import { ChevronDown, Search, X, Check } from 'lucide-react'

interface Option {
  id: number | string
  value: string
  label: string
  subtitle?: string
}

interface SearchableDropdownProps {
  options: Option[]
  value: string[]
  onChange: (values: string[]) => void
  placeholder?: string
  searchPlaceholder?: string
  multiple?: boolean
  loading?: boolean
  onSearch?: (query: string) => void
  error?: string
  className?: string
  disabled?: boolean
}

export function SearchableDropdown({
  options,
  value,
  onChange,
  placeholder = "Select options...",
  searchPlaceholder = "Search...",
  multiple = false,
  loading = false,
  onSearch,
  error,
  className = "",
  disabled = false
}: SearchableDropdownProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const dropdownRef = useRef<HTMLDivElement>(null)
  const searchRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (onSearch) {
      onSearch(searchQuery)
    }
  }, [searchQuery, onSearch])

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  useEffect(() => {
    if (isOpen && searchRef.current) {
      searchRef.current.focus()
    }
  }, [isOpen])

  const filteredOptions = options.filter(option =>
    option.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (option.subtitle && option.subtitle.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  const selectedOptions = options.filter(option => value.includes(option.value))

  const handleOptionToggle = (optionValue: string) => {
    if (multiple) {
      const newValue = value.includes(optionValue)
        ? value.filter(v => v !== optionValue)
        : [...value, optionValue]
      onChange(newValue)
    } else {
      onChange([optionValue])
      setIsOpen(false)
    }
  }

  const handleRemoveOption = (optionValue: string, event: React.MouseEvent) => {
    event.stopPropagation()
    onChange(value.filter(v => v !== optionValue))
  }

  const handleClearAll = () => {
    onChange([])
  }

  const getDisplayText = () => {
    if (value.length === 0) return placeholder
    if (multiple) {
      return `${value.length} selected`
    }
    const selected = selectedOptions[0]
    return selected ? selected.label : placeholder
  }

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className={`
          w-full px-3 py-2 text-left border rounded-md shadow-sm 
          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
          ${disabled ? 'bg-gray-100 cursor-not-allowed' : 'bg-white cursor-pointer hover:border-gray-400'}
          ${error ? 'border-red-300' : 'border-gray-300'}
          ${isOpen ? 'border-blue-500 ring-2 ring-blue-500' : ''}
        `}
      >
        <div className="flex items-center justify-between">
          <div className="flex-1 truncate">
            {multiple && value.length > 0 ? (
              <div className="flex flex-wrap gap-1">
                {selectedOptions.slice(0, 2).map(option => (
                  <span
                    key={option.id}
                    className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                  >
                    {option.label}
                    <X
                      className="ml-1 h-3 w-3 cursor-pointer hover:text-blue-600"
                      onClick={(e) => handleRemoveOption(option.value, e)}
                    />
                  </span>
                ))}
                {value.length > 2 && (
                  <span className="text-sm text-gray-500">
                    +{value.length - 2} more
                  </span>
                )}
              </div>
            ) : (
              <span className={value.length === 0 ? 'text-gray-500' : 'text-gray-900'}>
                {getDisplayText()}
              </span>
            )}
          </div>
          
          <div className="flex items-center space-x-1">
            {value.length > 0 && !disabled && (
              <X
                className="h-4 w-4 text-gray-400 hover:text-gray-600 cursor-pointer"
                onClick={(e) => {
                  e.stopPropagation()
                  handleClearAll()
                }}
              />
            )}
            <ChevronDown 
              className={`h-4 w-4 text-gray-400 transition-transform ${isOpen ? 'transform rotate-180' : ''}`}
            />
          </div>
        </div>
      </button>

      {/* Error Message */}
      {error && (
        <p className="mt-1 text-sm text-red-600">
          {error}
        </p>
      )}

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-hidden">
          {/* Search Input */}
          <div className="p-3 border-b border-gray-200">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                ref={searchRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                placeholder={searchPlaceholder}
              />
            </div>
          </div>

          {/* Options List */}
          <div className="max-h-48 overflow-y-auto">
            {loading ? (
              <div className="px-3 py-8 text-center text-gray-500">
                <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
                <span className="mt-2 block">Loading...</span>
              </div>
            ) : filteredOptions.length === 0 ? (
              <div className="px-3 py-8 text-center text-gray-500">
                {searchQuery ? 'No results found' : 'No options available'}
              </div>
            ) : (
              filteredOptions.map(option => (
                <button
                  key={option.id}
                  type="button"
                  onClick={() => handleOptionToggle(option.value)}
                  className={`
                    w-full px-3 py-2 text-left hover:bg-gray-50 focus:outline-none focus:bg-gray-50
                    flex items-center justify-between group
                  `}
                >
                  <div className="flex-1">
                    <div className="font-medium text-gray-900">
                      {option.label}
                    </div>
                    {option.subtitle && (
                      <div className="text-xs text-gray-500 truncate">
                        {option.subtitle}
                      </div>
                    )}
                  </div>
                  
                  {value.includes(option.value) && (
                    <Check className="h-4 w-4 text-blue-600 flex-shrink-0" />
                  )}
                </button>
              ))
            )}
          </div>

          {/* Multiple selection footer */}
          {multiple && value.length > 0 && (
            <div className="p-3 border-t border-gray-200 bg-gray-50">
              <div className="flex items-center justify-between text-sm text-gray-600">
                <span>{value.length} selected</span>
                <button
                  type="button"
                  onClick={handleClearAll}
                  className="text-blue-600 hover:text-blue-800 font-medium"
                >
                  Clear all
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}