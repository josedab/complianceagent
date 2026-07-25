'use client';

import { useState, useEffect, FormEvent } from 'react';
import Image from 'next/image';
import {
  User,
  Building,
  Bell,
  Shield,
  CreditCard,
  Key,
  Trash2,
  Plus,
  Loader2,
  Check,
  AlertCircle,
  Copy,
  Upload,
} from 'lucide-react';
import { settingsApi, apiKeysApi, billingApi, organizationsApi, authApi } from '@/lib/api';
import { useAuth } from '@/contexts/auth';

interface ProfileResponse {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_verified: boolean;
  last_login_at: string | null;
  oauth_provider: string | null;
  avatar_url: string | null;
  mfa_enabled: boolean;
}

interface NotificationPreferences {
  email_enabled: boolean;
  email_digest: string;
  slack_enabled: boolean;
  slack_webhook_url: string | null;
  webhook_enabled: boolean;
  webhook_url: string | null;
}

interface APIKeyRead {
  id: string;
  name: string;
  prefix: string;
  scopes: string[];
  status: string;
  created_at: string;
  expires_at: string | null;
  last_used_at: string | null;
  usage_count: number;
  created_by: string | null;
}

function LoadingSkeleton({ lines = 3 }: { lines?: number }) {
  return (
    <div className="animate-pulse space-y-4">
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="h-4 bg-gray-200 rounded w-full"
          style={{ width: `${80 - i * 15}%` }}
        />
      ))}
    </div>
  );
}

function Toast({
  message,
  type,
  onClose,
}: {
  message: string;
  type: 'success' | 'error';
  onClose: () => void;
}) {
  useEffect(() => {
    const timer = setTimeout(onClose, 4000);
    return () => clearTimeout(timer);
  }, [onClose]);

  return (
    <div
      className={`fixed top-4 right-4 z-50 flex items-center gap-2 px-4 py-3 rounded-lg shadow-lg text-sm font-medium ${
        type === 'success'
          ? 'bg-green-50 text-green-800 border border-green-200'
          : 'bg-red-50 text-red-800 border border-red-200'
      }`}
    >
      {type === 'success' ? <Check className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
      {message}
    </div>
  );
}

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('profile');

  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'organization', label: 'Organization', icon: Building },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'security', label: 'Security', icon: Shield },
    { id: 'billing', label: 'Billing', icon: CreditCard },
    { id: 'api', label: 'API Keys', icon: Key },
  ];

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
              const Icon = tab.icon;
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
              );
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
  );
}

function ProfileSettings() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<ProfileResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');

  useEffect(() => {
    settingsApi
      .getProfile()
      .then((res) => {
        const data = res.data;
        setProfile(data);
        setFullName(data.full_name || '');
        setEmail(data.email || '');
      })
      .catch(() => setToast({ message: 'Failed to load profile', type: 'error' }))
      .finally(() => setLoading(false));
  }, []);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const res = await settingsApi.updateProfile({ full_name: fullName, email });
      setProfile(res.data);
      setToast({ message: 'Profile updated successfully', type: 'success' });
    } catch {
      setToast({ message: 'Failed to update profile', type: 'error' });
    } finally {
      setSaving(false);
    }
  };

  const initials = (profile?.full_name || user?.full_name || 'U')
    .split(' ')
    .map((n: string) => n[0])
    .join('')
    .toUpperCase();

  return (
    <div className="card">
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
      <h2 className="text-lg font-semibold text-gray-900 mb-6">Profile Settings</h2>

      {loading ? (
        <LoadingSkeleton lines={5} />
      ) : (
        <form className="space-y-6" onSubmit={handleSubmit}>
          <div className="flex items-center gap-6">
            <div className="relative">
              {profile?.avatar_url ? (
                <Image
                  src={profile.avatar_url}
                  alt="Avatar"
                  width={80}
                  height={80}
                  unoptimized
                  className="h-20 w-20 rounded-full object-cover"
                />
              ) : (
                <div className="h-20 w-20 rounded-full bg-primary-100 flex items-center justify-center text-2xl font-bold text-primary-600">
                  {initials}
                </div>
              )}
            </div>
            <div>
              <label className="btn-secondary cursor-pointer inline-flex items-center gap-2">
                <Upload className="h-4 w-4" />
                Change Photo
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  className="hidden"
                  onChange={async (e) => {
                    const file = e.target.files?.[0];
                    if (!file) return;
                    try {
                      const res = await settingsApi.uploadAvatar(file);
                      setProfile(res.data);
                      setToast({ message: 'Avatar updated', type: 'success' });
                    } catch {
                      setToast({ message: 'Failed to upload avatar', type: 'error' });
                    }
                  }}
                />
              </label>
              {profile?.avatar_url && (
                <button
                  type="button"
                  className="ml-2 text-sm text-red-500 hover:text-red-700"
                  onClick={async () => {
                    try {
                      const res = await settingsApi.deleteAvatar();
                      setProfile(res.data);
                      setToast({ message: 'Avatar removed', type: 'success' });
                    } catch {
                      setToast({ message: 'Failed to remove avatar', type: 'error' });
                    }
                  }}
                >
                  Remove
                </button>
              )}
              <p className="text-xs text-gray-500 mt-1">JPG, PNG, WebP. Max 2MB</p>
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
  );
}

function OrganizationSettings() {
  const [orgs, setOrgs] = useState<Array<{ id: string; name: string; slug: string; plan: string }>>(
    []
  );
  const [members, setMembers] = useState<
    Array<{ id: string; user_id: string; role: string; user_email?: string; user_name?: string }>
  >([]);
  const [invitations, setInvitations] = useState<
    Array<{ id: string; email: string; role: string; status: string }>
  >([]);
  const [loading, setLoading] = useState(true);
  const [selectedOrg, setSelectedOrg] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [newSlug, setNewSlug] = useState('');
  const [invEmail, setInvEmail] = useState('');
  const [invRole, setInvRole] = useState('member');
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  useEffect(() => {
    organizationsApi
      .list()
      .then(async (res) => {
        setOrgs(res.data);
        if (res.data.length > 0) {
          await authApi.switchOrganization(res.data[0].id);
          setSelectedOrg(res.data[0].id);
        }
      })
      .catch(() => setToast({ message: 'Failed to load organizations', type: 'error' }))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedOrg) return;
    organizationsApi
      .listMembers(selectedOrg)
      .then((res) => setMembers(res.data))
      .catch(() => {});
    organizationsApi
      .listInvitations(selectedOrg)
      .then((res) => setInvitations(res.data))
      .catch(() => {});
  }, [selectedOrg]);

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    try {
      const res = await organizationsApi.create({ name: newName, slug: newSlug });
      setOrgs((prev) => [...prev, res.data]);
      await authApi.switchOrganization(res.data.id);
      setSelectedOrg(res.data.id);
      setShowCreate(false);
      setNewName('');
      setNewSlug('');
      setToast({ message: 'Organization created', type: 'success' });
    } catch {
      setToast({ message: 'Failed to create organization', type: 'error' });
    }
  };

  const handleInvite = async (e: FormEvent) => {
    e.preventDefault();
    if (!selectedOrg) return;
    try {
      await organizationsApi.createInvitation(selectedOrg, { email: invEmail, role: invRole });
      setInvEmail('');
      setToast({ message: 'Invitation sent', type: 'success' });
      organizationsApi.listInvitations(selectedOrg).then((res) => setInvitations(res.data));
    } catch {
      setToast({ message: 'Failed to send invitation', type: 'error' });
    }
  };

  return (
    <div className="space-y-6">
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-gray-900">Organizations</h2>
          <button
            onClick={() => setShowCreate(true)}
            className="btn-primary flex items-center gap-2"
          >
            <Plus className="h-4 w-4" /> New Organization
          </button>
        </div>

        {showCreate && (
          <form onSubmit={handleCreate} className="mb-6 p-4 bg-gray-50 rounded-lg space-y-3">
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Organization Name"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
            <input
              type="text"
              value={newSlug}
              onChange={(e) => setNewSlug(e.target.value)}
              placeholder="slug (lowercase, hyphens)"
              required
              pattern="^[a-z0-9-]+$"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
            <div className="flex gap-2">
              <button type="submit" className="btn-primary">
                Create
              </button>
              <button type="button" onClick={() => setShowCreate(false)} className="btn-secondary">
                Cancel
              </button>
            </div>
          </form>
        )}

        {loading ? (
          <LoadingSkeleton lines={3} />
        ) : (
          <div className="space-y-2">
            {orgs.map((org) => (
              <button
                key={org.id}
                onClick={async () => {
                  try {
                    await authApi.switchOrganization(org.id);
                    setSelectedOrg(org.id);
                  } catch {
                    setToast({ message: 'Failed to switch organization', type: 'error' });
                  }
                }}
                className={`w-full text-left p-3 rounded-lg border transition-colors ${selectedOrg === org.id ? 'border-primary-500 bg-primary-50' : 'border-gray-200 hover:bg-gray-50'}`}
              >
                <p className="font-medium text-gray-900">{org.name}</p>
                <p className="text-xs text-gray-500">
                  {org.slug} • {org.plan}
                </p>
              </button>
            ))}
            {orgs.length === 0 && (
              <p className="text-gray-500 text-center py-4">No organizations yet</p>
            )}
          </div>
        )}
      </div>

      {selectedOrg && (
        <>
          <div className="card">
            <h3 className="text-md font-semibold text-gray-900 mb-4">Members</h3>
            <div className="space-y-2">
              {members.map((m) => (
                <div
                  key={m.id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div>
                    <p className="font-medium text-gray-900">{m.user_name || 'Unknown'}</p>
                    <p className="text-xs text-gray-500">
                      {m.user_email} • {m.role}
                    </p>
                  </div>
                  {m.role !== 'owner' && (
                    <button
                      onClick={async () => {
                        await organizationsApi.removeMember(selectedOrg, m.user_id);
                        setMembers((prev) => prev.filter((x) => x.id !== m.id));
                      }}
                      className="text-red-500 hover:text-red-700 text-sm"
                    >
                      Remove
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <h3 className="text-md font-semibold text-gray-900 mb-4">Invite Member</h3>
            <form onSubmit={handleInvite} className="flex gap-3 items-end">
              <div className="flex-1">
                <input
                  type="email"
                  value={invEmail}
                  onChange={(e) => setInvEmail(e.target.value)}
                  placeholder="email@example.com"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <select
                value={invRole}
                onChange={(e) => setInvRole(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg"
              >
                <option value="member">Member</option>
                <option value="admin">Admin</option>
                <option value="viewer">Viewer</option>
              </select>
              <button type="submit" className="btn-primary">
                Invite
              </button>
            </form>
            {invitations.length > 0 && (
              <div className="mt-4 space-y-2">
                <p className="text-sm font-medium text-gray-700">Pending Invitations</p>
                {invitations.map((inv) => (
                  <div
                    key={inv.id}
                    className="flex items-center justify-between p-2 bg-yellow-50 rounded text-sm"
                  >
                    <span>
                      {inv.email} ({inv.role})
                    </span>
                    <button
                      onClick={async () => {
                        await organizationsApi.revokeInvitation(selectedOrg, inv.id);
                        setInvitations((prev) => prev.filter((x) => x.id !== inv.id));
                      }}
                      className="text-red-500 hover:text-red-700 text-xs"
                    >
                      Revoke
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

function NotificationSettings() {
  const [prefs, setPrefs] = useState<NotificationPreferences | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  useEffect(() => {
    settingsApi
      .getNotifications()
      .then((res) => setPrefs(res.data))
      .catch(() => setToast({ message: 'Failed to load notification preferences', type: 'error' }))
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    if (!prefs) return;
    setSaving(true);
    try {
      const res = await settingsApi.updateNotifications(prefs);
      setPrefs(res.data);
      setToast({ message: 'Notification preferences saved', type: 'success' });
    } catch {
      setToast({ message: 'Failed to save preferences', type: 'error' });
    } finally {
      setSaving(false);
    }
  };

  const updatePref = <K extends keyof NotificationPreferences>(
    key: K,
    value: NotificationPreferences[K]
  ) => {
    setPrefs((prev) => (prev ? { ...prev, [key]: value } : prev));
  };

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
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email Digest Frequency
                </label>
                <select
                  value={prefs.email_digest}
                  onChange={(e) =>
                    updatePref(
                      'email_digest',
                      e.target.value as NotificationPreferences['email_digest']
                    )
                  }
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
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Slack Webhook URL
                </label>
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
            <button
              onClick={handleSave}
              className="btn-primary flex items-center gap-2"
              disabled={saving}
            >
              {saving && <Loader2 className="h-4 w-4 animate-spin" />}
              Save Preferences
            </button>
          </div>
        </>
      ) : (
        <p className="text-gray-500">Could not load notification preferences.</p>
      )}
    </div>
  );
}

function SecuritySettings() {
  const { logout } = useAuth();
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  // MFA state
  const [mfaEnabled, setMfaEnabled] = useState(false);
  const [mfaSetupData, setMfaSetupData] = useState<{
    secret: string;
    otpauth_uri: string;
    recovery_codes: string[];
  } | null>(null);
  const [mfaCode, setMfaCode] = useState('');
  const [mfaLoading, setMfaLoading] = useState(false);

  // Account deactivation
  const [showDeactivate, setShowDeactivate] = useState(false);
  const [deactivatePassword, setDeactivatePassword] = useState('');

  useEffect(() => {
    settingsApi
      .getProfile()
      .then((res) => setMfaEnabled(res.data.mfa_enabled))
      .catch(() => {});
  }, []);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setToast({ message: 'New passwords do not match', type: 'error' });
      return;
    }
    if (newPassword.length < 8) {
      setToast({ message: 'Password must be at least 8 characters', type: 'error' });
      return;
    }
    setSaving(true);
    try {
      await settingsApi.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setToast({ message: 'Password changed. You will be logged out.', type: 'success' });
      setTimeout(() => logout(), 2000);
    } catch {
      setToast({
        message: 'Failed to change password. Check your current password.',
        type: 'error',
      });
    } finally {
      setSaving(false);
    }
  };

  const handleMfaSetup = async () => {
    setMfaLoading(true);
    try {
      const res = await authApi.mfaSetup();
      setMfaSetupData(res.data);
    } catch {
      setToast({ message: 'Failed to start 2FA setup', type: 'error' });
    } finally {
      setMfaLoading(false);
    }
  };

  const handleMfaConfirm = async () => {
    setMfaLoading(true);
    try {
      await authApi.mfaConfirm(mfaCode);
      setMfaEnabled(true);
      setMfaSetupData(null);
      setMfaCode('');
      setToast({ message: 'Two-factor authentication enabled', type: 'success' });
    } catch {
      setToast({ message: 'Invalid code. Try again.', type: 'error' });
    } finally {
      setMfaLoading(false);
    }
  };

  const handleMfaDisable = async () => {
    setMfaLoading(true);
    try {
      await authApi.mfaDisable(mfaCode);
      setMfaEnabled(false);
      setMfaCode('');
      setToast({ message: 'Two-factor authentication disabled', type: 'success' });
    } catch {
      setToast({ message: 'Invalid code', type: 'error' });
    } finally {
      setMfaLoading(false);
    }
  };

  const handleDeactivate = async () => {
    try {
      await authApi.deactivateAccount(deactivatePassword);
      await logout();
    } catch {
      setToast({ message: 'Failed to deactivate account. Check your password.', type: 'error' });
    }
  };

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
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Confirm New Password
            </label>
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
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Two-Factor Authentication</h2>
        {mfaEnabled ? (
          <div>
            <div className="flex items-center gap-2 mb-4">
              <Check className="h-5 w-5 text-green-500" />
              <span className="text-green-700 font-medium">2FA is enabled</span>
            </div>
            <div className="flex gap-3 items-end">
              <input
                type="text"
                value={mfaCode}
                onChange={(e) => setMfaCode(e.target.value)}
                placeholder="Enter TOTP code to disable"
                maxLength={6}
                className="px-3 py-2 border border-gray-300 rounded-lg w-48"
              />
              <button
                onClick={handleMfaDisable}
                disabled={mfaLoading || mfaCode.length !== 6}
                className="btn-secondary text-red-600 border-red-300 hover:bg-red-50"
              >
                {mfaLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Disable 2FA'}
              </button>
            </div>
          </div>
        ) : mfaSetupData ? (
          <div className="space-y-4">
            <p className="text-sm text-gray-600">
              Scan the QR code or enter the secret manually in your authenticator app.
            </p>
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-xs text-gray-500 mb-2">Manual entry secret:</p>
              <code className="text-sm font-mono break-all">{mfaSetupData.secret}</code>
            </div>
            <div className="p-4 bg-yellow-50 rounded-lg">
              <p className="text-xs font-semibold text-yellow-800 mb-2">
                Recovery codes — save these securely!
              </p>
              <div className="grid grid-cols-2 gap-1">
                {mfaSetupData.recovery_codes.map((c) => (
                  <code key={c} className="text-sm font-mono text-yellow-900">
                    {c}
                  </code>
                ))}
              </div>
            </div>
            <div className="flex gap-3 items-end">
              <input
                type="text"
                value={mfaCode}
                onChange={(e) => setMfaCode(e.target.value)}
                placeholder="Enter code from app"
                maxLength={6}
                className="px-3 py-2 border border-gray-300 rounded-lg w-48"
              />
              <button
                onClick={handleMfaConfirm}
                disabled={mfaLoading || mfaCode.length !== 6}
                className="btn-primary flex items-center gap-2"
              >
                {mfaLoading && <Loader2 className="h-4 w-4 animate-spin" />}
                Verify & Enable
              </button>
            </div>
          </div>
        ) : (
          <div>
            <p className="text-gray-600 mb-4">
              Add an extra layer of security with a time-based one-time password (TOTP) app.
            </p>
            <button
              onClick={handleMfaSetup}
              disabled={mfaLoading}
              className="btn-primary flex items-center gap-2"
            >
              {mfaLoading && <Loader2 className="h-4 w-4 animate-spin" />}
              Set Up 2FA
            </button>
          </div>
        )}
      </div>

      <div className="card border-red-200">
        <h2 className="text-lg font-semibold text-red-700 mb-4">Danger Zone</h2>
        {showDeactivate ? (
          <div className="space-y-3">
            <p className="text-sm text-gray-600">
              Enter your password to confirm account deactivation. Your data will be anonymized and
              scheduled for deletion in 30 days.
            </p>
            <input
              type="password"
              value={deactivatePassword}
              onChange={(e) => setDeactivatePassword(e.target.value)}
              placeholder="Current password"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
            <div className="flex gap-2">
              <button
                onClick={handleDeactivate}
                disabled={!deactivatePassword}
                className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                Deactivate Account
              </button>
              <button onClick={() => setShowDeactivate(false)} className="btn-secondary">
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <button
            onClick={() => setShowDeactivate(true)}
            className="text-red-600 hover:text-red-800 font-medium text-sm flex items-center gap-2"
          >
            <Trash2 className="h-4 w-4" /> Deactivate Account
          </button>
        )}
      </div>
    </div>
  );
}

function BillingSettings() {
  const [subscription, setSubscription] = useState<{
    plan_tier: string;
    status: string;
    billing_email: string;
    cancel_at_period_end: boolean;
  } | null>(null);
  const [usage, setUsage] = useState<{
    repositories: { used: number; limit: number };
    users: { used: number; limit: number };
  } | null>(null);
  const [plans, setPlans] = useState<
    Array<{ tier: string; name: string; price_monthly: number; features: string[] }>
  >([]);
  const [invoices, setInvoices] = useState<
    Array<{ id: string; date: string; amount: number; status: string }>
  >([]);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  useEffect(() => {
    Promise.all([
      billingApi.subscription().catch(() => ({ data: null })),
      billingApi.usage().catch(() => ({ data: null })),
      billingApi.plans().catch(() => ({ data: [] })),
      billingApi.invoices().catch(() => ({ data: [] })),
    ])
      .then(([sub, usg, pl, inv]) => {
        setSubscription(sub.data);
        setUsage(usg.data);
        setPlans(pl.data);
        setInvoices(inv.data);
      })
      .finally(() => setLoading(false));
  }, []);

  const handlePortal = async () => {
    try {
      const res = await billingApi.portal();
      window.open(res.data.portal_url, '_blank');
    } catch {
      setToast({
        message: 'Billing portal unavailable. Stripe may not be configured.',
        type: 'error',
      });
    }
  };

  if (loading)
    return (
      <div className="card">
        <LoadingSkeleton lines={5} />
      </div>
    );

  return (
    <div className="space-y-6">
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Subscription</h2>
        {subscription ? (
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <span className="text-xl font-bold text-primary-600 capitalize">
                {subscription.plan_tier}
              </span>
              <span
                className={`text-xs px-2 py-0.5 rounded-full ${subscription.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}
              >
                {subscription.status}
              </span>
            </div>
            <p className="text-sm text-gray-500">Billing email: {subscription.billing_email}</p>
            <button onClick={handlePortal} className="btn-secondary">
              Manage Billing →
            </button>
          </div>
        ) : (
          <p className="text-gray-500">No active subscription found.</p>
        )}
      </div>

      {usage && (
        <div className="card">
          <h3 className="text-md font-semibold text-gray-900 mb-4">Usage</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-500">Repositories</p>
              <p className="text-lg font-bold">
                {usage.repositories.used} / {usage.repositories.limit}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Team Members</p>
              <p className="text-lg font-bold">
                {usage.users.used} / {usage.users.limit}
              </p>
            </div>
          </div>
        </div>
      )}

      {invoices.length > 0 && (
        <div className="card">
          <h3 className="text-md font-semibold text-gray-900 mb-4">Recent Invoices</h3>
          <div className="space-y-2">
            {invoices.map((inv) => (
              <div
                key={inv.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg text-sm"
              >
                <span>{inv.date}</span>
                <span className="font-medium">${(inv.amount / 100).toFixed(2)}</span>
                <span className={inv.status === 'paid' ? 'text-green-600' : 'text-yellow-600'}>
                  {inv.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {plans.length > 0 && (
        <div className="card">
          <h3 className="text-md font-semibold text-gray-900 mb-4">Available Plans</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {plans.map((plan) => (
              <div
                key={plan.tier}
                className={`p-4 rounded-lg border ${subscription?.plan_tier === plan.tier ? 'border-primary-500 bg-primary-50' : 'border-gray-200'}`}
              >
                <p className="font-semibold text-gray-900">{plan.name}</p>
                <p className="text-lg font-bold text-primary-600">
                  ${(plan.price_monthly / 100).toFixed(0)}/mo
                </p>
                <ul className="mt-2 space-y-1">
                  {plan.features.slice(0, 3).map((f) => (
                    <li key={f} className="text-xs text-gray-500 flex items-center gap-1">
                      <Check className="h-3 w-3 text-green-500" />
                      {f}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function ApiKeySettings() {
  const [keys, setKeys] = useState<APIKeyRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [revokingId, setRevokingId] = useState<string | null>(null);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [newKeyName, setNewKeyName] = useState('');
  const [newKeyScopes, setNewKeyScopes] = useState<string[]>(['read']);
  const [newKeyExpiry, setNewKeyExpiry] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [createdKey, setCreatedKey] = useState<string | null>(null);

  const fetchKeys = async () => {
    try {
      const res = await apiKeysApi.list();
      setKeys(res.data.items);
    } catch {
      setToast({ message: 'Failed to load API keys', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchKeys();
  }, []);

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    if (!newKeyName.trim()) return;
    setCreating(true);
    try {
      const res = await apiKeysApi.create({
        name: newKeyName.trim(),
        scopes: newKeyScopes,
        expires_in_days: newKeyExpiry ? parseInt(newKeyExpiry) : undefined,
      });
      setCreatedKey(res.data.key);
      setNewKeyName('');
      setShowCreateForm(false);
      setToast({
        message: "API key created. Copy it now — it won't be shown again!",
        type: 'success',
      });
      await fetchKeys();
    } catch {
      setToast({ message: 'Failed to create API key', type: 'error' });
    } finally {
      setCreating(false);
    }
  };

  const handleRevoke = async (id: string) => {
    setRevokingId(id);
    try {
      await apiKeysApi.revoke(id);
      setToast({ message: 'API key revoked', type: 'success' });
      await fetchKeys();
    } catch {
      setToast({ message: 'Failed to revoke API key', type: 'error' });
    } finally {
      setRevokingId(null);
    }
  };

  const copyKey = (key: string) => {
    navigator.clipboard.writeText(key);
    setToast({ message: 'Copied to clipboard', type: 'success' });
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

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
          <form onSubmit={handleCreate} className="mb-6 p-4 bg-gray-50 rounded-lg space-y-3">
            <div>
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
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Scopes</label>
              <div className="flex flex-wrap gap-2">
                {[
                  'read',
                  'write',
                  'read:regulations',
                  'write:regulations',
                  'read:repositories',
                  'read:audit',
                  'read:billing',
                ].map((scope) => (
                  <label key={scope} className="inline-flex items-center gap-1 text-xs">
                    <input
                      type="checkbox"
                      checked={newKeyScopes.includes(scope)}
                      onChange={(e) => {
                        setNewKeyScopes((prev) =>
                          e.target.checked ? [...prev, scope] : prev.filter((s) => s !== scope)
                        );
                      }}
                      className="rounded border-gray-300 text-primary-600"
                    />
                    {scope}
                  </label>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Expires In (days, optional)
              </label>
              <input
                type="number"
                value={newKeyExpiry}
                onChange={(e) => setNewKeyExpiry(e.target.value)}
                min="1"
                max="365"
                placeholder="Never"
                className="w-48 px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>
            <div className="flex gap-2">
              <button
                type="submit"
                className="btn-primary flex items-center gap-2"
                disabled={creating}
              >
                {creating && <Loader2 className="h-4 w-4 animate-spin" />} Create
              </button>
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="btn-secondary"
              >
                Cancel
              </button>
            </div>
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
              <div
                key={apiKey.id}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
              >
                <div>
                  <p className="font-medium text-gray-900">{apiKey.name}</p>
                  <p className="text-sm text-gray-500 font-mono">{apiKey.prefix}••••••••••••</p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {apiKey.scopes.map((s) => (
                      <span
                        key={s}
                        className="text-[10px] px-1.5 py-0.5 bg-primary-100 text-primary-700 rounded"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                  <p className="text-xs text-gray-400 mt-1">
                    Created: {formatDate(apiKey.created_at)}
                    {apiKey.expires_at && <> • Expires: {formatDate(apiKey.expires_at)}</>}
                    {' • '}Last used:{' '}
                    {apiKey.last_used_at ? formatDate(apiKey.last_used_at) : 'Never'}
                    {' • '}Status:{' '}
                    <span
                      className={apiKey.status === 'active' ? 'text-green-600' : 'text-red-500'}
                    >
                      {apiKey.status}
                    </span>
                  </p>
                </div>
                <button
                  onClick={() => handleRevoke(apiKey.id)}
                  disabled={revokingId === apiKey.id || apiKey.status !== 'active'}
                  className="text-red-500 hover:text-red-700 p-2 disabled:opacity-50"
                  title="Revoke key"
                >
                  {revokingId === apiKey.id ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Trash2 className="h-4 w-4" />
                  )}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="card bg-blue-50 border-blue-200">
        <h3 className="font-semibold text-blue-900 mb-2">API Documentation</h3>
        <p className="text-blue-800 text-sm mb-4">
          Learn how to integrate ComplianceAgent into your workflow with our comprehensive API
          documentation.
        </p>
        <a href="/docs/api" className="text-blue-600 hover:text-blue-700 font-medium text-sm">
          View Documentation →
        </a>
      </div>
    </div>
  );
}
