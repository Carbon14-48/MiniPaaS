import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import OverviewCards from '../src/components/monitoring/OverviewCards'

describe('OverviewCards', () => {
  it('shows loading skeletons when loading', () => {
    const { container } = render(<OverviewCards apps={[]} loading={true} />)
    const skeletons = container.querySelectorAll('.skeleton')
    expect(skeletons.length).toBeGreaterThan(0)
  })

  it('displays zero state with empty apps', () => {
    render(<OverviewCards apps={[]} loading={false} />)
    expect(screen.getByText('Active Apps')).toBeDefined()
    expect(screen.getByText('Avg CPU')).toBeDefined()
    expect(screen.getByText('Avg RAM')).toBeDefined()
    expect(screen.getByText('Alerts')).toBeDefined()
  })

  it('computes average CPU correctly', () => {
    const apps = [
      { status: 'running', cpu_percent: 50, memory_percent: 30 },
      { status: 'running', cpu_percent: 70, memory_percent: 40 },
    ]
    render(<OverviewCards apps={apps} loading={false} />)
    expect(screen.getByText('60.0%')).toBeDefined()
  })

  it('computes average RAM correctly', () => {
    const apps = [
      { status: 'running', cpu_percent: 10, memory_percent: 20 },
      { status: 'running', cpu_percent: 10, memory_percent: 60 },
    ]
    render(<OverviewCards apps={apps} loading={false} />)
    expect(screen.getByText('40.0%')).toBeDefined()
  })

  it('shows running app count', () => {
    const apps = [
      { status: 'running', cpu_percent: 10, memory_percent: 20 },
      { status: 'stopped', cpu_percent: 0, memory_percent: 0 },
      { status: 'running', cpu_percent: 30, memory_percent: 40 },
    ]
    render(<OverviewCards apps={apps} loading={false} />)
    expect(screen.getByText('2')).toBeDefined()
  })

  it('shows alert count for high CPU or RAM', () => {
    const apps = [
      { status: 'running', cpu_percent: 90, memory_percent: 20 },
      { status: 'running', cpu_percent: 10, memory_percent: 85 },
      { status: 'running', cpu_percent: 10, memory_percent: 10 },
    ]
    render(<OverviewCards apps={apps} loading={false} />)
    expect(screen.getByText('2')).toBeDefined()
  })
})
