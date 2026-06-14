import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import StatusBadge from '../src/components/ui/StatusBadge'

describe('StatusBadge', () => {
  it('renders running status', () => {
    render(<StatusBadge status="running" />)
    expect(screen.getByText('Running')).toBeDefined()
  })

  it('renders failed status', () => {
    render(<StatusBadge status="failed" />)
    expect(screen.getByText('Failed')).toBeDefined()
  })

  it('renders building with animate class', () => {
    const { container } = render(<StatusBadge status="building" />)
    expect(screen.getByText('Building')).toBeDefined()
    expect(container.querySelector('.animate-ping')).toBeDefined()
  })

  it('renders stopped status', () => {
    render(<StatusBadge status="stopped" />)
    expect(screen.getByText('Stopped')).toBeDefined()
  })

  it('renders blocked status', () => {
    render(<StatusBadge status="blocked" />)
    expect(screen.getByText('Blocked')).toBeDefined()
  })

  it('falls back to status text for unknown status', () => {
    render(<StatusBadge status="unknown" />)
    expect(screen.getByText('unknown')).toBeDefined()
  })
})
