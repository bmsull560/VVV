import React, { useState } from 'react';

const Step2_ValueDrivers = ({ formData, setFormData }) => {
    const [newDriver, setNewDriver] = useState('');
    const [driverType, setDriverType] = useState('benefit'); // 'benefit' or 'cost_saving'
    const [suggestedDrivers, setSuggestedDrivers] = useState([
        "Increase Sales Revenue",
        "Reduce Operational Costs",
        "Improve Customer Retention",
        "Enhance Employee Productivity",
        "Expand Market Share"
    ]);

    const handleAddDriver = () => {
        if (newDriver.trim() === '') return;
        const driverToAdd = {
            id: Date.now().toString(), // Simple unique ID
            name: newDriver,
            type: driverType,
            // Potentially add more fields like description, impact_scale, etc. later
        };
        setFormData(prevData => ({
            ...prevData,
            valueDrivers: [...(prevData.valueDrivers || []), driverToAdd]
        }));
        setNewDriver('');
    };

    const handleSelectSuggestedDriver = (suggestedName) => {
        // For now, assume suggested drivers are benefits. This can be made more complex.
        const driverToAdd = {
            id: Date.now().toString(),
            name: suggestedName,
            type: 'benefit', 
        };
        setFormData(prevData => ({
            ...prevData,
            valueDrivers: [...(prevData.valueDrivers || []), driverToAdd]
        }));
        // Optionally remove from suggestions
        setSuggestedDrivers(prev => prev.filter(d => d !== suggestedName));
    };

    const handleRemoveDriver = (driverId) => {
        setFormData(prevData => ({
            ...prevData,
            valueDrivers: prevData.valueDrivers.filter(driver => driver.id !== driverId)
        }));
    };

    return (
        <div>
            <h2 className="text-xl font-semibold mb-4">Step 2: Define Value Drivers</h2>
            
            <div className="mb-6 p-4 border rounded bg-gray-50">
                <h3 className="text-lg font-medium mb-2">Add New Value Driver</h3>
                <div className="mb-3">
                    <label className="block text-gray-700 text-sm font-bold mb-1" htmlFor="newDriverName">
                        Driver Name
                    </label>
                    <input
                        className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                        id="newDriverName"
                        type="text"
                        placeholder="e.g., Reduce customer churn by X%"
                        value={newDriver}
                        onChange={(e) => setNewDriver(e.target.value)}
                    />
                </div>
                <div className="mb-3">
                    <label className="block text-gray-700 text-sm font-bold mb-1" htmlFor="driverType">
                        Driver Type
                    </label>
                    <select 
                        id="driverType"
                        className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                        value={driverType}
                        onChange={(e) => setDriverType(e.target.value)}
                    >
                        <option value="benefit">Benefit (e.g., Increased Revenue)</option>
                        <option value="cost_saving">Cost Saving (e.g., Reduced Expenses)</option>
                    </select>
                </div>
                <button
                    onClick={handleAddDriver}
                    className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
                >
                    Add Driver
                </button>
            </div>

            {suggestedDrivers.length > 0 && (
                <div className="mb-6 p-4 border rounded bg-sky-50">
                    <h3 className="text-lg font-medium mb-2">Suggested Value Drivers (AI Agent Placeholder)</h3>
                    <ul className="space-y-2">
                        {suggestedDrivers.map(driverName => (
                            <li key={driverName} className="flex justify-between items-center">
                                <span>{driverName}</span>
                                <button 
                                    onClick={() => handleSelectSuggestedDriver(driverName)}
                                    className="text-sm bg-blue-500 hover:bg-blue-600 text-white py-1 px-2 rounded"
                                >
                                    Select
                                </button>
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            <div className="mb-4">
                <h3 className="text-lg font-medium mb-2">Selected Value Drivers</h3>
                {(formData.valueDrivers && formData.valueDrivers.length > 0) ? (
                    <ul className="space-y-2">
                        {formData.valueDrivers.map(driver => (
                            <li key={driver.id} className="p-2 border rounded shadow-sm flex justify-between items-center">
                                <div>
                                    <span className="font-semibold">{driver.name}</span>
                                    <span className={`text-xs ml-2 px-2 py-0.5 rounded-full ${driver.type === 'benefit' ? 'bg-green-200 text-green-800' : 'bg-orange-200 text-orange-800'}`}>
                                        {driver.type === 'benefit' ? 'Benefit' : 'Cost Saving'}
                                    </span>
                                </div>
                                <button
                                    onClick={() => handleRemoveDriver(driver.id)}
                                    className="text-red-500 hover:text-red-700 font-semibold"
                                >
                                    Remove
                                </button>
                            </li>
                        ))}
                    </ul>
                ) : (
                    <p className="text-gray-500">No value drivers added yet.</p>
                )}
            </div>
        </div>
    );
};

export default Step2_ValueDrivers;
