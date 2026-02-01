// API Response Types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

// Auth Types
export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// Organization Types
export interface Organization {
  id: string;
  name: string;
  slug: string;
  industry?: string;
  jurisdictions: string[];
  created_at: string;
  updated_at: string;
}

export interface OrganizationMember {
  id: string;
  user_id: string;
  organization_id: string;
  role: 'owner' | 'admin' | 'member';
  user: User;
}

// Regulation Types
export interface Regulation {
  id: string;
  name: string;
  short_name: string;
  framework: RegulatoryFramework;
  jurisdiction: Jurisdiction;
  version: string;
  effective_date: string;
  description?: string;
  source_url?: string;
  created_at: string;
  updated_at: string;
}

export type RegulatoryFramework = 
  | 'GDPR'
  | 'CCPA'
  | 'HIPAA'
  | 'EU_AI_ACT'
  | 'PCI_DSS'
  | 'SOX'
  | 'NIS2'
  | 'DORA'
  | 'CUSTOM';

export type Jurisdiction =
  | 'EU'
  | 'UK'
  | 'US_FEDERAL'
  | 'US_CALIFORNIA'
  | 'US_NEW_YORK'
  | 'SINGAPORE'
  | 'SOUTH_KOREA'
  | 'CHINA'
  | 'INDIA'
  | 'GLOBAL';

// Requirement Types
export interface Requirement {
  id: string;
  regulation_id: string;
  requirement_id: string;
  title: string;
  description: string;
  obligation_type: ObligationType;
  category: RequirementCategory;
  subject?: string;
  action?: string;
  object?: string;
  timeframe?: string;
  citations: Citation[];
  source_text?: string;
  confidence: number;
  is_approved: boolean;
  approved_by?: string;
  approved_at?: string;
  created_at: string;
  updated_at: string;
}

export type ObligationType = 'MUST' | 'MUST_NOT' | 'SHOULD' | 'SHOULD_NOT' | 'MAY';

export type RequirementCategory =
  | 'DATA_COLLECTION'
  | 'DATA_STORAGE'
  | 'DATA_PROCESSING'
  | 'DATA_TRANSFER'
  | 'DATA_DELETION'
  | 'DATA_ACCESS'
  | 'CONSENT'
  | 'DOCUMENTATION'
  | 'SECURITY'
  | 'AUDIT'
  | 'BREACH_RESPONSE'
  | 'AI_TRANSPARENCY'
  | 'AI_RISK_ASSESSMENT'
  | 'AI_HUMAN_OVERSIGHT'
  | 'OTHER';

export interface Citation {
  article: string;
  paragraph?: string;
  text?: string;
}

// Repository Types
export interface Repository {
  id: string;
  profile_id: string;
  platform: 'github' | 'gitlab' | 'bitbucket';
  owner: string;
  name: string;
  full_name: string;
  default_branch: string;
  primary_language?: string;
  is_active: boolean;
  last_analyzed_at?: string;
  webhook_id?: string;
  created_at: string;
  updated_at: string;
}

export interface RepositoryAnalysis {
  id: string;
  repository_id: string;
  commit_sha: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  files_analyzed: number;
  compliance_score?: number;
  gaps_critical: number;
  gaps_major: number;
  gaps_minor: number;
  started_at: string;
  completed_at?: string;
}

// Codebase Mapping Types
export interface CodebaseMapping {
  id: string;
  repository_id: string;
  requirement_id: string;
  affected_files: AffectedFile[];
  data_flows: DataFlow[];
  existing_compliance: ExistingCompliance[];
  gaps: ComplianceGap[];
  compliance_status: ComplianceStatus;
  confidence: number;
  estimated_effort_hours?: number;
  notes?: string;
  reviewed_by?: string;
  reviewed_at?: string;
  created_at: string;
  updated_at: string;
}

export type ComplianceStatus = 
  | 'COMPLIANT'
  | 'PARTIAL_COMPLIANCE'
  | 'NON_COMPLIANT'
  | 'NOT_APPLICABLE'
  | 'PENDING_REVIEW';

export interface AffectedFile {
  file_path: string;
  functions: string[];
  relevance: number;
  status: ComplianceStatus;
  gaps: string[];
}

export interface DataFlow {
  name: string;
  entry_point: string;
  data_touched: string[];
  compliance_status: ComplianceStatus;
}

export interface ExistingCompliance {
  file_path: string;
  description: string;
}

export interface ComplianceGap {
  severity: 'critical' | 'major' | 'minor';
  description: string;
  suggestion: string;
  affected_file?: string;
}

// Compliance Action Types
export interface ComplianceAction {
  id: string;
  organization_id: string;
  repository_id: string;
  requirement_id: string;
  mapping_id?: string;
  title: string;
  description: string;
  status: ActionStatus;
  priority: ActionPriority;
  assigned_to?: string;
  estimated_effort_hours?: number;
  affected_files: string[];
  generated_code?: GeneratedCode;
  pr_number?: number;
  pr_url?: string;
  due_date?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
}

export type ActionStatus = 
  | 'pending'
  | 'in_progress'
  | 'review'
  | 'approved'
  | 'merged'
  | 'completed'
  | 'rejected';

export type ActionPriority = 'critical' | 'high' | 'medium' | 'low';

export interface GeneratedCode {
  changes: CodeChange[];
  tests: CodeFile[];
  documentation: CodeFile[];
  pr_suggestion: PullRequestSuggestion;
}

export interface CodeChange {
  file_path: string;
  operation: 'create' | 'modify' | 'delete';
  content?: string;
  diff?: string;
}

export interface CodeFile {
  file_path: string;
  content: string;
}

export interface PullRequestSuggestion {
  title: string;
  body: string;
}

// Audit Trail Types
export interface AuditTrailEntry {
  id: string;
  organization_id: string;
  event_type: AuditEventType;
  actor_type: 'user' | 'system' | 'ai';
  actor_id?: string;
  actor_email?: string;
  resource_type: string;
  resource_id: string;
  description: string;
  metadata: Record<string, unknown>;
  hash: string;
  previous_hash?: string;
  created_at: string;
}

export type AuditEventType =
  | 'regulation_detected'
  | 'requirement_extracted'
  | 'requirement_approved'
  | 'mapping_created'
  | 'mapping_reviewed'
  | 'code_generated'
  | 'action_created'
  | 'action_approved'
  | 'action_rejected'
  | 'pr_created'
  | 'pr_merged'
  | 'deployment_completed';

// Dashboard Types
export interface ComplianceStats {
  overall_score: number;
  compliant: number;
  partial: number;
  non_compliant: number;
  pending: number;
  trend_percentage?: number;
}

export interface FrameworkStatus {
  framework: RegulatoryFramework;
  name: string;
  status: ComplianceStatus;
  score: number;
  requirements_total: number;
  requirements_compliant: number;
}

export interface UpcomingDeadline {
  regulation_id: string;
  regulation_name: string;
  effective_date: string;
  days_remaining: number;
  priority: ActionPriority;
}

export interface RecentActivity {
  id: string;
  type: AuditEventType;
  title: string;
  description: string;
  timestamp: string;
  status?: string;
}

// Customer Profile Types
export interface CustomerProfile {
  id: string;
  organization_id: string;
  name: string;
  industry: string;
  jurisdictions: Jurisdiction[];
  data_types: string[];
  applicable_frameworks: RegulatoryFramework[];
  created_at: string;
  updated_at: string;
}

// Notification Types
export interface NotificationPreferences {
  email_enabled: boolean;
  slack_enabled: boolean;
  in_app_enabled: boolean;
  regulation_detected: boolean;
  action_required: boolean;
  deadline_approaching: boolean;
  pr_status_changed: boolean;
  weekly_digest: boolean;
}

export interface NotificationChannel {
  type: 'email' | 'slack' | 'in_app';
  config: Record<string, string>;
  is_verified: boolean;
}

// Billing Types
export interface Subscription {
  id: string;
  organization_id: string;
  plan: 'starter' | 'professional' | 'enterprise';
  status: 'active' | 'past_due' | 'canceled' | 'trialing';
  current_period_start: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
}

export interface UsageMetrics {
  repositories_count: number;
  repositories_limit: number;
  frameworks_count: number;
  frameworks_limit: number;
  api_calls_count: number;
  api_calls_limit: number;
  period_start: string;
  period_end: string;
}
