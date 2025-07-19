'use client'

import { useQuery } from '@tanstack/react-query'
import { jobsApi } from '@/lib/api'
import { X, Loader2, Clock, CheckCircle, AlertCircle, Square, Globe, Calendar } from 'lucide-react'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'

interface JobDetailsModalProps {
  jobId: number
  isOpen: boolean
  onClose: () => void
}

export function JobDetailsModal({ jobId, isOpen, onClose }: JobDetailsModalProps) {
  const { data: job, isLoading } = useQuery({
    queryKey: ['job', jobId],
    queryFn: () => jobsApi.get(jobId),
    enabled: isOpen,
  })

  const { data: jobStatus } = useQuery({
    queryKey: ['job-status', jobId],
    queryFn: () => jobsApi.getStatus(jobId),
    enabled: isOpen,
    refetchInterval: 3000, // Refetch every 3 seconds
  })

  const { data: executions } = useQuery({
    queryKey: ['job-executions', jobId],
    queryFn: () => jobsApi.getExecutions(jobId),
    enabled: isOpen,
    refetchInterval: 5000, // Refetch every 5 seconds
  })

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-red-600" />
      case 'cancelled':
        return <Square className="h-4 w-4 text-gray-600" />
      default:
        return <Clock className="h-4 w-4 text-yellow-600" />
    }
  }

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

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={onClose} />

        <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full sm:p-6">
          <div className="absolute top-0 right-0 pt-4 pr-4">
            <button
              onClick={onClose}
              className="bg-white rounded-md text-gray-400 hover:text-gray-600"
            >
              <X className="h-6 w-6" />
            </button>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
            </div>
          ) : job ? (
            <div className="space-y-6">
              {/* Header */}
              <div>
                <h3 className="text-lg leading-6 font-medium text-gray-900 mb-2">
                  {job.job_name}
                </h3>
                <div className="flex items-center space-x-4">
                  <div className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(jobStatus?.status || job.status)}`}>
                    {getStatusIcon(jobStatus?.status || job.status)}
                    <span className="capitalize">{jobStatus?.status || job.status}</span>
                  </div>
                  <span className="text-sm text-gray-600">
                    Spider: {job.spider_name}
                  </span>
                </div>
              </div>

              {/* Job Information */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Basic Info */}
                <div className="space-y-4">
                  <h4 className="text-md font-medium text-gray-900">Información General</h4>
                  
                  <div className="space-y-3">
                    <div className="flex items-center text-sm">
                      <Calendar className="h-4 w-4 mr-2 text-gray-400" />
                      <span className="text-gray-600">Programación:</span>
                      <span className="ml-2 capitalize">{job.schedule_type}</span>
                    </div>

                    {job.cron_expression && (
                      <div className="flex items-center text-sm">
                        <Clock className="h-4 w-4 mr-2 text-gray-400" />
                        <span className="text-gray-600">Cron:</span>
                        <span className="ml-2 font-mono text-xs">{job.cron_expression}</span>
                      </div>
                    )}

                    <div className="text-sm">
                      <span className="text-gray-600">Creado:</span>
                      <span className="ml-2">
                        {format(new Date(job.created_at), 'dd/MM/yyyy HH:mm', { locale: es })}
                      </span>
                    </div>

                    <div className="text-sm">
                      <span className="text-gray-600">Actualizado:</span>
                      <span className="ml-2">
                        {format(new Date(job.updated_at), 'dd/MM/yyyy HH:mm', { locale: es })}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Current Status */}
                <div className="space-y-4">
                  <h4 className="text-md font-medium text-gray-900">Estado Actual</h4>
                  
                  {jobStatus?.latest_execution && (
                    <div className="space-y-3">
                      <div className="text-sm">
                        <span className="text-gray-600">Elementos encontrados:</span>
                        <span className="ml-2 font-medium">
                          {jobStatus.latest_execution.items_scraped || 0}
                        </span>
                      </div>

                      {jobStatus.latest_execution.started_at && (
                        <div className="text-sm">
                          <span className="text-gray-600">Iniciado:</span>
                          <span className="ml-2">
                            {format(new Date(jobStatus.latest_execution.started_at), 'dd/MM/yyyy HH:mm', { locale: es })}
                          </span>
                        </div>
                      )}

                      {jobStatus.latest_execution.completed_at && (
                        <div className="text-sm">
                          <span className="text-gray-600">Completado:</span>
                          <span className="ml-2">
                            {format(new Date(jobStatus.latest_execution.completed_at), 'dd/MM/yyyy HH:mm', { locale: es })}
                          </span>
                        </div>
                      )}

                      {jobStatus.latest_execution.error_message && (
                        <div className="text-sm">
                          <span className="text-gray-600">Error:</span>
                          <p className="mt-1 text-red-600 text-xs bg-red-50 p-2 rounded">
                            {jobStatus.latest_execution.error_message}
                          </p>
                        </div>
                      )}
                    </div>
                  )}

                  {jobStatus?.celery_status && (
                    <div className="text-xs text-gray-500 bg-gray-50 p-2 rounded">
                      <div>Celery State: {jobStatus.celery_status.state}</div>
                      {jobStatus.celery_status.info && Object.keys(jobStatus.celery_status.info).length > 0 && (
                        <pre className="mt-1 whitespace-pre-wrap">
                          {JSON.stringify(jobStatus.celery_status.info, null, 2)}
                        </pre>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* URLs */}
              <div>
                <h4 className="text-md font-medium text-gray-900 mb-3">URLs de Inicio</h4>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {job.start_urls.map((url, index) => (
                    <div key={index} className="flex items-start space-x-2 text-sm">
                      <Globe className="h-4 w-4 mt-0.5 text-gray-400 flex-shrink-0" />
                      <a
                        href={url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800 break-all"
                      >
                        {url}
                      </a>
                    </div>
                  ))}
                </div>
              </div>

              {/* Job Config */}
              {job.job_config && Object.keys(job.job_config).length > 0 && (
                <div>
                  <h4 className="text-md font-medium text-gray-900 mb-3">Configuración</h4>
                  <pre className="text-xs bg-gray-50 p-3 rounded overflow-x-auto">
                    {JSON.stringify(job.job_config, null, 2)}
                  </pre>
                </div>
              )}

              {/* Execution History */}
              {executions && executions.length > 0 && (
                <div>
                  <h4 className="text-md font-medium text-gray-900 mb-3">Historial de Ejecuciones</h4>
                  <div className="space-y-3 max-h-60 overflow-y-auto">
                    {executions.map((execution) => (
                      <div
                        key={execution.execution_id}
                        className="border border-gray-200 rounded-lg p-3"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center space-x-2">
                            {getStatusIcon(execution.status)}
                            <span className="text-sm font-medium capitalize">
                              {execution.status}
                            </span>
                          </div>
                          <span className="text-xs text-gray-500">
                            ID: {execution.execution_id}
                          </span>
                        </div>
                        
                        <div className="text-xs text-gray-600 space-y-1">
                          <div>
                            Iniciado: {format(new Date(execution.started_at), 'dd/MM/yyyy HH:mm', { locale: es })}
                          </div>
                          {execution.completed_at && (
                            <div>
                              Completado: {format(new Date(execution.completed_at), 'dd/MM/yyyy HH:mm', { locale: es })}
                            </div>
                          )}
                          <div>
                            Elementos: {execution.items_scraped}
                          </div>
                          {execution.error_message && (
                            <div className="text-red-600 mt-1">
                              Error: {execution.error_message}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-12">
              <p className="text-red-600">Error al cargar los detalles del trabajo</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}