'use client'

import { useState, useEffect, useCallback } from 'react'
import { useForm } from 'react-hook-form'
import { CrawlJobCreate, MunicipioSelect, URLValidationResult } from '@/types'
import { municipiosApi } from '@/lib/api'
import { SearchableDropdown } from '@/components/ui/searchable-dropdown'
import { X, Plus, AlertTriangle, CheckCircle, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'

interface CreateJobModalProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (data: CrawlJobCreate) => void
  isLoading?: boolean
}

const SPIDER_OPTIONS = [
  { value: 'propiedades', label: 'Propiedades (Idealista)' },
]

const SCHEDULE_OPTIONS = [
  { value: 'manual', label: 'Manual' },
  { value: 'daily', label: 'Diario' },
  { value: 'weekly', label: 'Semanal' },
  { value: 'monthly', label: 'Mensual' },
]

export function CreateJobModal({ isOpen, onClose, onSubmit, isLoading }: CreateJobModalProps) {
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [municipios, setMunicipios] = useState<MunicipioSelect[]>([])
  const [selectedUrls, setSelectedUrls] = useState<string[]>([])
  const [municipiosLoading, setMunicipiosLoading] = useState(false)
  const [validationResult, setValidationResult] = useState<URLValidationResult | null>(null)
  const [validationLoading, setValidationLoading] = useState(false)

  const form = useForm<CrawlJobCreate>({
    defaultValues: {
      job_name: '',
      spider_name: 'propiedades',
      start_urls: [],
      schedule_type: 'manual',
      job_config: {}
    }
  })

  // Load municipios on component mount
  useEffect(() => {
    if (isOpen) {
      loadMunicipios()
    }
  }, [isOpen])

  // Update form when selected URLs change
  useEffect(() => {
    form.setValue('start_urls', selectedUrls)
    
    // Validate URLs when they change
    if (selectedUrls.length > 0) {
      validateUrls(selectedUrls)
    } else {
      setValidationResult(null)
    }
  }, [selectedUrls, form])

  const loadMunicipios = async (search?: string) => {
    try {
      setMunicipiosLoading(true)
      const data = await municipiosApi.list({ limit: 1000, search })
      setMunicipios(data)
    } catch (error) {
      console.error('Error loading municipios:', error)
      toast.error('Error cargando municipios')
    } finally {
      setMunicipiosLoading(false)
    }
  }

  const validateUrls = async (urls: string[]) => {
    if (urls.length === 0) {
      setValidationResult(null)
      return
    }

    try {
      setValidationLoading(true)
      const result = await municipiosApi.validateUrls(urls)
      setValidationResult(result)
    } catch (error) {
      console.error('Error validating URLs:', error)
      toast.error('Error validando URLs')
    } finally {
      setValidationLoading(false)
    }
  }

  const handleSearch = useCallback((query: string) => {
    loadMunicipios(query)
  }, [])

  const onFormSubmit = (data: CrawlJobCreate) => {
    // Ensure we have URLs selected
    if (selectedUrls.length === 0) {
      toast.error('Selecciona al menos un municipio')
      return
    }

    // Check validation result
    if (validationResult && !validationResult.valid) {
      toast.error('Algunas URLs no son válidas. Revisa la selección.')
      return
    }

    const submitData = {
      ...data,
      start_urls: selectedUrls
    }
    onSubmit(submitData)
  }

  const handleClose = () => {
    // Reset all state when closing
    setSelectedUrls([])
    setValidationResult(null)
    setShowAdvanced(false)
    form.reset()
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={onClose} />

        <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full sm:p-6">
          <div className="absolute top-0 right-0 pt-4 pr-4">
            <button
              onClick={handleClose}
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

                {/* Municipios Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Municipios *
                  </label>
                  <SearchableDropdown
                    options={municipios.map(m => ({
                      id: m.id,
                      value: m.url,
                      label: m.municipality_name,
                      subtitle: m.url
                    }))}
                    value={selectedUrls}
                    onChange={setSelectedUrls}
                    placeholder="Selecciona municipios..."
                    searchPlaceholder="Buscar municipios..."
                    multiple={true}
                    loading={municipiosLoading}
                    onSearch={handleSearch}
                    error={form.formState.errors.start_urls?.message}
                  />
                  
                  {/* URL Validation Results */}
                  {validationLoading && (
                    <div className="mt-2 flex items-center space-x-2 text-sm text-gray-600">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Validando URLs...</span>
                    </div>
                  )}
                  
                  {validationResult && (
                    <div className="mt-2 space-y-2">
                      {validationResult.valid ? (
                        <div className="flex items-center space-x-2 text-sm text-green-600">
                          <CheckCircle className="h-4 w-4" />
                          <span>
                            {validationResult.valid_count} URLs válidas de {validationResult.total_urls}
                          </span>
                        </div>
                      ) : (
                        <div className="space-y-1">
                          <div className="flex items-center space-x-2 text-sm text-red-600">
                            <AlertTriangle className="h-4 w-4" />
                            <span>
                              {validationResult.invalid_count} URLs inválidas de {validationResult.total_urls}
                            </span>
                          </div>
                          {validationResult.invalid_urls.length > 0 && (
                            <div className="ml-6">
                              <p className="text-xs text-gray-500 mb-1">URLs inválidas:</p>
                              <ul className="text-xs text-red-600 space-y-0.5">
                                {validationResult.invalid_urls.slice(0, 3).map((url, idx) => (
                                  <li key={idx} className="truncate" title={url}>
                                    • {url}
                                  </li>
                                ))}
                                {validationResult.invalid_urls.length > 3 && (
                                  <li className="text-gray-500">
                                    ... y {validationResult.invalid_urls.length - 3} más
                                  </li>
                                )}
                              </ul>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                  
                  <p className="mt-1 text-xs text-gray-500">
                    Selecciona los municipios donde quieres buscar propiedades. 
                    Las URLs se validan automáticamente.
                  </p>
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
                    onClick={handleClose}
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