import React, { useState } from 'react';

const Step3_DataInput = ({ formData, setFormData }) => {
    // Local state for managing input fields if needed, or directly update formData
    const handleInputChange = (driverId, fieldName, value) => {
        setFormData(prevData => {
            const updatedDataInputs = {
                ...prevData.dataInputs,
                [driverId]: {
                    ...(prevData.dataInputs?.[driverId] || {}),
                    [fieldName]: value,
                }
            };
            return { ...prevData, dataInputs: updatedDataInputs };
        });
    };

    return (
        <div>
            <h2 className="text-xl font-semibold mb-6">Step 3: Input Data for Value Drivers</h2>

            {(formData.valueDrivers && formData.valueDrivers.length > 0) ? (
                formData.valueDrivers.map(driver => (
                    <div key={driver.id} className="mb-6 p-4 border rounded shadow-sm bg-white">
                        <h3 className="text-lg font-medium text-blue-700 mb-3">{driver.name} 
                            <span className={`text-xs ml-2 px-2 py-0.5 rounded-full ${driver.type === 'benefit' ? 'bg-green-200 text-green-800' : 'bg-orange-200 text-orange-800'}`}>
                                {driver.type === 'benefit' ? 'Benefit' : 'Cost Saving'}
                            </span>
                        </h3>
                        
                        {/* Placeholder for manual data inputs related to this driver */}
                        {/* This section will need to be more dynamic based on driver type or user config */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label htmlFor={`baseline-${driver.id}`} className="block text-sm font-medium text-gray-700">
                                    Baseline Value
                                </label>
                                <input
                                    type="number"
                                    id={`baseline-${driver.id}`}
                                    className="mt-1 shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                                    placeholder="e.g., 100000"
                                    value={formData.dataInputs?.[driver.id]?.baseline || ''}
                                    onChange={(e) => handleInputChange(driver.id, 'baseline', e.target.value)}
                                />
                            </div>
                            <div>
                                <label htmlFor={`target-${driver.id}`} className="block text-sm font-medium text-gray-700">
                                    Target Value
                                </label>
                                <input
                                    type="number"
                                    id={`target-${driver.id}`}
                                    className="mt-1 shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                                    placeholder="e.g., 120000"
                                    value={formData.dataInputs?.[driver.id]?.target || ''}
                                    onChange={(e) => handleInputChange(driver.id, 'target', e.target.value)}
                                />
                            </div>
                            {/* Add more common fields or conditional fields here */}
                            <div className="md:col-span-2">
                                 <label htmlFor={`assumptions-${driver.id}`} className="block text-sm font-medium text-gray-700">
                                    Key Assumptions / Notes
                                </label>
                                <textarea
                                    id={`assumptions-${driver.id}`}
                                    rows="2"
                                    className="mt-1 shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                                    placeholder="Describe any assumptions or notes for this driver's data"
                                    value={formData.dataInputs?.[driver.id]?.assumptions || ''}
                                    onChange={(e) => handleInputChange(driver.id, 'assumptions', e.target.value)}
                                />
                            </div>
                        </div>
                    </div>
                ))
            ) : (
                <p className="text-gray-500">No value drivers selected in Step 2. Please go back and add value drivers.</p>
            )}

            <div className="mt-8 p-4 border rounded bg-gray-50">
                <h3 className="text-lg font-medium mb-3">Connect to Data Source (Placeholder)</h3>
                <p className="text-sm text-gray-600 mb-2">
                    Optionally, connect to an external data source to populate or validate your inputs.
                </p>
                <select className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline mb-3" disabled>
                    <option>Select Data Source Type (e.g., CRM, ERP, Database)</option>
                </select>
                <button 
                    className="bg-indigo-500 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline opacity-50 cursor-not-allowed"
                    disabled
                >
                    Connect (Feature Coming Soon)
                </button>
            </div>
        </div>
    );
};

export default Step3_DataInput;
