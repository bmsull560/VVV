/**
 * Model Builder API Service
 * Integrates the visual model builder with B2BValue's quantification services
 */

import { b2bValueAPI, QuantificationRequest, QuantificationResponse } from './b2bValueApi';
import { ModelComponent, CalculationSummary, CalculationResult } from '../utils/calculationEngine';

export type { ModelComponent, CalculationResult };


// Extended interfaces for model builder integration
export interface ModelBuilderData {
  id: string;
  model: {
    components: ModelComponent[];
    connections: ConnectionData[];
  };
  calculations: Record<string, CalculationResult>;
  summary: CalculationSummary;
  metadata: {
    created_at: string;
    updated_at: string;
    version: string;
    collaboration_users?: string[];
  };
}

export interface ConnectionData {
  id: string;
  source: string;
  target: string;
  type: 'input' | 'calculation' | 'output';
}

export interface ModelValidationResult {
  isValid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
  completeness: number; // 0-1 scale
}

export interface ValidationError {
  id: string;
  message: string;
  component_id?: string;
  severity: 'error' | 'warning';
}

export interface ValidationWarning {
  id: string;
  message: string;
  component_id?: string;
  suggestion?: string;
}

export interface ModelExportData {
  format: 'json' | 'excel' | 'pdf' | 'csv';
  data: ModelBuilderData;
  export_options?: {
    include_calculations?: boolean;
    include_visualizations?: boolean;
    include_metadata?: boolean;
  };
}

export interface CollaborationSession {
  id: string;
  model_id: string;
  participants: CollaborationUser[];
  changes: ModelChange[];
  created_at: string;
  last_activity: string;
}

export interface CollaborationUser {
  id: string;
  name: string;
  email: string;
  role: 'owner' | 'editor' | 'viewer';
  cursor_position?: { x: number; y: number };
  active_component?: string;
}

// Define specific types for change data based on change type
export type ChangeData = 
  | { type: 'add_component'; component: Partial<ModelComponent> }
  | { type: 'update_component'; componentId: string; updates: Partial<ModelComponent> }
  | { type: 'delete_component'; componentId: string }
  | { type: 'update_connection'; connectionId: string; updates: Partial<ConnectionData> };

export interface ModelChange {
  id: string;
  user_id: string;
  timestamp: string;
  change_type: 'add_component' | 'update_component' | 'delete_component' | 'update_connection';
  component_id?: string;
  data: ChangeData;
}

// Define context data types for AI Assistant
export interface DiscoveryData {
  user_input?: string;
  project_type?: string;
  industry?: string;
  investment_amount?: number;
  metrics?: Array<{ name: string; value?: number; unit?: string }>;
  value_drivers?: Array<{
    category: string;
    description: string;
    metrics: Array<{ name: string; value?: number; unit?: string }>;
  }>;
  [key: string]: unknown;
}

export interface AIContext {
  discovery_data?: DiscoveryData;
  current_focus?: string;
}

export interface AIAssistantRequest {
  model_data: ModelBuilderData;
  user_query: string;
  context: AIContext;
}

export interface AIAssistantResponse {
  suggestions: AISuggestion[];
  optimizations: AIOptimization[];
  validation_feedback: string;
  confidence: number;
}

// Define implementation types for AI suggestions
export type SuggestionImplementation = 
  | { type: 'component'; componentType: ModelComponent['type']; properties: Partial<ModelComponent['properties']> }
  | { type: 'connection'; sourceId: string; targetId: string; connectionType: ConnectionData['type'] }
  | { type: 'calculation'; formula: string; dependencies: string[] }
  | { type: 'optimization'; steps: string[]; priority: 'high' | 'medium' | 'low' };

export interface AISuggestion {
  id: string;
  type: 'component' | 'connection' | 'calculation' | 'optimization';
  title: string;
  description: string;
  implementation: SuggestionImplementation;
  impact_score: number;
}

export interface AIOptimization {
  id: string;
  area: string;
  description: string;
  expected_improvement: string;
  implementation_steps: string[];
}

class ModelBuilderAPIClient {
  private isDevelopment = import.meta.env.DEV || false;

  /**
   * Convert model builder data to quantification request format
   */
  private convertToQuantificationRequest(modelData: ModelBuilderData, investmentAmount: number): QuantificationRequest {
    const metrics: { [key: string]: number } = {};
    
    // Extract metrics from model components
    modelData.model.components.forEach(component => {
      if (component.type === 'input' && component.properties.value !== undefined) {
        metrics[component.properties.name || component.id] = component.properties.value;
      }
    });

    // Add calculated values
    Object.entries(modelData.calculations).forEach(([key, result]) => {
      metrics[key] = result.value;
    });

    return {
      investment_amount: investmentAmount,
      metrics,
      time_horizon_years: 3, // Default to 3 years
      sensitivity_variations: [
        { metric_name: 'productivity_gain', percentage_change: -10 },
        { metric_name: 'productivity_gain', percentage_change: 10 },
        { metric_name: 'cost_reduction', percentage_change: -15 },
        { metric_name: 'cost_reduction', percentage_change: 15 }
      ]
    };
  }

  /**
   * Calculate ROI using backend quantification services
   */
  async calculateROIWithBackend(modelData: ModelBuilderData, investmentAmount: number): Promise<QuantificationResponse> {
    try {
      const quantificationRequest = this.convertToQuantificationRequest(modelData, investmentAmount);
      
      if (this.isDevelopment) {
        // Return mock data in development mode
        return {
          roi_summary: {
            total_annual_value: modelData.summary.netBenefit,
            roi_percentage: modelData.summary.roi,
            payback_period_months: modelData.summary.paybackPeriod || 18,
            confidence_score: modelData.summary.confidence
          },
          sensitivity_analysis: [
            {
              scenario_name: 'Conservative',
              resulting_roi_percentage: modelData.summary.roi * 0.8,
              resulting_total_annual_value: modelData.summary.netBenefit * 0.8,
              risk_level: 'low'
            },
            {
              scenario_name: 'Optimistic',
              resulting_roi_percentage: modelData.summary.roi * 1.2,
              resulting_total_annual_value: modelData.summary.netBenefit * 1.2,
              risk_level: 'medium'
            }
          ],
          financial_projections: {
            year_1_benefit: modelData.summary.netBenefit * 0.7,
            year_2_benefit: modelData.summary.netBenefit,
            year_3_benefit: modelData.summary.netBenefit * 1.1,
            total_npv: modelData.summary.npv || modelData.summary.netBenefit * 2.5,
            irr_percentage: modelData.summary.irr || 25
          }
        };
      }

      return await b2bValueAPI.quantifyROI(quantificationRequest);
    } catch (error) {
      console.error('Failed to calculate ROI with backend:', error);
      throw new Error('ROI calculation failed. Please check your model configuration.');
    }
  }

  /**
   * Validate model structure and completeness
   */
  async validateModel(modelData: ModelBuilderData): Promise<ModelValidationResult> {
    const errors: ValidationError[] = [];
    const warnings: ValidationWarning[] = [];
    
    // Check for required components
    const hasInputs = modelData.model.components.some(c => c.type === 'input');
    const hasCalculations = modelData.model.components.some(c => c.type === 'calculation');
    const hasOutputs = modelData.model.components.some(c => c.type === 'output');

    if (!hasInputs) {
      errors.push({
        id: 'missing_inputs',
        message: 'Model must have at least one input component',
        severity: 'error'
      });
    }

    if (!hasCalculations) {
      warnings.push({
        id: 'no_calculations',
        message: 'Consider adding calculation components to show business logic',
        suggestion: 'Add ROI, NPV, or cost-benefit calculations'
      });
    }

    if (!hasOutputs) {
      warnings.push({
        id: 'no_outputs',
        message: 'Add output components to display key results',
        suggestion: 'Add components to show final ROI, total benefits, or payback period'
      });
    }

    // Check component connections
    const unconnectedComponents = modelData.model.components.filter(component => {
      const isConnected = modelData.model.connections.some(conn => 
        conn.source === component.id || conn.target === component.id
      );
      return !isConnected && modelData.model.components.length > 1;
    });

    unconnectedComponents.forEach(component => {
      warnings.push({
        id: `unconnected_${component.id}`,
        message: `Component "${component.properties.label || component.id}" is not connected`,
        component_id: component.id,
        suggestion: 'Connect this component to show data flow'
      });
    });

    // Calculate completeness score
    const totalChecks = 5; // inputs, calculations, outputs, connections, values
    let passedChecks = 0;
    
    if (hasInputs) passedChecks++;
    if (hasCalculations) passedChecks++;
    if (hasOutputs) passedChecks++;
    if (modelData.model.connections.length > 0) passedChecks++;
    if (Object.keys(modelData.calculations).length > 0) passedChecks++;

    const completeness = passedChecks / totalChecks;

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
      completeness
    };
  }

  /**
   * Export model data in various formats
   */
  async exportModel(modelData: ModelBuilderData, format: 'json' | 'excel' | 'pdf' | 'csv'): Promise<Blob> {
    const exportData: ModelExportData = {
      format,
      data: modelData,
      export_options: {
        include_calculations: true,
        include_visualizations: true,
        include_metadata: true
      }
    };

    switch (format) {
      case 'json':
        return new Blob([JSON.stringify(exportData.data, null, 2)], { type: 'application/json' });
      
      case 'csv': {
        const csvData = this.convertToCSV(modelData);
        return new Blob([csvData], { type: 'text/csv' });
      }
      
      case 'excel':
      case 'pdf':
        // In a real implementation, this would call backend services
        throw new Error(`${format} export not yet implemented. Please use JSON or CSV format.`);
      
      default:
        throw new Error(`Unsupported export format: ${format}`);
    }
  }

  /**
   * Import model data from file
   */
  async importModel(file: File): Promise<ModelBuilderData> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = (event) => {
        try {
          const content = event.target?.result as string;
          
          if (file.type === 'application/json' || file.name.endsWith('.json')) {
            const modelData = JSON.parse(content);
            
            // Validate imported data structure
            if (!modelData.model || !modelData.model.components) {
              throw new Error('Invalid model file format');
            }
            
            // Add metadata if missing
            if (!modelData.metadata) {
              modelData.metadata = {
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
                version: '1.0.0'
              };
            }
            
            resolve(modelData);
          } else {
            reject(new Error('Unsupported file format. Please use JSON files.'));
          }
        } catch (error) {
          reject(new Error(`Failed to parse model file: ${error}`));
        }
      };
      
      reader.onerror = () => reject(new Error('Failed to read file'));
      reader.readAsText(file);
    });
  }

  /**
   * Save model to backend (when available)
   */
  async saveModel(modelData: ModelBuilderData, modelId?: string): Promise<{ id: string; success: boolean }> {
    if (this.isDevelopment) {
      // In development, save to localStorage
      const id = modelId || `model_${Date.now()}`;
      localStorage.setItem(`model_${id}`, JSON.stringify(modelData));
      return { id, success: true };
    }

    // In production, this would call the backend API
    throw new Error('Model saving to backend not yet implemented');
  }

  /**
   * Load model from backend
   */
  async loadModel(modelId: string): Promise<ModelBuilderData> {
    if (this.isDevelopment) {
      const data = localStorage.getItem(`model_${modelId}`);
      if (!data) {
        throw new Error('Model not found');
      }
      return JSON.parse(data);
    }

    // In production, this would call the backend API
    throw new Error('Model loading from backend not yet implemented');
  }

  /**
   * Delete a model by ID
   */
  async deleteModel(modelId: string): Promise<void> {
    if (this.isDevelopment) {
      localStorage.removeItem(`model_${modelId}`);
      return;
    }
    throw new Error('Model deletion from backend not yet implemented');
  }

  /**
   * List all models (IDs, names, updatedAt)
   */
  async listModels(): Promise<{ models: Array<{ id: string; name: string; updatedAt: string }> }> {
    if (this.isDevelopment) {
      const models: Array<{ id: string; name: string; updatedAt: string }> = [];
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith('model_')) {
          try {
            const data = JSON.parse(localStorage.getItem(key) || '{}');
            models.push({
              id: key.replace('model_', ''),
              name: data.metadata?.name || key.replace('model_', 'Untitled '),
              updatedAt: data.metadata?.updated_at || ''
            });
          } catch {
            // skip invalid entries
          }
        }
      }
      return { models };
    }
    throw new Error('Model listing from backend not yet implemented');
  }

  /**
   * Get AI assistance for model optimization
   */
  async getAIAssistance(request: AIAssistantRequest): Promise<AIAssistantResponse> {
    // This would integrate with the B2BValue AI agents
    // For now, return mock suggestions based on model analysis
    
    const suggestions: AISuggestion[] = [];
    const optimizations: AIOptimization[] = [];

    // Analyze model and provide suggestions
    if (request.model_data.model.components.length < 3) {
      suggestions.push({
        id: 'add_components',
        type: 'component',
        title: 'Add More Components',
        description: 'Consider adding more input and calculation components to create a comprehensive model',
        implementation: { type: 'component', componentType: 'input', properties: { label: 'Additional Cost Factor' } },
        impact_score: 0.7
      });
    }

    if (Object.keys(request.model_data.calculations).length === 0) {
      suggestions.push({
        id: 'add_calculations',
        type: 'calculation',
        title: 'Add Financial Calculations',
        description: 'Include ROI, NPV, or payback period calculations',
        implementation: { type: 'calculation', formula: 'roi', dependencies: [] },
        impact_score: 0.9
      });
    }

    return {
      suggestions,
      optimizations,
      validation_feedback: 'Your model structure looks good. Consider adding more detailed calculations for better accuracy.',
      confidence: 0.85
    };
  }

  /**
   * Convert model data to CSV format
   */
  private convertToCSV(modelData: ModelBuilderData): string {
    const headers = ['Component ID', 'Type', 'Label', 'Value', 'Formula'];
    const rows = [headers.join(',')];

    modelData.model.components.forEach(component => {
      const row = [
        component.id,
        component.type,
        component.properties.label || '',
        component.properties.value || '',
        component.properties.formula || ''
      ].map(value => `"${value}"`);
      rows.push(row.join(','));
    });

    // Add calculations section
    rows.push('', 'Calculations:');
    Object.entries(modelData.calculations).forEach(([key, result]) => {
      rows.push(`"${key}","calculation","","${result.value}",""`);
    });

    return rows.join('\n');
  }
}

// Create and export singleton instance
export const modelBuilderAPI = new ModelBuilderAPIClient();
