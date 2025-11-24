import axios from 'axios'

const API_BASE = 'http://127.0.0.1:8000'

export const api = {
  async register(payload) {
    return axios.post(`${API_BASE}/register`, payload)
  },
  async login(payload) {
    return axios.post(`${API_BASE}/login`, payload)
  },
  async getProfile(userId) {
    return axios.get(`${API_BASE}/me`, { params: { user_id: userId } })
  },
  async updateProfile(userId, payload) {
    return axios.put(`${API_BASE}/me`, payload, { params: { user_id: userId } })
  },
  async getSettings(userId) {
    return axios.get(`${API_BASE}/settings`, { params: { user_id: userId } })
  },
  async saveSettings(userId, payload) {
    return axios.post(`${API_BASE}/settings`, payload, { params: { user_id: userId } })
  },
  async getNotificationSettings(userId) {
    return axios.get(`${API_BASE}/notification-settings`, { params: { user_id: userId } })
  },
  async saveNotificationSettings(userId, payload) {
    return axios.post(`${API_BASE}/notification-settings`, payload, { params: { user_id: userId } })
  },
  async getPredictions(userId) {
    return axios.get(`${API_BASE}/predictions`, { params: { user_id: userId } })
  },
  async addPeriod(userId, payload) {
    return axios.post(`${API_BASE}/periods`, payload, { params: { user_id: userId } })
  },
  async listPeriods(userId) {
    return axios.get(`${API_BASE}/periods`, { params: { user_id: userId } })
  },
  async updatePeriod(userId, periodId, payload) {
    return axios.patch(`${API_BASE}/periods/${periodId}`, payload, { params: { user_id: userId } })
  },
  async getCycleHistory(userId) {
    return axios.get(`${API_BASE}/cycle-history`, { params: { user_id: userId } })
  },
  async exportData(userId) {
    return axios.get(`${API_BASE}/export-data`, {
      params: { user_id: userId },
      responseType: 'json',
    })
  },
  async deleteAccount(userId) {
    return axios.delete(`${API_BASE}/account`, { params: { user_id: userId } })
  },
  async requestPasswordReset(email) {
  return axios.post(`${API_BASE}/request-password-reset`, { email })
},
async resetPassword(token, newPassword) {
  return axios.post(`${API_BASE}/reset-password`, {
    token,
    new_password: newPassword,
  })
},
//AI FAQ helper
  async askFaq(question, userId) {
    return axios.post(`${API_BASE}/ai/faq`, {
      question,
      user_id: userId ?? null,
    })
  },

}

