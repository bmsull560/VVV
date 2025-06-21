/**
 * B2BValue API Service Layer
 * Connects the frontend UI to the production-ready B2BValue agents
 */

import axios, { AxiosInstance } from 'axios';

// API Configuration
const API_BASE_URL = process.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_TIMEOUT = 30000; // 30 seconds

// API Client Setup
class B2BValueAPIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: API_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor for logging
    this.client.interceptors.request.use(
      (config) => {
        console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('API Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Response Error:', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }

  // ==========================================
  // Phase 1: Discovery API (/api/discover-value)
  // Uses: Intake Assistant + Value Driver Agents
  // ==========================================
  
  async discoverValue(query: string): Promise<DiscoveryResponse> {
    try {
      const response = await this.client.post('/api/discover-value', {
        user_query: query,
        analysis_type: 'comprehensive'
      });
      return response.data;
    } catch (error) {
      throw new Error(`Discovery failed: ${error}`);
    }
  }

  // ==========================================
  // Phase 2: Quantification API (/api/quantify-roi)
  // Uses: ROI Calculator + Sensitivity Analysis Agents
  // ==========================================
  
  async quantifyROI(data: QuantificationRequest): Promise<QuantificationResponse> {
    try {
      const response = await this.client.post('/api/quantify-roi', data);
      return response.data;
    } catch (error) {
      throw new Error(`ROI quantification failed: ${error}`);
    }
  }

  // ==========================================
  // Phase 3: Narrative Generation API (/api/generate-narrative)
  // Uses: Analytics Aggregator + Data Correlator Agents
  // ==========================================
  
  async generateNarrative(data: NarrativeRequest): Promise<NarrativeResponse> {
    try {
      const response = await this.client.post('/api/generate-narrative', data);
      return response.data;
    } catch (error) {
      throw new Error(`Narrative generation failed: ${error}`);
    }
  }

  // ==========================================
  // Phase 4: Business Case Composition API (/api/compose-business-case)
  // Uses: Risk Mitigation + Database Connector Agents
  // ==========================================
  
  async composeBusinessCase(data: CompositionRequest): Promise<ComposedBusinessCase> {
    try {
      const response = await this.client.post('/api/compose-business-case', data);
      return response.data;
    } catch (error) {
      throw new Error(`Business case composition failed: ${error}`);
    }
  }

  // ==========================================
  // Additional Utility APIs
  // ==========================================
  
  async healthCheck(): Promise<{ status: string; agents: string[] }> {
    try {
      const response = await this.client.get('/api/health');
      return response.data;
    } catch (error) {
      throw new Error(`Health check failed: ${error}`);
    }
  }

  async getTemplates(): Promise<BusinessCaseTemplate[]> {
    try {
      const response = await this.client.get('/api/templates');
      return response.data;
    } catch (error) {
      throw new Error(`Template retrieval failed: ${error}`);
    }
  }
}

// ==========================================
// Type Definitions (Based on Design Brief)
// ==========================================

// Phase 1: Discovery Types
export interface DiscoveryResponse {
  value_drivers: ValueDriverPillar[];
  personas: Persona[];
  suggested_metrics: Tier3Metric[];
  project_insights: {
    industry_context: string;
    complexity_assessment: string;
    recommended_approach: string;
  };
}

export interface ValueDriverPillar {
  pillar: string;
  tier_2_drivers: string[];
  tier_3_metrics: Tier3Metric[];
}

export interface Tier3Metric {
  name: string;
  description: string;
  unit: string;
  suggested_value?: number;
  confidence_level: 'high' | 'medium' | 'low';
}

export interface Persona {
  name: string;
  description: string;
  priorities: string[];
  concerns: string[];
}

// Phase 2: Quantification Types
export interface QuantificationRequest {
  investment_amount: number;
  metrics: { [key: string]: number };
  sensitivity_variations?: SensitivityVariation[];
  time_horizon_years?: number;
}

export interface QuantificationResponse {
  roi_summary: RoiSummary;
  sensitivity_analysis: SensitivityScenarioOutput[];
  financial_projections: {
    year_1_benefit: number;
    year_2_benefit: number;
    year_3_benefit: number;
    total_npv: number;
    irr_percentage: number;
  };
}

export interface RoiSummary {
  total_annual_value: number;
  roi_percentage: number;
  payback_period_months: number;
  confidence_score: number;
}

export interface SensitivityVariation {
  metric_name: string;
  percentage_change: number;
}

export interface SensitivityScenarioOutput {
  scenario_name: string;
  resulting_roi_percentage: number;
  resulting_total_annual_value: number;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
}

// Phase 3: Narrative Types
export interface NarrativeRequest {
  discovery_data: DiscoveryResponse;
  quantification_data: QuantificationResponse;
  target_audience: string[];
  narrative_style: 'executive' | 'technical' | 'financial';
}

export interface NarrativeResponse {
  narrative_text: string;
  key_points: string[];
  ai_critique: {
    critique_summary: string;
    suggestions: string[];
    confidence_score: number;
    strengths: string[];
    areas_for_improvement: string[];
  };
  executive_summary: string;
  talking_points: string[];
}

// Phase 4: Composition Types
export interface CompositionRequest {
  discovery_data: DiscoveryResponse;
  quantification_data: QuantificationResponse;
  narrative_data: NarrativeResponse;
  document_template?: string;
  export_format: 'pdf' | 'docx' | 'presentation';
}

export interface ComposedBusinessCase {
  title: string;
  executive_summary: string;
  introduction: string;
  value_drivers_section: string;
  financial_projections_section: string;
  risk_assessment_section: string;
  implementation_roadmap: string;
  conclusion: string;
  appendices: string[];
  table_of_contents: string[];
  metadata: {
    created_date: string;
    version: string;
    confidence_score: number;
    total_pages: number;
  };
}

export interface BusinessCaseTemplate {
  id: string;
  name: string;
  description: string;
  industry: string;
  use_case: string;
  estimated_completion_time: string;
}

// Create and export singleton instance
export const b2bValueAPI = new B2BValueAPIClient();

// Export types for use in components
export type {
  DiscoveryResponse,
  QuantificationRequest,
  QuantificationResponse,
  NarrativeRequest,
  NarrativeResponse,
  CompositionRequest,
  ComposedBusinessCase,
  BusinessCaseTemplate,
  ValueDriverPillar,
  Tier3Metric,
  Persona,
  RoiSummary
};
