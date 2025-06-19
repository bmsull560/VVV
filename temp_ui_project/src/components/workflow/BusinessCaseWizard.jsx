import React, { useState } from 'react';
import Step1_BasicInfo from './Step1_BasicInfo';
// Import other steps here as they are created
import Step2_ValueDrivers from './Step2_ValueDrivers';
import Step3_DataInput from './Step3_DataInput';
import Step4_Review from './Step4_Review';
// import AnalysisResults from '../AnalysisResults'; // Assuming this will be used for the final step

const BusinessCaseWizard = () => {
    const [currentStep, setCurrentStep] = useState(1);
    const [formData, setFormData] = useState({
        // Basic Info
        projectName: '',
        clientName: '',
        industry: '',
        keyStakeholderPersona: '',
        // Value Drivers
        valueDrivers: [],
        // Data Inputs (will be more complex)
        dataInputs: {},
        // ... other data fields
    });

    const handleChange = (input) => (e) => {
        setFormData({ ...formData, [input]: e.target.value });
    };

    const handleNext = () => {
        // Add validation logic here before proceeding
        setCurrentStep((prev) => prev + 1);
    };

    const handleBack = () => {
        setCurrentStep((prev) => prev - 1);
    };

    const handleSubmit = () => {
        // Process and submit final data
        console.log('Final Form Data:', formData);
        // Navigate to results or final step
        // setCurrentStep(SOME_FINAL_STEP_NUMBER_OR_ID);
    };

    const renderStep = () => {
        switch (currentStep) {
            case 1:
                return <Step1_BasicInfo formData={formData} handleChange={handleChange} />;
            case 2:
                return <Step2_ValueDrivers formData={formData} setFormData={setFormData} />;
            case 3:
                return <Step3_DataInput formData={formData} setFormData={setFormData} />;
            case 4:
                return <Step4_Review formData={formData} setCurrentStep={setCurrentStep} />;
            // case 5: // Example: Assuming step 5 is results
            //     return <AnalysisResults data={formData} />; // Adjust as needed
            default:
                return <Step1_BasicInfo formData={formData} handleChange={handleChange} />;
        }
    };

    return (
        <div className="container mx-auto p-4">
            <h1 className="text-2xl font-bold mb-6">New Business Case Creation</h1>
            
            {/* Progress Bar (Optional) */}
            {/* You can add a progress bar here to show current step */}

            <div className="bg-white shadow-md rounded px-8 pt-6 pb-8 mb-4">
                {renderStep()}
            </div>

            <div className="flex items-center justify-between mt-6">
                {currentStep > 1 && currentStep < 5 && ( // Adjust step count as needed
                    <button
                        onClick={handleBack}
                        className="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
                    >
                        Back
                    </button>
                )}
                {currentStep < 4 && ( // Adjust step count for when "Next" is shown
                    <button
                        onClick={handleNext}
                        className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
                    >
                        Next
                    </button>
                )}
                {currentStep === 4 && ( // Adjust step count for when "Submit" is shown
                    <button
                        onClick={handleSubmit}
                        className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
                    >
                        Generate Analysis (or Submit)
                    </button>
                )}
            </div>
        </div>
    );
};

export default BusinessCaseWizard;
