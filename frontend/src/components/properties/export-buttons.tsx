'use client'

import { exportApi } from '@/lib/api'
import { Download, FileSpreadsheet, FileText } from 'lucide-react'
import { useAuth } from '@/hooks/use-auth'

interface ExportButtonsProps {
  filters?: {
    poblacion?: string
    min_precio?: string
    max_precio?: string
  }
}

export function ExportButtons({ filters }: ExportButtonsProps) {
  const { user } = useAuth()

  const handleExport = (url: string, filename: string) => {
    // Create a temporary link and click it to download
    const token = localStorage.getItem('access_token')
    const link = document.createElement('a')
    link.href = `${url}&token=${token}`
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const exportCSV = () => {
    const url = exportApi.exportPropertiesCSV(filters)
    handleExport(url, `propiedades_${new Date().toISOString().split('T')[0]}.csv`)
  }

  const exportExcel = () => {
    const url = exportApi.exportPropertiesExcel(filters)
    handleExport(url, `propiedades_${new Date().toISOString().split('T')[0]}.xlsx`)
  }

  const exportJobs = () => {
    const url = exportApi.exportJobsCSV()
    handleExport(url, `trabajos_${new Date().toISOString().split('T')[0]}.csv`)
  }

  const exportAnalytics = () => {
    const url = exportApi.exportAnalyticsJSON()
    handleExport(url, `analytics_${new Date().toISOString().split('T')[0]}.json`)
  }

  if (!user) return null

  return (
    <div className="flex flex-wrap gap-2">
      <button
        onClick={exportCSV}
        className="flex items-center space-x-1 px-3 py-2 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
      >
        <FileText className="h-4 w-4" />
        <span>CSV</span>
      </button>

      <button
        onClick={exportExcel}
        className="flex items-center space-x-1 px-3 py-2 text-sm bg-green-100 text-green-700 rounded-md hover:bg-green-200"
      >
        <FileSpreadsheet className="h-4 w-4" />
        <span>Excel</span>
      </button>

      <button
        onClick={exportJobs}
        className="flex items-center space-x-1 px-3 py-2 text-sm bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200"
      >
        <Download className="h-4 w-4" />
        <span>Trabajos</span>
      </button>

      {user.role === 'admin' && (
        <button
          onClick={exportAnalytics}
          className="flex items-center space-x-1 px-3 py-2 text-sm bg-purple-100 text-purple-700 rounded-md hover:bg-purple-200"
        >
          <Download className="h-4 w-4" />
          <span>Análisis</span>
        </button>
      )}
    </div>
  )
}