import React from 'react'

const butterflies = [
  { left: '5%', top: '70%', delay: '0s', scale: 0.8 },
  { left: '20%', top: '80%', delay: '2s', scale: 1.1 },
  { left: '60%', top: '75%', delay: '1s', scale: 0.9 },
  { left: '80%', top: '85%', delay: '3s', scale: 1.0 },
  { left: '40%', top: '78%', delay: '1.5s', scale: 0.7 },
]

function ButterflyBackground() {
  return (
    <div className="butterfly-layer" aria-hidden="true">
      {butterflies.map((b, idx) => (
        <div
          key={idx}
          className="butterfly"
          style={{
            left: b.left,
            top: b.top,
            animationDelay: b.delay,
            transform: `scale(${b.scale})`,
          }}
        >
          🦋
        </div>
      ))}
    </div>
  )
}

export default ButterflyBackground
