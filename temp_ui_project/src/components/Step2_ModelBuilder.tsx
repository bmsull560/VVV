import React, { useState, useCallback, useEffect } from 'react';
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
  // All hooks and logic must be declared here, before the return statement}

  return (
    <DndProvider backend={HTML5Backend}>
      <div className={styles.container}>
        <Card className={styles.headerCard}>
          <CardHeader>
            <div className={styles.headerTitle}>
              <Brain className={styles.icon} />
              <span>Step 2: Model Builder</span>
              {state.collaborationMode && <Badge color="blue">Collaboration</Badge>}
            </div>
            <div className={styles.headerActions}>
              <Button variant="secondary" onClick={onBack} aria-label="Back to Discovery">
                <Play className={styles.icon} /> Back
              </Button>
              <Button variant="primary" onClick={handleCalculate} disabled={state.isCalculating} aria-label="Calculate Model">
                <Zap className={styles.icon} />
                {state.isCalculating ? 'Calculating...' : 'Calculate'}
              </Button>
              <Button variant="outline" onClick={handleExport} disabled={state.isExporting} aria-label="Export Model">
                <Download className={styles.icon} /> Export
              </Button>
              <Button variant="outline" asChild>
                <label htmlFor="import-model" aria-label="Import Model">
                  <Upload className={styles.icon} /> Import
                  <input
                    id="import-model"
                    type="file"
                    accept=".json,.csv,.xlsx,.xls,.pdf"
                    style={{ display: 'none' }}
                    onChange={e => {
                      if (e.target.files && e.target.files[0]) handleImport(e.target.files[0]);
                    }}
                  />
                </label>
              </Button>
              <Button variant="outline" onClick={handleGenerateScenarios} disabled={state.isGenerating} aria-label="Generate Scenarios">
                <Sparkles className={styles.icon} />
                {state.isGenerating ? 'Generating...' : 'Scenarios'}
              </Button>
              <Button variant="outline" onClick={handleGetAIAssistance} aria-label="AI Assistance">
                <Cpu className={styles.icon} /> AI Assistant
              </Button>
            </div>
          </CardHeader>
        </Card>

        {alert && (
          <Alert className={styles.alert} variant={alert.type}>
            <AlertDescription>{alert.message}</AlertDescription>
          </Alert>
        )}

        <div className={styles.mainContent}>
          <Tabs defaultValue="canvas" className={styles.tabs}>
            <TabsList>
              <TabsTrigger value="canvas">Model Canvas</TabsTrigger>
              <TabsTrigger value="properties">Properties</TabsTrigger>
              <TabsTrigger value="calculations">Calculations</TabsTrigger>
              <TabsTrigger value="library">Library</TabsTrigger>
            </TabsList>
            <TabsContent value="canvas">
              <ModelCanvas
                model={state.model ? state.model.model : { components: [], connections: [] }}
                selectedComponent={state.selectedComponent}
                onSelectComponent={id => setState(prev => ({ ...prev, selectedComponent: id }))}
                onModelChange={modelData => setState(prev => ({ ...prev, model: { ...prev.model!, model: modelData } as ModelBuilderData, hasUnsavedChanges: true }))}
                onAddComponent={handleAddComponent}
                calculations={state.calculations}
                readOnly={false}
                className={styles.canvas}
              />
            </TabsContent>
            <TabsContent value="properties">
              <PropertiesPanel
                componentId={state.selectedComponent}
                model={state.model ? state.model.model : { components: [], connections: [] }}
                onUpdateComponent={(id, props) => {
                  if (!state.model) return;
                  setState(prev => ({
                    ...prev,
                    model: {
                      ...prev.model!,
                      model: {
                        ...prev.model!.model,
                        components: prev.model!.model.components.map(c =>
                          c.id === id ? { ...c, properties: { ...c.properties, ...props } } : c
                        )
                      }
                    },
                    hasUnsavedChanges: true
                  }));
                }}
                className={styles.propertiesPanel}
              />
            </TabsContent>
            <TabsContent value="calculations">
              <CalculationPanel
                calculations={state.calculations}
                getFormattedValue={getFormattedValue}
                isCalculating={state.isCalculating}
                className={styles.calculationPanel}
              />
            </TabsContent>
            <TabsContent value="library">
              <ComponentLibrary
                onAddComponent={handleAddComponent}
                className={styles.library}
              />
            </TabsContent>
          </Tabs>
        </div>
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
        model: state.model ? state.model.model : { components: [], connections: [] },
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
      const investmentAmount = discoveryData.investment_amount || 100000;
      await modelBuilderAPI.calculateROIWithBackend(modelData, investmentAmount);
      const localCalculations = performCalculations(state.model.model.components);
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
        const localCalculations = performCalculations(state.model.model.components);
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
      const modelData: ModelBuilderData = {
        model: state.model ? state.model.model : { components: [], connections: [] },
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
        model: state.model ? state.model.model : { components: [], connections: [] },
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
      setState((prev: ModelBuilderState) => ({
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
    setState((prev: ModelBuilderState) => {
      if (prev.model) {
        const newComponent: ModelComponent = {
          id: `component-${Date.now()}`,
          type,
          properties: {
            label: `New ${type}`,
            value: 0
          },
          position: { x: 100, y: 100 }
        };
        return {
          ...prev,
          model: {
            ...prev.model,
            model: {
              ...prev.model.model,
              components: [...prev.model.model.components, newComponent]
            }
          },
          hasUnsavedChanges: true
        };
    const modelData: ModelBuilderData = {
      model: state.model ? state.model.model : { components: [], connections: [] },
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

// handleImport is declared only once below. Remove all duplicate declarations.

  try {
    const importedData = await modelBuilderAPI.importModel(file);
    setState((prev: ModelBuilderState) => ({
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

// handleGetAIAssistance is declared only once below. Remove all duplicate declarations.

  if (!state.model) return;

  setState(prev => ({ ...prev, showAIAssistant: true }));

  try {
    const modelData: ModelBuilderData = {
      model: state.model.model,
      calculations: state.calculations,
      metadata: state.model.metadata,
      summary: state.model.summary
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

// ...

// handleAddComponent is declared only once below. Remove all duplicate declarations.

  setState(prev => {
    if (prev.model) {
      const newComponent: ModelComponent = {
        id: `component-${Date.now()}`,
        type,
        properties: {
          label: `New ${type}`,
          value: 0
        },
        position: { x: 100, y: 100 }
      };
      return {
        ...prev,
        model: {
          ...prev.model,
          model: {
            ...prev.model.model,
            components: [...prev.model.model.components, newComponent]
          }
        },
        hasUnsavedChanges: true
      };
    }
    return prev;
  });
}, []);

// ...

const handleContinue = useCallback(() => {
  if (!state.model) return;

  const modelBuilderData: ModelBuilderData = {
    model: state.model.model,
    calculations: state.calculations,
    metadata: state.model.metadata,
    summary: state.model.summary
  };

  onNext({
    ...discoveryData,
    modelBuilderData,
    localCalculations: state.calculations,
    validationResults: state.validationResult || undefined
  });
}, [state.model, state.calculations, state.validationResult, discoveryData, onNext]);

      </div>
    </DndProvider>
  );
};
export default Step2_ModelBuilder;
