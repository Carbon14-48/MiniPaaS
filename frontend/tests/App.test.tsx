import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from '../src/App'

describe('App', () => {
  it('renders home page at root', () => {
    render(<App />)
    expect(screen.getByText(/MiniPaaS|mini.?paas/i)).toBeDefined()
  })
})
