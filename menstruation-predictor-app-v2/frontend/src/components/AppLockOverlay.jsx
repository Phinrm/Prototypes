// src/components/AppLockOverlay.jsx
import React, { useState } from 'react'
import { api } from '../api'

function AppLockOverlay({ email, onUnlocked }) {
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleUnlock = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      await api.login({ email, password }) // just verifies; we ignore response
      onUnlocked()
    } catch (err) {
      console.error(err)
      setError('Wrong password, try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-lock-overlay">
      <div className="card app-lock-card">
        <h2 className="card-title">App locked 🔒</h2>
        <p className="card-subtitle">
          For extra privacy, enter your PinkCycle password to unlock.
        </p>
        <form className="form" onSubmit={handleUnlock}>
          <div className="form-row">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          {error && <div className="error-banner">{error}</div>}
          <button className="primary-btn" type="submit" disabled={loading}>
            {loading ? 'Checking…' : 'Unlock'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default AppLockOverlay
