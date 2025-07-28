'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { propertiesApi } from '@/lib/api'
import { Property } from '@/types'
import { PropertyCard } from '../properties/property-card'
import { PropertyFilters } from '../properties/property-filters'
import { ExportButtons } from '../properties/export-buttons'
import { Loader2, Home, AlertCircle, Play, Database } from 'lucide-react'

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

  // Better error handling - distinguish between actual errors and empty results
  if (error) {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Propiedades</h2>
          <p className="mt-1 text-sm text-gray-600">
            Explora las propiedades encontradas por los crawlers
          </p>
        </div>

        {/* Error State */}
        <div className="text-center py-12">
          <div className="mx-auto h-12 w-12 text-red-400">
            <AlertCircle className="h-12 w-12" />
          </div>
          <h3 className="mt-4 text-lg font-medium text-gray-900">
            Error al cargar las propiedades
          </h3>
          <p className="mt-2 text-sm text-gray-500">
            Ha ocurrido un problema al conectar con la base de datos.
          </p>
          <div className="mt-6">
            <button
              onClick={() => window.location.reload()}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              Intentar de nuevo
            </button>
          </div>
        </div>
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
        <div className="text-center py-16">
          <div className="mx-auto h-16 w-16 text-gray-400">
            <Database className="h-16 w-16" />
          </div>
          <h3 className="mt-4 text-lg font-medium text-gray-900">
            No hay propiedades disponibles
          </h3>
          <p className="mt-2 text-sm text-gray-500 max-w-md mx-auto">
            Aún no se han encontrado propiedades en la base de datos. Para comenzar a ver propiedades, necesitas ejecutar un trabajo de crawling.
          </p>
          
          {/* Call to Action */}
          <div className="mt-8 space-y-4">
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <button
                onClick={() => {
                  // Navigate to jobs tab - you might want to use a router here
                  const jobsTab = document.querySelector('[data-tab="jobs"]') as HTMLElement;
                  if (jobsTab) jobsTab.click();
                }}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <Play className="h-4 w-4 mr-2" />
                Crear trabajo de crawling
              </button>
              
              <button
                onClick={() => window.location.reload()}
                className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Actualizar
              </button>
            </div>
            
            {/* Instructions */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 max-w-lg mx-auto">
              <h4 className="text-sm font-medium text-blue-900 mb-2">
                ¿Cómo empezar?
              </h4>
              <ol className="text-sm text-blue-700 space-y-1 list-decimal list-inside">
                <li>Ve a la pestaña "Trabajos de Crawling"</li>
                <li>Haz clic en "Crear Nuevo Trabajo"</li>
                <li>Configura las URLs de Idealista que quieres crawlear</li>
                <li>Ejecuta el trabajo y espera a que termine</li>
                <li>Las propiedades aparecerán aquí automáticamente</li>
              </ol>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}