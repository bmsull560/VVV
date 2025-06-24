import { useState, useCallback } from 'react';
import { ModelBuilderData, ModelComponent, ConnectionData } from '../services/modelBuilderApi';
import { modelBuilderAPI } from '../services/modelBuilderApi';

interface UseModelBuilderReturn {
  model: ModelBuilderData | null;
  isLoading: boolean;
  error: string | null;
  loadModel: (modelId: string) => Promise<void>;
  createModel: (newModel: ModelBuilderData) => Promise<ModelBuilderData>;
  updateModel: (updatedModel: ModelBuilderData) => Promise<ModelBuilderData>;
  removeModel: (modelId: string) => Promise<void>;
  listUserModels: () => Promise<Array<{ id: string; name: string; updatedAt: string }>>;
  addComponent: (component: Omit<ModelComponent, 'id'>) => void;
  updateComponent: (componentId: string, updates: Partial<ModelComponent>) => void;
  removeComponent: (componentId: string) => void;
  addConnection: (connection: Omit<ConnectionData, 'id'>) => void;
  removeConnection: (connectionId: string) => void;
  clearError: () => void;
}

export const useModelBuilder = (): UseModelBuilderReturn => {
  const [model, setModel] = useState<ModelBuilderData | null>(null);
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
      const loadedModel: ModelBuilderData = await modelBuilderAPI.loadModel(modelId);
      setModel(loadedModel);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load model');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [clearError]);

  // Create a new model
  const createModel = useCallback(async (newModel: ModelBuilderData): Promise<ModelBuilderData> => {
    try {
      setIsLoading(true);
      clearError();
      await modelBuilderAPI.saveModel(newModel);
      setModel(newModel);
      return newModel;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create model');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [clearError]);

  // Update an existing model
  const updateModel = useCallback(async (updatedModel: ModelBuilderData): Promise<ModelBuilderData> => {
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

  // Add a component to the current model
  const addComponent = useCallback((component: Omit<ModelComponent, 'id'>): void => {
    if (!model) return;
    const newComponent: ModelComponent = {
      ...component,
      id: `comp-${Date.now()}`,
    };
    setModel({
      ...model,
      model: {
        ...model.model,
        components: [...model.model.components, newComponent],
      },
    });
  }, [model]);

  // Update a component in the current model
  const updateComponent = useCallback((componentId: string, updates: Partial<ModelComponent>): void => {
    if (!model) return;
    setModel({
      ...model,
      model: {
        ...model.model,
        components: model.model.components.map((comp: ModelComponent) =>
          comp.id === componentId ? { ...comp, ...updates } : comp
        ),
      },
    });
  }, [model]);

  // Remove a component from the current model
  const removeComponent = useCallback((componentId: string): void => {
    if (!model) return;
    setModel({
      ...model,
      model: {
        ...model.model,
        components: model.model.components.filter((comp: ModelComponent) => comp.id !== componentId),
        connections: model.model.connections.filter((conn: ConnectionData) => conn.source !== componentId && conn.target !== componentId),
      },
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
      model: {
        ...model.model,
        connections: [...model.model.connections, newConnection],
      },
    });
  }, [model]);

  // Remove a connection between components
  const removeConnection = useCallback((connectionId: string): void => {
    if (!model) return;
    setModel({
      ...model,
      model: {
        ...model.model,
        connections: model.model.connections.filter((conn: ConnectionData) => conn.id !== connectionId),
      },
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
    clearError,
  };
};
