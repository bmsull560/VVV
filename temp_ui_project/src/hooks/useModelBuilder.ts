import { useState, useCallback } from 'react';
import { ModelData, ModelComponent, Connection } from '../types/model';
import { getModel, saveModel, listModels, deleteModel } from '../api/modelBuilderApi';

interface UseModelBuilderReturn {
  model: ModelData | null;
  isLoading: boolean;
  error: string | null;
  loadModel: (modelId: string) => Promise<void>;
  createModel: (model: Omit<ModelData, 'id'>) => Promise<ModelData>;
  updateModel: (model: ModelData) => Promise<ModelData>;
  removeModel: (modelId: string) => Promise<void>;
  listUserModels: () => Promise<Array<{ id: string; name: string; updatedAt: string }>>;
  addComponent: (component: Omit<ModelComponent, 'id'>) => void;
  updateComponent: (componentId: string, updates: Partial<ModelComponent>) => void;
  removeComponent: (componentId: string) => void;
  addConnection: (connection: Omit<Connection, 'id'>) => void;
  removeConnection: (connectionId: string) => void;
  clearError: () => void;
}

export const useModelBuilder = (): UseModelBuilderReturn => {
  const [model, setModel] = useState<ModelData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Clear any error state
  const clearError = useCallback(() => setError(null), []);

  // Load a model by ID
  const loadModel = useCallback(async (modelId: string) => {
    try {
      setIsLoading(true);
      clearError();
      const loadedModel = await getModel(modelId);
      setModel(loadedModel);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load model');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [clearError]);

  // Create a new model
  const createModel = useCallback(async (newModel: Omit<ModelData, 'id'>) => {
    try {
      setIsLoading(true);
      clearError();
      const createdModel = await saveModel(newModel);
      setModel(createdModel);
      return createdModel;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create model');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [clearError]);

  // Update an existing model
  const updateModel = useCallback(async (updatedModel: ModelData) => {
    if (!updatedModel.id) {
      throw new Error('Cannot update a model without an ID');
    }
    
    try {
      setIsLoading(true);
      clearError();
      const savedModel = await saveModel(updatedModel);
      setModel(savedModel);
      return savedModel;
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
      await deleteModel(modelId);
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
      const response = await listModels();
      return response.models;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to list models');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [clearError]);

  // Add a component to the current model
  const addComponent = useCallback((component: Omit<ModelComponent, 'id'>) => {
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
  const updateComponent = useCallback((componentId: string, updates: Partial<ModelComponent>) => {
    if (!model) return;
    
    setModel({
      ...model,
      components: model.components.map(comp => 
        comp.id === componentId ? { ...comp, ...updates } : comp
      ),
    });
  }, [model]);

  // Remove a component from the current model
  const removeComponent = useCallback((componentId: string) => {
    if (!model) return;
    
    setModel({
      ...model,
      components: model.components.filter(comp => comp.id !== componentId),
      connections: model.connections.filter(
        conn => conn.source !== componentId && conn.target !== componentId
      ),
    });
  }, [model]);

  // Add a connection between components
  const addConnection = useCallback((connection: Omit<Connection, 'id'>) => {
    if (!model) return;
    
    const newConnection: Connection = {
      ...connection,
      id: `conn-${Date.now()}`,
    };
    
    setModel({
      ...model,
      connections: [...model.connections, newConnection],
    });
  }, [model]);

  // Remove a connection between components
  const removeConnection = useCallback((connectionId: string) => {
    if (!model) return;
    
    setModel({
      ...model,
      connections: model.connections.filter(conn => conn.id !== connectionId),
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
