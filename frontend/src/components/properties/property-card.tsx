'use client'

import { Property } from '@/types'
import { ExternalLink, MapPin, Home, Ruler, Euro } from 'lucide-react'

interface PropertyCardProps {
  property: Property
}

export function PropertyCard({ property }: PropertyCardProps) {
  const formatPrice = (price?: number) => {
    if (!price) return 'Precio no disponible'
    return new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price)
  }

  const calculatePricePerM2 = () => {
    if (!property.precio || !property.metros) return null
    const metros = parseFloat(property.metros.replace(/[^\d.]/g, ''))
    if (metros > 0) {
      return Math.round(property.precio / metros)
    }
    return null
  }

  const pricePerM2 = calculatePricePerM2()

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
      <div className="p-6">
        {/* Header */}
        <div className="flex justify-between items-start mb-4">
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-medium text-gray-900 line-clamp-2">
              {property.nombre || 'Propiedad sin nombre'}
            </h3>
            {property.poblacion && (
              <div className="flex items-center mt-1 text-sm text-gray-600">
                <MapPin className="h-4 w-4 mr-1" />
                <span>{property.poblacion}</span>
              </div>
            )}
          </div>
          <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
            property.estatus === 'activo' 
              ? 'bg-green-100 text-green-800' 
              : 'bg-gray-100 text-gray-800'
          }`}>
            {property.estatus}
          </div>
        </div>

        {/* Price */}
        <div className="mb-4">
          <div className="text-2xl font-bold text-gray-900">
            {formatPrice(property.precio)}
          </div>
          {pricePerM2 && (
            <div className="text-sm text-gray-600">
              {pricePerM2.toLocaleString('es-ES')} €/m²
            </div>
          )}
        </div>

        {/* Details */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          {property.metros && (
            <div className="flex items-center text-sm text-gray-600">
              <Ruler className="h-4 w-4 mr-2" />
              <span>{property.metros}</span>
            </div>
          )}

          {property.habitaciones && (
            <div className="flex items-center text-sm text-gray-600">
              <Home className="h-4 w-4 mr-2" />
              <span>{property.habitaciones} hab.</span>
            </div>
          )}

          {property.planta && (
            <div className="text-sm text-gray-600">
              <span className="font-medium">Planta:</span> {property.planta}
            </div>
          )}

          {property.ascensor !== undefined && (
            <div className="text-sm text-gray-600">
              <span className="font-medium">Ascensor:</span> {property.ascensor ? 'Sí' : 'No'}
            </div>
          )}
        </div>

        {/* Description */}
        {property.descripcion && (
          <div className="mb-4">
            <p className="text-sm text-gray-600 line-clamp-3">
              {property.descripcion}
            </p>
          </div>
        )}

        {/* Footer */}
        <div className="flex justify-between items-center pt-4 border-t border-gray-100">
          <div className="text-xs text-gray-500">
            {property.fecha_crawl && (
              <span>
                Actualizado: {new Date(property.fecha_crawl).toLocaleDateString('es-ES')}
              </span>
            )}
          </div>

          {property.url && (
            <a
              href={property.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center space-x-1 text-sm text-blue-600 hover:text-blue-800"
            >
              <span>Ver propiedad</span>
              <ExternalLink className="h-4 w-4" />
            </a>
          )}
        </div>
      </div>
    </div>
  )
}