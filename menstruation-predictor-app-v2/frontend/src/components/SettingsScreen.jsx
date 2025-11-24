import React, { useEffect, useState } from 'react'
import { api } from '../api'

const defaultTrackedSymptoms = 'cramps,bloating,headache,breast_tenderness,acne,mood_swings,low_energy,poor_sleep,anxiety'

function SettingsScreen({ user, settings, notifications, userId, onSaved }) {
  const [profile, setProfile] = useState(user)
  const [cycleSettings, setCycleSettings] = useState(settings)
  const [notifSettings, setNotifSettings] = useState(notifications)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    setProfile(user)
  }, [user])

  useEffect(() => {
    setCycleSettings(
      settings || {
        average_cycle_length: 28,
        average_period_length: 5,
        first_period_start_date: '',
        uses_hormonal_contraceptives: false,
        show_fertile_window: true,
        irregular_cycle_mode: false,
        pregnancy_mode: false,
        lactation_mode: false,
        tracked_symptoms: defaultTrackedSymptoms,
      },
    )
  }, [settings])

  useEffect(() => {
    setNotifSettings(
      notifications || {
        notify_period: true,
        period_reminder_days_before: 2,
        notify_period_end: false,
        notify_fertile_window: true,
        notify_ovulation: true,
        notify_daily_log: false,
        daily_log_time: '',
        notify_medication: false,
        medication_time: '',
      },
    )
  }, [notifications])

  const handleProfileChange = (field, value) => {
    setProfile((prev) => ({ ...prev, [field]: value }))
  }

  const handleCycleChange = (field, value) => {
    setCycleSettings((prev) => ({ ...prev, [field]: value }))
  }

  const handleNotifChange = (field, value) => {
    setNotifSettings((prev) => ({ ...prev, [field]: value }))
  }

  const handleExport = async () => {
    try {
      const res = await api.exportData(userId)
      const dataStr = JSON.stringify(res.data, null, 2)
      const blob = new Blob([dataStr], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'pinkcycle-export.json'
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error(err)
      setError('Could not export your data.')
    }
  }

  const handleDelete = async () => {
    if (!window.confirm('Are you sure you want to delete your account and all data?')) return
    try {
      await api.deleteAccount(userId)
      window.localStorage.removeItem('pinkcycle_user_id')
      window.location.reload()
    } catch (err) {
      console.error(err)
      setError('Could not delete account.')
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setSuccess('')
    try {
      const profilePayload = {
        email: profile.email,
        age: profile.age,
        height_cm: profile.height_cm,
        weight_kg: profile.weight_kg,
        goal: profile.goal,
        contraceptive_method: profile.contraceptive_method,
        language: profile.language || 'en',
        region: profile.region || 'KE',
        theme: profile.theme || 'pink',
        data_sharing_consent: !!profile.data_sharing_consent,
        app_lock_enabled: !!profile.app_lock_enabled,
        wearable_integration_enabled: !!profile.wearable_integration_enabled,
      }

      const settingsPayload = {
        average_cycle_length: Number(cycleSettings.average_cycle_length),
        average_period_length: Number(cycleSettings.average_period_length),
        first_period_start_date: cycleSettings.first_period_start_date || null,
        uses_hormonal_contraceptives: !!cycleSettings.uses_hormonal_contraceptives,
        show_fertile_window: !!cycleSettings.show_fertile_window,
        irregular_cycle_mode: !!cycleSettings.irregular_cycle_mode,
        pregnancy_mode: !!cycleSettings.pregnancy_mode,
        lactation_mode: !!cycleSettings.lactation_mode,
        tracked_symptoms:
          cycleSettings.tracked_symptoms || defaultTrackedSymptoms,
      }

      const notifPayload = {
        notify_period: !!notifSettings.notify_period,
        period_reminder_days_before: Number(
          notifSettings.period_reminder_days_before || 2,
        ),
        notify_period_end: !!notifSettings.notify_period_end,
        notify_fertile_window: !!notifSettings.notify_fertile_window,
        notify_ovulation: !!notifSettings.notify_ovulation,
        notify_daily_log: !!notifSettings.notify_daily_log,
        daily_log_time: notifSettings.daily_log_time || null,
        notify_medication: !!notifSettings.notify_medication,
        medication_time: notifSettings.medication_time || null,
      }

      const [profileRes, settingsRes, notifRes] = await Promise.all([
        api.updateProfile(userId, profilePayload),
        api.saveSettings(userId, settingsPayload),
        api.saveNotificationSettings(userId, notifPayload),
      ])

      setSuccess('Settings saved ✨')
      onSaved(profileRes.data, settingsRes.data, notifRes.data)
    } catch (err) {
      console.error(err)
      setError('Something went wrong while saving your settings.')
    } finally {
      setLoading(false)
    }
  }

  if (!profile || !cycleSettings || !notifSettings) {
    return <div className="card">Loading settings…</div>
  }

  const trackedSymptomsText =
    cycleSettings.tracked_symptoms || defaultTrackedSymptoms

  return (
    <form className="card settings-card" onSubmit={handleSubmit}>
      <h2 className="card-title">Settings ⚙️</h2>
      <p className="card-subtitle">
        Tune PinkCycle to your body, your privacy, and your vibe.
      </p>

      {error && <div className="error-banner">{error}</div>}
      {success && <div className="info-banner">{success}</div>}

      {/* Account & Profile */}
      <section className="settings-section">
        <h3>Account &amp; Profile</h3>
        <div className="settings-grid">
          <div className="form-row">
            <label>Email (account)</label>
            <input type="email" value={profile.email} disabled />
          </div>

          <div className="form-row inline">
            <div>
              <label>Age</label>
              <input
                type="number"
                value={profile.age ?? ''}
                onChange={(e) => handleProfileChange('age', Number(e.target.value))}
              />
            </div>
            <div>
              <label>Height (cm)</label>
              <input
                type="number"
                value={profile.height_cm ?? ''}
                onChange={(e) =>
                  handleProfileChange('height_cm', Number(e.target.value))
                }
              />
            </div>
            <div>
              <label>Weight (kg)</label>
              <input
                type="number"
                value={profile.weight_kg ?? ''}
                onChange={(e) =>
                  handleProfileChange('weight_kg', Number(e.target.value))
                }
              />
            </div>
          </div>

          <div className="form-row inline">
            <div>
              <label>Goal</label>
              <select
                value={profile.goal || 'track_cycle'}
                onChange={(e) => handleProfileChange('goal', e.target.value)}
              >
                <option value="track_cycle">Track cycle</option>
                <option value="conceive">Try to conceive</option>
                <option value="avoid_pregnancy">Avoid pregnancy</option>
                <option value="perimenopause">Perimenopause</option>
              </select>
            </div>
            <div>
              <label>Contraceptive method</label>
              <select
                value={profile.contraceptive_method || 'none'}
                onChange={(e) =>
                  handleProfileChange('contraceptive_method', e.target.value)
                }
              >
                <option value="none">None</option>
                <option value="pill">Pill</option>
                <option value="iud">IUD</option>
                <option value="implant">Implant</option>
                <option value="injection">Injection</option>
              </select>
            </div>
          </div>
        </div>
      </section>

      {/* Cycle Tracking & Prediction */}
      <section className="settings-section">
        <h3>Cycle tracking &amp; prediction</h3>
        <div className="settings-grid">
          <div className="form-row inline">
            <div>
              <label>First day of your last period</label>
              <input
                type="date"
                value={cycleSettings.first_period_start_date || ''}
                onChange={(e) =>
                  handleCycleChange('first_period_start_date', e.target.value)
                }
              />
            </div>
            <div>
              <label>Average cycle length (days)</label>
              <input
                type="number"
                min="15"
                max="60"
                value={cycleSettings.average_cycle_length}
                onChange={(e) =>
                  handleCycleChange('average_cycle_length', e.target.value)
                }
                required
              />
            </div>
            <div>
              <label>Average period length (days)</label>
              <input
                type="number"
                min="2"
                max="15"
                value={cycleSettings.average_period_length}
                onChange={(e) =>
                  handleCycleChange('average_period_length', e.target.value)
                }
                required
              />
            </div>
          </div>

          <div className="form-row checkbox-row">
            <label>
              <input
                type="checkbox"
                checked={cycleSettings.uses_hormonal_contraceptives}
                onChange={(e) =>
                  handleCycleChange('uses_hormonal_contraceptives', e.target.checked)
                }
              />
              I use hormonal contraceptives
            </label>
          </div>

          <div className="form-row checkbox-row">
            <label>
              <input
                type="checkbox"
                checked={cycleSettings.show_fertile_window}
                onChange={(e) =>
                  handleCycleChange('show_fertile_window', e.target.checked)
                }
              />
              Show fertile window on calendar
            </label>
          </div>

          <div className="form-row checkbox-row">
            <label>
              <input
                type="checkbox"
                checked={cycleSettings.irregular_cycle_mode}
                onChange={(e) =>
                  handleCycleChange('irregular_cycle_mode', e.target.checked)
                }
              />
              My cycles are irregular (softer predictions)
            </label>
          </div>

          <div className="form-row inline">
            <div className="form-row checkbox-row">
              <label>
                <input
                  type="checkbox"
                  checked={cycleSettings.pregnancy_mode}
                  onChange={(e) =>
                    handleCycleChange('pregnancy_mode', e.target.checked)
                  }
                />
                Pregnancy mode
              </label>
            </div>
            <div className="form-row checkbox-row">
              <label>
                <input
                  type="checkbox"
                  checked={cycleSettings.lactation_mode}
                  onChange={(e) =>
                    handleCycleChange('lactation_mode', e.target.checked)
                  }
                />
                Lactation / breastfeeding mode
              </label>
            </div>
          </div>

          <div className="form-row">
            <label>Tracked symptoms (comma separated)</label>
            <input
              type="text"
              value={trackedSymptomsText}
              onChange={(e) =>
                handleCycleChange('tracked_symptoms', e.target.value)
              }
            />
            <span className="help-text">
              These will be used when you later log moods, cramps, and other symptoms.
            </span>
          </div>
        </div>
      </section>

      {/* Notifications & reminders */}
      <section className="settings-section">
        <h3>Notifications &amp; reminders 🔔</h3>
        <div className="settings-grid">
          <div className="form-row inline">
            <div className="form-row checkbox-row">
              <label>
                <input
                  type="checkbox"
                  checked={notifSettings.notify_period}
                  onChange={(e) =>
                    handleNotifChange('notify_period', e.target.checked)
                  }
                />
                Remind me before my period
              </label>
            </div>
            <div>
              <label>Days before period</label>
              <input
                type="number"
                min="0"
                max="5"
                value={notifSettings.period_reminder_days_before}
                onChange={(e) =>
                  handleNotifChange(
                    'period_reminder_days_before',
                    e.target.value,
                  )
                }
              />
            </div>
          </div>

          <div className="form-row checkbox-row">
            <label>
              <input
                type="checkbox"
                checked={notifSettings.notify_period_end}
                onChange={(e) =>
                  handleNotifChange('notify_period_end', e.target.checked)
                }
              />
              Remind me to log when my period ends
            </label>
          </div>

          <div className="form-row inline">
            <div className="form-row checkbox-row">
              <label>
                <input
                  type="checkbox"
                  checked={notifSettings.notify_fertile_window}
                  onChange={(e) =>
                    handleNotifChange('notify_fertile_window', e.target.checked)
                  }
                />
                Fertile window reminders
              </label>
            </div>
            <div className="form-row checkbox-row">
              <label>
                <input
                  type="checkbox"
                  checked={notifSettings.notify_ovulation}
                  onChange={(e) =>
                    handleNotifChange('notify_ovulation', e.target.checked)
                  }
                />
                Ovulation day reminder
              </label>
            </div>
          </div>

          <div className="form-row inline">
            <div className="form-row checkbox-row">
              <label>
                <input
                  type="checkbox"
                  checked={notifSettings.notify_daily_log}
                  onChange={(e) =>
                    handleNotifChange('notify_daily_log', e.target.checked)
                  }
                />
                Daily log reminder
              </label>
            </div>
            <div>
              <label>Daily log time</label>
              <input
                type="time"
                value={notifSettings.daily_log_time || ''}
                onChange={(e) =>
                  handleNotifChange('daily_log_time', e.target.value)
                }
              />
            </div>
          </div>

          <div className="form-row inline">
            <div className="form-row checkbox-row">
              <label>
                <input
                  type="checkbox"
                  checked={notifSettings.notify_medication}
                  onChange={(e) =>
                    handleNotifChange('notify_medication', e.target.checked)
                  }
                />
                Medication / pill reminders
              </label>
            </div>
            <div>
              <label>Medication reminder time</label>
              <input
                type="time"
                value={notifSettings.medication_time || ''}
                onChange={(e) =>
                  handleNotifChange('medication_time', e.target.value)
                }
              />
            </div>
          </div>
        </div>
      </section>

      {/* Privacy & Security */}
      <section className="settings-section">
        <h3>Privacy &amp; security 🔒</h3>
        <div className="settings-grid">
          <div className="form-row checkbox-row">
            <label>
              <input
                type="checkbox"
                checked={profile.app_lock_enabled || false}
                onChange={(e) =>
                  handleProfileChange('app_lock_enabled', e.target.checked)
                }
              />
              Require app lock on this device (PIN/biometric handled by OS)
            </label>
          </div>
          <div className="form-row checkbox-row">
            <label>
              <input
                type="checkbox"
                checked={profile.data_sharing_consent || false}
                onChange={(e) =>
                  handleProfileChange('data_sharing_consent', e.target.checked)
                }
              />
              Allow anonymised data to be used to improve PinkCycle (optional)
            </label>
          </div>
          <div className="form-row">
            <label>Privacy policy</label>
            <p className="help-text">
              In a real app, this would open a detailed privacy policy page explaining how your
              cycle data is protected.
            </p>
          </div>
        </div>
      </section>

      {/* Integrations & appearance */}
      <section className="settings-section">
        <h3>Integrations &amp; appearance 🌐</h3>
        <div className="settings-grid">
          <div className="form-row inline">
            <div>
              <label>Language</label>
              <select
                value={profile.language || 'en'}
                onChange={(e) => handleProfileChange('language', e.target.value)}
              >
                <option value="en">English</option>
              </select>
            </div>
            <div>
              <label>Region</label>
              <input
                type="text"
                value={profile.region || ''}
                onChange={(e) => handleProfileChange('region', e.target.value)}
                placeholder="e.g. KE"
              />
            </div>
          </div>

          <div className="form-row">
            <label>Theme</label>
            <select
              value={profile.theme || 'pink'}
              onChange={(e) => handleProfileChange('theme', e.target.value)}
            >
              <option value="pink">Pink butterflies</option>
              <option value="dark">Midnight glow</option>
              <option value="soft">Soft pastels</option>
            </select>
          </div>

          <div className="form-row checkbox-row">
            <label>
              <input
                type="checkbox"
                checked={profile.wearable_integration_enabled || false}
                onChange={(e) =>
                  handleProfileChange(
                    'wearable_integration_enabled',
                    e.target.checked,
                  )
                }
              />
              Enable wearable integration (future: Apple Watch, Fitbit, etc.)
            </label>
          </div>
        </div>
      </section>

      {/* Data management */}
      <section className="settings-section">
        <h3>Data management 📦</h3>
        <div className="settings-grid">
          <div className="form-row inline">
            <button
              type="button"
              className="ghost-btn"
              onClick={handleExport}
            >
              Export my data (JSON)
            </button>
            <button
              type="button"
              className="ghost-btn danger"
              onClick={handleDelete}
            >
              Delete account &amp; data
            </button>
          </div>
          <p className="help-text">
            Cloud backup &amp; restore would typically connect to iCloud, Google Drive, or
            similar. Here we give you a local export you can store or share with a clinician.
          </p>
        </div>
      </section>

      <div className="settings-footer">
        <button className="primary-btn" type="submit" disabled={loading}>
          {loading ? 'Saving…' : 'Save all settings'}
        </button>
      </div>
    </form>
  )
}

export default SettingsScreen
