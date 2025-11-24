import React, { useState } from 'react'
import { api } from '../api'

function FaqAssistant({ userId }) {
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: "Hi lovely 💕 I'm PinkCycle's AI buddy. Ask me anything about your cycle or how to use the app.",
    },
  ])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleAsk = async (e) => {
    e.preventDefault()
    if (!question.trim()) return

    const q = question.trim()
    setQuestion('')
    setError('')

    // Show user message immediately
    setMessages((prev) => [...prev, { role: 'user', text: q }])
    setLoading(true)

    try {
      const res = await api.askFaq(q, userId)
      const answer = res.data.answer || 'Sorry, I could not come up with a helpful answer right now.'
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text: answer },
      ])
    } catch (err) {
      console.error(err)
      setError('The AI assistant is currently unavailable. Please try again in a bit.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h2 className="card-title">Ask PinkCycle AI 💬</h2>
      <p className="card-subtitle">
        Ask questions about your cycle, symptoms, fertile window, or how to use this app.
        I&apos;m not a doctor, but I can give gentle, general guidance.
      </p>

      <div className="faq-chat">
        <div className="faq-messages">
          {messages.map((m, idx) => (
            <div
              key={idx}
              className={m.role === 'user' ? 'faq-bubble user' : 'faq-bubble assistant'}
            >
              {m.text}
            </div>
          ))}
          {loading && (
            <div className="faq-bubble assistant">
              Thinking about a kind answer for you… ✨
            </div>
          )}
        </div>

        {error && <div className="error-banner">{error}</div>}

        <form className="faq-input-row" onSubmit={handleAsk}>
          <input
            type="text"
            placeholder="Type your question here…"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
          <button className="primary-btn" type="submit" disabled={loading}>
            Ask
          </button>
        </form>

        <p className="help-text" style={{ marginTop: 8 }}>
          This AI can&apos;t diagnose or replace a doctor. For severe pain, very heavy bleeding,
          or worrying changes, please see a healthcare professional.
        </p>
      </div>
    </div>
  )
}

export default FaqAssistant
