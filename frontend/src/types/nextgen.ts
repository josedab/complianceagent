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
