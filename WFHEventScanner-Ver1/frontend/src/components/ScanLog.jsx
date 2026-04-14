import { useEffect, useState } from 'react'
import { Table, Button, Badge } from 'react-bootstrap'
import { getScans } from '../api.js'

const POLL_MS = 5000

export default function ScanLog() {
  const [rows, setRows] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    let timer
    const load = async () => {
      try { setRows(await getScans(100)) } catch (e) { setError(e.message) }
    }
    load()
    timer = setInterval(load, POLL_MS)
    return () => clearInterval(timer)
  }, [])

  const exportCsv = () => {
    const header = 'time,name,color,staff,duplicate\n'
    const body = rows.map((r) =>
      `${r.scanned_at},${r.name},${r.color},${r.scanned_by},${r.is_duplicate}`
    ).join('\n')
    const blob = new Blob([header + body], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = 'scan_log.csv'; a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h2 className="mb-0">Scan log</h2>
        <Button variant="outline-primary" size="sm" onClick={exportCsv}>Export CSV</Button>
      </div>
      {error && <div className="text-danger">Failed to load: {error}</div>}
      <Table striped hover responsive size="sm">
        <thead>
          <tr><th>Time</th><th>Name</th><th>Color</th><th>Staff</th><th>Flags</th></tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id}>
              <td>{new Date(r.scanned_at).toLocaleTimeString()}</td>
              <td>{r.name}</td>
              <td><span className="color-swatch" style={{ backgroundColor: r.color?.toLowerCase() }} />{r.color}</td>
              <td>{r.scanned_by}</td>
              <td>{r.is_duplicate && <Badge bg="warning" text="dark">dup</Badge>}</td>
            </tr>
          ))}
          {rows.length === 0 && (
            <tr><td colSpan={5} className="text-center text-muted">no scans yet</td></tr>
          )}
        </tbody>
      </Table>
    </div>
  )
}
