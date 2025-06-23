/**
 * B2BValue API Service Layer
 * Connects the frontend UI to the production-ready B2BValue agents
 */

import axios, { AxiosInstance } from 'axios';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_TIMEOUT = 30000; // 30 seconds
const DEVELOPMENT_MODE = import.meta.env.DEV || false;

// Mock Data for Development (when backend is not available)
const MOCK_DISCOVERY_RESPONSE: DiscoveryResponse = {
  value_drivers: [
    {
      pillar: "Cost Reduction",
      tier_2_drivers: ["Operational Efficiency", "Process Automation", "Resource Optimization"],
      tier_3_metrics: [
        {
          name: "productivity_gain",
          description: "Percentage increase in staff productivity",
          unit: "percentage",
          suggested_value: 25,
          confidence_level: "high"
        },
        {
          name: "cost_reduction",
          description: "Annual cost savings from automation",
          unit: "dollars",
          suggested_value: 150000,
          confidence_level: "medium"
        }
      ]
    },
    {
      pillar: "Revenue Enhancement",
      tier_2_drivers: ["Customer Experience", "Sales Acceleration", "Market Expansion"],
      tier_3_metrics: [
        {
          name: "customer_satisfaction",
          description: "Improvement in customer satisfaction scores",
          unit: "percentage",
          suggested_value: 20,
          confidence_level: "medium"
        }
      ]
    }
  ],
  personas: [
    {
      name: "CFO",
      description: "Chief Financial Officer focused on ROI and cost management",
      priorities: ["Cost reduction", "ROI optimization", "Budget efficiency"],
      concerns: ["Implementation costs", "Payback period", "Financial risk"]
    },
    {
      name: "CIO",
      description: "Chief Information Officer focused on technology strategy",
      priorities: ["Digital transformation", "System integration", "Technology modernization"],
      concerns: ["Technical complexity", "Security", "System reliability"]
    }
  ],
  suggested_metrics: [
    {
      name: "productivity_gain",
      description: "Percentage increase in staff productivity",
      unit: "percentage",
      suggested_value: 25,
      confidence_level: "high"
    },
    {
      name: "cost_reduction",
      description: "Annual cost savings from automation",
      unit: "dollars",
      suggested_value: 150000,
      confidence_level: "medium"
    }
  ],
  project_insights: {
    industry_context: "Technology sector showing strong adoption of automation solutions",
    complexity_assessment: "Medium complexity - requires careful change management",
    recommended_approach: "Phased implementation with pilot program"
  }
};

const MOCK_QUANTIFICATION_RESPONSE: QuantificationResponse = {
  roi_summary: {
    total_annual_value: 450000,
    roi_percentage: 1.8,
    payback_period_months: 14,
    confidence_score: 0.85
  },
  sensitivity_analysis: [
    {
      scenario_name: "Conservative (-10% productivity)",
      resulting_roi_percentage: 1.5,
      resulting_total_annual_value: 380000,
      risk_level: "low"
    },
    {
      scenario_name: "Optimistic (+10% productivity)",
      resulting_roi_percentage: 2.1,
      resulting_total_annual_value: 520000,
      risk_level: "medium"
    }
  ],
  financial_projections: {
    year_1_benefit: 300000,
    year_2_benefit: 450000,
    year_3_benefit: 500000,
    total_npv: 1050000,
    irr_percentage: 0.45
  }
};

const MOCK_NARRATIVE_RESPONSE: NarrativeResponse = {
  narrative_text: `Executive Summary

The implementation of an AI-powered customer service chatbot represents a strategic investment opportunity that will fundamentally transform our customer experience while delivering substantial operational efficiencies and cost savings.

Strategic Business Case

In today's competitive landscape, customer expectations for instant, accurate support have never been higher. Our analysis reveals that implementing an AI-powered customer service solution will address three critical business challenges:

1. Operational Efficiency: Current response times averaging 4-6 hours will be reduced to under 60 seconds for standard inquiries, representing a 99% improvement in responsiveness.

2. Cost Optimization: By automating routine inquiries that represent 70% of our current support volume, we project annual cost savings of $150,000 while redirecting human agents to high-value, complex customer issues.

3. Scalability: The solution provides 24/7 availability and can handle unlimited concurrent conversations, eliminating capacity constraints during peak periods.

Financial Impact

Our comprehensive ROI analysis demonstrates compelling financial returns:
• Total Annual Value: $450,000
• Return on Investment: 180%
• Payback Period: 14 months
• 3-Year NPV: $1,050,000

These projections are based on conservative assumptions and include comprehensive sensitivity analysis accounting for various implementation scenarios.

Implementation Approach

We recommend a phased implementation beginning with a pilot program targeting our most common inquiry types. This approach minimizes risk while allowing for optimization based on real-world performance data.

The technology integration leverages our existing CRM infrastructure, ensuring seamless deployment without disrupting current operations.

Conclusion

This investment aligns with our digital transformation strategy while delivering measurable improvements in customer satisfaction, operational efficiency, and financial performance. The compelling ROI, combined with competitive advantages in customer experience, makes this initiative a strategic imperative for our continued growth and market leadership.`,
  
  key_points: [
    "99% improvement in customer response times (from hours to seconds)",
    "$450,000 total annual value with 180% ROI",
    "24/7 availability eliminating capacity constraints",
    "70% automation of routine inquiries reduces operational costs",
    "Seamless integration with existing CRM infrastructure",
    "Phased implementation approach minimizes deployment risk",
    "14-month payback period with $1,050,000 three-year NPV"
  ],
  
  ai_critique: {
    critique_summary: "This business case narrative effectively combines quantitative financial projections with strategic positioning. The structure follows best practices with clear executive summary, detailed analysis, and actionable recommendations. The narrative successfully translates technical benefits into business value that resonates with executive decision-makers.",
    suggestions: [
      "Consider adding a competitive analysis section to strengthen market positioning",
      "Include specific customer satisfaction metrics and improvement targets",
      "Add risk mitigation strategies for potential implementation challenges",
      "Reference industry benchmarks to validate projected efficiency gains"
    ],
    confidence_score: 0.87,
    strengths: [
      "Clear structure and logical flow",
      "Strong financial analysis with specific metrics",
      "Effective translation of technical benefits to business value",
      "Professional tone appropriate for executive audience"
    ],
    areas_for_improvement: [
      "Competitive analysis",
      "Customer satisfaction metrics",
      "Risk mitigation strategies",
      "Industry benchmark references"
    ]
  },
  
  executive_summary: "The implementation of an AI-powered customer service chatbot represents a strategic investment opportunity that will fundamentally transform our customer experience while delivering substantial operational efficiencies and cost savings.",
  
  talking_points: [
    "The AI-powered chatbot will improve customer response times by 99%.",
    "The solution will provide annual cost savings of $150,000.",
    "The phased implementation approach minimizes risk and allows for optimization based on real-world performance data.",
    "24/7 availability eliminates capacity constraints during peak periods.",
    "Integration with existing CRM infrastructure ensures seamless deployment."
  ]
};

const MOCK_COMPOSITION_RESPONSE: ComposedBusinessCase = {
  title: "AI-Powered Customer Service Chatbot Business Case",
  executive_summary: "The implementation of an AI-powered customer service chatbot represents a strategic investment opportunity that will fundamentally transform our customer experience while delivering substantial operational efficiencies and cost savings.",
  introduction: "In today's competitive landscape, customer expectations for instant, accurate support have never been higher.",
  value_drivers_section: "Our analysis reveals that implementing an AI-powered customer service solution will address three critical business challenges: Operational Efficiency, Cost Optimization, and Scalability.",
  financial_projections_section: "Our comprehensive ROI analysis demonstrates compelling financial returns: Total Annual Value: $450,000, Return on Investment: 180%, Payback Period: 14 months, 3-Year NPV: $1,050,000",
  risk_assessment_section: "We recommend a phased implementation beginning with a pilot program targeting our most common inquiry types.",
  implementation_roadmap: "The technology integration leverages our existing CRM infrastructure, ensuring seamless deployment without disrupting current operations.",
  conclusion: "This investment aligns with our digital transformation strategy while delivering measurable improvements in customer satisfaction, operational efficiency, and financial performance.",
  appendices: ["Appendix A: ROI Analysis", "Appendix B: Sensitivity Analysis"],
  table_of_contents: ["Executive Summary", "Introduction", "Value Drivers", "Financial Projections", "Risk Assessment", "Implementation Roadmap", "Conclusion"],
  metadata: {
    created_date: "2023-02-20",
    version: "1.0",
    confidence_score: 0.85,
    total_pages: 12
  }
};

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
    if (DEVELOPMENT_MODE) {
      return MOCK_DISCOVERY_RESPONSE;
    }
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
    if (DEVELOPMENT_MODE) {
      return MOCK_QUANTIFICATION_RESPONSE;
    }
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
    if (DEVELOPMENT_MODE) {
      return MOCK_NARRATIVE_RESPONSE;
    }
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
    if (DEVELOPMENT_MODE) {
      return MOCK_COMPOSITION_RESPONSE;
    }
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
interface DiscoveryRequest {
  user_query: string;
  analysis_type?: string;
}

interface DiscoveryResponse {
  value_drivers: ValueDriverPillar[];
  personas: Persona[];
  suggested_metrics: Tier3Metric[];
  project_insights: {
    industry_context: string;
    complexity_assessment: string;
    recommended_approach: string;
  };
}

interface ValueDriverPillar {
  pillar: string;
  tier_2_drivers: string[];
  tier_3_metrics: Tier3Metric[];
}

interface Tier3Metric {
  name: string;
  description: string;
  unit: string;
  suggested_value?: number;
  confidence_level: 'high' | 'medium' | 'low';
}

interface Persona {
  name: string;
  description: string;
  priorities: string[];
  concerns: string[];
}

// Phase 2: Quantification Types
interface QuantificationRequest {
  investment_amount: number;
  metrics: { [key: string]: number };
  sensitivity_variations?: SensitivityVariation[];
  time_horizon_years?: number;
}

interface QuantificationResponse {
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

interface RoiSummary {
  total_annual_value: number;
  roi_percentage: number;
  payback_period_months: number;
  confidence_score: number;
}

interface SensitivityVariation {
  metric_name: string;
  percentage_change: number;
}

interface SensitivityScenarioOutput {
  scenario_name: string;
  resulting_roi_percentage: number;
  resulting_total_annual_value: number;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
}

// Phase 3: Narrative Types
interface NarrativeRequest {
  discovery_data: DiscoveryResponse;
  quantification_data: QuantificationResponse;
  target_audience: string[];
  narrative_style: 'executive' | 'technical' | 'financial';
}

interface NarrativeResponse {
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
interface CompositionRequest {
  discovery_data: DiscoveryResponse;
  quantification_data: QuantificationResponse;
  narrative_data: NarrativeResponse;
  document_template?: string;
  export_format: 'pdf' | 'docx' | 'presentation';
  user_feedback?: { approved: boolean; comments?: string };
}

interface ComposedBusinessCase {
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

interface BusinessCaseTemplate {
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
  DiscoveryRequest,
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
