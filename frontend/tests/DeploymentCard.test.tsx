import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import DeploymentCard from '../src/components/ui/DeploymentCard'
import type { Deployment } from '../src/lib/api'

const baseDeployment: Deployment = {
  id: 'dep-1',
  user_id: 1,
  app_name: 'myapp',
  repo_url: 'https://github.com/user/myapp',
  branch: 'main',
  status: 'running',
  created_at: '2025-01-15T10:00:00Z',
  updated_at: '2025-01-15T10:05:00Z',
}

describe('DeploymentCard', () => {
  it('renders app name and repo', () => {
    render(<DeploymentCard deployment={baseDeployment} />)
    expect(screen.getByText('myapp')).toBeDefined()
    expect(screen.getByText(/user\/myapp/)).toBeDefined()
  })

  it('shows running status', () => {
    render(<DeploymentCard deployment={baseDeployment} />)
    expect(screen.getByText('RUNNING')).toBeDefined()
  })

  it('shows blocked status with error message', () => {
    const blocked = { ...baseDeployment, status: 'blocked' as const, error_message: 'Security policy violation' }
    render(<DeploymentCard deployment={blocked} />)
    expect(screen.getByText('BLOCKED')).toBeDefined()
    expect(screen.getByText('Blocked by Security Scanner')).toBeDefined()
    expect(screen.getByText('Security policy violation')).toBeDefined()
  })

  it('shows stop button for running deployment', () => {
    const onStop = vi.fn()
    render(<DeploymentCard deployment={baseDeployment} onStop={onStop} />)
    const btn = screen.getByText('Stop')
    fireEvent.click(btn)
    expect(onStop).toHaveBeenCalledWith('dep-1')
  })

  it('shows start button for stopped deployment', () => {
    const onStart = vi.fn()
    const stopped = { ...baseDeployment, status: 'stopped' as const }
    render(<DeploymentCard deployment={stopped} onStart={onStart} />)
    const btn = screen.getByText('Start')
    fireEvent.click(btn)
    expect(onStart).toHaveBeenCalledWith('dep-1')
  })

  it('shows host_port URL when present', () => {
    const withPort = { ...baseDeployment, host_port: 3000 }
    render(<DeploymentCard deployment={withPort} />)
    expect(screen.getByText('localhost:3000')).toBeDefined()
  })

  it('calls onDelete when delete button clicked', () => {
    const onDelete = vi.fn()
    render(<DeploymentCard deployment={baseDeployment} onDelete={onDelete} />)
    const btn = screen.getByText('Delete')
    fireEvent.click(btn)
    expect(onDelete).toHaveBeenCalledWith('dep-1')
  })
})
