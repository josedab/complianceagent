'use client'

import { useState, useEffect, FormEvent } from 'react'
import { User, Building, Bell, Shield, CreditCard, Key, Trash2, Plus, Loader2, Check, AlertCircle, Copy } from 'lucide-react'
import { settingsApi, apiKeysApi } from '@/lib/api'
import { useAuth } from '@/contexts/auth'

interface ProfileResponse {
  id: string
  email: string
  full_name: string
  is_active: boolean
  is_verified: boolean
  last_login_at: string | null
  oauth_provider: string | null
}

interface NotificationPreferences {
  email_enabled: boolean
  email_digest: string
  slack_enabled: boolean
  slack_webhook_url: string | null
  webhook_enabled: boolean
  webhook_url: string | null
}

interface APIKeyRead {
  id: string
  name: string
  prefix: string
  scopes: string[]
  status: string
  created_at: string
  last_used_at: string | null
  usage_count: number
}

function LoadingSkeleton({ lines = 3 }: { lines?: number }) {
  return (
    <div className="animate-pulse space-y-4">
      {Array.from({ length: lines }).map((_, i) => (
        <div key={i} className="h-4 bg-gray-200 rounded w-full" style={{ width: `${80 - i * 15}%` }} />
      ))}
    </div>
  )
}

function Toast({ message, type, onClose }: { message: string; type: 'success' | 'error'; onClose: () => void }) {
  useEffect(() => {
    const timer = setTimeout(onClose, 4000)
    return () => clearTimeout(timer)
  }, [onClose])

  return (
    <div className={`fixed top-4 right-4 z-50 flex items-center gap-2 px-4 py-3 rounded-lg shadow-lg text-sm font-medium ${
      type === 'success' ? 'bg-green-50 text-green-800 border border-green-200' : 'bg-red-50 text-red-800 border border-red-200'
    }`}>
      {type === 'success' ? <Check className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
      {message}
    </div>
  )
}

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('profile')

  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'organization', label: 'Organization', icon: Building },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'security', label: 'Security', icon: Shield },
    { id: 'billing', label: 'Billing', icon: CreditCard },
    { id: 'api', label: 'API Keys', icon: Key },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-500">Manage your account and preferences</p>
      </div>

      <div className="flex flex-col md:flex-row gap-6">
        {/* Sidebar */}
        <div className="w-full md:w-64 flex-shrink-0">
          <nav className="space-y-1">
            {tabs.map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center gap-3 px-4 py-2 rounded-lg text-left transition-colors ${
                    activeTab === tab.id
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  <span>{tab.label}</span>
                </button>
              )
            })}
          </nav>
        </div>

        {/* Content */}
        <div className="flex-1">
          {activeTab === 'profile' && <ProfileSettings />}
          {activeTab === 'organization' && <OrganizationSettings />}
          {activeTab === 'notifications' && <NotificationSettings />}
          {activeTab === 'security' && <SecuritySettings />}
          {activeTab === 'billing' && <BillingSettings />}
          {activeTab === 'api' && <ApiKeySettings />}
        </div>
      </div>
    </div>
  )
}

function ProfileSettings() {
  const { user } = useAuth()
  const [profile, setProfile] = useState<ProfileResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null)
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')

  useEffect(() => {
    settingsApi.getProfile()
      .then((res) => {
        const data = res.data
        setProfile(data)
        setFullName(data.full_name || '')
        setEmail(data.email || '')
      })
      .catch(() => setToast({ message: 'Failed to load profile', type: 'error' }))
      .finally(() => setLoading(false))
  }, [])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setSaving(true)
    try {
      const res = await settingsApi.updateProfile({ full_name: fullName, email })
      setProfile(res.data)
      setToast({ message: 'Profile updated successfully', type: 'success' })
    } catch {
      setToast({ message: 'Failed to update profile', type: 'error' })
    } finally {
      setSaving(false)
    }
  }

  const initials = (profile?.full_name || user?.full_name || 'U')
    .split(' ')
    .map((n: string) => n[0])
    .join('')
    .toUpperCase()

  return (
    <div className="card">
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
      <h2 className="text-lg font-semibold text-gray-900 mb-6">Profile Settings</h2>

      {loading ? (
        <LoadingSkeleton lines={5} />
      ) : (
        <form className="space-y-6" onSubmit={handleSubmit}>
          <div className="flex items-center gap-6">
            <div className="h-20 w-20 rounded-full bg-primary-100 flex items-center justify-center text-2xl font-bold text-primary-600">
              {initials}
            </div>
            <div>
              <button type="button" className="btn-secondary">Change Photo</button>
              <p className="text-xs text-gray-500 mt-1">JPG, PNG. Max 2MB</p>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          {profile?.oauth_provider && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Login Provider</label>
              <input
                type="text"
                value={profile.oauth_provider}
                disabled
                className="w-full px-3 py-2 border border-gray-200 rounded-lg bg-gray-50 text-gray-500"
              />
            </div>
          )}

          {profile?.last_login_at && (
            <p className="text-xs text-gray-400">
              Last login: {new Date(profile.last_login_at).toLocaleString()}
            </p>
          )}

          <div className="flex justify-end">
            <button type="submit" className="btn-primary flex items-center gap-2" disabled={saving}>
              {saving && <Loader2 className="h-4 w-4 animate-spin" />}
              Save Changes
            </button>
          </div>
        </form>
      )}
    </div>
  )
}

function OrganizationSettings() {
  const { user } = useAuth()

  return (
    <div className="space-y-6">
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-6">Organization Settings</h2>
        <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg mb-6">
          <div className="h-12 w-12 rounded-full bg-primary-100 flex items-center justify-center font-bold text-primary-600">
            {(user?.full_name || 'U')[0]}
          </div>
          <div>
            <p className="font-medium text-gray-900">{user?.full_name || 'User'}</p>
            <p className="text-sm text-gray-500">{user?.email || ''}</p>
          </div>
        </div>
        <div className="p-6 border-2 border-dashed border-gray-200 rounded-lg text-center">
          <Building className="h-10 w-10 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 font-medium">Coming Soon</p>
          <p className="text-sm text-gray-400 mt-1">
            Organization management features are under development.
          </p>
        </div>
      </div>
    </div>
  )
}

function NotificationSettings() {
  const [prefs, setPrefs] = useState<NotificationPreferences | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null)

  useEffect(() => {
    settingsApi.getNotifications()
      .then((res) => setPrefs(res.data))
      .catch(() => setToast({ message: 'Failed to load notification preferences', type: 'error' }))
      .finally(() => setLoading(false))
  }, [])

  const handleSave = async () => {
    if (!prefs) return
    setSaving(true)
    try {
      const res = await settingsApi.updateNotifications(prefs)
      setPrefs(res.data)
      setToast({ message: 'Notification preferences saved', type: 'success' })
    } catch {
      setToast({ message: 'Failed to save preferences', type: 'error' })
    } finally {
      setSaving(false)
    }
  }

  const updatePref = <K extends keyof NotificationPreferences>(key: K, value: NotificationPreferences[K]) => {
    setPrefs((prev) => prev ? { ...prev, [key]: value } : prev)
  }

  return (
    <div className="card">
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
      <h2 className="text-lg font-semibold text-gray-900 mb-6">Notification Preferences</h2>

      {loading ? (
        <LoadingSkeleton lines={5} />
      ) : prefs ? (
        <>
          <div className="space-y-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="font-medium text-gray-900">Email Notifications</p>
                <p className="text-sm text-gray-500">Receive compliance updates via email</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={prefs.email_enabled}
                  onChange={(e) => updatePref('email_enabled', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
              </label>
            </div>

            {prefs.email_enabled && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email Digest Frequency</label>
                <select
                  value={prefs.email_digest}
                  onChange={(e) => updatePref('email_digest', e.target.value as NotificationPreferences['email_digest'])}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="realtime">Real-time</option>
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="never">Never</option>
                </select>
              </div>
            )}

            <div className="flex items-start justify-between">
              <div>
                <p className="font-medium text-gray-900">Slack Notifications</p>
                <p className="text-sm text-gray-500">Send compliance alerts to Slack</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={prefs.slack_enabled}
                  onChange={(e) => updatePref('slack_enabled', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
              </label>
            </div>

            {prefs.slack_enabled && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Slack Webhook URL</label>
                <input
                  type="url"
                  value={prefs.slack_webhook_url || ''}
                  onChange={(e) => updatePref('slack_webhook_url', e.target.value || null)}
                  placeholder="https://hooks.slack.com/services/..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
            )}

            <div className="flex items-start justify-between">
              <div>
                <p className="font-medium text-gray-900">Webhook Notifications</p>
                <p className="text-sm text-gray-500">Send events to a custom webhook endpoint</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={prefs.webhook_enabled}
                  onChange={(e) => updatePref('webhook_enabled', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
              </label>
            </div>

            {prefs.webhook_enabled && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Webhook URL</label>
                <input
                  type="url"
                  value={prefs.webhook_url || ''}
                  onChange={(e) => updatePref('webhook_url', e.target.value || null)}
                  placeholder="https://your-server.com/webhook"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
            )}
          </div>

          <div className="mt-6 pt-6 border-t flex justify-end">
            <button onClick={handleSave} className="btn-primary flex items-center gap-2" disabled={saving}>
              {saving && <Loader2 className="h-4 w-4 animate-spin" />}
              Save Preferences
            </button>
          </div>
        </>
      ) : (
        <p className="text-gray-500">Could not load notification preferences.</p>
      )}
    </div>
  )
}

function SecuritySettings() {
  const { logout } = useAuth()
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [saving, setSaving] = useState(false)
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (newPassword !== confirmPassword) {
      setToast({ message: 'New passwords do not match', type: 'error' })
      return
    }
    if (newPassword.length < 8) {
      setToast({ message: 'Password must be at least 8 characters', type: 'error' })
      return
    }
    setSaving(true)
    try {
      await settingsApi.changePassword({ current_password: currentPassword, new_password: newPassword })
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
      setToast({ message: 'Password changed. You will be logged out.', type: 'success' })
      setTimeout(() => logout(), 2000)
    } catch {
      setToast({ message: 'Failed to change password. Check your current password.', type: 'error' })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-6">Change Password</h2>

        <form className="space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Current Password</label>
            <input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">New Password</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              minLength={8}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Confirm New Password</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              minLength={8}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <button type="submit" className="btn-primary flex items-center gap-2" disabled={saving}>
            {saving && <Loader2 className="h-4 w-4 animate-spin" />}
            Update Password
          </button>
        </form>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-6">Two-Factor Authentication</h2>
        <p className="text-gray-600 mb-4">
          Add an extra layer of security to your account by enabling two-factor authentication.
        </p>
        <button className="btn-primary" disabled>Enable 2FA (Coming Soon)</button>
      </div>
    </div>
  )
}

function BillingSettings() {
  return (
    <div className="space-y-6">
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-6">Billing & Subscription</h2>
        <div className="p-6 border-2 border-dashed border-gray-200 rounded-lg text-center">
          <CreditCard className="h-10 w-10 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 font-medium">Coming Soon</p>
          <p className="text-sm text-gray-400 mt-1">
            Billing and subscription management features are under development.
          </p>
        </div>
      </div>
    </div>
  )
}

function ApiKeySettings() {
  const [keys, setKeys] = useState<APIKeyRead[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [revokingId, setRevokingId] = useState<string | null>(null)
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null)
  const [newKeyName, setNewKeyName] = useState('')
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [createdKey, setCreatedKey] = useState<string | null>(null)

  const fetchKeys = async () => {
    try {
      const res = await apiKeysApi.list()
      setKeys(res.data.items)
    } catch {
      setToast({ message: 'Failed to load API keys', type: 'error' })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchKeys() }, [])

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault()
    if (!newKeyName.trim()) return
    setCreating(true)
    try {
      const res = await apiKeysApi.create({ name: newKeyName.trim() })
      setCreatedKey(res.data.key)
      setNewKeyName('')
      setShowCreateForm(false)
      setToast({ message: 'API key created. Copy it now — it won\'t be shown again!', type: 'success' })
      await fetchKeys()
    } catch {
      setToast({ message: 'Failed to create API key', type: 'error' })
    } finally {
      setCreating(false)
    }
  }

  const handleRevoke = async (id: string) => {
    setRevokingId(id)
    try {
      await apiKeysApi.revoke(id)
      setToast({ message: 'API key revoked', type: 'success' })
      await fetchKeys()
    } catch {
      setToast({ message: 'Failed to revoke API key', type: 'error' })
    } finally {
      setRevokingId(null)
    }
  }

  const copyKey = (key: string) => {
    navigator.clipboard.writeText(key)
    setToast({ message: 'Copied to clipboard', type: 'success' })
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  }

  return (
    <div className="space-y-6">
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}

      {createdKey && (
        <div className="card bg-yellow-50 border-yellow-300">
          <h3 className="font-semibold text-yellow-900 mb-2">🔑 Your New API Key</h3>
          <p className="text-yellow-800 text-sm mb-3">
            Copy this key now. It will not be shown again.
          </p>
          <div className="flex items-center gap-2">
            <code className="flex-1 p-3 bg-white rounded-lg border border-yellow-200 font-mono text-sm break-all">
              {createdKey}
            </code>
            <button
              onClick={() => copyKey(createdKey)}
              className="btn-secondary p-2 flex-shrink-0"
              title="Copy to clipboard"
            >
              <Copy className="h-4 w-4" />
            </button>
          </div>
          <button
            onClick={() => setCreatedKey(null)}
            className="mt-3 text-yellow-700 hover:text-yellow-900 text-sm font-medium"
          >
            Dismiss
          </button>
        </div>
      )}

      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">API Keys</h2>
            <p className="text-gray-500">Manage API keys for programmatic access</p>
          </div>
          <button
            onClick={() => setShowCreateForm(true)}
            className="btn-primary flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            Generate Key
          </button>
        </div>

        {showCreateForm && (
          <form onSubmit={handleCreate} className="mb-6 p-4 bg-gray-50 rounded-lg flex items-end gap-3">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">Key Name</label>
              <input
                type="text"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                placeholder="e.g. Production API Key"
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <button type="submit" className="btn-primary flex items-center gap-2" disabled={creating}>
              {creating && <Loader2 className="h-4 w-4 animate-spin" />}
              Create
            </button>
            <button type="button" onClick={() => setShowCreateForm(false)} className="btn-secondary">
              Cancel
            </button>
          </form>
        )}

        {loading ? (
          <LoadingSkeleton lines={4} />
        ) : keys.length === 0 ? (
          <div className="text-center py-8">
            <Key className="h-10 w-10 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">No API keys yet. Generate one to get started.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {keys.map((apiKey) => (
              <div key={apiKey.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium text-gray-900">{apiKey.name}</p>
                  <p className="text-sm text-gray-500 font-mono">{apiKey.prefix}••••••••••••</p>
                  <p className="text-xs text-gray-400 mt-1">
                    Created: {formatDate(apiKey.created_at)}
                    {' • '}Last used: {apiKey.last_used_at ? formatDate(apiKey.last_used_at) : 'Never'}
                    {' • '}Status: <span className={apiKey.status === 'active' ? 'text-green-600' : 'text-red-500'}>{apiKey.status}</span>
                  </p>
                </div>
                <button
                  onClick={() => handleRevoke(apiKey.id)}
                  disabled={revokingId === apiKey.id || apiKey.status !== 'active'}
                  className="text-red-500 hover:text-red-700 p-2 disabled:opacity-50"
                  title="Revoke key"
                >
                  {revokingId === apiKey.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="card bg-blue-50 border-blue-200">
        <h3 className="font-semibold text-blue-900 mb-2">API Documentation</h3>
        <p className="text-blue-800 text-sm mb-4">
          Learn how to integrate ComplianceAgent into your workflow with our comprehensive API documentation.
        </p>
        <a href="/docs/api" className="text-blue-600 hover:text-blue-700 font-medium text-sm">
          View Documentation →
        </a>
      </div>
    </div>
  )
}
