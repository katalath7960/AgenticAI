import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const api = axios.create({ baseURL, timeout: 8000 })

export const postScan = (payload, scannedBy = 'staff') =>
  api.post('/api/scan', { payload, scanned_by: scannedBy }).then((r) => r.data)

export const getStats = () => api.get('/api/stats').then((r) => r.data)
export const getScans = (limit = 50) =>
  api.get('/api/scans', { params: { limit } }).then((r) => r.data)
