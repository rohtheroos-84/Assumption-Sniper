import React from 'react'

const Layout: React.FC<{children: React.ReactNode}> = ({children}) => {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-surface border-b border-gray-800">
        <div className="h-container py-4 flex items-center justify-between">
          <div className="text-primary font-semibold">assumption sniper</div>
          <nav>
            <a href="/" className="text-sm text-gray-300 hover:text-white mr-4">home</a>
            <a href="/runs" className="text-sm text-gray-300 hover:text-white">runs</a>
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
