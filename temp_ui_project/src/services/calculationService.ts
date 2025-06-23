import { CalculationResult, CalculationSummary } from '../utils/calculationEngine';

// Interface for backend ROI calculation requests
interface ROICalculationRequest {
  drivers: Array<{
    pillar: string;
    description: string;
    metrics: Array<{
      name: string;
      value: number;
      unit: string;
      confidence?: number;
    }>;
  }>;
  investment: number;
  analysisYears?: number;
  discountRate?: number;
}

// Interface for backend ROI calculation response
interface ROICalculationResponse {
  total_annual_gain: number;
  roi_percentage: number;
  payback_period_months: number;
  npv: number;
  irr: number;
  confidence_score: number;
  detailed_calculations: Record<string, CalculationResult>;
}

class CalculationService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  }

  /**
   * Convert frontend model components to backend-compatible format
   */
  private convertToBackendFormat(components: Record<string, unknown>): ROICalculationRequest {
    const drivers: ROICalculationRequest['drivers'] = [];
    let investment = 0;

    // Process each component and convert to driver format
    Object.entries(components).forEach(([componentId, component]) => {
      if (typeof component === 'object' && component !== null) {
        const comp = component as Record<string, unknown>;
        
        if (comp.type === 'investment') {
          investment = Number(comp.amount) || 0;
        } else if (comp.type === 'revenue' || comp.type === 'cost_savings' || comp.type === 'productivity') {
          // Map to appropriate driver pillar
          const pillarMap: Record<string, string> = {
            'revenue': 'Revenue Enhancement',
            'cost_savings': 'Cost Reduction', 
            'productivity': 'Productivity Gains'
          };

          const pillar = pillarMap[comp.type as string] || 'Other Benefits';
          
          let existingDriver = drivers.find(d => d.pillar === pillar);
          if (!existingDriver) {
            existingDriver = {
              pillar,
              description: `Benefits from ${pillar.toLowerCase()} (${componentId})`,
              metrics: []
            };
            drivers.push(existingDriver);
          }

          // Add metrics from component properties
          if (comp.annualValue) {
            existingDriver.metrics.push({
              name: 'annual_benefit',
              value: Number(comp.annualValue),
              unit: 'USD',
              confidence: Number(comp.confidence) || 0.7
            });
          }
        }
      }
    });

    return {
      drivers,
      investment,
      analysisYears: 3,
      discountRate: 0.10
    };
  }

  /**
   * Send calculation request to B2BValue backend ROI calculator
   */
  async calculateROI(components: Record<string, unknown>): Promise<ROICalculationResponse> {
    try {
      const requestData = this.convertToBackendFormat(components);
      
      const response = await fetch(`${this.baseUrl}/api/quantify-roi`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(requestData)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Backend ROI calculation failed:', error);
      
      // Fallback to frontend calculation if backend is unavailable
      return this.fallbackCalculation(components);
    }
  }

  /**
   * Fallback calculation using frontend engine when backend is unavailable
   */
  private fallbackCalculation(components: Record<string, unknown>): ROICalculationResponse {
    let totalRevenue = 0;
    let totalCosts = 0;
    let investment = 0;

    Object.values(components).forEach(component => {
      if (typeof component === 'object' && component !== null) {
        const comp = component as Record<string, unknown>;
        
        if (comp.type === 'revenue' && comp.annualValue) {
          totalRevenue += Number(comp.annualValue);
        } else if (comp.type === 'cost_savings' && comp.annualValue) {
          totalCosts += Number(comp.annualValue);
        } else if (comp.type === 'investment' && comp.amount) {
          investment += Number(comp.amount);
        }
      }
    });

    const totalAnnualGain = totalRevenue + totalCosts;
    const roiPercentage = investment > 0 ? ((totalAnnualGain * 3 - investment) / investment) * 100 : 0;
    const paybackMonths = totalAnnualGain > 0 ? (investment / totalAnnualGain) * 12 : 0;
    
    // Simple NPV calculation (3 years, 10% discount rate)
    const npv = totalAnnualGain > 0 ? 
      (totalAnnualGain / 1.1) + (totalAnnualGain / 1.21) + (totalAnnualGain / 1.331) - investment : 
      -investment;

    // Simple IRR approximation
    const irr = totalAnnualGain > 0 && investment > 0 ? 
      Math.pow(totalAnnualGain * 3 / investment, 1/3) - 1 : 0;

    return {
      total_annual_gain: totalAnnualGain,
      roi_percentage: roiPercentage,
      payback_period_months: paybackMonths,
      npv,
      irr: irr * 100,
      confidence_score: 0.6, // Lower confidence for fallback calculation
      detailed_calculations: {}
    };
  }

  /**
   * Convert backend response to frontend summary format
   */
  convertToSummary(response: ROICalculationResponse): CalculationSummary {
    return {
      totalRevenue: response.total_annual_gain,
      totalCosts: 0, // Backend doesn't separate revenue/costs in response
      netValue: response.total_annual_gain,
      netBenefit: response.total_annual_gain,
      roi: response.roi_percentage,
      confidence: response.confidence_score,
      paybackPeriod: response.payback_period_months / 12, // Convert to years
      npv: response.npv,
      irr: response.irr
    };
  }

  /**
   * Health check for backend service
   */
  async healthCheck(): Promise<boolean> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);
      
      const response = await fetch(`${this.baseUrl}/health`, {
        method: 'GET',
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      return response.ok;
    } catch {
      return false;
    }
  }
}

export const calculationService = new CalculationService();
export type { ROICalculationRequest, ROICalculationResponse };
