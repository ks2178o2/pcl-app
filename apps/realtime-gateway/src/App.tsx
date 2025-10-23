import React from 'react'
import { EnhancedContextManagement } from './components/admin/EnhancedContextManagement'
import { EnhancedUploadManager } from './components/admin/EnhancedUploadManager'

function App() {
  return (
    <div className="app">
      <h1>Realtime Gateway</h1>
      <EnhancedContextManagement />
      <EnhancedUploadManager />
    </div>
  )
}

export default App
