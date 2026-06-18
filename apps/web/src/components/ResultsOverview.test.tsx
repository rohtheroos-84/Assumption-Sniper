import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import ResultsOverview from './ResultsOverview'

describe('ResultsOverview', () => {
  it('renders run title and decomposition payload', () => {
    render(
      <ResultsOverview
        run={{
          title: 'Campus delivery pilot',
          decomposition: { targets: ['students'], goals: ['fast delivery'] },
        }}
      />,
    )

    expect(screen.getByText('Overview')).toBeInTheDocument()
    expect(screen.getByText(/Campus delivery pilot/)).toBeInTheDocument()
    expect(screen.getByText(/"targets"/)).toBeInTheDocument()
  })

  it('shows placeholder when decomposition is missing', () => {
    render(<ResultsOverview run={{ title: 'Untitled' }} />)
    expect(screen.getByText('No decomposition yet')).toBeInTheDocument()
  })
})
