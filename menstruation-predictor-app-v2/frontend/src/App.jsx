import React, { useEffect, useState } from 'react'
import { api } from './api'
import AuthScreen from './components/AuthScreen'
import Dashboard from './components/Dashboard'
import PeriodForm from './components/PeriodForm'
import HistoryView from './components/HistoryView'
import SettingsScreen from './components/SettingsScreen'
import ButterflyBackground from './components/ButterflyBackground'
import AppLockOverlay from './components/AppLockOverlay'
import ResetPasswordScreen from './components/ResetPasswordScreen'
import FaqAssistant from './components/FaqAssistant'

function App() {
  // Optional: password reset route handling
  const loc = window.location
  if (loc.pathname === '/reset-password') {
    const params = new URLSearchParams(loc.search)
    const token = params.get('token')

    if (!token) {
      return (
        <div className="app-root">
          <div className="app-container">
            <header className="app-header">
              <h1 className="logo">PinkCycle</h1>
              <p className="tagline">Reset link is missing or invalid.</p>
            </header>
          </div>
        </div>
      )
    }

    return <ResetPasswordScreen token={token} />
  }

  const [user, setUser] = useState(null)
  const [userId, setUserId] = useState(null)
  const [predictions, setPredictions] = useState(null)
  const [settings, setSettings] = useState(null)
  const [notifications, setNotifications] = useState(null)
  const [view, setView] = useState('dashboard') // dashboard | period | history | settings
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [locked, setLocked] = useState(false)
  
  useEffect(() => {
    const storedId = window.localStorage.getItem('pinkcycle_user_id')
    if (storedId) {
      const parsed = Number(storedId)
      if (!Number.isNaN(parsed)) {
        api
          .getProfile(parsed)
          .then((res) => {
            setUser(res.data)
            setUserId(parsed)
            refreshCore(parsed)
          })
          .catch(() => {
            window.localStorage.removeItem('pinkcycle_user_id')
          })
      }
    }
  }, [])

  useEffect(() => {
    if (user?.app_lock_enabled) {
      setLocked(true)
    } else {
      setLocked(false)
    }
  }, [user])

  const refreshCore = async (uid) => {
    setLoading(true)
    setError('')
    try {
      const [settingsRes, notifRes, predictionsRes] = await Promise.allSettled([
        api.getSettings(uid),
        api.getNotificationSettings(uid),
        api.getPredictions(uid),
      ])
      if (settingsRes.status === 'fulfilled') {
        setSettings(settingsRes.value.data)
      }
      if (notifRes.status === 'fulfilled') {
        setNotifications(notifRes.value.data)
      }
      if (predictionsRes.status === 'fulfilled') {
        setPredictions(predictionsRes.value.data)
      }
    } catch (err) {
      console.error(err)
      setError('Could not fully refresh your data.')
    } finally {
      setLoading(false)
    }
  }

  const handleLoggedIn = (profile) => {
    setUser(profile)
    setUserId(profile.id)
    window.localStorage.setItem('pinkcycle_user_id', String(profile.id))
    refreshCore(profile.id)
  }

  const handleLogout = () => {
    setUser(null)
    setUserId(null)
    setPredictions(null)
    setSettings(null)
    setNotifications(null)
    window.localStorage.removeItem('pinkcycle_user_id')
  }

  const handlePeriodSaved = async () => {
    if (!userId) return
    await refreshCore(userId)
    setView('dashboard')
  }

  const handleSettingsSaved = async (updatedProfile, updatedSettings, updatedNotifications) => {
    if (updatedProfile) setUser(updatedProfile)
    if (updatedSettings) setSettings(updatedSettings)
    if (updatedNotifications) setNotifications(updatedNotifications)
    if (userId) {
      await refreshCore(userId)
    }
    setView('dashboard')
  }

  // 👉 Not logged in: show auth screen, no references to user.theme/user.email here
  if (!userId || !user) {
    return (
      <div className="app-root">
        <ButterflyBackground />
        <div className="app-container">
          <header className="app-header">
            <h1 className="logo">PinkCycle</h1>
            <p className="tagline">Sign in to start tracking your unique rhythm 💖</p>
          </header>
          <AuthScreen onLoggedIn={handleLoggedIn} />
        </div>
      </div>
    )
  }

  // 👉 Logged in: show dashboard, settings, etc. with theme + app lock
  return (
    <div className={`app-root theme-${user.theme || 'pink'}`}>
      <ButterflyBackground />

      {locked && (
        <AppLockOverlay
          email={user.email}
          onUnlocked={() => setLocked(false)}
        />
      )}

      <div className="app-container">
        <header className="app-header app-header-row">
          <div>
            <h1 className="logo">PinkCycle</h1>
            <p className="tagline">Welcome back, {user.email.split('@')[0]} ✨</p>
          </div>
          <button className="ghost-btn" onClick={handleLogout}>
            Log out
          </button>
        </header>

        <nav className="nav-tabs">
          <button
            className={view === 'dashboard' ? 'tab active' : 'tab'}
            onClick={() => setView('dashboard')}
          >
            Dashboard
          </button>
          <button
            className={view === 'period' ? 'tab active' : 'tab'}
            onClick={() => setView('period')}
          >
            Log Period
          </button>
          <button
            className={view === 'history' ? 'tab active' : 'tab'}
            onClick={() => setView('history')}
          >
            History
          </button>
          <button
            className={view === 'settings' ? 'tab active' : 'tab'}
            onClick={() => setView('settings')}
          >
            Settings
          </button>
          <button
            className={view === 'faq' ? 'tab active' : 'tab'}
            onClick={() => setView('faq')}
          >
            AI FAQ
          </button>
        </nav>

        {loading && <div className="info-banner">Refreshing your cycle data…</div>}
        {error && <div className="error-banner">{error}</div>}

        <main className="content">
          {view === 'dashboard' && (
            <Dashboard
              user={user}
              settings={settings}
              predictions={predictions}
            />
          )}
          {view === 'period' && <PeriodForm userId={userId} onSaved={handlePeriodSaved} />}
          {view === 'history' && <HistoryView userId={userId} />}
          {view === 'settings' && (
            <SettingsScreen
              user={user}
              settings={settings}
              notifications={notifications}
              userId={userId}
              onSaved={handleSettingsSaved}
            />
          )}
           {view === 'faq' && <FaqAssistant userId={userId} />}
        </main>
      </div>
    </div>
  )
}

export default App
