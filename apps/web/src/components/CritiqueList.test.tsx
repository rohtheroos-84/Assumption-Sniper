import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import CritiqueList from './CritiqueList'
import * as api from '../lib/api'

vi.mock('../lib/api', () => ({
  fetchCritiques: vi.fn(),
}))

describe('CritiqueList', () => {
  beforeEach(() => {
    vi.mocked(api.fetchCritiques).mockResolvedValue([
      { id: 'c1', summary: 'Ops cost too high', severity: 'high' },
      { id: 'c2', summary: 'Weak differentiation', severity: 'low' },
      { id: 'c3', text: 'Adoption risk in schools', severity: 'medium' },
    ])
  })

  it('loads and renders critiques', async () => {
    render(<CritiqueList runId="run-1" />)
    await waitFor(() => {
      expect(screen.getByText('Ops cost too high')).toBeInTheDocument()
    })
    expect(screen.getByText('Weak differentiation')).toBeInTheDocument()
  })

  it('filters critiques by severity', async () => {
    render(<CritiqueList runId="run-1" />)
    await waitFor(() => expect(screen.getByText('Ops cost too high')).toBeInTheDocument())

    fireEvent.change(screen.getByDisplayValue('All severities'), { target: { value: 'high' } })
    expect(screen.getByText('Ops cost too high')).toBeInTheDocument()
    expect(screen.queryByText('Weak differentiation')).not.toBeInTheDocument()
  })
})
