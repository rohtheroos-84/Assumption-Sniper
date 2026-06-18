import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import RunProgress from './RunProgress'

const subscribeToRunEvents = vi.fn(() => () => {})

vi.mock('../context/RunContext', () => ({
  useRun: () => ({
    currentRun: {
      id: 'run-42',
      status: 'running',
      events: [{ message: 'decomposition started' }],
    },
    subscribeToRunEvents,
  }),
}))

describe('RunProgress', () => {
  it('renders active run status and events', () => {
    render(<RunProgress />)
    expect(screen.getByText(/Run: run-42/)).toBeInTheDocument()
    expect(screen.getByText(/status: running/)).toBeInTheDocument()
    expect(screen.getByText('decomposition started')).toBeInTheDocument()
  })
})
