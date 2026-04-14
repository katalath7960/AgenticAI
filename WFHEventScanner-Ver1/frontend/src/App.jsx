import { Routes, Route, Navigate } from 'react-router-dom'
import { Container } from 'react-bootstrap'
import Navbar from './components/Navbar.jsx'
import Scanner from './components/Scanner.jsx'
import ScanLog from './components/ScanLog.jsx'
import StatsPage from './pages/StatsPage.jsx'

export default function App() {
  return (
    <>
      <Navbar />
      <Container className="py-4">
        <Routes>
          <Route path="/" element={<Scanner />} />
          <Route path="/log" element={<ScanLog />} />
          <Route path="/stats" element={<StatsPage />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Container>
    </>
  )
}

function NotFound() {
  return (
    <div className="text-center py-5">
      <h1 className="display-1">404</h1>
      <p className="lead">Page not found.</p>
      <a href="/">Back to scanner</a>
    </div>
  )
}
