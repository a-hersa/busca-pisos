'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { jobsApi } from '@/lib/api'
import { CrawlJob, CrawlJobCreate } from '@/types'
import { JobCard } from '../jobs/job-card'
import { CreateJobModal } from '../jobs/create-job-modal'
import { JobDetailsModal } from '../jobs/job-details-modal'
import { Plus, Loader2, RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'

export function JobsTab() {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null)
  const queryClient = useQueryClient()

  const { data: jobs, isLoading, error, refetch } = useQuery({
    queryKey: ['jobs'],
    queryFn: jobsApi.list,
    refetchInterval: 5000, // Refetch every 5 seconds for real-time updates
  })

  const createJobMutation = useMutation({
    mutationFn: (data: CrawlJobCreate) => jobsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
      setIsCreateModalOpen(false)
      toast.success('Trabajo creado exitosamente')
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Error al crear el trabajo'
      toast.error(message)
    },
  })

  const deleteJobMutation = useMutation({
    mutationFn: (jobId: number) => jobsApi.delete(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
      toast.success('Trabajo eliminado')
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Error al eliminar el trabajo'
      toast.error(message)
    },
  })

  const runJobMutation = useMutation({
    mutationFn: (jobId: number) => jobsApi.run(jobId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
      toast.success(`Trabajo iniciado (Task ID: ${data.task_id})`)
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Error al ejecutar el trabajo'
      toast.error(message)
    },
  })

  const cancelJobMutation = useMutation({
    mutationFn: (jobId: number) => jobsApi.cancel(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
      toast.success('Trabajo cancelado')
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Error al cancelar el trabajo'
      toast.error(message)
    },
  })

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">Error al cargar los trabajos</p>
        <button
          onClick={() => refetch()}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Reintentar
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Trabajos de Crawling</h2>
          <p className="mt-1 text-sm text-gray-600">
            Gestiona y monitorea tus trabajos de scraping de propiedades
          </p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={() => refetch()}
            disabled={isLoading}
            className="flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Actualizar</span>
          </button>
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="flex items-center space-x-2 px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
          >
            <Plus className="h-4 w-4" />
            <span>Nuevo Trabajo</span>
          </button>
        </div>
      </div>

      {/* Jobs Grid */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
        </div>
      ) : jobs && jobs.length > 0 ? (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {jobs.map((job) => (
            <JobCard
              key={job.job_id}
              job={job}
              onView={() => setSelectedJobId(job.job_id)}
              onRun={() => runJobMutation.mutate(job.job_id)}
              onCancel={() => cancelJobMutation.mutate(job.job_id)}
              onDelete={() => {
                if (confirm('¿Estás seguro de que quieres eliminar este trabajo?')) {
                  deleteJobMutation.mutate(job.job_id)
                }
              }}
              isRunning={runJobMutation.isPending}
              isCancelling={cancelJobMutation.isPending}
              isDeleting={deleteJobMutation.isPending}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <div className="mx-auto h-12 w-12 text-gray-400">
            <Briefcase className="h-12 w-12" />
          </div>
          <h3 className="mt-2 text-sm font-medium text-gray-900">
            No hay trabajos
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            Comienza creando tu primer trabajo de crawling.
          </p>
          <div className="mt-6">
            <button
              onClick={() => setIsCreateModalOpen(true)}
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              <Plus className="h-4 w-4 mr-2" />
              Nuevo Trabajo
            </button>
          </div>
        </div>
      )}

      {/* Modals */}
      <CreateJobModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSubmit={(data) => createJobMutation.mutate(data)}
        isLoading={createJobMutation.isPending}
      />

      {selectedJobId && (
        <JobDetailsModal
          jobId={selectedJobId}
          isOpen={true}
          onClose={() => setSelectedJobId(null)}
        />
      )}
    </div>
  )
}