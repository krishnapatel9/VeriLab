import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import { wakeBackend } from './api/client'
import { ServerWakeBanner } from './components/ServerWakeBanner'
import './index.css'

// Start waking the backend now, so it's up by the time the user submits anything.
wakeBackend()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ServerWakeBanner />
    <App />
  </React.StrictMode>,
)
