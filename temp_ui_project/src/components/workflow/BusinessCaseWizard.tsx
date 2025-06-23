import { useState } from 'react';
import type { FC } from 'react';
import { ChevronLeft, ChevronRight, Check } from 'lucide-react';
import Step1_BasicInfo from './Step1_BasicInfo';
import Step2_ModelBuilder from '../Step2_ModelBuilder';
import Step3_NarrativeGeneration from './Step3_NarrativeGeneration';
import Step4_Composition from './Step4_Composition';
import { 
  DiscoveryResponse,
  QuantificationResponse,
  NarrativeResponse,
  ComposedBusinessCase,
  DiscoveryData
} from '../../services/b2bValueApi';
import { CalculationResult } from '../../utils/calculationEngine';
import { ModelValidationResult } from '../../services/modelBuilderApi';
import { adaptDiscoveryResponseToData } from '../../utils/typeAdapters';
import styles from './BusinessCaseWizard.module.css';

// Re-export TemplateContext from Step1_BasicInfo
import type { IndustryTemplate } from '../../types/industryTemplates';
import type { ModelBuilderData } from '../../services/modelBuilderApi';

export interface TemplateContext {
  industry: string;
  commonValueDrivers: string[];
  keyMetrics: string[];
  template?: IndustryTemplate;
}

export interface WizardData {
  discoveryData: DiscoveryResponse | null;
  templateContext: TemplateContext | null;
  quantificationData: QuantificationResponse | null;
  narrativeData: NarrativeResponse | null;
  userFeedback: { approved: boolean; comments?: string } | null;
  compositionData: ComposedBusinessCase | null;
}

type WizardStep = 1 | 2 | 3 | 4;

interface Step {
  id: WizardStep;
  name: string;
  description: string;
}

const STEPS: Step[] = [
  { id: 1, name: 'Discovery', description: 'Identify value drivers' },
  { id: 2, name: 'Model', description: 'Build financial model' },
  { id: 3, name: 'Narrative', description: 'Craft your story' },
  { id: 4, name: 'Composition', description: 'Finalize and export' },
];

const BusinessCaseWizard: FC = () => {
  const [currentStep, setCurrentStep] = useState<WizardStep>(1);
  const [wizardData, setWizardData] = useState<WizardData>({
    discoveryData: null,
    templateContext: null,
    quantificationData: null,
    narrativeData: null,
    userFeedback: null,
    compositionData: null,
  });

  const handleStep1Complete = (data: { 
    discoveryData: DiscoveryResponse; 
    templateContext?: TemplateContext 
  }) => {
    if (!data.templateContext) {
      console.error('Template context is required');
      return;
    }
    setWizardData(prev => ({
      ...prev,
      discoveryData: data.discoveryData,
      templateContext: data.templateContext,
    }));
    setCurrentStep(2);
  };

  const handleStep2Complete = (data: DiscoveryData & {
    modelBuilderData: ModelBuilderData;
    quantificationResults?: QuantificationResponse;
    localCalculations?: Record<string, CalculationResult>;
    validationResults?: ModelValidationResult;
  }) => {
    setWizardData(prev => ({
      ...prev,
      quantificationData: data.quantificationResults || null,
    }));
    setCurrentStep(3);
  };

  const handleStep4Complete = (compositionData: ComposedBusinessCase) => {
    setWizardData(prev => ({
      ...prev,
      compositionData,
      templateContext: prev.templateContext || null,
    }));
    console.log('Business Case Complete:', { ...wizardData, compositionData });
  };

  const handleStepNavigation = (step: number) => {
    if (step >= 1 && step <= 4) {
      setCurrentStep(step as WizardStep);
    }
  };

  const isStepComplete = (step: WizardStep): boolean => {
    switch (step) {
      case 1: return !!(wizardData.discoveryData && wizardData.templateContext);
      case 2: return !!wizardData.quantificationData;
      case 3: return !!(wizardData.narrativeData && wizardData.userFeedback);
      case 4: return !!wizardData.compositionData;
      default: return false;
    }
  };

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <Step1_BasicInfo
            onNext={handleStep1Complete}
          />
        );
      case 2:
        if (!wizardData.discoveryData || !wizardData.templateContext) {
          return <div>Error: Missing required data for this step</div>;
        }
        try {
          const discoveryData = adaptDiscoveryResponseToData(wizardData.discoveryData);
          return (
            <Step2_ModelBuilder
              onNext={handleStep2Complete}
              discoveryData={discoveryData}
              onBack={() => handleStepNavigation(1)}
            />
          );
        } catch (error) {
          console.error('Error adapting discovery data:', error);
          return <div>Error: Failed to prepare data for model builder</div>;
        }
      case 3:
        if (!wizardData.discoveryData || !wizardData.quantificationData) {
          return <div>Error: Missing required data for this step</div>;
        }
        return (
          <Step3_NarrativeGeneration
            discoveryData={wizardData.discoveryData}
            quantificationData={wizardData.quantificationData}
            onNavigate={(step) => handleStepNavigation(step)}
            onNarrativeComplete={(narrativeData, userFeedback) => {
              setWizardData(prev => ({
                ...prev,
                narrativeData,
                userFeedback: userFeedback || null
              }));
              setCurrentStep(4);
            }}
          />
        );
      case 4:
        if (!wizardData.discoveryData || !wizardData.quantificationData || !wizardData.narrativeData) {
          return <div>Error: Missing required data for this step</div>;
        }
        return (
          <Step4_Composition
            discoveryData={wizardData.discoveryData}
            quantificationData={wizardData.quantificationData}
            narrativeData={wizardData.narrativeData}
            userFeedback={wizardData.userFeedback || { approved: false, comments: '' }}
            onNavigate={(step) => handleStepNavigation(step)}
            onCompositionComplete={(compositionData) => {
              setWizardData(prev => ({
                ...prev,
                compositionData
              }));
              handleStep4Complete(compositionData);
            }}
          />
        );
      default:
        return <div>Invalid step</div>;
    }
  };

  // Calculate progress percentage based on current step
  const progress = ((currentStep - 1) / (STEPS.length - 1)) * 100;

  return (
    <div className={styles.wizardContainer}>
      {/* Sidebar */}
      <aside className={styles.sidebar}>
        <div className={styles.sidebarHeader}>
          <h1 className={styles.sidebarTitle}>Business Case Builder</h1>
          <p className={styles.sidebarDescription}>
            Complete all steps to finalize your business case
          </p>
        </div>
        
        <nav aria-label="Progress">
          <ol className={styles.stepsList}>
            {STEPS.map((step) => {
              const isActive = step.id === currentStep;
              const isComplete = isStepComplete(step.id);
              const stepClass = [
                styles.stepItem,
                isActive ? styles.stepItemActive : '',
                isComplete ? styles.stepItemCompleted : ''
              ].filter(Boolean).join(' ');

              return (
                <li key={step.id} className={stepClass}>
                  <button
                    type="button"
                    onClick={() => handleStepNavigation(step.id)}
                    className="flex items-center w-full text-left"
                    disabled={!isComplete && step.id > currentStep}
                  >
                    <span className={styles.stepNumber}>
                      {isComplete ? <Check size={16} /> : step.id}
                    </span>
                    <div>
                      <div className="font-medium">{step.name}</div>
                      <div className="text-sm opacity-75">{step.description}</div>
                    </div>
                  </button>
                </li>
              );
            })}
          </ol>
        </nav>
      </aside>

      {/* Main Content */}
      <main className={styles.stepContent}>
        {/* Progress Bar */}
        <div className={styles.progressContainer}>
          <div className={styles.progressBar}>
            <div 
              className={styles.progressIndicator} 
              style={{ width: `${progress}%` }}
              aria-valuenow={progress}
              aria-valuemin={0}
              aria-valuemax={100}
              role="progressbar"
            />
          </div>
          <div className={styles.progressText}>
            Step {currentStep} of {STEPS.length}: {STEPS[currentStep - 1]?.name}
          </div>
        </div>
        
        {/* Current Step Content */}
        <div className={styles.stepPanel}>
          {renderStep()}
        </div>
        
        {/* Navigation */}
        <div className={styles.navigation}>
          <button
            type="button"
            onClick={() => handleStepNavigation((currentStep - 1) as WizardStep)}
            disabled={currentStep === 1}
            className={`${styles.button} ${styles.buttonSecondary}`}
            aria-label="Previous step"
          >
            <ChevronLeft className={styles.buttonIcon} />
            Previous
          </button>
          
          <div className={styles.stepInfo}>
            {STEPS[currentStep - 1]?.description}
          </div>
          
          <button
            type="button"
            onClick={() => handleStepNavigation((currentStep + 1) as WizardStep)}
            disabled={currentStep === STEPS.length}
            className={`${styles.button} ${styles.buttonPrimary}`}
            aria-label={currentStep === STEPS.length ? 'Complete' : 'Next step'}
          >
            {currentStep === STEPS.length ? 'Complete' : 'Next'}
            <ChevronRight className={styles.buttonIcon} />
          </button>
        </div>
      </main>
    </div>
  );
};

export default BusinessCaseWizard;
