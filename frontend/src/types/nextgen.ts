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

// Matches the real DriftEventSchema returned by GET /drift-detection/events
export interface DriftEventRecord {
  id: string;
  repo: string;
  branch: string;
  drift_type: string;
  severity: DriftSeverity;
  regulation: string;
  description: string;
  file_path: string;
  commit_sha: string;
  previous_score: number;
  current_score: number;
  detected_at: string | null;
  resolved_at: string | null;
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

export interface AuditFrameworkSummary {
  framework: string;
  control_count: number;
}

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

// IDE Compliance Co-Pilot Types
export interface RAGSearchResult {
  regulation: string;
  article: string;
  text: string;
  relevance_score: number;
  metadata: Record<string, unknown>;
}

export interface SuggestionFeedback {
  id: string;
  rating: string;
  comment: string;
  was_applied: boolean;
  submitted_at: string;
}

export interface FeedbackStats {
  total_feedback: number;
  helpful_count: number;
  not_helpful_count: number;
  incorrect_count: number;
  application_rate: number;
  top_appreciated_rules: string[];
  top_rejected_rules: string[];
}

// Impact Simulator Types
export interface BlastRadiusComponent {
  component_path: string;
  component_type: string;
  impact_level: string;
  regulations_affected: string[];
  estimated_effort_hours: number;
  change_type: string;
  description: string;
}

export interface BlastRadiusAnalysis {
  scenario_id: string;
  total_components: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  components: BlastRadiusComponent[];
  total_effort_hours: number;
  risk_score: number;
}

export interface ScenarioComparison {
  scenarios: Record<string, unknown>[];
  winner: string;
  recommendation: string;
  comparison_matrix: Record<string, Record<string, number>>;
}

// Remediation Workflow Types
export interface ApprovalStep {
  id: string;
  approver_role: string;
  approver_name: string;
  status: string;
  comment: string;
  decided_at: string | null;
  order: number;
}

export interface ApprovalChain {
  id: string;
  workflow_id: string | null;
  steps: ApprovalStep[];
  current_step: number;
  is_complete: boolean;
  final_status: string;
}

export interface RollbackRecord {
  id: string;
  workflow_id: string | null;
  reason: string;
  rolled_back_by: string;
  original_state: string;
  rolled_back_at: string;
  files_reverted: string[];
  success: boolean;
}

export interface RemediationAnalytics {
  total_workflows: number;
  completed_workflows: number;
  in_progress_workflows: number;
  failed_workflows: number;
  rolled_back_workflows: number;
  avg_time_to_remediate_hours: number;
  fix_success_rate: number;
  auto_fix_rate: number;
  top_violation_types: Record<string, unknown>[];
  monthly_trend: Record<string, unknown>[];
}

// Posture Scoring Types
export interface DimensionDetail {
  dimension: string;
  score: number;
  max_score: number;
  grade: string;
  findings_count: number;
  critical_findings: number;
  drivers: Record<string, unknown>[];
  trend: string;
}

export interface PostureScore {
  overall_score: number;
  overall_grade: string;
  dimensions: DimensionDetail[];
  calculated_at: string;
  repo: string;
  recommendations: string[];
}

export interface PostureBenchmark {
  industry: string;
  your_score: number;
  industry_avg: number;
  industry_median: number;
  industry_p75: number;
  industry_p90: number;
  percentile: number;
  peer_count: number;
  dimension_comparison: Record<string, unknown>[];
}

export interface PostureScoreHistory {
  repo: string;
  history: Record<string, unknown>[];
  trend: string;
  improvement_rate: number;
}

// Drift Detection Enhanced Types
export interface DriftTrend {
  repo: string;
  period: string;
  data_points: Record<string, unknown>[];
  trend_direction: string;
  avg_score: number;
  min_score: number;
  max_score: number;
  volatility: number;
}

// Marketplace Enhanced Types
export interface UsageSummary {
  installation_id: string;
  period: string;
  total_requests: number;
  total_tokens: number;
  avg_response_time_ms: number;
  endpoints_breakdown: Record<string, number>;
  quota_limit: number;
  quota_used: number;
  quota_remaining: number;
  overage: boolean;
}

// Multi-LLM Enhanced Types
export interface DivergenceReport {
  consensus_id: string;
  total_obligations: number;
  agreed_count: number;
  diverged_count: number;
  divergence_rate: number;
  divergences: Record<string, unknown>[];
  needs_human_review: boolean;
  severity: string;
}

export interface ProviderHealthMetrics {
  provider: string;
  model_name: string;
  enabled: boolean;
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  success_rate: number;
  avg_latency_ms: number;
  p95_latency_ms: number;
  total_tokens_used: number;
  estimated_cost_usd: number;
  last_error: string | null;
  last_used: string | null;
  uptime_percentage: number;
}

// Evidence Vault Enhanced Types
export interface CoverageMetrics {
  framework: string;
  total_controls: number;
  controls_with_evidence: number;
  controls_partial: number;
  controls_missing: number;
  coverage_percentage: number;
  evidence_freshness_avg_days: number;
  stale_evidence_count: number;
  control_breakdown: Record<string, unknown>[];
}

export interface EvidenceGap {
  control_id: string;
  control_name: string;
  framework: string;
  gap_type: string;
  last_evidence_date: string | null;
  required_evidence_types: string[];
  remediation_suggestion: string;
  priority: string;
}

// Self-Hosted Enhanced Types
export interface OfflineBundle {
  id: string;
  name: string;
  version: string;
  regulations: string[];
  total_rules: number;
  size_mb: number;
  checksum: string;
  is_installed: boolean;
}

export interface AirGapStatus {
  is_air_gapped: boolean;
  local_llm_available: boolean;
  local_llm_model: string;
  offline_bundles_installed: number;
  last_bundle_update: string | null;
  license_status: string;
  connectivity_check: string;
  storage_used_gb: number;
  storage_total_gb: number;
}

// Industry Packs Enhanced Types
export interface WizardStep {
  step_type: string;
  title: string;
  description: string;
  questions: WizardQuestion[];
  completed: boolean;
  answers: Record<string, unknown>;
}

export interface WizardQuestion {
  id: string;
  question: string;
  question_type: string;
  options: Record<string, string>[];
  required: boolean;
  depends_on: string | null;
  depends_value: string | null;
}

// ═══════════════════════════════════════════════════════════════
// Next-Gen v3 Feature Types
// ═══════════════════════════════════════════════════════════════

// Feature 1: Cross-Border Data Transfer Automation
export interface DataFlowRecord {
  id: string;
  source_jurisdiction: string;
  destination_jurisdiction: string;
  data_categories: string[];
  data_subjects: string[];
  transfer_mechanism: string;
  purpose: string;
  volume_estimate: string;
  risk_level: string;
  is_compliant: boolean;
  services_involved: string[];
  detected_at: string | null;
}

export interface SCCDocument {
  id: string;
  data_flow_id: string;
  module_type: string;
  version: string;
  parties: Record<string, string>;
  annexes: Record<string, unknown>[];
  supplementary_measures: string[];
  status: string;
  generated_at: string | null;
}

export interface TransferImpactAssessment {
  id: string;
  data_flow_id: string;
  risk_level: string;
  legal_basis_adequate: boolean;
  supplementary_measures_needed: string[];
  government_access_risk: string;
  recommendations: string[];
  assessed_at: string | null;
}

export interface AdequacyDecisionRecord {
  country_code: string;
  country_name: string;
  status: string;
  decision_reference: string;
  scope: string;
}

export interface TransferAlertRecord {
  id: string;
  alert_type: string;
  severity: string;
  jurisdiction: string;
  title: string;
  description: string;
  affected_flows: string[];
  recommended_action: string;
  created_at: string | null;
  acknowledged: boolean;
}

export interface TransferReportRecord {
  total_flows: number;
  compliant_flows: number;
  non_compliant_flows: number;
  flows_by_mechanism: Record<string, number>;
  flows_by_risk: Record<string, number>;
  jurisdictions_involved: string[];
  active_sccs: number;
  pending_tias: number;
  active_alerts: number;
}

// Feature 2: Regulatory Compliance Stress Testing
export interface StressScenario {
  id: string;
  name: string;
  scenario_type: string;
  description: string;
  parameters: Record<string, unknown>;
  probability: number;
  severity: string;
}

export interface StressSimulationRun {
  id: string;
  scenario_id: string;
  iterations: number;
  confidence_level: number;
  status: string;
  results: StressSimulationResult[];
  started_at: string | null;
  completed_at: string | null;
}

export interface StressSimulationResult {
  id: string;
  run_id: string;
  metric: string;
  p50: number;
  p95: number;
  p99: number;
  mean: number;
  std_dev: number;
}

export interface StressTestReportRecord {
  id: string;
  total_scenarios: number;
  total_simulations: number;
  aggregate_exposure: number;
  worst_case_scenario: string;
  recommendations: string[];
}

// Feature 3: Zero-Trust Compliance Architecture Scanner
export interface ZeroTrustViolation {
  id: string;
  policy_id: string;
  resource_name: string;
  violation_type: string;
  severity: string;
  description: string;
  framework: string;
  remediation_hint: string;
  iac_file: string;
  status: string;
  detected_at: string | null;
}

export interface ZeroTrustScanResult {
  id: string;
  scan_type: string;
  resources_scanned: number;
  violations_found: number;
  compliance_score: number;
  scanned_at: string | null;
}

export interface ZeroTrustPolicy {
  id: string;
  name: string;
  framework: string;
  description: string;
  severity: string;
}

// Feature 4: Continuous Compliance Training Copilot
export interface TrainingModuleRecord {
  id: string;
  title: string;
  regulation: string;
  topic: string;
  format: string;
  duration_minutes: number;
  skill_level: string;
  tags: string[];
}

export interface DeveloperTrainingProfile {
  id: string;
  developer_id: string;
  name: string;
  skill_level: string;
  completed_modules: string[];
  compliance_score: number;
  strengths: string[];
  weaknesses: string[];
}

export interface TrainingAssignmentRecord {
  id: string;
  developer_id: string;
  module_id: string;
  trigger: string;
  status: string;
  quiz_score: number | null;
  assigned_at: string | null;
  completed_at: string | null;
}

export interface TeamTrainingReport {
  team: string;
  total_developers: number;
  avg_score: number;
  modules_completed: number;
  violation_reduction_pct: number;
  top_gaps: string[];
}

// Feature 5: AI Model Compliance Observatory
export type AIRiskLevel = 'prohibited' | 'high_risk' | 'limited_risk' | 'minimal_risk';

export interface AIModelRecord {
  id: string;
  name: string;
  model_type: string;
  version: string;
  framework: string;
  use_case: string;
  risk_level: AIRiskLevel;
  status: string;
  owner: string;
}

export interface BiasMetricRecord {
  id: string;
  model_id: string;
  metric_type: string;
  value: number;
  threshold: number;
  is_passing: boolean;
  protected_attribute: string;
}

export interface AIModelComplianceReport {
  id: string;
  model_id: string;
  risk_level: string;
  documentation_complete: boolean;
  human_oversight_implemented: boolean;
  overall_compliant: boolean;
  issues: string[];
  recommendations: string[];
}

export interface AIObservatoryDashboard {
  total_models: number;
  by_risk_level: Record<string, number>;
  compliant_count: number;
  non_compliant_count: number;
  avg_bias_score: number;
  models_needing_review: number;
}

// Feature 6: Regulation-to-Test-Case Generator
export interface RegTestSuite {
  id: string;
  regulation: string;
  framework: string;
  total_tests: number;
  coverage_pct: number;
  generated_at: string | null;
}

export interface RegulationCoverageRecord {
  regulation: string;
  total_articles: number;
  covered_articles: number;
  coverage_pct: number;
  uncovered_articles: string[];
  status: string;
}

// Feature 7: Regulatory Change Sentiment Analyzer
export interface RegulatorySentimentRecord {
  id: string;
  regulation: string;
  jurisdiction: string;
  trend: string;
  enforcement_probability: number;
  avg_fine_amount: number;
  key_topics: string[];
}

export interface RiskHeatmapCellRecord {
  regulation: string;
  jurisdiction: string;
  risk_score: number;
  trend: string;
  color: string;
}

export interface PrioritizationRecord {
  regulation: string;
  priority_rank: number;
  risk_score: number;
  effort_estimate: string;
  rationale: string;
}

// Feature 8: Incident Response Compliance Playbook
export interface PlaybookRecord {
  id: string;
  name: string;
  incident_type: string;
  description: string;
  steps: Record<string, unknown>[];
  notification_requirements: Record<string, unknown>[];
  evidence_checklist: string[];
  jurisdictions: string[];
}

export interface IncidentRecord {
  id: string;
  playbook_id: string;
  incident_type: string;
  severity: string;
  title: string;
  description: string;
  status: string;
  affected_data_subjects: number;
  jurisdictions_affected: string[];
  started_at: string | null;
  resolved_at: string | null;
}

// Feature 9: Compliance Cost Attribution Engine
export interface CostEntryRecord {
  id: string;
  regulation: string;
  category: string;
  amount: number;
  currency: string;
  description: string;
  code_module: string;
}

export interface CostDashboardRecord {
  total_compliance_cost: number;
  cost_by_regulation: Record<string, number>;
  cost_by_category: Record<string, number>;
  month_over_month_change: number;
  top_cost_drivers: Record<string, unknown>[];
}

export interface ROIAnalysisRecord {
  id: string;
  regulation: string;
  investment: number;
  savings: number;
  roi_pct: number;
  payback_months: number;
}

// Feature 10: Blockchain-Based Compliance Audit Trail
export interface AuditBlockRecord {
  id: string;
  index: number;
  block_type: string;
  data: Record<string, unknown>;
  previous_hash: string;
  hash: string;
  timestamp: string;
}

export interface BlockchainStateRecord {
  chain_length: number;
  latest_hash: string;
  is_valid: boolean;
}

export interface VerificationResultRecord {
  chain_length: number;
  is_valid: boolean;
  invalid_blocks: number[];
  verification_time_ms: number;
}

export interface SmartContractRecord {
  id: string;
  name: string;
  contract_type: string;
  conditions: Record<string, unknown>[];
  auto_approve: boolean;
}

// ═══════════════════════════════════════════════════════════════
// Next-Gen v4 Feature Types (39 dashboard wiring)
// ═══════════════════════════════════════════════════════════════

// API Gateway
export interface GatewayClient {
  id: string;
  name: string;
  description: string;
  api_key: string;
  scopes: string[];
  rate_limit_per_minute: number;
  webhook_url: string;
  active: boolean;
  created_at: string | null;
}
export interface GatewayStats {
  total_clients: number;
  active_clients: number;
  total_requests: number;
  requests_today: number;
  rate_limited_count: number;
  by_endpoint: Record<string, number>;
  by_client: Record<string, number>;
}

// API Monetization
export interface MonetizationApi {
  id: string;
  name: string;
  description: string;
  endpoint: string;
  regulation: string;
  version: string;
  status: string;
  requests_per_month: number;
  avg_latency_ms: number;
  pricing_per_request: number;
  documentation_url: string;
  supported_languages: string[];
  tags: string[];
}
export interface MonetizationRevenue {
  total_apis: number;
  total_developers: number;
  total_requests_month: number;
  monthly_revenue: number;
  top_api: string;
  revenue_growth_pct: number;
  avg_revenue_per_api: number;
}

// Agent Swarm
export interface SwarmAgent {
  id: string;
  role: string;
  status: string;
  findings_count: number;
}
export interface SwarmSession {
  id: string;
  repo: string;
  frameworks: string[];
  files: string[];
  status: string;
  agents: SwarmAgent[];
  findings: Record<string, unknown>[];
  created_at: string | null;
}
export interface SwarmStats {
  total_sessions: number;
  active_sessions: number;
  total_findings: number;
  agents_deployed: number;
}

// Agents Marketplace
export interface MarketplaceAgent {
  id: string;
  name: string;
  slug: string;
  description: string;
  category: string;
  author: string;
  version: string;
  status: string;
  downloads: number;
  rating: number;
  rating_count: number;
  tags: string[];
  frameworks: string[];
  published_at: string | null;
}
export interface AgentsMarketplaceStats {
  total_agents: number;
  published_agents: number;
  total_installations: number;
  total_executions: number;
  by_category: Record<string, number>;
  top_agents: Record<string, unknown>[];
}

// Arch Advisor
export interface ArchDiagram {
  id: string;
  title: string;
  frameworks: string[];
  diagram_format: string;
  diagram_code: string;
  recommendations: string[];
  generated_at: string | null;
}
export interface ArchAdvisorStatsRecord {
  total_diagrams: number;
  by_framework: Record<string, number>;
  by_format: Record<string, number>;
  avg_components: number;
}

// Audit Workspace
export interface AuditWorkspaceItem {
  id: string;
  framework: string;
  phase: string;
  readiness_pct: number;
}

// Auto Healing
export interface AutoHealingRun {
  id: string;
  trigger_type: string;
  trigger_source: string;
  state: string;
  repository: string;
  branch: string;
  regulation: string;
  violations_detected: number;
  fixes_generated: number;
  fixes_applied: number;
  tests_passed: boolean;
  pr_number: number | null;
  pr_url: string | null;
  approval_policy: string;
  approved_by: string | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
}
export interface AutoHealingMetrics {
  total_runs: number;
  successful_runs: number;
  failed_runs: number;
  rejected_runs: number;
  avg_time_to_fix_hours: number;
  auto_merge_rate: number;
  fix_acceptance_rate: number;
  violations_resolved: number;
}

// Autonomous OS
export interface AutonomousOSEvent {
  id: string;
  event_type: string;
  source_service: string;
  payload: Record<string, unknown>;
  processed: boolean;
  created_at: string | null;
}
export interface AutonomousOSStats {
  total_events: number;
  total_decisions: number;
  autonomous_decisions: number;
  avg_confidence: number;
  autonomy_level: string;
}

// Auto Remediation
export interface AutoRemediationPipeline {
  id: string;
  repo: string;
  branch: string;
  trigger_event: string;
  status: string;
  risk_level: string;
  approval_policy: string;
  violations_detected: number;
  fixes_generated: number;
  pr_url: string;
  created_at: string | null;
}
export interface AutoRemediationStats {
  total_pipelines: number;
  by_status: Record<string, number>;
  total_fixes_generated: number;
  total_fixes_merged: number;
  auto_merge_rate: number;
}

// Board Reports
export interface BoardExecutiveSummary {
  title: string;
  period: string;
  overall_score: number;
  overall_status: string;
  narrative: string;
  highlights: { category: string; score: number; status: string; trend: string }[];
  top_risks: string[];
  action_items: string[];
}

// Cert Autopilot
export interface CertJourney {
  id: string | null;
  framework: string;
  current_phase: string;
  progress_percent: number;
  started_at: string;
  estimated_completion: string;
  phases: Record<string, unknown>[];
}

// Cert Pipeline
export interface CertRun {
  id: string;
  repo: string;
  framework: string;
  owner: string;
  stage: string;
  progress_pct: number;
  gaps: Record<string, unknown>[];
  evidence_collected: number;
  started_at: string | null;
  completed_at: string | null;
}
export interface CertPipelineStats {
  total_runs: number;
  completed_runs: number;
  in_progress_runs: number;
  total_gaps: number;
  resolved_gaps: number;
  by_framework: Record<string, number>;
  avg_completion_days: number;
}

// Chaos Engineering
export interface ChaosExperiment {
  id: string;
  name: string;
  description: string;
  experiment_type: string;
  status: string;
  target_service: string;
  target_environment: string;
  blast_radius: string;
  affected_frameworks: string[];
  time_to_detect_seconds: number | null;
  time_to_remediate_seconds: number | null;
  detection_method: string;
  auto_rollback: boolean;
}
export interface ChaosStats {
  total_experiments: number;
  experiments_detected: number;
  experiments_undetected: number;
  avg_mttd_seconds: number;
  avg_mttr_seconds: number;
  detection_rate: number;
  game_days_completed: number;
  controls_validated: number;
  blind_spots_found: number;
}

// CICD Runtime
export interface CICDCheck {
  id: string;
  deployment_id: string;
  repo: string;
  phase: string;
  checks_passed: number;
  checks_failed: number;
  gate_decision: string;
  violations: Record<string, unknown>[];
  duration_ms: number;
  checked_at: string | null;
}
export interface CICDStats {
  total_checks: number;
  deployments_gated: number;
  rollbacks: number;
  attestations_issued: number;
  avg_check_duration_ms: number;
  pass_rate: number;
}

// Client SDK
export interface ClientSDKPackageRecord {
  runtime: string;
  version: string;
  description: string;
  download_count: number;
  latest_release: string | null;
}
export interface ClientSDKStatsRecord {
  total_endpoints: number;
  total_packages: number;
  total_api_keys: number;
  total_requests: number;
}

// Code Review Agent
export interface CodeReviewRecord {
  id: string;
  repo: string;
  pr_number: number;
  commit_sha: string;
  overall_risk: string;
  decision: string;
  suggestions: Record<string, unknown>[];
  files_analyzed: number;
  hunks_analyzed: number;
  compliance_score_before: number;
  compliance_score_after: number;
  auto_approve_eligible: boolean;
  review_time_ms: number;
  created_at: string | null;
}
export interface CodeReviewStats {
  total_reviews: number;
  auto_approved: number;
  suggestions_made: number;
  suggestions_accepted: number;
  acceptance_rate: number;
  avg_review_time_ms: number;
  by_risk_level: Record<string, number>;
}

// Compliance API Standard
export interface ApiSpecVersionRecord {
  version: string;
  status: string;
  published_at: string | null;
}
export interface ComplianceApiStandardStatsRecord {
  total_specs: number;
  total_conformance_checks: number;
  avg_compliance_score: number;
  compliant_apis: number;
}

// Compliance Badge
export interface ComplianceBadgeRecord {
  repo: string;
  grade: string;
  score: number;
  label: string;
  color: string;
  style: string;
}
export interface ComplianceScorecardRecord {
  id: string;
  repo: string;
  overall_score: number;
  overall_grade: string;
  frameworks: Record<string, unknown>[];
  trend: Record<string, unknown>[];
  last_scan_at: string | null;
  is_public: boolean;
}

// Compliance Cloning
export interface ReferenceRepoRecord {
  id: string;
  name: string;
  url: string;
  description: string;
  languages: string[];
  frameworks: string[];
  compliance_score: number;
  patterns_count: number;
  industry: string;
  verified: boolean;
}

// Compliance Data Lake
export interface DataLakeEventRecord {
  id: string;
  tenant_id: string;
  category: string;
  source_service: string;
  repo: string;
  framework: string;
  timestamp: string | null;
}
export interface DataLakeStatsRecord {
  total_events: number;
  by_category: Record<string, number>;
  by_tenant: Record<string, number>;
  storage_size_mb: number;
}

// Compliance Debt
export interface ComplianceDebtItemRecord {
  id: string;
  title: string;
  description: string;
  framework: string;
  rule_id: string;
  file_path: string;
  severity: string;
  risk_cost_usd: number;
  remediation_cost_usd: number;
  repo: string;
  status: string;
  created_at: string | null;
}
export interface ComplianceDebtStatsRecord {
  total_items: number;
  open_items: number;
  resolved_items: number;
  total_risk_cost_usd: number;
  total_remediation_cost_usd: number;
  by_severity: Record<string, number>;
  by_framework: Record<string, number>;
}

// Compliance Editor
export interface EditorSessionRecord {
  id: string;
  user_id: string;
  files: { path: string; language: string; issues_count: number; fixes_available: number }[];
  status: string;
  created_at: string | null;
}
export interface EditorStatsRecord {
  total_sessions: number;
  active_sessions: number;
  total_fixes_applied: number;
  total_issues_found: number;
}

// Compliance Export
export interface ExportJobRecord {
  id: string;
  data_type: string;
  format: string;
  status: string;
  row_count: number;
  file_size_bytes: number;
  download_url: string;
  created_at: string | null;
  completed_at: string | null;
}
export interface ExportSummaryRecord {
  total_exports: number;
  by_format: Record<string, number>;
  by_data_type: Record<string, number>;
  total_rows_exported: number;
  total_bytes_exported: number;
  active_schedules: number;
  configured_connectors: number;
}

// Compliance Observability
export interface ObservabilityMetricRecord {
  name: string;
  metric_type: string;
  value: number;
  labels: Record<string, string>;
  unit: string;
  recorded_at: string | null;
}
export interface ObservabilityPipelineStatsRecord {
  metrics_emitted: number;
  exporters_configured: number;
  active_alerts: number;
  metrics_by_type: Record<string, number>;
}

// Compliance SDK
export interface ComplianceSdkPackageRecord {
  language: string;
  name: string;
  version: string;
  install_command: string;
  registry_url: string;
  description: string;
}
export interface ComplianceSdkUsageRecord {
  total_keys: number;
  active_keys: number;
  total_requests: number;
  requests_by_tier: Record<string, number>;
  requests_by_endpoint: Record<string, number>;
  avg_response_time_ms: number;
  sdk_downloads: Record<string, number>;
}

// Cost Engine
export interface CostAttributionRecord {
  id: string;
  team: string;
  repository: string;
  framework: string;
  category: string;
  hours: number;
  estimated_cost: number;
  created_at: string;
}
export interface CostAttributionListRecord {
  attributions: CostAttributionRecord[];
  total: number;
  total_hours: number;
  total_cost: number;
}

// Cross Cloud Mesh
export interface CloudAccountRecord {
  id: string;
  provider: string;
  account_id: string;
  name: string;
  regions: string[];
  status: string;
  resources_discovered: number;
  created_at: string | null;
}
export interface CloudPostureRecord {
  overall_score: number;
  accounts: number;
  total_resources: number;
  total_findings: number;
  critical_findings: number;
  by_provider: Record<string, number>;
}
export interface CrossCloudStatsRecord {
  total_accounts: number;
  total_resources: number;
  total_scans: number;
  avg_compliance_score: number;
  providers: string[];
}

// Cross Org Benchmark
export interface OrgBenchmarkStatsRecord {
  total_participants: number;
  by_industry: Record<string, number>;
  global_avg_score: number;
  data_freshness_hours: number;
}

// Cross Repo Graph
export interface RepoNodeRecord {
  id: string;
  name: string;
  full_name: string;
  score: number;
  grade: string;
  violations: number;
  frameworks: string[];
}
export interface CrossRepoGraphRecord {
  organization_id: string;
  nodes: RepoNodeRecord[];
  edges: Record<string, unknown>[];
  overall_score: number;
  hotspots: Record<string, unknown>[];
}

// Data Mesh Federation
export interface DataMeshNodeRecord {
  id: string;
  org_name: string;
  endpoint_url: string;
  role: string;
  status: string;
  joined_at: string | null;
}
export interface FederationStatsRecord {
  total_nodes: number;
  total_insights: number;
  verified_insights: number;
  active_nodes: number;
}

// Entity Rollup
export interface EntityHierarchyRecord {
  id: string;
  name: string;
  parent_id: string | null;
  level: string;
  compliance_score: number;
  frameworks: string[];
  member_count: number;
}

// Game Engine
export interface GameScenarioRecord {
  id: string;
  title: string;
  description: string;
  category: string;
  difficulty: string;
  estimated_minutes: number;
  max_score: number;
  decisions_count: number;
  frameworks: string[];
}
export interface GameLeaderboardRecord {
  display_name: string;
  organization: string;
  total_xp: number;
  level: number;
  scenarios_completed: number;
  achievements_count: number;
  accuracy_rate: number;
  rank: number;
}

// Horizon Scanner
export interface HorizonTimelineRecord {
  total_tracked: number;
  high_impact_count: number;
  upcoming: Record<string, unknown>[];
  alerts: Record<string, unknown>[];
}

// Policy Marketplace
export interface PolicyPackRecord {
  id: string;
  creator_id: string;
  title: string;
  description: string;
  version: string;
  regulations: string[];
  languages: string[];
  pricing_model: string;
  price_usd: number;
  revenue_share_pct: number;
  status: string;
  downloads: number;
  rating: number;
  review_count: number;
  tags: string[];
  created_at: string;
  updated_at: string;
}
export interface PolicyMarketplaceStatsRecord {
  total_packs: number;
  total_creators: number;
  total_downloads: number;
  total_gmv_usd: number;
  top_categories: Record<string, unknown>[];
}

// Regulation Diff
export interface RegulationVersionRecord {
  id: string;
  regulation: string;
  version: string;
  title: string;
  effective_date: string;
  total_articles: number;
  total_words: number;
  source_url: string;
}
export interface RegulationDiffSummaryRecord {
  id: string;
  regulation: string;
  from_version: string;
  to_version: string;
  total_changes: number;
  critical_changes: number;
  ai_summary: string;
}

// Compliance Copilot
export interface CopilotViolationRecord {
  id: string;
  file_path: string;
  line_start: number;
  line_end: number;
  rule_id: string;
  framework: string;
  article_ref: string;
  severity: string;
  message: string;
}

// IaC Policy Engine
export interface IaCPolicyRuleRecord {
  id: string;
  name: string;
  description: string;
  provider: string;
  framework: string;
  severity: string;
  enabled: boolean;
  metadata: Record<string, unknown>;
}

// Knowledge Graph
export interface KnowledgeGraphSummaryRecord {
  id: string;
  name: string;
  node_count: number;
  edge_count: number;
  node_types: Record<string, number>;
}

// Pair Programming
export interface PairSuggestionRecord {
  id: string;
  file_path: string;
  line_number: number;
  severity: string;
  rule_id: string;
  regulation: string;
  article: string;
  message: string;
  explanation: string;
  suggested_fix: string;
}
export interface PairRegulationContextRecord {
  regulation: string;
  article: string;
  title: string;
  summary: string;
  relevance_score: number;
  applicable_patterns: string[];
}

// Impact Simulator (hook only needed)
export interface ImpactScenarioRecord {
  id: string;
  name: string;
  description: string;
  category: string;
  difficulty: string;
  regulation: string;
}
