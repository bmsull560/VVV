import React, { useState } from 'react';
import Step1_BasicInfo from './Step1_BasicInfo.tsx';
import Step2_ModelBuilder from '../Step2_ModelBuilder.tsx';
// Import other steps here as they are created
import Step3_NarrativeGeneration from './Step3_NarrativeGeneration.tsx';
import Step4_Composition from './Step4_Composition.tsx';

const BusinessCaseWizard = () => {
    const [currentStep, setCurrentStep] = useState(1);
    const [wizardData, setWizardData] = useState({
        discoveryData: null,
        quantificationData: null,
        narrativeData: null,
        userFeedback: null,
        compositionData: null
    });

    const handleStep1Complete = (discoveryData) => {
        setWizardData(prev => ({ ...prev, discoveryData }));
        setCurrentStep(2);
    };

    const handleStep2Complete = (quantificationData) => {
        setWizardData(prev => ({ ...prev, quantificationData }));
        setCurrentStep(3);
    };

    const handleStep3Complete = (narrativeData, userFeedback) => {
        setWizardData(prev => ({ ...prev, narrativeData, userFeedback }));
        setCurrentStep(4);
    };

    const handleStep4Complete = (compositionData) => {
        setWizardData(prev => ({ ...prev, compositionData }));
        // Navigate to final results or completion
        console.log('Business Case Complete:', { ...wizardData, compositionData });
    };

    const handleStepNavigation = (targetStep) => {
        setCurrentStep(targetStep);
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
                return (
                    <Step2_ModelBuilder 
                        onNext={handleStep2Complete}
                        onNavigate={handleStepNavigation}
                        discoveryData={wizardData.discoveryData}
                    />
                );
            case 3:
                return (
                    <Step3_NarrativeGeneration 
                        discoveryData={wizardData.discoveryData}
                        quantificationData={wizardData.quantificationData}
                        onNavigate={handleStepNavigation}
                        onNarrativeComplete={handleStep3Complete}
                    />
                );
            case 4:
                return (wizardData.discoveryData && wizardData.quantificationData && wizardData.narrativeData) ? (
                    <Step4_Composition
                        discoveryData={wizardData.discoveryData}
                        quantificationData={wizardData.quantificationData}
                        narrativeData={wizardData.narrativeData}
                        userFeedback={wizardData.userFeedback}
                        onNavigate={handleStepNavigation}
                        onCompositionComplete={handleStep4Complete}
                    />
                ) : (
                    <div className="text-center py-8">
                        <p className="text-gray-600">Previous step data not available. Please complete earlier steps first.</p>
                        <button 
                            onClick={() => setCurrentStep(Math.max(1, currentStep - 1))}
                            className="mt-4 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                        >
                            Go Back
                        </button>
                    </div>
                );
            default:
                return (
                    <Step1_BasicInfo 
                        onNext={handleStep1Complete}
                    />
                );
        }
    };

    const getStepTitle = () => {
        switch (currentStep) {
            case 1: return "Discovery Phase";
            case 2: return "ROI Quantification";
            case 3: return "Narrative Generation";
            case 4: return "Business Case Composition";
            default: return "Business Case Creation";
        }
    };

    return (
        <div className="min-h-screen bg-gray-50">
            <div className="container mx-auto py-8">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-gray-800 mb-2">AI-Powered Business Case Generator</h1>
                    <p className="text-gray-600">Create comprehensive, data-driven business cases in minutes</p>
                </div>
                
                {/* Progress Bar */}
                <div className="mb-8">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-gray-700">Progress: {getStepTitle()}</span>
                        <span className="text-sm text-gray-500">Step {currentStep} of 4</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${(currentStep / 4) * 100}%` }}
                        ></div>
                    </div>
                </div>

                {/* Step Content */}
                <div className="bg-white shadow-sm rounded-lg">
                    {renderStep()}
                </div>
            </div>
        </div>
    );
};

export default BusinessCaseWizard;
