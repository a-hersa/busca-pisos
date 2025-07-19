'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { propertiesApi } from '@/lib/api'
import { Property } from '@/types'
import { PropertyCard } from '../properties/property-card'
import { PropertyFilters } from '../properties/property-filters'
import { ExportButtons } from '../properties/export-buttons'
import { Loader2, Home } from 'lucide-react'

export function PropertiesTab() {
  const [filters, setFilters] = useState({
    poblacion: '',
    min_precio: '',
    max_precio: '',
    habitaciones: '',
    ascensor: '',
    search: '',
    sort_by: 'fecha_crawl',
    sort_order: 'desc',
    skip: 0,
    limit: 20
  })

  const { data: properties, isLoading, error } = useQuery({
    queryKey: ['properties', filters],
    queryFn: () => propertiesApi.list({
      skip: filters.skip,
      limit: filters.limit,
      poblacion: filters.poblacion || undefined,
      min_precio: filters.min_precio ? Number(filters.min_precio) : undefined,
      max_precio: filters.max_precio ? Number(filters.max_precio) : undefined,
    }),
  })

  const handleFilterChange = (newFilters: Partial<typeof filters>) => {
    setFilters(prev => ({ ...prev, ...newFilters, skip: 0 })) // Reset pagination when filtering
  }

  const handlePageChange = (newSkip: number) => {
    setFilters(prev => ({ ...prev, skip: newSkip }))
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">Error al cargar las propiedades</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Propiedades</h2>
        <p className="mt-1 text-sm text-gray-600">
          Explora las propiedades encontradas por los crawlers
        </p>
      </div>

      {/* Filters */}
      <PropertyFilters
        filters={filters}
        onFilterChange={handleFilterChange}
      />

      {/* Export Options */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium text-gray-900">Exportar Datos</h3>
          <ExportButtons filters={filters} />
        </div>
      </div>

      {/* Properties Grid */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
        </div>
      ) : properties && properties.length > 0 ? (
        <>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {properties.map((property) => (
              <PropertyCard key={property.p_id} property={property} />
            ))}
          </div>

          {/* Pagination */}
          <div className="flex justify-between items-center">
            <button
              onClick={() => handlePageChange(Math.max(0, filters.skip - filters.limit))}
              disabled={filters.skip === 0}
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Anterior
            </button>

            <span className="text-sm text-gray-600">
              Mostrando {filters.skip + 1} - {filters.skip + (properties?.length || 0)} propiedades
            </span>

            <button
              onClick={() => handlePageChange(filters.skip + filters.limit)}
              disabled={!properties || properties.length < filters.limit}
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Siguiente
            </button>
          </div>
        </>
      ) : (
        <div className="text-center py-12">
          <div className="mx-auto h-12 w-12 text-gray-400">
            <Home className="h-12 w-12" />
          </div>
          <h3 className="mt-2 text-sm font-medium text-gray-900">
            No se encontraron propiedades
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            Intenta ajustar los filtros o ejecuta un trabajo de crawling.
          </p>
        </div>
      )}
    </div>
  )
}