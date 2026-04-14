import { Navbar as RBNavbar, Nav, Container, Button } from 'react-bootstrap'
import { NavLink } from 'react-router-dom'
import { useState } from 'react'

const EVENT_NAME = import.meta.env.VITE_EVENT_NAME || 'WFH Event'

export default function Navbar() {
  const [dark, setDark] = useState(false)
  const toggle = () => {
    const next = !dark
    setDark(next)
    document.documentElement.setAttribute('data-bs-theme', next ? 'dark' : 'light')
  }
  return (
    <RBNavbar bg={dark ? 'dark' : 'primary'} variant="dark" expand="md" sticky="top">
      <Container>
        <RBNavbar.Brand as={NavLink} to="/">{EVENT_NAME}</RBNavbar.Brand>
        <RBNavbar.Toggle />
        <RBNavbar.Collapse>
          <Nav className="me-auto">
            <Nav.Link as={NavLink} to="/" end>Scanner</Nav.Link>
            <Nav.Link as={NavLink} to="/log">Log</Nav.Link>
            <Nav.Link as={NavLink} to="/stats">Stats</Nav.Link>
          </Nav>
          <Button size="sm" variant="outline-light" onClick={toggle}>
            {dark ? 'Light' : 'Dark'}
          </Button>
        </RBNavbar.Collapse>
      </Container>
    </RBNavbar>
  )
}
