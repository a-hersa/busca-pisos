'use client'

import { CrawlJob } from '@/types'
import { 
  Play, 
  Square, 
  Eye, 
  Trash2, 
  Calendar,
  Clock,
  Globe,
  AlertCircle,
  CheckCircle,
  Loader2
} from 'lucide-react'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'

interface JobCardProps {
  job: CrawlJob
  onView: () => void
  onRun: () => void
  onCancel: () => void
  onDelete: () => void
  isRunning?: boolean
  isCancelling?: boolean
  isDeleting?: boolean
}

export function JobCard({ 
  job, 
  onView, 
  onRun, 
  onCancel, 
  onDelete,
  isRunning,
  isCancelling,
  isDeleting
}: JobCardProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'bg-blue-100 text-blue-800'
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      case 'cancelled':
        return 'bg-gray-100 text-gray-800'
      default:
        return 'bg-yellow-100 text-yellow-800'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <Loader2 className="h-4 w-4 animate-spin" />
      case 'completed':
        return <CheckCircle className="h-4 w-4" />
      case 'failed':
        return <AlertCircle className="h-4 w-4" />
      case 'cancelled':
        return <Square className="h-4 w-4" />
      default:
        return <Clock className="h-4 w-4" />
    }
  }

  const canRun = job.status !== 'running'
  const canCancel = job.status === 'running'

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
      <div className="p-6">
        {/* Header */}
        <div className="flex justify-between items-start mb-4">
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-medium text-gray-900 truncate">
              {job.job_name}
            </h3>
            <p className="text-sm text-gray-500">
              Spider: {job.spider_name}
            </p>
          </div>
          <div className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(job.status)}`}>
            {getStatusIcon(job.status)}
            <span className="capitalize">{job.status}</span>
          </div>
        </div>

        {/* URLs */}
        <div className="mb-4">
          <div className="flex items-center text-sm text-gray-600 mb-2">
            <Globe className="h-4 w-4 mr-1" />
            <span>{job.start_urls.length} URL(s)</span>
          </div>
          <div className="text-xs text-gray-500 space-y-1 max-h-20 overflow-y-auto">
            {job.start_urls.slice(0, 2).map((url, index) => (
              <div key={index} className="truncate">
                {url}
              </div>
            ))}
            {job.start_urls.length > 2 && (
              <div className="text-gray-400">
                +{job.start_urls.length - 2} más...
              </div>
            )}
          </div>
        </div>

        {/* Schedule */}
        <div className="mb-4">
          <div className="flex items-center text-sm text-gray-600">
            <Calendar className="h-4 w-4 mr-1" />
            <span className="capitalize">{job.schedule_type}</span>
            {job.cron_expression && (
              <span className="ml-2 text-xs text-gray-500">
                ({job.cron_expression})
              </span>
            )}
          </div>
        </div>

        {/* Timestamps */}
        <div className="text-xs text-gray-500 mb-4 space-y-1">
          <div>
            Creado: {format(new Date(job.created_at), 'dd/MM/yyyy HH:mm', { locale: es })}
          </div>
          {job.updated_at !== job.created_at && (
            <div>
              Actualizado: {format(new Date(job.updated_at), 'dd/MM/yyyy HH:mm', { locale: es })}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex justify-between items-center pt-4 border-t border-gray-100">
          <button
            onClick={onView}
            className="flex items-center space-x-1 text-sm text-gray-600 hover:text-gray-900"
          >
            <Eye className="h-4 w-4" />
            <span>Ver detalles</span>
          </button>

          <div className="flex space-x-2">
            {canCancel && (
              <button
                onClick={onCancel}
                disabled={isCancelling}
                className="flex items-center space-x-1 px-3 py-1 text-xs font-medium text-red-700 bg-red-100 rounded-md hover:bg-red-200 disabled:opacity-50"
              >
                {isCancelling ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <Square className="h-3 w-3" />
                )}
                <span>Cancelar</span>
              </button>
            )}

            {canRun && (
              <button
                onClick={onRun}
                disabled={isRunning}
                className="flex items-center space-x-1 px-3 py-1 text-xs font-medium text-green-700 bg-green-100 rounded-md hover:bg-green-200 disabled:opacity-50"
              >
                {isRunning ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <Play className="h-3 w-3" />
                )}
                <span>Ejecutar</span>
              </button>
            )}

            <button
              onClick={onDelete}
              disabled={isDeleting || job.status === 'running'}
              className="flex items-center space-x-1 px-3 py-1 text-xs font-medium text-red-700 bg-red-100 rounded-md hover:bg-red-200 disabled:opacity-50"
            >
              {isDeleting ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <Trash2 className="h-3 w-3" />
              )}
              <span>Eliminar</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}