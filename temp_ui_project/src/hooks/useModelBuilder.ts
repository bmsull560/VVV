import { useState, useCallback } from 'react';
import { ModelData, ModelConnection as ConnectionData, QuantifyRoiRequest, QuantifyRoiResponse, ExportModelRequest, ExportModelResponse, RoiSummary } from '../api/types';
import * as modelBuilderAPI from '../api/modelBuilderApi';
import { ModelComponent } from '../utils/calculationEngine';

interface UseModelBuilderReturn {
  model: ModelData | null;
  isLoading: boolean;
  error: string | null;
  loadModel: (modelId: string) => Promise<void>;
  createModel: (newModel: ModelData) => Promise<ModelData>;
  updateModel: (updatedModel: ModelData) => Promise<ModelData>;
  removeModel: (modelId: string) => Promise<void>;
  listUserModels: () => Promise<Array<{ id: string; name: string; updatedAt: string }>>;
  calculateModel: (request: QuantifyRoiRequest) => Promise<QuantifyRoiResponse>;
  exportModel: (request: ExportModelRequest) => Promise<ExportModelResponse>;
  addComponent: (component: Omit<ModelComponent, 'id'>) => void;
  updateComponent: (componentId: string, updates: Partial<ModelComponent>) => void;
  removeComponent: (componentId: string) => void;
  addConnection: (connection: Omit<ConnectionData, 'id'>) => void;
  removeConnection: (connectionId: string) => void;
  clearError: () => void;
}

export const useModelBuilder = (): UseModelBuilderReturn => {
  const [model, setModel] = useState<ModelData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Clear any error state
  const clearError = useCallback((): void => {
    setError(null);
  }, []);

  // Load a model by ID
  const loadModel = useCallback(async (modelId: string): Promise<void> => {
    try {
      setIsLoading(true);
      clearError();
      const loadedModel: ModelData = await modelBuilderAPI.getModel(modelId);
      setModel(loadedModel);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load model');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [clearError]);

  // Create a new model
  const createModel = useCallback(async (newModel: ModelData): Promise<ModelData> => {
    try {
      setIsLoading(true);
      clearError();
      const savedModel = await modelBuilderAPI.saveModel(newModel);
      setModel({ ...newModel, id: savedModel.modelId });
      return { ...newModel, id: savedModel.modelId };
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create model');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [clearError]);

  // Update an existing model
  const updateModel = useCallback(async (updatedModel: ModelData): Promise<ModelData> => {
    try {
      setIsLoading(true);
      clearError();
      await modelBuilderAPI.saveModel(updatedModel);
      setModel(updatedModel);
      return updatedModel;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update model');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [clearError]);

  // Delete a model
  const removeModel = useCallback(async (modelId: string) => {
    try {
      setIsLoading(true);
      clearError();
      await modelBuilderAPI.deleteModel(modelId);
      if (model?.id === modelId) {
        setModel(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete model');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [model?.id, clearError]);

  // List all models for the current user
  const listUserModels = useCallback(async () => {
    try {
      setIsLoading(true);
      clearError();
      const response = await modelBuilderAPI.listModels();
      return response.models;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to list models');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [clearError]);

  // Calculate model ROI and sensitivity
  const calculateModel = useCallback(async (request: QuantifyRoiRequest): Promise<QuantifyRoiResponse> => {
    try {
      setIsLoading(true);
      clearError();
      const response = await modelBuilderAPI.calculateModel(request);
      // Optionally update model state with calculation results if needed
      if (model) {
        setModel({ ...model, summary: response.quantification.roi_summary });
      }
      return response;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to calculate model');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [clearError, model]);

  // Export model
  const exportModel = useCallback(async (request: ExportModelRequest): Promise<ExportModelResponse> => {
    try {
      setIsLoading(true);
      clearError();
      const response = await modelBuilderAPI.exportModel(request);
      return response;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to export model');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [clearError]);

  // Add a component to the current model
  const addComponent = useCallback((component: Omit<ModelComponent, 'id'>): void => {
    if (!model) return;
    const newComponent: ModelComponent = {
      ...component,
      id: `comp-${Date.now()}`,
    };
    setModel({
      ...model,
      components: [...model.components, newComponent],
    });
  }, [model]);

  // Update a component in the current model
  const updateComponent = useCallback((componentId: string, updates: Partial<ModelComponent>): void => {
    if (!model) return;
    setModel({
      ...model,
      components: model.components.map((comp: ModelComponent) =>
          comp.id === componentId ? { ...comp, ...updates } : comp
        ),
    });
  }, [model]);

  // Remove a component from the current model
  const removeComponent = useCallback((componentId: string): void => {
    if (!model) return;
    setModel({
      ...model,
      components: model.components.filter((comp: ModelComponent) => comp.id !== componentId),
      connections: model.connections.filter((conn: ConnectionData) => conn.source !== componentId && conn.target !== componentId),
    });
  }, [model]);

  // Add a connection between components
  const addConnection = useCallback((connection: Omit<ConnectionData, 'id'>): void => {
    if (!model) return;
    const newConnection: ConnectionData = {
      ...connection,
      id: `conn-${Date.now()}`,
    };
    setModel({
      ...model,
      connections: [...model.connections, newConnection],
    });
  }, [model]);

  // Remove a connection between components
  const removeConnection = useCallback((connectionId: string): void => {
    if (!model) return;
    setModel({
      ...model,
      connections: model.connections.filter((conn: ConnectionData) => conn.id !== connectionId),
    });
  }, [model]);

  return {
    model,
    isLoading,
    error,
    loadModel,
    createModel,
    updateModel,
    removeModel,
    listUserModels,
    addComponent,
    updateComponent,
    removeComponent,
    addConnection,
    removeConnection,
    calculateModel,
    exportModel,
    clearError,
  };
};
