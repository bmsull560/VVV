// Types for the model builder API
export interface ModelComponent {
  id: string;
  type: string;
  properties: Record<string, any>;
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

export interface ModelData {
  id?: string;
  name: string;
  description?: string;
  components: ModelComponent[];
  connections: ModelConnection[];
  createdAt?: string;
  updatedAt?: string;
  metadata?: Record<string, any>;
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

export interface ApiError {
  message: string;
  status?: number;
  details?: any;
}
