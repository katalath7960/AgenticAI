import { useEffect, useRef, useState } from 'react'
import { Html5QrcodeScanner } from 'html5-qrcode'
import { Button, Alert, Spinner } from 'react-bootstrap'
import AttendeeCard from './AttendeeCard.jsx'
import { postScan } from '../api.js'

const SCAN_COOLDOWN_MS = 2000

export default function Scanner() {
  const [active, setActive] = useState(true)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const scannerRef = useRef(null)
  const cooldownRef = useRef(0)

  useEffect(() => {
    if (!active) return
    const el = document.getElementById('qr-viewport')
    if (!el) return
    const scanner = new Html5QrcodeScanner(
      'qr-viewport',
      {
        fps: 10,
        qrbox: { width: 260, height: 260 },
        rememberLastUsedCamera: true,
        videoConstraints: { facingMode: 'environment' },
      },
      false
    )
    scannerRef.current = scanner

    const onSuccess = async (decodedText) => {
      const now = Date.now()
      if (now < cooldownRef.current) return
      cooldownRef.current = now + SCAN_COOLDOWN_MS
      setLoading(true); setError(null)
      try {
        const data = await postScan(decodedText)
        setResult(data)
      } catch (e) {
        setError(e.response?.data?.error || e.message)
        setResult(null)
      } finally {
        setLoading(false)
      }
    }
    scanner.render(onSuccess, () => {})
    return () => { scanner.clear().catch(() => {}) }
  }, [active])

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h2 className="mb-0">Scan entry pass</h2>
        <Button variant={active ? 'outline-danger' : 'outline-success'} onClick={() => setActive(!active)}>
          {active ? 'Stop camera' : 'Start camera'}
        </Button>
      </div>
      <div className="scanner-viewport mb-3">
        {active && <div id="qr-viewport" />}
      </div>
      {loading && <div className="text-center my-3"><Spinner size="sm" /> checking in…</div>}
      {error && <Alert variant="danger" onClose={() => setError(null)} dismissible>{error}</Alert>}
      {result && <AttendeeCard result={result} onDismiss={() => setResult(null)} />}
    </div>
  )
}
