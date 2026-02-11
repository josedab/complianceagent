// Next-Gen Feature Types - Compliance Testing Suite
export interface ComplianceTestPattern {
  id: string;
  name: string;
  category: TestPatternCategory;
  regulation: string;
  description: string;
  assertions: string[];
  tags: string[];
}

export type TestPatternCategory =
  | 'data_privacy'
  | 'consent'
  | 'encryption'
  | 'access_control'
  | 'audit_logging'
  | 'data_retention'
  | 'data_deletion'
  | 'breach_notification'
  | 'tokenization'
  | 'ai_transparency';

export type TestFramework = 'pytest' | 'jest' | 'junit' | 'mocha' | 'rspec' | 'go_test';

export interface GeneratedTest {
  id: string;
  pattern_id: string;
  test_name: string;
  test_code: string;
  framework: TestFramework;
  regulation: string;
  requirement_ref: string;
  description: string;
  confidence: number;
  target_file: string;
}

export interface TestSuiteResult {
  id: string;
  status: 'pending' | 'generating' | 'completed' | 'failed' | 'validating';
  regulation: string;
  framework: TestFramework;
  tests: GeneratedTest[];
  patterns_used: string[];
  total_tests: number;
  coverage_estimate: number;
  generation_time_ms: number;
}

export interface TestValidationResult {
  suite_id: string;
  total_tests: number;
  valid_tests: number;
  invalid_tests: number;
  errors: string[];
  warnings: string[];
}

export interface FrameworkDetectionResult {
  detected_frameworks: TestFramework[];
  primary_language: string;
  config_files_found: string[];
  recommended_framework: TestFramework;
}

// Architecture Advisor Types
export type PatternType =
  | 'microservices'
  | 'monolith'
  | 'event_driven'
  | 'serverless'
  | 'data_lake'
  | 'api_gateway'
  | 'cqrs'
  | 'data_mesh';

export type RiskSeverity = 'critical' | 'high' | 'medium' | 'low' | 'info';

export interface ArchitecturePattern {
  pattern_type: PatternType;
  confidence: number;
  evidence: string[];
  description: string;
}

export interface ComplianceRisk {
  id: string;
  pattern: PatternType;
  regulation: string;
  severity: RiskSeverity;
  title: string;
  description: string;
  affected_components: string[];
  recommendation: string;
}

export interface ArchitectureRecommendation {
  id: string;
  title: string;
  description: string;
  regulation: string;
  current_pattern: PatternType;
  recommended_pattern: string;
  effort_estimate_days: number;
  impact: RiskSeverity;
  trade_offs: string[];
}

export interface ArchitectureScore {
  overall_score: number;
  data_isolation_score: number;
  encryption_score: number;
  audit_trail_score: number;
  access_control_score: number;
  data_flow_score: number;
  max_score: number;
  grade: string;
  risks_found: number;
  recommendations_count: number;
}

export interface DesignReviewResult {
  id: string;
  repo: string;
  detected_patterns: ArchitecturePattern[];
  risks: ComplianceRisk[];
  recommendations: ArchitectureRecommendation[];
  score: ArchitectureScore;
  regulations_analyzed: string[];
}

// Drift Detection Types
export type DriftSeverity = 'critical' | 'high' | 'medium' | 'low';
export type DriftType = 'regression' | 'configuration_change' | 'policy_violation' | 'new_requirement';

export interface DriftEvent {
  id: string;
  repo: string;
  drift_type: DriftType;
  severity: DriftSeverity;
  description: string;
  baseline_score: number;
  current_score: number;
  delta: number;
  detected_at: string;
}

export interface DriftBaseline {
  id: string;
  repo: string;
  branch: string;
  score: number;
  captured_at: string;
}

export interface DriftReport {
  repo: string;
  total_events: number;
  critical_count: number;
  high_count: number;
  events: DriftEvent[];
  baseline?: DriftBaseline;
}

// Cost Calculator Types
export type ComplexityLevel = 'simple' | 'moderate' | 'complex' | 'very_complex';

export interface CostPrediction {
  id: string;
  regulation: string;
  estimated_dev_days: number;
  estimated_cost_usd: number;
  confidence: number;
  risk_score: number;
  breakdown: CostBreakdownItem[];
}

export interface CostBreakdownItem {
  phase: string;
  description: string;
  dev_days: number;
  cost_usd: number;
}

export interface ROISummary {
  manual_cost_usd: number;
  automated_cost_usd: number;
  savings_usd: number;
  savings_percentage: number;
  payback_period_months: number;
  time_saved_days: number;
}

// Evidence Vault Types
export type EvidenceType =
  | 'scan_result'
  | 'policy_document'
  | 'test_result'
  | 'code_review'
  | 'training_record'
  | 'incident_response'
  | 'risk_assessment'
  | 'vendor_assessment'
  | 'change_record';

export type ControlFramework = 'soc2' | 'iso27001' | 'hipaa' | 'pci_dss' | 'gdpr' | 'nist';

export interface EvidenceItem {
  id: string;
  evidence_type: EvidenceType;
  title: string;
  description: string;
  content_hash: string;
  framework: ControlFramework;
  control_id: string;
  created_at: string;
}

export interface AuditReport {
  framework: ControlFramework;
  total_controls: number;
  controls_with_evidence: number;
  coverage_percentage: number;
  generated_at: string;
}

export interface AuditorSession {
  id: string;
  auditor_email: string;
  auditor_name: string;
  is_active: boolean;
  expires_at: string;
}

// Marketplace Types
export type MarketplacePlan = 'free' | 'team' | 'business' | 'enterprise';
export type AppPlatform = 'github' | 'gitlab';

export interface MarketplaceListing {
  app_name: string;
  description: string;
  platforms: AppPlatform[];
  plans: MarketplacePlanInfo[];
  total_installations: number;
}

export interface MarketplacePlanInfo {
  name: MarketplacePlan;
  display_name: string;
  price_monthly: number;
  features: string[];
}

export interface AppInstallation {
  id: string;
  platform: AppPlatform;
  account_login: string;
  plan: MarketplacePlan;
  status: 'active' | 'suspended' | 'uninstalled';
  repositories: string[];
  installed_at: string;
}

// Federated Intelligence Types
export type ThreatCategory =
  | 'regulatory_change'
  | 'enforcement_action'
  | 'data_breach_pattern'
  | 'compliance_gap'
  | 'emerging_regulation';

export interface ComplianceThreat {
  id: string;
  title: string;
  description: string;
  category: ThreatCategory;
  severity: RiskSeverity;
  regulations: string[];
  industries: string[];
  verified: boolean;
}

export interface IndustryBenchmark {
  industry: string;
  avg_compliance_score: number;
  common_frameworks: string[];
  top_risks: string[];
}

// Industry Packs Types
export type IndustryVertical =
  | 'fintech'
  | 'healthtech'
  | 'ai_company'
  | 'ecommerce'
  | 'saas'
  | 'insurance'
  | 'government';

export interface IndustryPack {
  name: string;
  vertical: IndustryVertical;
  description: string;
  regulations: RegulationBundle[];
  policy_templates: PolicyTemplate[];
  status: 'available' | 'provisioned' | 'active';
}

export interface RegulationBundle {
  regulation: string;
  description: string;
  priority: 'critical' | 'high' | 'medium' | 'low';
}

export interface PolicyTemplate {
  name: string;
  description: string;
  category: string;
}

// Compliance Sandbox Types
export interface SandboxScenario {
  id: string;
  title: string;
  description: string;
  regulation: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  estimated_minutes: number;
  tags: string[];
}

export interface SandboxEnvironment {
  id: string;
  scenario_id: string;
  status: 'provisioning' | 'active' | 'completed' | 'expired';
  progress: number;
  started_at: string;
}

// Natural Language Query Types
export type QueryIntent =
  | 'regulation_lookup'
  | 'code_search'
  | 'violation_check'
  | 'audit_query'
  | 'status_report'
  | 'comparison'
  | 'recommendation';

export interface QuerySource {
  source_type: string;
  title: string;
  reference: string;
  relevance_score: number;
  snippet: string;
}

export interface CodeReference {
  file_path: string;
  line_start: number;
  line_end: number;
  snippet: string;
  language: string;
  relevance: number;
}

export interface QueryResult {
  id: string;
  query: string;
  intent: string;
  answer: string;
  confidence: number;
  sources: QuerySource[];
  code_references: CodeReference[];
  follow_up_suggestions: string[];
  processing_time_ms: number;
}

export interface QueryHistoryItem {
  id: string;
  query: string;
  intent: string;
  answer_preview: string;
  was_helpful: boolean | null;
  timestamp: string | null;
}

// Multi-LLM Consensus Types
export type ConsensusStrategy = 'majority_vote' | 'highest_confidence' | 'weighted_average';

export interface ProviderResult {
  provider: string;
  model_name: string;
  obligations: Record<string, unknown>[];
  entities: string[];
  confidence: number;
  latency_ms: number;
  error: string | null;
}

export interface ConsensusResult {
  id: string;
  status: string;
  strategy: string;
  provider_results: ProviderResult[];
  obligations: Record<string, unknown>[];
  entities: string[];
  confidence: number;
  agreement_score: number;
  needs_human_review: boolean;
  total_latency_ms: number;
}

export interface ProviderInfo {
  provider: string;
  model_name: string;
  enabled: boolean;
  weight: number;
}

export interface MultiLLMConfig {
  providers: ProviderInfo[];
  consensus_strategy: string;
  min_providers: number;
  divergence_threshold: number;
  fallback_to_single: boolean;
}

// Impact Timeline Types
export type TimelineEventType =
  | 'regulation_effective'
  | 'amendment'
  | 'enforcement_deadline'
  | 'guidance_update'
  | 'predicted';

export interface TimelineEvent {
  id: string;
  title: string;
  event_type: string;
  framework: string;
  jurisdiction: string;
  days_remaining: number;
  impact_score: number;
  estimated_effort_hours: number;
  affected_repos: string[];
  is_predicted: boolean;
  confidence: number;
}

export interface TimelineView {
  events: TimelineEvent[];
  total_events: number;
  upcoming_deadlines: number;
  overdue_count: number;
  total_effort_hours: number;
}

export interface RemediationTask {
  id: string;
  title: string;
  priority: string;
  status: string;
  estimated_hours: number;
  due_date: string | null;
}

// Audit Autopilot Types
export type AuditFramework = 'soc2' | 'iso27001' | 'hipaa' | 'pci_dss';

export interface GapAnalysis {
  id: string;
  framework: string;
  total_controls: number;
  controls_met: number;
  controls_partial: number;
  controls_missing: number;
  readiness_score: number;
  critical_gaps: string[];
  estimated_remediation_hours: number;
}

export interface EvidencePackage {
  id: string;
  framework: string;
  title: string;
  total_items: number;
  controls_covered: number;
  total_controls: number;
  coverage_percent: number;
}

export interface ReadinessReport {
  id: string;
  framework: string;
  overall_readiness: number;
  recommendations: string[];
  estimated_prep_weeks: number;
}

// Policy SDK Types
export type PolicyLanguage = 'yaml' | 'rego' | 'python' | 'typescript';
export type PolicyCategory = 'data_privacy' | 'encryption' | 'access_control' | 'audit_logging' | 'ai_transparency' | 'custom';
export type PolicySeverity = 'critical' | 'high' | 'medium' | 'low';

export interface PolicyDefinition {
  id: string;
  name: string;
  description: string;
  version: string;
  language: PolicyLanguage;
  category: string;
  severity: string;
  frameworks: string[];
  is_community: boolean;
  author: string;
}

export interface PolicyValidation {
  policy_id: string;
  is_valid: boolean;
  errors: string[];
  warnings: string[];
  coverage: number;
}

export interface MarketplaceEntry {
  id: string;
  name: string;
  publisher: string;
  installs: number;
  stars: number;
  verified: boolean;
}

export interface SDKInfo {
  language: string;
  package_name: string;
  install_command: string;
  version: string;
  docs_url: string;
}
