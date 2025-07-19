'use client'

import { Search, Filter, X } from 'lucide-react'

interface PropertyFiltersProps {
  filters: {
    poblacion: string
    min_precio: string
    max_precio: string
  }
  onFilterChange: (filters: Partial<{
    poblacion: string
    min_precio: string
    max_precio: string
  }>) => void
}

export function PropertyFilters({ filters, onFilterChange }: PropertyFiltersProps) {
  const handleClearFilters = () => {
    onFilterChange({
      poblacion: '',
      min_precio: '',
      max_precio: ''
    })
  }

  const hasActiveFilters = filters.poblacion || filters.min_precio || filters.max_precio

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Filter className="h-5 w-5 text-gray-400" />
          <h3 className="text-lg font-medium text-gray-900">Filtros</h3>
        </div>
        {hasActiveFilters && (
          <button
            onClick={handleClearFilters}
            className="flex items-center space-x-1 text-sm text-gray-500 hover:text-gray-700"
          >
            <X className="h-4 w-4" />
            <span>Limpiar filtros</span>
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Location Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Población
          </label>
          <div className="relative">
            <input
              type="text"
              value={filters.poblacion}
              onChange={(e) => onFilterChange({ poblacion: e.target.value })}
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="ej. Barcelona, Madrid..."
            />
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-4 w-4 text-gray-400" />
            </div>
          </div>
        </div>

        {/* Min Price Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Precio Mínimo (€)
          </label>
          <input
            type="number"
            value={filters.min_precio}
            onChange={(e) => onFilterChange({ min_precio: e.target.value })}
            className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder="0"
            min="0"
          />
        </div>

        {/* Max Price Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Precio Máximo (€)
          </label>
          <input
            type="number"
            value={filters.max_precio}
            onChange={(e) => onFilterChange({ max_precio: e.target.value })}
            className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder="1000000"
            min="0"
          />
        </div>
      </div>

      {/* Quick Filter Buttons */}
      <div className="mt-4 flex flex-wrap gap-2">
        <button
          onClick={() => onFilterChange({ min_precio: '', max_precio: '50000' })}
          className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200"
        >
          Hasta 50k€
        </button>
        <button
          onClick={() => onFilterChange({ min_precio: '50000', max_precio: '100000' })}
          className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200"
        >
          50k€ - 100k€
        </button>
        <button
          onClick={() => onFilterChange({ min_precio: '100000', max_precio: '200000' })}
          className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200"
        >
          100k€ - 200k€
        </button>
        <button
          onClick={() => onFilterChange({ min_precio: '200000', max_precio: '' })}
          className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200"
        >
          Más de 200k€
        </button>
      </div>
    </div>
  )
}