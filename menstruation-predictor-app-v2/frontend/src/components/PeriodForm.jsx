import React, { useState } from 'react'
import { api } from '../api'

function PeriodForm({ userId, onSaved }) {
  const today = new Date().toISOString().slice(0, 10)
  const [startDate, setStartDate] = useState(today)
  const [endDate, setEndDate] = useState(today)
  const [flow, setFlow] = useState('medium')
  const [exclude, setExclude] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      const payload = {
        start_date: startDate,
        end_date: endDate,
        flow_intensity: flow,
        exclude_from_stats: exclude,
      }
      await api.addPeriod(userId, payload)
      onSaved()
    } catch (err) {
      console.error(err)
      setError('Could not save period log. Please check your dates.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="card">
      <h2 className="card-title">Log your period 💗</h2>
      <p className="card-subtitle">
        Tracking several cycles helps PinkCycle learn your personal rhythm.
      </p>
      <form className="form" onSubmit={handleSubmit}>
        <div className="form-row inline">
          <div>
            <label>Start date</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              required
            />
          </div>
          <div>
            <label>End date</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              required
            />
          </div>
        </div>

        <div className="form-row inline">
          <div>
            <label>Flow intensity</label>
            <select value={flow} onChange={(e) => setFlow(e.target.value)}>
              <option value="light">Light</option>
              <option value="medium">Medium</option>
              <option value="heavy">Heavy</option>
            </select>
          </div>
          <div className="form-row checkbox-row">
            <label>
              <input
                type="checkbox"
                checked={exclude}
                onChange={(e) => setExclude(e.target.checked)}
              />
              Exclude this cycle from stats (e.g. illness/travel)
            </label>
          </div>
        </div>

        {error && <div className="error-banner">{error}</div>}

        <button type="submit" className="primary-btn" disabled={saving}>
          {saving ? 'Saving…' : 'Save Period Log'}
        </button>
      </form>
    </div>
  )
}

export default PeriodForm
