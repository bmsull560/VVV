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
  Zap,
  Cpu,
  ArrowLeft,

} from 'lucide-react';
import PropertiesPanel from './model-builder/PropertiesPanel';
import ModelCanvas from './model-builder/ModelCanvas';
import CalculationPanel from './model-builder/CalculationPanel';
import ComponentLibrary from './model-builder/ComponentLibrary';
import { ModelComponent, CalculationResult, calculationEngine } from '../utils/calculationEngine';
import { modelBuilderAPI, ModelValidationResult, AIAssistantResponse, ConnectionData, DiscoveryData } from '../services/modelBuilderApi';
import { ModelData } from '../api/types';
import styles from './Step2_ModelBuilder.module.css';

interface Step2ModelBuilderProps {
  discoveryData: DiscoveryData;
  onNext: (data: DiscoveryData & { modelData: ModelData; quantificationResults?: unknown; localCalculations?: Record<string, CalculationResult>; validationResults?: ModelValidationResult; }) => void;
  modelData?: ModelData;
  quantificationResults?: unknown;
  localCalculations?: Record<string, CalculationResult>;
  validationResults?: ModelValidationResult;
  onBack: () => void;
}

interface ModelBuilderState {
  model: ModelData | null;
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
  alert: { type: 'success' | 'warning' | 'error'; message: string } | null;
}

const Step2_ModelBuilder: React.FC<Step2ModelBuilderProps> = ({
  discoveryData,
  onNext,
  onBack,
  modelData: initialModelData,
  localCalculations: initialLocalCalculations,
  validationResults: initialValidationResults
}) => {
  const [state, setState] = useState<ModelBuilderState>({
    model: initialModelData || null,
    selectedComponent: null,
    calculations: initialLocalCalculations || {},
    isCalculating: false,
    isGenerating: false,
    hasUnsavedChanges: false,
    showAIAssistant: false,
    validationResult: initialValidationResults || null,
    exportFormat: 'json',
    isExporting: false,
    aiSuggestions: null,
    collaborationMode: false,
    alert: null,
  });

  const setAlert = useCallback((type: 'success' | 'warning' | 'error', message: string) => {
    setState(prev => ({ ...prev, alert: { type, message } }));
    setTimeout(() => setState(prev => ({ ...prev, alert: null })), 5000);
  }, []);

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
        ...state.model,
      });
      setState(prev => ({ ...prev, hasUnsavedChanges: false }));
      setAlert('success', 'Model saved automatically!');
    } catch (error) {
      console.error('Auto-save failed:', error);
      setAlert('error', 'Auto-save failed. Please check your connection.');
    }
  }, [state.hasUnsavedChanges, state.model, state.calculations, setAlert]);

  useEffect(() => {
    const interval = setInterval(handleAutoSave, 30000);
    return () => clearInterval(interval);
  }, [handleAutoSave]);

  const handleCalculate = useCallback(async () => {
    if (!state.model) {
      setAlert('warning', 'No model to calculate. Please add components.');
      return;
    }
    setState(prev => ({ ...prev, isCalculating: true }));
    try {
      const response = await modelBuilderAPI.calculateModel(
        state.model,
      );
      const newCalculations = performCalculations(response.components);

      setState(prev => ({
        ...prev,
        calculations: newCalculations,
        model: response,
        validationResult: response.validationResult || null,
        isCalculating: false,
        hasUnsavedChanges: true
      }));
      setAlert('success', 'Model calculated successfully!');
    } catch (error) {
      console.error('Calculation failed:', error);
      setAlert('error', 'Calculation failed. Please check the model components.');
      setState(prev => ({ ...prev, isCalculating: false }));
    }
  }, [state.model, state.calculations, performCalculations, setAlert]);

  const handleExport = useCallback(async () => {
    if (!state.model) {
      setAlert('warning', 'No model to export.');
      return;
    }
    setState(prev => ({ ...prev, isExporting: true }));
    try {
      const data = await modelBuilderAPI.exportModel(state.model.id!, state.exportFormat);
      const blob = new Blob([data], { type: 'application/json' }); // Adjust type based on format
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `model.${state.exportFormat}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      setAlert('success', `Model exported as ${state.exportFormat}!`);
    } catch (error) {
      console.error('Export failed:', error);
      setAlert('error', 'Export failed. Please try again.');
    } finally {
      setState(prev => ({ ...prev, isExporting: false }));
    }
  }, [state.model, state.exportFormat, setAlert]);

  const handleImport = useCallback(async (file: File) => {
    try {
      const reader = new FileReader();
      reader.onload = async (e) => {
        try {
          const content = e.target?.result as string;
          const importedModel: ModelData = JSON.parse(content);
          const response = await modelBuilderAPI.importModel(importedModel);
          setState(prev => ({
            ...prev,
            model: response,
            calculations: performCalculations(response.components),
            validationResult: response.validationResult || null,
            hasUnsavedChanges: true,
            selectedComponent: null
          }));
          setAlert('success', 'Model imported successfully!');
        } catch (parseError) {
          console.error('Error parsing imported file:', parseError);
          setAlert('error', 'Invalid file format. Please import a valid model file.');
        }
      };
      reader.readAsText(file);
    } catch (error) {
      console.error('Import failed:', error);
      setAlert('error', 'Import failed. Please try again.');
    }
  }, [performCalculations, setAlert]);

  const handleAddComponent = useCallback((component: ModelComponent) => {
    setState(prev => {
      const newModel = prev.model ? { ...prev.model } : { components: [], connections: [], name: '', description: '', metadata: { created_at: new Date().toISOString(), updated_at: new Date().toISOString(), version: '1.0.0' } };
      newModel.components = [...newModel.components, component];
      return {
        ...prev,
        model: newModel,
        hasUnsavedChanges: true,
        selectedComponent: component.id
      };
    });
  }, []);

  const handleGenerateScenarios = useCallback(async () => {
    if (!state.model) {
      setAlert('warning', 'No model to generate scenarios for.');
      return;
    }
    setState(prev => ({ ...prev, isGenerating: true }));
    try {
      const response = await modelBuilderAPI.generateScenarios(state.model.id!);
      setState(prev => ({
        ...prev,
        model: response, // Assuming response contains updated model with scenarios
        isGenerating: false,
        hasUnsavedChanges: true
      }));
      setAlert('success', 'Scenarios generated successfully!');
    } catch (error) {
      console.error('Scenario generation failed:', error);
      setAlert('error', 'Scenario generation failed. Please try again.');
    } finally {
      setState(prev => ({ ...prev, isGenerating: false }));
    }
  }, [state.model, setAlert]);

  const handleGetAIAssistance = useCallback(async () => {
    if (!state.model) {
      setAlert('warning', 'No model to get AI assistance for.');
      return;
    }
    setState(prev => ({ ...prev, showAIAssistant: true }));
    try {
      const response = await modelBuilderAPI.getAIAssistance(state.model.id!);
      setState(prev => ({ ...prev, aiSuggestions: response }));
      setAlert('success', 'AI assistance received!');
    } catch (error) {
      console.error('AI assistance failed:', error);
      setAlert('error', 'Failed to get AI assistance. Please try again.');
    }
  }, [state.model, setAlert]);

  const handleContinue = useCallback(() => {
    if (!state.model) {
      setAlert('error', 'Cannot continue: Model is empty.');
      return;
    }
    
    const modelData: ModelData = {
      ...state.model,
    };
    
    onNext({
      ...discoveryData,
      modelData,
      localCalculations: state.calculations,
      validationResults: state.validationResult || undefined
    });
  }, [state.model, state.calculations, state.validationResult, discoveryData, onNext, setAlert]);

  return (
    <DndProvider backend={HTML5Backend}>
      <div className={styles.container}>
        <Card className={styles.card}>
          <CardHeader className={styles.header}>
            <div className={styles.headerLeft}>
              <Badge variant="secondary" className={styles.badge}>
                <Brain className={styles.icon} />
                Step 2: Model Builder
              </Badge>
              <h2 className={styles.title}>Build Your Financial Model</h2>
            </div>
            <div className={styles.headerRight}>
              <Button variant="outline" onClick={onBack} aria-label="Go back">
                <ArrowLeft className={styles.icon} /> Back
              </Button>
              <Button variant="default" onClick={handleContinue} disabled={!state.model} aria-label="Continue to Next Step">
                <Play className={styles.icon} /> Continue 
              </Button>
            </div>
          </CardHeader>
          <CardContent className={styles.cardContent}>
            <div className={styles.toolbar}>
              <Button variant="default" onClick={handleCalculate} disabled={state.isCalculating} aria-label="Calculate Model">
                <Zap className={styles.icon} />
                {state.isCalculating ? 'Calculating...' : 'Calculate'}
              </Button>
              <Button variant="outline" onClick={handleExport} disabled={state.isExporting} aria-label="Export Model">
                <Download className={styles.icon} /> Export
              </Button>
              <label htmlFor="import-model" className={styles.visuallyHidden}>
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
              <Button variant="outline" onClick={() => document.getElementById('import-model')?.click()} aria-label="Import Model">
                <Upload className={styles.icon} /> Import
              </Button>
              <Button variant="outline" onClick={handleGenerateScenarios} disabled={state.isGenerating} aria-label="Generate Scenarios">
                <Sparkles className={styles.icon} />
                {state.isGenerating ? 'Generating...' : 'Scenarios'}
              </Button>
              <Button variant="outline" onClick={handleGetAIAssistance} aria-label="AI Assistance">
                <Cpu className={styles.icon} /> AI Assistant
              </Button>
            </div>

            {state.alert && (
              <Alert className={styles.alert} variant={state.alert.type === 'error' ? 'destructive' : 'default'}>
                <AlertDescription>{state.alert.message}</AlertDescription>
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
                    model={state.model || { components: [], connections: [], name: '', description: '', metadata: { created_at: new Date().toISOString(), updated_at: new Date().toISOString(), version: '1.0.0' } }}
                    selectedComponent={state.selectedComponent}
                    onSelectComponent={(id: string) => setState(prev => ({ ...prev, selectedComponent: id }))}
                    onModelChange={(modelData: {components: ModelComponent[]; connections: ConnectionData[]}) => {
                      if (!state.model) return;
                      setState(prev => ({
                        ...prev, 
                        model: { 
                          ...prev.model!,
                          components: modelData.components,
                          connections: modelData.connections
                        },
                        hasUnsavedChanges: true 
                      }));
                    }}
                    onAddComponent={handleAddComponent}
                    calculations={state.calculations}
                    readOnly={false}
                    className={styles.canvas}
                  />
                </TabsContent>
                <TabsContent value="properties">
                  <PropertiesPanel
                    selectedComponent={state.selectedComponent}
                    model={state.model || { components: [], connections: [], name: '', description: '', metadata: { created_at: new Date().toISOString(), updated_at: new Date().toISOString(), version: '1.0.0' } }}
                    onUpdateComponent={(id: string, props: Record<string, unknown>) => {
                      if (!state.model) return;
                      setState(prev => ({
                        ...prev,
                        model: {
                          ...prev.model!,
                          components: prev.model!.components.map((c: ModelComponent) =>
                            c.id === id ? { ...c, properties: { ...c.properties, ...props } } : c
                          )
                        },
                        hasUnsavedChanges: true
                      }));
                    }}
                  />
                </TabsContent>
                <TabsContent value="calculations">
                  <CalculationPanel
                    calculations={state.calculations}
                    getFormattedValue={getFormattedValue}
                    isCalculating={state.isCalculating}
                  />
                </TabsContent>
                <TabsContent value="library">
                  <ComponentLibrary
                    onAddComponent={handleAddComponent}
                  />
                </TabsContent>
              </Tabs>
            </div>
          </CardContent>
        </Card>
      </div>
    </DndProvider>
  );
};

export default Step2_ModelBuilder;