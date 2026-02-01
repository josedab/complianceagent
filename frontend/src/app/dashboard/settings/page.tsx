'use client'

import { useState } from 'react'
import { User, Building, Bell, Shield, CreditCard, Key, Trash2, Plus } from 'lucide-react'

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
  return (
    <div className="card">
      <h2 className="text-lg font-semibold text-gray-900 mb-6">Profile Settings</h2>
      
      <form className="space-y-6">
        <div className="flex items-center gap-6">
          <div className="h-20 w-20 rounded-full bg-primary-100 flex items-center justify-center text-2xl font-bold text-primary-600">
            JD
          </div>
          <div>
            <button type="button" className="btn-secondary">Change Photo</button>
            <p className="text-xs text-gray-500 mt-1">JPG, PNG. Max 2MB</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">First Name</label>
            <input
              type="text"
              defaultValue="John"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Last Name</label>
            <input
              type="text"
              defaultValue="Doe"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <input
            type="email"
            defaultValue="john.doe@acme.com"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
          <input
            type="text"
            defaultValue="Engineering Manager"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        <div className="flex justify-end">
          <button type="submit" className="btn-primary">Save Changes</button>
        </div>
      </form>
    </div>
  )
}

function OrganizationSettings() {
  return (
    <div className="space-y-6">
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-6">Organization Settings</h2>
        
        <form className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Organization Name</label>
            <input
              type="text"
              defaultValue="Acme Corporation"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Industry</label>
            <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500">
              <option>Technology</option>
              <option>Finance</option>
              <option>Healthcare</option>
              <option>E-commerce</option>
              <option>Other</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Jurisdictions</label>
            <div className="flex flex-wrap gap-2">
              {['EU', 'US', 'UK', 'CA'].map((j) => (
                <span key={j} className="px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-sm flex items-center gap-1">
                  {j}
                  <button type="button" className="hover:text-primary-900">×</button>
                </span>
              ))}
              <button type="button" className="px-3 py-1 border border-dashed border-gray-300 rounded-full text-sm text-gray-500 hover:border-gray-400">
                + Add
              </button>
            </div>
          </div>

          <div className="flex justify-end">
            <button type="submit" className="btn-primary">Save Changes</button>
          </div>
        </form>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Team Members</h2>
        
        <div className="space-y-3">
          {[
            { name: 'John Doe', email: 'john.doe@acme.com', role: 'Admin' },
            { name: 'Jane Smith', email: 'jane.smith@acme.com', role: 'Member' },
            { name: 'Bob Wilson', email: 'bob.wilson@acme.com', role: 'Member' },
          ].map((member) => (
            <div key={member.email} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-full bg-primary-100 flex items-center justify-center font-medium text-primary-600">
                  {member.name.split(' ').map(n => n[0]).join('')}
                </div>
                <div>
                  <p className="font-medium text-gray-900">{member.name}</p>
                  <p className="text-sm text-gray-500">{member.email}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <select className="text-sm border border-gray-200 rounded-lg px-2 py-1">
                  <option selected={member.role === 'Admin'}>Admin</option>
                  <option selected={member.role === 'Member'}>Member</option>
                </select>
                <button className="text-red-500 hover:text-red-700 p-1">
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
        </div>

        <button className="mt-4 btn-secondary flex items-center gap-2">
          <Plus className="h-4 w-4" />
          Invite Team Member
        </button>
      </div>
    </div>
  )
}

function NotificationSettings() {
  return (
    <div className="card">
      <h2 className="text-lg font-semibold text-gray-900 mb-6">Notification Preferences</h2>
      
      <div className="space-y-6">
        {[
          { id: 'reg_updates', label: 'Regulatory Updates', desc: 'Get notified when new regulations or amendments are detected' },
          { id: 'compliance_alerts', label: 'Compliance Alerts', desc: 'Alerts when compliance gaps are detected in your codebase' },
          { id: 'action_reminders', label: 'Action Reminders', desc: 'Reminders for pending compliance actions' },
          { id: 'pr_updates', label: 'PR Updates', desc: 'Notifications when compliance PRs are merged or need attention' },
          { id: 'weekly_digest', label: 'Weekly Digest', desc: 'Weekly summary of compliance status and activities' },
        ].map((pref) => (
          <div key={pref.id} className="flex items-start justify-between">
            <div>
              <p className="font-medium text-gray-900">{pref.label}</p>
              <p className="text-sm text-gray-500">{pref.desc}</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" defaultChecked className="sr-only peer" />
              <div className="w-11 h-6 bg-gray-200 peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
            </label>
          </div>
        ))}
      </div>

      <div className="mt-6 pt-6 border-t">
        <h3 className="font-medium text-gray-900 mb-4">Notification Channels</h3>
        <div className="space-y-3">
          {[
            { id: 'email', label: 'Email' },
            { id: 'slack', label: 'Slack' },
            { id: 'in_app', label: 'In-App' },
          ].map((channel) => (
            <label key={channel.id} className="flex items-center gap-3">
              <input type="checkbox" defaultChecked className="h-4 w-4 text-primary-600 rounded" />
              <span>{channel.label}</span>
            </label>
          ))}
        </div>
      </div>
    </div>
  )
}

function SecuritySettings() {
  return (
    <div className="space-y-6">
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-6">Change Password</h2>
        
        <form className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Current Password</label>
            <input
              type="password"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">New Password</label>
            <input
              type="password"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Confirm New Password</label>
            <input
              type="password"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <button type="submit" className="btn-primary">Update Password</button>
        </form>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-6">Two-Factor Authentication</h2>
        <p className="text-gray-600 mb-4">
          Add an extra layer of security to your account by enabling two-factor authentication.
        </p>
        <button className="btn-primary">Enable 2FA</button>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Active Sessions</h2>
        <div className="space-y-3">
          {[
            { device: 'MacBook Pro', location: 'San Francisco, CA', current: true },
            { device: 'iPhone 15', location: 'San Francisco, CA', current: false },
          ].map((session, i) => (
            <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <p className="font-medium text-gray-900">
                  {session.device}
                  {session.current && <span className="ml-2 text-xs text-green-600">(Current)</span>}
                </p>
                <p className="text-sm text-gray-500">{session.location}</p>
              </div>
              {!session.current && (
                <button className="text-red-500 hover:text-red-700 text-sm">Revoke</button>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function BillingSettings() {
  return (
    <div className="space-y-6">
      <div className="card">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Current Plan</h2>
            <p className="text-gray-500">Professional Plan</p>
          </div>
          <span className="px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-sm font-medium">
            Active
          </span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-2xl font-bold text-gray-900">5</p>
            <p className="text-sm text-gray-500">Repositories</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-2xl font-bold text-gray-900">10</p>
            <p className="text-sm text-gray-500">Frameworks</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-2xl font-bold text-gray-900">20</p>
            <p className="text-sm text-gray-500">Team Members</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-2xl font-bold text-gray-900">$1,500</p>
            <p className="text-sm text-gray-500">/month</p>
          </div>
        </div>

        <div className="flex gap-3">
          <button className="btn-primary">Upgrade Plan</button>
          <button className="btn-secondary">Manage Subscription</button>
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Payment Method</h2>
        <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg mb-4">
          <div className="h-10 w-16 bg-gradient-to-r from-blue-600 to-blue-800 rounded flex items-center justify-center text-white text-xs font-bold">
            VISA
          </div>
          <div>
            <p className="font-medium text-gray-900">•••• •••• •••• 4242</p>
            <p className="text-sm text-gray-500">Expires 12/2027</p>
          </div>
        </div>
        <button className="btn-secondary">Update Payment Method</button>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Billing History</h2>
        <div className="space-y-2">
          {[
            { date: 'Jan 1, 2026', amount: '$1,500.00', status: 'Paid' },
            { date: 'Dec 1, 2025', amount: '$1,500.00', status: 'Paid' },
            { date: 'Nov 1, 2025', amount: '$1,500.00', status: 'Paid' },
          ].map((invoice, i) => (
            <div key={i} className="flex items-center justify-between py-2 border-b last:border-0">
              <div>
                <p className="font-medium text-gray-900">{invoice.date}</p>
                <p className="text-sm text-gray-500">{invoice.amount}</p>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-green-600 text-sm">{invoice.status}</span>
                <button className="text-primary-600 hover:text-primary-700 text-sm">Download</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function ApiKeySettings() {
  return (
    <div className="space-y-6">
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">API Keys</h2>
            <p className="text-gray-500">Manage API keys for programmatic access</p>
          </div>
          <button className="btn-primary flex items-center gap-2">
            <Plus className="h-4 w-4" />
            Generate Key
          </button>
        </div>

        <div className="space-y-3">
          {[
            { name: 'Production API Key', prefix: 'ca_prod_', created: 'Jan 15, 2026', lastUsed: '2 hours ago' },
            { name: 'Development API Key', prefix: 'ca_dev_', created: 'Jan 10, 2026', lastUsed: 'Never' },
          ].map((key) => (
            <div key={key.name} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <p className="font-medium text-gray-900">{key.name}</p>
                <p className="text-sm text-gray-500 font-mono">{key.prefix}••••••••••••</p>
                <p className="text-xs text-gray-400 mt-1">
                  Created: {key.created} • Last used: {key.lastUsed}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button className="btn-secondary text-sm py-1">Regenerate</button>
                <button className="text-red-500 hover:text-red-700 p-2">
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
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
