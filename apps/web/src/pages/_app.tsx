import '../styles/globals.css'
import type { AppProps } from 'next/app'
import { RunProvider } from '../context/RunContext'

export default function App({ Component, pageProps }: AppProps) {
  return (
    <RunProvider>
      <Component {...pageProps} />
    </RunProvider>
  )
}
