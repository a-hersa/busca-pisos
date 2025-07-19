'use client'

import { useState } from 'react'
import { useForm, useFieldArray } from 'react-hook-form'
import { CrawlJobCreate } from '@/types'
import { X, Plus, Trash2, Loader2 } from 'lucide-react'

interface CreateJobModalProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (data: CrawlJobCreate) => void
  isLoading?: boolean
}

const SPIDER_OPTIONS = [
  { value: 'propiedades', label: 'Propiedades (Idealista)' },
  { value: 'municipios', label: 'Municipios' },
]

const SCHEDULE_OPTIONS = [
  { value: 'manual', label: 'Manual' },
  { value: 'daily', label: 'Diario' },
  { value: 'weekly', label: 'Semanal' },
  { value: 'monthly', label: 'Mensual' },
]

export function CreateJobModal({ isOpen, onClose, onSubmit, isLoading }: CreateJobModalProps) {
  const [showAdvanced, setShowAdvanced] = useState(false)

  const form = useForm<CrawlJobCreate>({
    defaultValues: {
      job_name: '',
      spider_name: 'propiedades',
      start_urls: [''],
      schedule_type: 'manual',
      job_config: {}
    }
  })

  // @ts-ignore
  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: 'start_urls'
  })

  const onFormSubmit = (data: CrawlJobCreate) => {
    // Filter out empty URLs
    const filteredData = {
      ...data,
      start_urls: data.start_urls.filter(url => url.trim() !== '')
    }
    onSubmit(filteredData)
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={onClose} />

        <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full sm:p-6">
          <div className="absolute top-0 right-0 pt-4 pr-4">
            <button
              onClick={onClose}
              className="bg-white rounded-md text-gray-400 hover:text-gray-600"
            >
              <X className="h-6 w-6" />
            </button>
          </div>

          <div className="sm:flex sm:items-start">
            <div className="w-full">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Crear Nuevo Trabajo de Crawling
              </h3>

              <form onSubmit={form.handleSubmit(onFormSubmit)} className="space-y-6">
                {/* Job Name */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Nombre del Trabajo *
                  </label>
                  <input
                    {...form.register('job_name', { required: 'El nombre es requerido' })}
                    type="text"
                    className="block w-full border border-gray-300 rounded-md px-3 py-2 shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="ej. Crawl Propiedades Barcelona"
                  />
                  {form.formState.errors.job_name && (
                    <p className="mt-1 text-sm text-red-600">
                      {form.formState.errors.job_name.message}
                    </p>
                  )}
                </div>

                {/* Spider Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Spider *
                  </label>
                  <select
                    {...form.register('spider_name', { required: 'Selecciona un spider' })}
                    className="block w-full border border-gray-300 rounded-md px-3 py-2 shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    {SPIDER_OPTIONS.map(option => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Start URLs */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    URLs de Inicio *
                  </label>
                  <div className="space-y-2">
                    {fields.map((field, index) => (
                      <div key={field.id} className="flex space-x-2">
                        <input
                          {...form.register(`start_urls.${index}` as const)}
                          type="url"
                          className="flex-1 border border-gray-300 rounded-md px-3 py-2 shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                          placeholder="https://www.idealista.com/..."
                        />
                        {fields.length > 1 && (
                          <button
                            type="button"
                            onClick={() => remove(index)}
                            className="px-3 py-2 border border-gray-300 rounded-md text-red-600 hover:bg-red-50"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        )}
                      </div>
                    ))}
                    <button
                      type="button"
                      onClick={() => append('')}
                      className="flex items-center space-x-1 text-sm text-blue-600 hover:text-blue-800"
                    >
                      <Plus className="h-4 w-4" />
                      <span>Agregar URL</span>
                    </button>
                  </div>
                </div>

                {/* Schedule Type */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Tipo de Programación
                  </label>
                  <select
                    {...form.register('schedule_type')}
                    className="block w-full border border-gray-300 rounded-md px-3 py-2 shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    {SCHEDULE_OPTIONS.map(option => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Cron Expression */}
                {form.watch('schedule_type') !== 'manual' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Expresión Cron (opcional)
                    </label>
                    <input
                      {...form.register('cron_expression')}
                      type="text"
                      className="block w-full border border-gray-300 rounded-md px-3 py-2 shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      placeholder="0 9 * * * (todos los días a las 9:00)"
                    />
                    <p className="mt-1 text-xs text-gray-500">
                      Deja vacío para usar programación predeterminada
                    </p>
                  </div>
                )}

                {/* Advanced Options */}
                <div>
                  <button
                    type="button"
                    onClick={() => setShowAdvanced(!showAdvanced)}
                    className="text-sm text-blue-600 hover:text-blue-800"
                  >
                    {showAdvanced ? 'Ocultar' : 'Mostrar'} opciones avanzadas
                  </button>

                  {showAdvanced && (
                    <div className="mt-4 p-4 border border-gray-200 rounded-md">
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Configuración JSON (opcional)
                      </label>
                      <textarea
                        {...form.register('job_config')}
                        rows={4}
                        className="block w-full border border-gray-300 rounded-md px-3 py-2 shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        placeholder='{"max_pages": 10, "delay": 2}'
                      />
                      <p className="mt-1 text-xs text-gray-500">
                        Configuración adicional en formato JSON
                      </p>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex justify-end space-x-3 pt-4">
                  <button
                    type="button"
                    onClick={onClose}
                    className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="flex items-center space-x-2 px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                  >
                    {isLoading ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Plus className="h-4 w-4" />
                    )}
                    <span>Crear Trabajo</span>
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}