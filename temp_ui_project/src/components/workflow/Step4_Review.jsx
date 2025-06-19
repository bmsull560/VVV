import React from 'react';

const Step4_Review = ({ formData, setCurrentStep }) => {
    const { 
        projectName, 
        clientName, 
        industry, 
        keyStakeholderPersona, 
        valueDrivers = [], 
        dataInputs = {} 
    } = formData;

    return (
        <div>
            <h2 className="text-xl font-semibold mb-6">Step 4: Review Your Business Case</h2>

            {/* Section 1: Basic Information */}
            <div className="mb-6 p-4 border rounded shadow-sm bg-white">
                <div className="flex justify-between items-center mb-3">
                    <h3 className="text-lg font-medium text-gray-800">Basic Information</h3>
                    <button 
                        onClick={() => setCurrentStep(1)} 
                        className="text-sm text-blue-600 hover:underline"
                    >
                        Edit
                    </button>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-2">
                    <p><strong>Project Name:</strong> {projectName || 'N/A'}</p>
                    <p><strong>Client Name:</strong> {clientName || 'N/A'}</p>
                    <p><strong>Industry:</strong> {industry || 'N/A'}</p>
                    <p><strong>Key Stakeholder:</strong> {keyStakeholderPersona || 'N/A'}</p>
                </div>
            </div>

            {/* Section 2: Value Drivers */}
            <div className="mb-6 p-4 border rounded shadow-sm bg-white">
                <div className="flex justify-between items-center mb-3">
                    <h3 className="text-lg font-medium text-gray-800">Value Drivers</h3>
                    <button 
                        onClick={() => setCurrentStep(2)} 
                        className="text-sm text-blue-600 hover:underline"
                    >
                        Edit
                    </button>
                </div>
                {valueDrivers.length > 0 ? (
                    <ul className="list-disc pl-5 space-y-1">
                        {valueDrivers.map(driver => (
                            <li key={driver.id}>
                                {driver.name} 
                                <span className={`text-xs ml-2 px-2 py-0.5 rounded-full ${driver.type === 'benefit' ? 'bg-green-200 text-green-800' : 'bg-orange-200 text-orange-800'}`}>
                                    {driver.type === 'benefit' ? 'Benefit' : 'Cost Saving'}
                                </span>
                            </li>
                        ))}
                    </ul>
                ) : (
                    <p className="text-gray-500">No value drivers defined.</p>
                )}
            </div>

            {/* Section 3: Data Inputs */}
            <div className="mb-6 p-4 border rounded shadow-sm bg-white">
                <div className="flex justify-between items-center mb-3">
                    <h3 className="text-lg font-medium text-gray-800">Data Inputs</h3>
                    <button 
                        onClick={() => setCurrentStep(3)} 
                        className="text-sm text-blue-600 hover:underline"
                    >
                        Edit
                    </button>
                </div>
                {valueDrivers.length > 0 ? (
                    valueDrivers.map(driver => (
                        <div key={`data-${driver.id}`} className="mb-3 pb-2 border-b last:border-b-0">
                            <h4 className="font-semibold text-gray-700">{driver.name}</h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-1 text-sm">
                                <p><strong>Baseline:</strong> {dataInputs[driver.id]?.baseline || 'N/A'}</p>
                                <p><strong>Target:</strong> {dataInputs[driver.id]?.target || 'N/A'}</p>
                                <p className="md:col-span-2"><strong>Assumptions:</strong> {dataInputs[driver.id]?.assumptions || 'N/A'}</p>
                            </div>
                        </div>
                    ))
                ) : (
                    <p className="text-gray-500">No data entered as no value drivers were defined.</p>
                )}
            </div>

            <p className="text-sm text-gray-600 mt-6">
                Please review all the information above. If everything is correct, you can proceed to generate the analysis.
                You can use the "Edit" buttons to go back to a specific step and make changes.
            </p>
        </div>
    );
};

export default Step4_Review;
