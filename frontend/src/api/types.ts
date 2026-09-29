// API response types (subset of fields the UI consumes). All monetary figures
// are modelled estimates in INR from the backend risk engine.

export interface User {
  id: number; username: string; name: string; role: string
  org_id?: number | null; organization?: string | null; is_demo?: boolean
}
export interface LoginResponse { token: string; user: User }
export interface DemoUser { username: string; password: string; name: string; role: string }

export interface Enterprise {
  risk_score: number
  risk_band: string
  risk_score_breakdown: {
    ale_component: number; control_component: number; critical_vuln_component: number
    weights: { ale: number; control: number; critical_vulns: number }
  }
  total_ale_inr: number
  expected_annual_loss_inr: number
  total_exposure_inr: number
  var95_inr: number
  var99_inr: number
  var_detail: { mean_inr: number; p50_inr: number; simulations: number; var95_inr: number; var99_inr: number }
  avg_control_effectiveness: number
  likelihood_avg: number
  open_vulns: number
  critical_vulns: number
  asset_count: number
  control_count: number
}

export interface Contributor {
  label: string; asset_id: number; vuln_id: number; severity: string; category: string
  ale_inr: number; share: number; likelihood: number; sle_inr: number
  control_weakness: string; recommended_action: string; expected_reduction_inr: number
}

export interface FindingImpact {
  components: Record<string, number>
  exposure_factor: number; sle_inr: number; severity_factor: number
}
export interface FindingFrequency {
  base_rate: number; exposure_multiplier: number; age_multiplier: number; threat_multiplier: number
  raw_lambda: number; control_effectiveness: number; after_controls: number
  ml_probability: number; ml_multiplier: number; aro: number; annualized_likelihood: number
}
export interface Finding {
  asset_id: number; asset_name: string; bu_name: string; vuln_id: number; title: string
  cve_id: string; severity: string; category: string
  sle_inr: number; aro: number; ale_inr: number; likelihood: number; exposure_factor: number
  ml_probability: number; impact: FindingImpact; frequency: FindingFrequency; formula: string
  controls_considered: { key: string; effectiveness: number }[]
}

export interface ControlOut {
  key: string; name: string; category: string; effectiveness: number; rating: string
  detail: Record<string, any>; inputs: Record<string, any>
}

export interface ByAsset {
  asset_id: number; name: string; bu_name: string; criticality: number; tier: string
  ale_inr: number; exposure_inr: number; vuln_count: number
}
export interface ByBU { business_unit: string; ale_inr: number; share: number; asset_count: number }
export interface ByCategory { category: string; ale_inr: number; share: number }

export interface FrameworkControl {
  control_ref: string; category: string; title: string; internal_control_key: string
  effectiveness: number | null; status: string
}
export interface Framework {
  key: string; name: string; full_name: string; version: string; control_count: number
  counts: Record<string, number>; coverage_pct: number; assessment_index: number
  controls: FrameworkControl[]; disclaimer: string
}
export interface FrameworkRollup { assessment_index: number; frameworks: number; weakest?: string }

export interface TrendPoint {
  [k: string]: any
}
export interface Trend { points: TrendPoint[]; count: number; latest?: any; note?: string }

export interface RiskResult {
  org: Record<string, any>; generated_at: string; enterprise: Enterprise
  findings: Finding[]; contributors: Contributor[]; by_asset: ByAsset[]
  by_business_unit: ByBU[]; by_category: ByCategory[]; controls: ControlOut[]
  criticality_by_asset: Record<string, any>
}

export interface Dashboard {
  organization: Record<string, any>; generated_at: string; enterprise: Enterprise
  headline_inr: { total_ale: string; total_exposure: string; var95: string; var99: string }
  top_contributors: Contributor[]; by_business_unit: ByBU[]; by_category: ByCategory[]
  weakest_controls: ControlOut[]; top_assets: ByAsset[]
  framework_coverage: { key: string; name: string; assessment_index: number; coverage_pct: number; counts: Record<string, number> }[]
  framework_rollup: FrameworkRollup
  ml_model: { metrics: Record<string, any>; importances: Record<string, number> }
  trend: Trend; role: string; disclaimer: string
}

export interface OptimizeSelected {
  key: string; name: string; cost_inr: number; effort: string; control_key: string
  category: string; action: string; marginal_ale_reduction_inr: number; efficiency: number
}
export interface CurvePoint { cumulative_cost_inr: number; cumulative_ale_reduction_inr: number; label: string }
export interface OptimizeResult {
  budget_inr: number; baseline: Record<string, any>
  selected: OptimizeSelected[]; not_selected: OptimizeSelected[]; selected_count: number
  total_cost_inr: number; budget_utilization: number; marginal_sum_ale_reduction_inr: number
  joint_ale_reduction_inr: number; joint_ale_reduction_pct: number; joint_after: Record<string, any>
  portfolio_rosi_percent: number; note: string; curve: CurvePoint[]
  budget_display: string; total_cost_display: string; joint_ale_reduction_display: string
}

export interface Recommendation {
  key: string; title: string; control_key: string; category: string; action: string
  cost_inr: number; effort: string; priority: string; expected_ale_reduction_inr: number
  expected_risk_reduction: number; rosi_percent: number
  affected_assets: { asset_id: number; name: string; ale_reduction_inr: number }[]
  rationale: { why: string; current_control: any; assets_affected: number; formula: string; disclaimer: string }
  cost_display?: string; expected_ale_reduction_display?: string
}

export interface InvestmentOption {
  key: string; name: string; category: string; control_key: string; action: string
  cost_inr: number; cost_display: string; effort: string
  marginal_ale_reduction_inr: number; marginal_ale_reduction_display: string
  rosi_percent: number; efficiency: number
}

export interface Assumption {
  key: string; label: string; value: number; unit: string; category: string
  description: string; editable: boolean; value_display: string
}

export interface ScenarioDelta {
  ale_reduction_inr: number; ale_reduction_pct: number; exposure_reduction_inr: number
  var95_reduction_inr: number; risk_score_delta: number; control_eff_delta: number
}
export interface ScenarioResult {
  label: string; cost_inr: number; applied: any[]
  before: Record<string, any>; after: Record<string, any>; delta: ScenarioDelta
  rosi_percent: number; investments?: { key: string; name: string; cost_inr: number }[]
}

export interface AssistantAnswer {
  intent: string; answer?: string; data?: any; numbers_source?: string
  action_required?: string; budget_inr?: number; question: string
}
