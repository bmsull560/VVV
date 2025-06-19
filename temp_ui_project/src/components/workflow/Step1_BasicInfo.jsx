import React from 'react';

const Step1_BasicInfo = ({ formData, handleChange }) => {
    const industries = ["Technology", "Healthcare", "Finance", "Manufacturing", "Retail", "Other"];
    const personas = ["Executive (CEO, CFO)", "IT Manager", "Sales Lead", "Operations Manager", "Other"];

    return (
        <div>
            <h2 className="text-xl font-semibold mb-4">Step 1: Basic Information</h2>
            <div className="mb-4">
                <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="projectName">
                    Project Name
                </label>
                <input
                    className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                    id="projectName"
                    type="text"
                    placeholder="Enter project name"
                    value={formData.projectName || ''}
                    onChange={handleChange('projectName')}
                />
            </div>
            <div className="mb-4">
                <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="clientName">
                    Client Name (Optional)
                </label>
                <input
                    className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                    id="clientName"
                    type="text"
                    placeholder="Enter client name"
                    value={formData.clientName || ''}
                    onChange={handleChange('clientName')}
                />
            </div>
            <div className="mb-4">
                <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="industry">
                    Industry
                </label>
                <select
                    className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                    id="industry"
                    value={formData.industry || ''}
                    onChange={handleChange('industry')}
                >
                    <option value="" disabled>Select industry</option>
                    {industries.map(industry => (
                        <option key={industry} value={industry}>{industry}</option>
                    ))}
                </select>
            </div>
            <div className="mb-4">
                <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="keyStakeholderPersona">
                    Key Stakeholder Persona
                </label>
                <select
                    className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                    id="keyStakeholderPersona"
                    value={formData.keyStakeholderPersona || ''}
                    onChange={handleChange('keyStakeholderPersona')}
                >
                    <option value="" disabled>Select key stakeholder persona</option>
                    {personas.map(persona => (
                        <option key={persona} value={persona}>{persona}</option>
                    ))}
                </select>
            </div>
        </div>
    );
};

export default Step1_BasicInfo;
