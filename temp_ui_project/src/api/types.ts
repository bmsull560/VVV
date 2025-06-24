// Types for the model builder API
import { ComponentProperties, ModelComponent } from '../utils/calculationEngine';
import { ModelValidationResult } from '../services/modelBuilderApi';

export interface ModelConnection {
  id: string;
  source: string;
  target: string;
  type: 'input' | 'calculation' | 'output';
  sourceHandle?: string;
  targetHandle?: string;
}

/**
 * Represents the data structure for a model, including components and connections.
 */
export interface ModelData {
  id?: string;
  name: string;
  description?: string;
  components: ModelComponent<ComponentProperties>[];
  connections: ModelConnection[];
  createdAt?: string;
  updatedAt?: string;
  metadata?: Record<string, unknown>;
  summary?: RoiSummary;
  validationResult?: ModelValidationResult;
  scenarios?: Scenario[];
}

export interface Scenario {
  name: string;
  data: Record<string, unknown>;

}

export interface SaveModelResponse {
  success: boolean;
  modelId: string;
  message?: string;
}

export interface ListModelsResponse {
  models: Array<{
    id: string;
    name: string;
    description?: string;
    updatedAt: string;
  }>;
}

/**
 * Represents an API error response.
 */
export interface ApiError {
  message: string;
  status?: number;
  details?: unknown;
}

export interface Tier3Metric {
  name: string;
  type: string;
  default_value: unknown; // Can be more specific if needed
  value?: unknown;
}

export interface Tier2Driver {
  name: string;
  description: string;
  keywords_found: string[];
  tier_3_metrics: Tier3Metric[];
}

export interface ValueDriverPillar {
  pillar: string;
  tier_2_drivers: Tier2Driver[];
}


// --- Types for /api/quantify-roi ---

export interface RoiSummary {
  total_annual_value: number;
  roi_percentage: number;
  payback_period_months: number;
}

export interface SensitivityVariationInput {
  metric_name: string;
  pillar_name: string;
  tier2_driver_name: string;
  percentage_change: number;
}

export interface SensitivityScenarioOutput {
  scenario_name: string;
  varied_metric: string;
  percentage_change: number;
  resulting_roi_percentage: number;
  resulting_total_annual_value: number;
}

export interface QuantificationData {
  roi_summary: RoiSummary;
  sensitivity_analysis_results?: SensitivityScenarioOutput[];
}

export interface QuantificationExecutionDetails {
  roi_calculator_agent_time_ms?: number;
  sensitivity_analysis_agent_time_ms?: number;
}

export interface QuantifyRoiRequest {
  value_drivers: ValueDriverPillar[];
  investment_amount: number;
  sensitivity_variations?: SensitivityVariationInput[];
}

export interface QuantifyRoiResponse {
  quantification: QuantificationData;
  execution_details?: QuantificationExecutionDetails;
}

// --- End Types for /api/quantify-roi ---


// --- Types for /api/export-model ---

export interface ExportModelRequest {
  model_id: string; // Assuming UUID will be string in frontend
  export_format: string; // e.g., "excel", "pdf"
}

export interface ExportModelResponse {
  success: boolean;
  message?: string;
  file_content?: string; // Base64 encoded file content
  file_name?: string;
  content_type?: string;
}

// --- End Types for /api/export-model ---
