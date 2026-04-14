import { useEffect } from 'react'
import { Card, Button, Badge } from 'react-bootstrap'

const AUTO_DISMISS_MS = 5000

export default function AttendeeCard({ result, onDismiss }) {
  useEffect(() => {
    const t = setTimeout(onDismiss, AUTO_DISMISS_MS)
    return () => clearTimeout(t)
  }, [result, onDismiss])

  const a = result.attendee
  const variant = result.duplicate ? 'warning' : 'success'
  const icon = result.duplicate ? '⚠' : '✓'
  const title = result.duplicate ? 'Already checked in' : 'Checked in'

  return (
    <Card bg={variant} text="dark" className="result-card shadow-sm">
      <Card.Body className="text-center">
        <h3>{icon} {title}</h3>
        {a && (
          <>
            <h1 className="display-5 my-2">{a.first_name} {a.last_name}</h1>
            <p className="mb-1">
              <span className="color-swatch" style={{ backgroundColor: a.color?.toLowerCase() }} />
              <strong>Table: {a.color}</strong>
            </p>
            <p className="text-muted mb-3">{a.event_name}</p>
            {result.duplicate && <Badge bg="secondary">duplicate scan</Badge>}
          </>
        )}
        <div className="mt-3">
          <Button variant="dark" onClick={onDismiss}>Next</Button>
        </div>
      </Card.Body>
    </Card>
  )
}
