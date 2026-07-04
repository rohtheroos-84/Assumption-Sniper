import React from 'react'

const Layout: React.FC<{children: React.ReactNode}> = ({children}) => {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-surface border-b border-gray-800">
        <div className="h-container py-4 flex items-center justify-between">
          <div className="text-primary font-semibold">assumption sniper</div>
          <nav className="flex gap-4 text-sm">
            <a href="/" className="text-gray-300 hover:text-white">home</a>
            <a href="/demo" className="text-gray-300 hover:text-white">demo</a>
            <a href="/app" className="text-gray-300 hover:text-white">app</a>
            <a href="/runs" className="text-gray-300 hover:text-white">runs</a>
            <a href="/beta" className="text-gray-300 hover:text-white">beta</a>
          </nav>
        </div>
      </header>
      <main className="flex-1">{children}</main>
      <footer className="bg-surface border-t border-gray-800 py-6">
        <div className="h-container text-sm text-gray-400">built for prototyping</div>
      </footer>
    </div>
  )
}

export default Layout
