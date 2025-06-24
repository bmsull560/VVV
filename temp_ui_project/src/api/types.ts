// Types for the model builder API
import { CalculationSummary, ComponentProperties, ModelComponent } from '../utils/calculationEngine';

export interface ModelConnection {
  id: string;
  source: string;
  target: string;
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
  summary?: CalculationSummary;
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
