import React, { useState } from 'react'
import { api } from '../api'

function AuthScreen({ onLoggedIn }) {
  const [mode, setMode] = useState('login') // login | register
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [age, setAge] = useState('')
  const [height, setHeight] = useState('')
  const [weight, setWeight] = useState('')
  const [goal, setGoal] = useState('track_cycle')
  const [contraceptive, setContraceptive] = useState('none')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [resetRequested, setResetRequested] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      if (mode === 'login') {
        const res = await api.login({ email, password })
        onLoggedIn(res.data)
      } else {
        const payload = {
          email,
          password,
          age: age ? Number(age) : null,
          height_cm: height ? Number(height) : null,
          weight_kg: weight ? Number(weight) : null,
          goal,
          contraceptive_method: contraceptive,
          language: 'en',
          region: 'KE',
          theme: 'pink',
          data_sharing_consent: false,
          app_lock_enabled: false,
          wearable_integration_enabled: false,
        }
        const res = await api.register(payload)
        onLoggedIn(res.data)
      }
    } catch (err) {
      console.error(err)
      setError('Could not ' + (mode === 'login' ? 'log you in.' : 'create your account.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card auth-card">
      <div className="auth-toggle">
        <button
          className={mode === 'login' ? 'tab small active' : 'tab small'}
          onClick={() => setMode('login')}
        >
          Login
        </button>
        <button
          className={mode === 'register' ? 'tab small active' : 'tab small'}
          onClick={() => setMode('register')}
        >
          Sign up
        </button>
      </div>

      <form className="form" onSubmit={handleSubmit}>
        <div className="form-row">
          <label>Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>

        <div className="form-row">
          <label>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={6}
          />
        </div>

        {mode === 'login' && (
          <button
            type="button"
            className="link-button"
            onClick={async () => {
              if (!email) {
                setError('Enter your email first, then click "Forgot password?".')
                return
              }
              try {
                setError('')
                await api.requestPasswordReset(email)
                setResetRequested(true)
              } catch (err) {
                console.error(err)
                // still show generic message
                setResetRequested(true)
              }
            }}
          >
            Forgot password?
          </button>
        )}

        {mode === 'register' && (
          <>
            <div className="form-row inline">
              <div>
                <label>Age</label>
                <input
                  type="number"
                  min="10"
                  max="60"
                  value={age}
                  onChange={(e) => setAge(e.target.value)}
                />
              </div>
              <div>
                <label>Height (cm)</label>
                <input
                  type="number"
                  min="120"
                  max="220"
                  value={height}
                  onChange={(e) => setHeight(e.target.value)}
                />
              </div>
              <div>
                <label>Weight (kg)</label>
                <input
                  type="number"
                  min="35"
                  max="160"
                  value={weight}
                  onChange={(e) => setWeight(e.target.value)}
                />
              </div>
            </div>

            <div className="form-row inline">
              <div>
                <label>Goal</label>
                <select value={goal} onChange={(e) => setGoal(e.target.value)}>
                  <option value="track_cycle">Track cycle</option>
                  <option value="conceive">Try to conceive</option>
                  <option value="avoid_pregnancy">Avoid pregnancy</option>
                  <option value="perimenopause">Perimenopause</option>
                </select>
              </div>
              <div>
                <label>Contraceptive method</label>
                <select
                  value={contraceptive}
                  onChange={(e) => setContraceptive(e.target.value)}
                >
                  <option value="none">None</option>
                  <option value="pill">Pill</option>
                  <option value="iud">IUD</option>
                  <option value="implant">Implant</option>
                  <option value="injection">Injection</option>
                </select>
              </div>
            </div>
          </>
        )}

        {error && <div className="error-banner">{error}</div>}

        {resetRequested && (
          <div className="info-banner">
            If an account exists for {email}, a reset link was emailed to you.
          </div>
        )}

        <button className="primary-btn" type="submit" disabled={loading}>
          {loading ? 'Please wait…' : mode === 'login' ? 'Login' : 'Create account'}
        </button>
      </form>
    </div>
  )
}

export default AuthScreen
