const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

const handleResponse = async (response: Response) => {
  const data = await response.json();
  
  if (!response.ok) {
    const error = new Error(data.detail || 'API Error') as any;
    error.response = { data, status: response.status };
    throw error;
  }
  
  return data;
};

export const api = {
  get: async (endpoint: string) => {
    const token = localStorage.getItem('access_token');
    const headers: any = {};
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
    
    const response = await fetch(`${API_URL}${endpoint}`, { headers });
    return handleResponse(response);
  },
  post: async (endpoint: string, data: any) => {
    const token = localStorage.getItem('access_token');
    const headers: any = { 'Content-Type': 'application/json' };
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
    
    const response = await fetch(`${API_URL}${endpoint}`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },
  put: async (endpoint: string, data: any) => {
    const token = localStorage.getItem('access_token');
    const headers: any = { 'Content-Type': 'application/json' };
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
    
    const response = await fetch(`${API_URL}${endpoint}`, {
      method: 'PUT',
      headers,
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },
  delete: async (endpoint: string) => {
    const token = localStorage.getItem('access_token');
    const headers: any = {};
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
    
    const response = await fetch(`${API_URL}${endpoint}`, {
      method: 'DELETE',
      headers,
    });
    return handleResponse(response);
  },
};

export const authApi = {
  login: (credentials: any) => api.post('/auth/login', credentials),
  register: (userData: any) => api.post('/auth/register', userData),
  logout: () => api.post('/auth/logout', {}),
  me: () => api.get('/auth/me'),
};

// Helper function to clean undefined parameters
const cleanParams = (params: any) => {
  if (!params) return {};
  const cleaned: any = {};
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      cleaned[key] = value;
    }
  }
  return cleaned;
};

export const propertiesApi = {
  list: (params?: any) => {
    const cleanedParams = cleanParams(params);
    const queryString = Object.keys(cleanedParams).length > 0 ? '?' + new URLSearchParams(cleanedParams).toString() : '';
    return api.get(`/api/properties${queryString}`);
  },
  getAll: (params?: any) => {
    const cleanedParams = cleanParams(params);
    const queryString = Object.keys(cleanedParams).length > 0 ? '?' + new URLSearchParams(cleanedParams).toString() : '';
    return api.get(`/api/properties${queryString}`);
  },
  getById: (id: number) => api.get(`/api/properties/${id}`),
  search: (params: any) => {
    const cleanedParams = cleanParams(params);
    return api.get(`/api/properties/search?${new URLSearchParams(cleanedParams).toString()}`);
  },
};

export const jobsApi = {
  list: (params?: any) => {
    const cleanedParams = cleanParams(params);
    const queryString = Object.keys(cleanedParams).length > 0 ? '?' + new URLSearchParams(cleanedParams).toString() : '';
    return api.get(`/api/jobs${queryString}`);
  },
  getAll: (params?: any) => {
    const cleanedParams = cleanParams(params);
    const queryString = Object.keys(cleanedParams).length > 0 ? '?' + new URLSearchParams(cleanedParams).toString() : '';
    return api.get(`/api/jobs${queryString}`);
  },
  getById: (id: number) => api.get(`/api/jobs/${id}`),
  create: (data: any) => api.post('/api/jobs', data),
  update: (id: number, data: any) => api.put(`/api/jobs/${id}`, data),
  delete: (id: number) => api.delete(`/api/jobs/${id}`),
  run: (id: number) => api.post(`/api/jobs/${id}/run`, {}),
  cancel: (id: number) => api.post(`/api/jobs/${id}/cancel`, {}),
  getResults: (id: number) => api.get(`/api/jobs/${id}/results`),
};

export const adminApi = {
  getUsers: () => api.get('/api/admin/users'),
  getSystemStats: () => api.get('/api/admin/stats'),
  deleteUser: (id: number) => api.delete(`/api/admin/users/${id}`),
};

export const analyticsApi = {
  getOverview: () => api.get('/api/analytics/dashboard'),
  getDashboard: () => api.get('/api/analytics/dashboard'),
  getPriceHistory: (params?: any) => api.get(`/api/analytics/price-history${params ? '?' + new URLSearchParams(params).toString() : ''}`),
  getLocationStats: () => api.get('/api/analytics/locations'),
};

export const exportApi = {
  exportData: (format: string, data: any) => api.post(`/api/export/${format}`, data),
};

export const municipiosApi = {
  list: (params?: { limit?: number; search?: string }) => {
    const cleanedParams = cleanParams(params);
    const queryString = Object.keys(cleanedParams).length > 0 ? '?' + new URLSearchParams(cleanedParams).toString() : '';
    return api.get(`/api/municipios${queryString}`);
  },
  validateUrls: (urls: string[]) => api.post('/api/jobs/validate-urls', urls),
};