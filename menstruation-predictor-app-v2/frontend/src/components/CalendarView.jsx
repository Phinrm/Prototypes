import React from 'react'

function sameDay(a, b) {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  )
}

function inRange(day, start, end) {
  return day >= start && day <= end
}

function CalendarView({ predictions }) {
  const today = new Date()
  const year = today.getFullYear()
  const month = today.getMonth()

  const firstOfMonth = new Date(year, month, 1)
  const startDay = firstOfMonth.getDay()
  const daysInMonth = new Date(year, month + 1, 0).getDate()

  const cells = []
  for (let i = 0; i < startDay; i++) {
    cells.push(null)
  }
  for (let d = 1; d <= daysInMonth; d++) {
    cells.push(new Date(year, month, d))
  }

  const nextPeriodStart = predictions.next_period_start
    ? new Date(predictions.next_period_start)
    : null
  const nextPeriodEnd = predictions.next_period_end ? new Date(predictions.next_period_end) : null
  const fertileStart = predictions.fertile_window_start
    ? new Date(predictions.fertile_window_start)
    : null
  const fertileEnd = predictions.fertile_window_end
    ? new Date(predictions.fertile_window_end)
    : null

  return (
    <div className="calendar">
      <div className="calendar-header">
        {today.toLocaleString('default', { month: 'long' })} {year}
      </div>
      <div className="calendar-grid">
        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((d) => (
          <div key={d} className="calendar-cell header">
            {d}
          </div>
        ))}
        {cells.map((day, idx) => {
          if (!day) return <div key={idx} className="calendar-cell empty" />

          const isToday = sameDay(day, today)
          const isPeriod =
            nextPeriodStart && nextPeriodEnd && inRange(day, nextPeriodStart, nextPeriodEnd)
          const isFertile =
            predictions.show_fertile_window &&
            fertileStart &&
            fertileEnd &&
            inRange(day, fertileStart, fertileEnd)

          let className = 'calendar-cell day'
          if (isPeriod) className += ' period-day'
          if (isFertile) className += ' fertile-day'
          if (isToday) className += ' today'

          return (
            <div key={idx} className={className}>
              <span className="day-number">{day.getDate()}</span>
            </div>
          )
        })}
      </div>
      <div className="calendar-legend">
        <span className="legend-item">
          <span className="dot period" /> Predicted period
        </span>
        {predictions.show_fertile_window && (
          <span className="legend-item">
            <span className="dot fertile" /> Fertile window
          </span>
        )}
        <span className="legend-item">
          <span className="dot today-dot" /> Today
        </span>
      </div>
    </div>
  )
}

export default CalendarView
