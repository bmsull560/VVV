import React, { useState, useCallback, useEffect, useRef } from 'react';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { Card, CardHeader, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Alert, AlertDescription } from '../components/ui/alert';
import {
  Brain,
  Play,
  Upload,
  Download,
  Sparkles,
  Settings,
  Zap,
  TrendingUp,
  FileInput,
  Cpu
} from 'lucide-react';
import PropertiesPanel from './model-builder/PropertiesPanel';
import ModelCanvas from './model-builder/ModelCanvas';
import CalculationPanel from './model-builder/CalculationPanel';
import ComponentLibrary from './model-builder/ComponentLibrary';
import { ModelComponent, CalculationResult, calculationEngine } from '../utils/calculationEngine';
import { modelBuilderAPI, ModelBuilderData, ModelValidationResult, AIAssistantResponse, ConnectionData, DiscoveryData } from '../services/modelBuilderApi';
import styles from './Step2_ModelBuilder.module.css';

interface Step2ModelBuilderProps {
  discoveryData: DiscoveryData;
  onNext: (data: DiscoveryData & { modelBuilderData: ModelBuilderData; quantificationResults?: unknown; localCalculations?: Record<string, CalculationResult>; validationResults?: ModelValidationResult; }) => void;
  onBack: () => void;
}

interface ModelBuilderState {
  model: ModelBuilderData | null;
  selectedComponent: string | null;
  calculations: Record<string, CalculationResult>;
  isCalculating: boolean;
  isGenerating: boolean;
  hasUnsavedChanges: boolean;
  showAIAssistant: boolean;
  validationResult: ModelValidationResult | null;
  exportFormat: 'json' | 'csv' | 'excel' | 'pdf';
  isExporting: boolean;
  aiSuggestions: AIAssistantResponse | null;
  collaborationMode: boolean;
}

const Step2_ModelBuilder: React.FC<Step2ModelBuilderProps> = ({
  discoveryData,
  onNext,
  onBack
}) => {
  const [state, setState] = useState<ModelBuilderState>({
    model: null,
    selectedComponent: null,
    calculations: {},
    isCalculating: false,
    isGenerating: false,
    hasUnsavedChanges: false,
    showAIAssistant: false,
    validationResult: null,
    exportFormat: 'json',
    isExporting: false,
    aiSuggestions: null,
    collaborationMode: false
  });

  const [alert, setAlert] = useState<{
    type: 'success' | 'warning' | 'error';
    message: string;
  } | null>(null);

  const performCalculations = useCallback((components: ModelComponent[]): Record<string, CalculationResult> => {
    const results: Record<string, CalculationResult> = {};
    
    components.forEach(component => {
      calculationEngine.registerComponent(component);
      
      try {
        const result = calculationEngine.calculateComponent(component.id);
        if (result) {
          results[component.id] = result;
        }
      } catch (error) {
        console.warn(`Calculation failed for component ${component.id}:`, error);
        results[component.id] = {
          value: 0,
          formatted: '$0',
          confidence: 0.5,
          dependencies: []
        };
      }
    });
    
    return results;
  }, []);

  const getFormattedValue = useCallback((id: string) => {
    const calculation = state.calculations[id];
    if (!calculation) return '$0';
    return calculation.formatted;
  }, [state.calculations]);

  const handleAutoSave = useCallback(async () => {
    if (!state.hasUnsavedChanges || !state.model) return;

    try {
      await modelBuilderAPI.saveModel({
        model: state.model ? state.model.model : { components: [], connections: [] },
        calculations: state.calculations,
        summary: state.model ? state.model.summary : {
          totalRevenue: 0,
          totalCosts: 0,
          netValue: 0,
          netBenefit: 0,
          roi: 0,
          confidence: 0
        },
        metadata: state.model ? state.model.metadata : {
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          version: '1.0.0'
        }
      });
      
      setState(prev => ({ ...prev, hasUnsavedChanges: false }));
    } catch (error) {
      console.error('Auto-save failed:', error);
    }
  }, [state.hasUnsavedChanges, state.model, state.calculations]);

  useEffect(() => {
    const interval = setInterval(handleAutoSave, 30000); 
    return () => clearInterval(interval);
  }, [handleAutoSave]);

  const handleCalculate = useCallback(async () => {
    if (!state.model) return;

    setState(prev => ({ ...prev, isCalculating: true }));
    
    try {
      const modelData: ModelBuilderData = {
        model: state.model,
        calculations: state.calculations,
        summary: {
          totalRevenue: 0,
          totalCosts: 0,
          netValue: 0,
          netBenefit: 0,
          roi: 0,
          confidence: 0
        },
        metadata: {
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          version: '1.0.0'
        }
      };

      // Get investment amount from discovery data or use default
      const investmentAmount = discoveryData.investment_amount || 100000;
      
      await modelBuilderAPI.calculateROIWithBackend(modelData, investmentAmount);
      
      const localCalculations = performCalculations(state.model.components);
      
      setState(prev => ({
        ...prev,
        calculations: localCalculations,
        isCalculating: false,
        hasUnsavedChanges: true
      }));

      setAlert({
        type: 'success',
        message: 'Model calculations completed successfully'
      });
    } catch (error) {
      console.error('Calculation error:', error);
      
      try {
        const localCalculations = performCalculations(state.model.components);
        setState(prev => ({
          ...prev,
          calculations: localCalculations,
          isCalculating: false,
          hasUnsavedChanges: true
        }));
        
        setAlert({
          type: 'warning',
          message: 'Using local calculations (backend unavailable)'
        });
      } catch (localError) {
        setState(prev => ({ ...prev, isCalculating: false }));
        setAlert({
          type: 'error',
          message: `Calculation failed: ${localError instanceof Error ? localError.message : 'Unknown error'}`
        });
      }
    }
  }, [state.model, state.calculations, performCalculations, discoveryData]);

  const handleGenerateScenarios = useCallback(async () => {
    if (!state.model) return;

    setState(prev => ({ ...prev, isGenerating: true }));

    try {
      // Get AI suggestions for scenario generation
      const modelData: ModelBuilderData = {
        model: state.model,
        calculations: state.calculations,
        summary: {
          totalRevenue: 0,
          totalCosts: 0,
          netValue: 0,
          netBenefit: 0,
          roi: 0,
          confidence: 0
        },
        metadata: {
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          version: '1.0.0'
        }
      };

      const aiResponse = await modelBuilderAPI.getAIAssistance({
        model_data: modelData,
        user_query: 'Generate different scenarios for this model',
        context: {
          discovery_data: discoveryData,
          current_focus: 'scenario_generation'
        }
      });

      setState(prev => ({
        ...prev,
        aiSuggestions: aiResponse,
        isGenerating: false,
        hasUnsavedChanges: true
      }));

      setAlert({
        type: 'success',
        message: 'Scenarios generated successfully'
      });
    } catch (error) {
      setState(prev => ({ ...prev, isGenerating: false }));
      setAlert({
        type: 'error',
        message: `Scenario generation failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      });
    }
  }, [state.model, state.calculations, discoveryData]);

  const handleExport = useCallback(async () => {
    if (!state.model) {
      setAlert({
        type: 'error',
        message: 'No model to export'
      });
      return;
    }

    setState(prev => ({ ...prev, isExporting: true }));

    try {
      const modelData: ModelBuilderData = {
        model: state.model,
        calculations: state.calculations,
        summary: {
          totalRevenue: 0,
          totalCosts: 0,
          netValue: 0,
          netBenefit: 0,
          roi: 0,
          confidence: 0
        },
        metadata: {
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          version: '1.0.0'
        }
      };

      await modelBuilderAPI.exportModel(modelData, state.exportFormat);

      setAlert({
        type: 'success',
        message: `Model exported successfully as ${state.exportFormat.toUpperCase()}`
      });
    } catch (error) {
      console.error('Export failed:', error);
      setAlert({
        type: 'error',
        message: `Export failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      });
    } finally {
      setState(prev => ({ ...prev, isExporting: false }));
    }
  }, [state.model, state.calculations, state.exportFormat]);

  const handleImport = useCallback(async (file: File) => {
    try {
      const importedData = await modelBuilderAPI.importModel(file);
      setState(prev => ({
        ...prev,
        model: importedData.model,
        calculations: importedData.calculations,
        hasUnsavedChanges: true
      }));

      setAlert({
        type: 'success',
        message: 'Model imported successfully'
      });
    } catch (error) {
      console.error('Import failed:', error);
      setAlert({
        type: 'error',
        message: `Import failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      });
    }
  }, []);

  const handleGetAIAssistance = useCallback(async () => {
    if (!state.model) return;

    setState(prev => ({ ...prev, showAIAssistant: true }));

    try {
      const modelData: ModelBuilderData = {
        model: state.model ? state.model.model : { components: [], connections: [] },
        calculations: state.calculations,
        metadata: state.model ? state.model.metadata : {
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          version: '1.0.0'
        },
        summary: state.model ? state.model.summary : {
          totalRevenue: 0,
          totalCosts: 0,
          netValue: Object.values(state.calculations).reduce((sum, calc) => sum + calc.value, 0),
          netBenefit: 0,
          roi: 0,
          confidence: 0.8
        }
      };

      const aiResponse = await modelBuilderAPI.getAIAssistance({
        model_data: modelData,
        user_query: 'Please analyze this model and provide optimization suggestions',
        context: {
          discovery_data: discoveryData,
          current_focus: 'optimization'
        }
      });

      setState(prev => ({
        ...prev,
        aiSuggestions: aiResponse,
        showAIAssistant: false
      }));

      setAlert({
        type: 'success',
        message: 'AI assistance completed successfully'
      });

    } catch (error) {
      console.error('AI assistance error:', error);
      setState(prev => ({ ...prev, showAIAssistant: false }));
      setAlert({
        type: 'error',
        message: 'Failed to get AI assistance'
      });
    }
  }, [state.model, state.calculations, discoveryData]);

  const handleAddComponent = useCallback((type: string) => {
    const newComponent: ModelComponent = {
      id: `component-${Date.now()}`,
      type,
      properties: {
        label: `New ${type}`,
        value: 0
      },
      position: { x: 100, y: 100 }
    };

    setState(prev => {
      if (prev.model) {
        return {
          ...prev,
          model: {
      model: prev.model
        ? {
            ...prev.model,
            model: {
              ...prev.model.model,
              components: model.components
            }
          }
        : prev.model,
      hasUnsavedChanges: true
    }));
  }, []);

  const handleModelCanvasUpdate = useCallback((model: { components: ModelComponent[] }) => {
    setState(prev => ({
      ...prev,
      model:
        model.components.length > 0 && prev.model
          ? {
              ...prev.model,
              model: {
                ...prev.model.model,
                components: model.components
              }
            }
          : null,
      hasUnsavedChanges: true
    }));
  }, []);

  const handleSelectComponent = useCallback((componentId: string | null) => {
    setState(prev => ({
      ...prev,
      selectedComponent: componentId
    }));
  }, []);

  const handleContinue = useCallback(() => {
    if (!state.model) return;

    const modelBuilderData: ModelBuilderData = {
      ...state.model,
      calculations: state.calculations
    };

    onNext({
      ...discoveryData,
      modelBuilderData,
      localCalculations: state.calculations,
      validationResults: state.validationResult || undefined
    });
  }, [state.model, state.calculations, state.validationResult, discoveryData, onNext]);

  const fileInputRef = useRef<HTMLInputElement>(null);

  return (
    <DndProvider backend={HTML5Backend}>
      <div className={styles.container}>
        {alert && (
          <div
            role={alert.type === 'error' ? 'alert' : 'status'}
            aria-live={alert.type === 'error' ? 'assertive' : 'polite'}
          >
            <Alert
              className={`${styles.alert} ${styles[alert.type]}`}
              variant={alert.type === 'error' ? 'destructive' : 'default'}
            >
              <AlertDescription>{alert.message}</AlertDescription>
            </Alert>
          </div>
        )}

        {/* Loading spinner overlay for async actions */}
        {(state.isCalculating || state.isGenerating || state.isExporting || state.showAIAssistant) && (
          <div className={styles.loadingOverlay} role="status" aria-live="polite">
            <div className={styles.spinner} aria-label="Loading" />
          </div>
        )}
        <div className={styles.header}>
          {/* Type-safe metrics display */}
          <div className={styles.metrics}>
            {state.model?.model.components.length ?? 0} components • 
            {Object.keys(state.calculations ?? {}).length} calculations
          </div>
          <div>
            <h2 className={styles.title}>Visual Model Builder</h2>
            <p className={styles.description}>
              Create your financial model with drag-and-drop components
            </p>
          </div>
          
          <div className={styles.actions}>
            {state.hasUnsavedChanges && (
              <Badge variant="outline" className={styles.badge}>
                Unsaved Changes
              </Badge>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={handleGetAIAssistance}
              disabled={state.showAIAssistant}
              aria-busy={state.showAIAssistant}
            >
              {state.showAIAssistant ? (
                <Brain className={styles.icon} />
              ) : (
                <Sparkles className={styles.icon} />
              )}
              {state.showAIAssistant ? 'Loading...' : 'AI Assist'}
            </Button>
          </div>
        </div>

        {discoveryData && (
          <Alert>
            <Sparkles className={styles.icon} />
            <AlertDescription>
              Using discovery data: Investment ${discoveryData.investment_amount?.toLocaleString()} 
              with {discoveryData.metrics?.length || 0} identified metrics. 
              Components will be pre-populated with smart defaults.
            </AlertDescription>
          </Alert>
        )}

        <div className={styles.interface}>
          <div className={styles.library}>
            <Tabs defaultValue="library">
              <TabsList className={styles.tabs}>
                <TabsTrigger value="library">
                  <FileInput className={styles.icon} />
                  Library
                </TabsTrigger>
                <TabsTrigger value="properties">
                  <Settings className={styles.icon} />
                  Properties
                </TabsTrigger>
              </TabsList>
              
              <TabsContent value="library" className={styles.content}>
                <ComponentLibrary onAddComponent={handleAddComponent} />
              </TabsContent>
              
              <TabsContent value="properties" className={styles.content}>
                <PropertiesPanel
                  model={state.model ? { components: state.model.model.components } : null}
                  setModel={handlePropertiesPanelUpdate}
                  selectedComponent={state.selectedComponent}
                  calculations={state.calculations}
                  getFormattedValue={getFormattedValue}
                />
              </TabsContent>
            </Tabs>
          </div>

          <div className={styles.canvas}>
            <Card className={styles.card}>
              <CardHeader className={styles.cardHeader}>
                <div className={styles.cardTitle}>
                  <Cpu className={styles.icon} />
                  Financial Model Canvas
                </div>
                <div className={styles.cardActions}>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={handleCalculate} 
                    disabled={state.isCalculating}
                    aria-busy={state.isCalculating}
                  >
                    <Play className={styles.icon} />
                    {state.isCalculating ? 'Calculating...' : 'Calculate'}
                  </Button>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={handleExport} 
                    disabled={state.isExporting}
                    aria-busy={state.isExporting}
                  >
                    <Download className={styles.icon} />
                    {state.isExporting ? 'Exporting...' : ''}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={state.isExporting}
                  >
                    <label htmlFor="model-import-file" className="cursor-pointer flex items-center">
                      <Upload className="h-4 w-4 mr-2" />
                      Import Model
                    </label>
                    <input
                      id="model-import-file"
                      type="file"
                      accept=".json"
                      onChange={(e) => e.target.files?.[0] && handleImport(e.target.files[0])}
                      className="hidden"
                      aria-label="Import financial model file"
                      ref={fileInputRef}
                      disabled={state.isExporting}
                    />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className={styles.cardContent}>
                <ModelCanvas
                  model={state.model ? { components: state.model.model.components, connections: state.model.model.connections } : null}
                  setModel={handleModelCanvasUpdate}
                  selectedComponent={state.selectedComponent}
                  setSelectedComponent={handleSelectComponent}
                  calculations={state.calculations}
                  getFormattedValue={getFormattedValue}
                />
              </CardContent>
            </Card>
          </div>

          <div className={styles.calculations}>
            <CalculationPanel
              model={state.model ? { components: state.model.model.components } : null}
              calculations={state.calculations}
              isCalculating={state.isCalculating}
              isGenerating={state.isGenerating}
              generateScenarios={handleGenerateScenarios}
              getFormattedValue={getFormattedValue}
              recalculate={handleCalculate}
            />
          </div>
        </div>

        <div className={styles.navigation}>
          <Button variant="outline" onClick={onBack}>
            <TrendingUp className={styles.icon} />
            Back to Discovery
          </Button>
          
          <div className={styles.actions}>
            <div className={styles.metrics}>
              {state.model?.components.length || 0} components • 
              {Object.keys(state.calculations).length} calculations
            </div>
            <Button 
              onClick={handleContinue}
              disabled={!state.model || state.model.components.length === 0}
            >
              Continue to Narrative
              <Zap className={styles.icon} />
            </Button>
          </div>
        </div>
      </div>
    </DndProvider>
  );
};

export default Step2_ModelBuilder;
