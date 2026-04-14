import { useEffect, useState } from 'react'
import { Card, Row, Col, ProgressBar } from 'react-bootstrap'
import { getStats } from '../api.js'

export default function StatsPage() {
  const [s, setS] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    const load = async () => {
      try { setS(await getStats()) } catch (e) { setError(e.message) }
    }
    load()
    const t = setInterval(load, 5000)
    return () => clearInterval(t)
  }, [])

  if (error) return <div className="text-danger">Error: {error}</div>
  if (!s) return <div>Loading…</div>

  const pct = s.total ? Math.round((s.checked_in / s.total) * 100) : 0

  return (
    <div>
      <h2 className="mb-3">Stats</h2>
      <Row className="g-3 mb-4">
        <Col md={3}><Metric title="Total" value={s.total} /></Col>
        <Col md={3}><Metric title="Pending" value={s.pending} /></Col>
        <Col md={3}><Metric title="Sent" value={s.sent} /></Col>
        <Col md={3}><Metric title="Checked in" value={s.checked_in} /></Col>
      </Row>
      <Card>
        <Card.Body>
          <div className="d-flex justify-content-between">
            <strong>Attendance</strong><span>{pct}%</span>
          </div>
          <ProgressBar now={pct} className="mt-2" />
          <small className="text-muted">Scans today: {s.scans_today}</small>
        </Card.Body>
      </Card>
    </div>
  )
}

function Metric({ title, value }) {
  return (
    <Card className="text-center h-100">
      <Card.Body>
        <Card.Subtitle className="text-muted">{title}</Card.Subtitle>
        <Card.Title className="display-5 mt-2">{value}</Card.Title>
      </Card.Body>
    </Card>
  )
}
