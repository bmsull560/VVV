// Types for the model builder API
/**
 * Represents a model component with typed properties.
 * @template T Properties type for the component
 */
export interface ModelComponent<T = Record<string, unknown>> {
  id: string;
  type: string;
  properties: T;
  position: {
    x: number;
    y: number;
  };
  size?: {
    width: number;
    height: number;
  };
}

export interface ModelConnection {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
}

/**
 * Represents the data structure for a model, including components and connections.
 * @template T Properties type for components
 * @template M Metadata type
 */
export interface ModelData<T = Record<string, unknown>, M = Record<string, unknown>> {
  id?: string;
  name: string;
  description?: string;
  components: ModelComponent<T>[];
  connections: ModelConnection[];
  createdAt?: string;
  updatedAt?: string;
  metadata?: M;
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
