import React, { useEffect, useState } from 'react'
import { api } from '../api'

function HistoryView({ userId }) {
  const [history, setHistory] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      setError('')
      try {
        const res = await api.getCycleHistory(userId)
        setHistory(res.data)
      } catch (err) {
        console.error(err)
        setError('Could not load history.')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [userId])

  if (loading) {
    return <div className="card">Loading history…</div>
  }

  if (error) {
    return <div className="card error-banner">{error}</div>
  }

  if (!history || history.periods.length === 0) {
    return (
      <div className="card">
        <h2 className="card-title">Cycle history</h2>
        <p>You haven&apos;t logged any periods yet. Start logging to see patterns over time.</p>
      </div>
    )
  }

  return (
    <div className="card">
      <h2 className="card-title">Cycle history 📊</h2>
      <table className="history-table">
        <thead>
          <tr>
            <th>Period start</th>
            <th>Period end</th>
            <th>Length (days)</th>
            <th>Cycle to next</th>
            <th>Included in stats</th>
          </tr>
        </thead>
        <tbody>
          {history.periods.map((p, idx) => {
            const start = new Date(p.start_date)
            const end = new Date(p.end_date)
            const periodLength = (end - start) / (1000 * 60 * 60 * 24) + 1

            return (
              <tr key={idx}>
                <td>{start.toLocaleDateString()}</td>
                <td>{end.toLocaleDateString()}</td>
                <td>{periodLength}</td>
                <td>{p.cycle_length ?? '-'}</td>
                <td>{p.excluded_from_stats ? 'No' : 'Yes'}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

export default HistoryView
