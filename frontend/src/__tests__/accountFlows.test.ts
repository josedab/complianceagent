/**
 * Tests for account settings, auth MFA flow, notification bell,
 * search, organization management, and API key controls.
 */
import * as apiModule from '@/lib/api';

describe('Account API clients', () => {
  const { api } = apiModule;

  beforeEach(() => {
    jest.spyOn(api, 'get').mockResolvedValue({ data: {} } as never);
    jest.spyOn(api, 'post').mockResolvedValue({ data: {} } as never);
    jest.spyOn(api, 'put').mockResolvedValue({ data: {} } as never);
    jest.spyOn(api, 'patch').mockResolvedValue({ data: {} } as never);
    jest.spyOn(api, 'delete').mockResolvedValue({ data: {} } as never);
  });

  afterEach(() => jest.restoreAllMocks());

  // Auth MFA
  it('authApi.mfaSetup calls POST /auth/mfa/setup', async () => {
    await apiModule.authApi.mfaSetup();
    expect(api.post).toHaveBeenCalledWith('/auth/mfa/setup');
  });

  it('authApi.mfaConfirm calls POST /auth/mfa/confirm', async () => {
    await apiModule.authApi.mfaConfirm('123456');
    expect(api.post).toHaveBeenCalledWith('/auth/mfa/confirm', { totp_code: '123456' });
  });

  it('authApi.mfaDisable calls POST /auth/mfa/disable', async () => {
    await apiModule.authApi.mfaDisable('654321');
    expect(api.post).toHaveBeenCalledWith('/auth/mfa/disable', { totp_code: '654321' });
  });

  it('authApi.mfaChallenge sends mfa_token and totp_code', async () => {
    await apiModule.authApi.mfaChallenge('tok', '123456');
    expect(api.post).toHaveBeenCalledWith('/auth/mfa/challenge', {
      mfa_token: 'tok',
      totp_code: '123456',
    });
  });

  it('authApi.verifyEmail sends token in the request body', async () => {
    await apiModule.authApi.verifyEmail('my-token');
    expect(api.post).toHaveBeenCalledWith('/auth/verify-email', { token: 'my-token' });
  });

  it('authApi.deactivateAccount sends password', async () => {
    await apiModule.authApi.deactivateAccount('pw');
    expect(api.post).toHaveBeenCalledWith('/auth/deactivate', {
      password: 'pw',
      confirm: true,
    });
  });

  // Notifications
  it('notificationsApi.unreadCount calls GET /notifications/unread-count', async () => {
    await apiModule.notificationsApi.unreadCount();
    expect(api.get).toHaveBeenCalledWith('/notifications/unread-count');
  });

  it('notificationsApi.markRead calls PATCH', async () => {
    await apiModule.notificationsApi.markRead('id-1');
    expect(api.patch).toHaveBeenCalledWith('/notifications/id-1/read');
  });

  it('notificationsApi.markAllRead calls POST', async () => {
    await apiModule.notificationsApi.markAllRead();
    expect(api.post).toHaveBeenCalledWith('/notifications/mark-all-read');
  });

  it('notificationsApi.delete calls DELETE', async () => {
    await apiModule.notificationsApi.delete('id-1');
    expect(api.delete).toHaveBeenCalledWith('/notifications/id-1');
  });

  // Search
  it('searchApi.search sends query param', async () => {
    await apiModule.searchApi.search('test', { limit: 5 });
    expect(api.get).toHaveBeenCalledWith('/search', {
      params: { q: 'test', limit: 5 },
    });
  });

  // Billing
  it('billingApi.subscription calls GET', async () => {
    await apiModule.billingApi.subscription();
    expect(api.get).toHaveBeenCalledWith('/billing/subscription');
  });

  it('billingApi.usage calls GET', async () => {
    await apiModule.billingApi.usage();
    expect(api.get).toHaveBeenCalledWith('/billing/usage');
  });

  // Organizations
  it('organizationsApi.listMembers calls GET with org id', async () => {
    await apiModule.organizationsApi.listMembers('org-1');
    expect(api.get).toHaveBeenCalledWith('/organizations/org-1/members');
  });

  it('organizationsApi.createInvitation sends email and role', async () => {
    await apiModule.organizationsApi.createInvitation('org-1', {
      email: 'test@example.com',
      role: 'member',
    });
    expect(api.post).toHaveBeenCalledWith('/organizations/org-1/invitations', {
      email: 'test@example.com',
      role: 'member',
    });
  });

  it('organizationsApi.acceptInvitation sends token', async () => {
    await apiModule.organizationsApi.acceptInvitation('tok123');
    expect(api.post).toHaveBeenCalledWith('/organizations/invitations/accept', {
      token: 'tok123',
    });
  });

  // API Keys scopes endpoint
  it('apiKeysApi.scopes calls GET /api-keys/scopes', async () => {
    await apiModule.apiKeysApi.scopes();
    expect(api.get).toHaveBeenCalledWith('/api-keys/scopes');
  });

  it('apiKeysApi.create sends scopes and expiry', async () => {
    await apiModule.apiKeysApi.create({
      name: 'Test Key',
      scopes: ['read', 'write'],
      expires_in_days: 30,
    });
    expect(api.post).toHaveBeenCalledWith('/api-keys', {
      name: 'Test Key',
      scopes: ['read', 'write'],
      expires_in_days: 30,
    });
  });

  // Settings avatar
  it('settingsApi.deleteAvatar calls DELETE', async () => {
    await apiModule.settingsApi.deleteAvatar();
    expect(api.delete).toHaveBeenCalledWith('/settings/avatar');
  });
});
