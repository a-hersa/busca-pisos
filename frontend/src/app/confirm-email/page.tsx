'use client'

import { useEffect, useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { CheckCircle, XCircle, Loader2 } from 'lucide-react'

export default function ConfirmEmailPage() {
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [message, setMessage] = useState('')
  const searchParams = useSearchParams()
  const router = useRouter()
  const token = searchParams.get('token')

  useEffect(() => {
    const confirmEmail = async () => {
      if (!token) {
        setStatus('error')
        setMessage('Token de confirmación no válido')
        return
      }

      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'
        const response = await fetch(`${apiUrl}/auth/confirm-email/${token}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        })

        if (response.ok) {
          const data = await response.json()
          setStatus('success')
          setMessage('Tu email ha sido confirmado exitosamente. Ahora puedes iniciar sesión.')
          
          // Redirect to home page after 3 seconds
          setTimeout(() => {
            router.push('/')
          }, 3000)
        } else {
          const errorData = await response.json()
          setStatus('error')
          setMessage(errorData.detail || 'Error al confirmar el email')
        }
      } catch (error) {
        setStatus('error')
        setMessage('Error de conexión. Por favor, inténtalo de nuevo.')
      }
    }

    confirmEmail()
  }, [token, router])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
            Confirmación de Email
          </h2>
        </div>
        
        <div className="bg-white py-8 px-6 shadow rounded-lg sm:px-10">
          <div className="text-center">
            {status === 'loading' && (
              <div className="space-y-4">
                <Loader2 className="mx-auto h-12 w-12 text-blue-600 animate-spin" />
                <p className="text-gray-600">Confirmando tu email...</p>
              </div>
            )}
            
            {status === 'success' && (
              <div className="space-y-4">
                <CheckCircle className="mx-auto h-12 w-12 text-green-600" />
                <div>
                  <h3 className="text-lg font-medium text-green-800">
                    ¡Email Confirmado!
                  </h3>
                  <p className="text-green-600 mt-2">{message}</p>
                  <p className="text-sm text-gray-500 mt-4">
                    Serás redirigido al login en unos segundos...
                  </p>
                </div>
              </div>
            )}
            
            {status === 'error' && (
              <div className="space-y-4">
                <XCircle className="mx-auto h-12 w-12 text-red-600" />
                <div>
                  <h3 className="text-lg font-medium text-red-800">
                    Error de Confirmación
                  </h3>
                  <p className="text-red-600 mt-2">{message}</p>
                  <div className="mt-6 space-y-3">
                    <button
                      onClick={() => router.push('/')}
                      className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      Ir al Inicio
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}