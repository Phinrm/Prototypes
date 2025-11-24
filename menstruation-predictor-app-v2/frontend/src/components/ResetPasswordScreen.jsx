import React, { useState } from 'react'
import { api } from '../api'

function ResetPasswordScreen({ token }) {
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setStatus('')
    if (password !== confirm) {
      setError('Passwords do not match.')
      return
    }
    setLoading(true)
    try {
      await api.resetPassword(token, password)
      setStatus('Password updated! You can now close this tab and log in with your new password.')
    } catch (err) {
      console.error(err)
      setError('The link may be invalid or expired.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-root">
      <div className="app-container">
        <header className="app-header">
          <h1 className="logo">PinkCycle</h1>
          <p className="tagline">Reset your password 💕</p>
        </header>

        <div className="card auth-card">
          <form className="form" onSubmit={handleSubmit}>
            <div className="form-row">
              <label>New password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
              />
            </div>
            <div className="form-row">
              <label>Confirm new password</label>
              <input
                type="password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                required
                minLength={6}
              />
            </div>

            {error && <div className="error-banner">{error}</div>}
            {status && <div className="info-banner">{status}</div>}

            <button className="primary-btn" type="submit" disabled={loading}>
              {loading ? 'Saving…' : 'Reset password'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

export default ResetPasswordScreen
