import React from 'react'
import CalendarView from './CalendarView'

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString()
}

function Dashboard({ user, settings, predictions }) {
  if (!settings) {
    return (
      <div className="card">
        <h2 className="card-title">Welcome, lovely 🩷</h2>
        <p className="card-subtitle">
          To get accurate predictions, please open <strong>Settings</strong> and fill in your
          basic cycle info (last period date, average cycle &amp; period length).
        </p>
      </div>
    )
  }

  if (!predictions) {
    return (
      <div className="card">
        <h2 className="card-title">Your cycle</h2>
        <p>We&apos;re still waiting for enough data to generate predictions.</p>
      </div>
    )
  }

  const { show_fertile_window, irregular_cycle_mode, pregnancy_mode, lactation_mode } = predictions

  return (
    <div className="dashboard-grid">
      <section className="card highlight-card">
        <h2 className="card-title">Your cycle at a glance 💖</h2>
        <p className="cycle-day">
          Today is cycle day <strong>{predictions.cycle_day_today ?? '–'}</strong>
        </p>

        {pregnancy_mode && (
          <div className="info-banner">
            Pregnancy/Lactation mode is on. Predictions may be less accurate and are for
            awareness only.
          </div>
        )}

        {irregular_cycle_mode && (
          <div className="info-banner">
            Irregular cycle mode enabled – we&apos;ll still do our best, but predictions are
            softer estimates.
          </div>
        )}

        <div className="stat-row">
          <div className="stat">
            <span className="stat-label">Next period</span>
            <span className="stat-value">{formatDate(predictions.next_period_start)}</span>
            <span className="stat-note">
              Expected to last about {predictions.period_length_used} days.
            </span>
          </div>

          {show_fertile_window && (
            <div className="stat">
              <span className="stat-label">Fertile window</span>
              <span className="stat-value">
                {formatDate(predictions.fertile_window_start)} –{' '}
                {formatDate(predictions.fertile_window_end)}
              </span>
              <span className="stat-note">
                Ovulation around {formatDate(predictions.ovulation_day)} (approximate).
              </span>
            </div>
          )}
        </div>

        <div className="stat-row small">
          <div className="stat">
            <span className="stat-label">Cycle length used</span>
            <span className="stat-value">
              {predictions.cycle_length_used ? `${predictions.cycle_length_used} days` : '–'}
            </span>
          </div>
          <div className="stat">
            <span className="stat-label">Average period length</span>
            <span className="stat-value">
              {predictions.period_length_used ? `${predictions.period_length_used} days` : '–'}
            </span>
          </div>
        </div>
      </section>

      <section className="card">
        <h2 className="card-title">Cycle calendar 🌙</h2>
        <CalendarView predictions={predictions} />
      </section>
    </div>
  )
}

export default Dashboard
