import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import IdeaInput from './IdeaInput'

const createRun = vi.fn().mockResolvedValue({ id: 'run-1', status: 'queued' })

vi.mock('../context/RunContext', () => ({
  useRun: () => ({ createRun }),
}))

describe('IdeaInput', () => {
  it('renders idea textarea and submit button', () => {
    render(<IdeaInput />)
    expect(screen.getByLabelText(/idea \/ hypothesis/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /start run/i })).toBeInTheDocument()
  })

  it('does not submit when input is empty', async () => {
    createRun.mockClear()
    render(<IdeaInput />)
    fireEvent.click(screen.getByRole('button', { name: /start run/i }))
    expect(createRun).not.toHaveBeenCalled()
  })

  it('submits trimmed idea text and clears input', async () => {
    createRun.mockClear()
    render(<IdeaInput />)
    const textarea = screen.getByLabelText(/idea \/ hypothesis/i)
    fireEvent.change(textarea, { target: { value: '  campus food delivery  ' } })
    fireEvent.click(screen.getByRole('button', { name: /start run/i }))

    await waitFor(() => {
      expect(createRun).toHaveBeenCalledWith('campus food delivery')
    })
    expect(textarea).toHaveValue('')
  })
})
