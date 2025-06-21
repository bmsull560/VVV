import React, { useEffect, useState } from 'react';

import { Users, DollarSign, Zap } from 'lucide-react';

const ValueDriverCard = ({ driver }) => (
  <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
    <div className="flex items-center mb-2">
      <Zap className="w-5 h-5 text-yellow-500 mr-3" />
      <h4 className="font-semibold text-md text-gray-800">{driver.pillar}</h4>
    </div>
    <ul className="list-disc list-inside pl-2 text-sm text-gray-600">
      {driver.keywords.map((keyword, index) => (
        <li key={index}>{keyword}</li>
      ))}
    </ul>
  </div>
);

const PersonaCard = ({ persona }) => (
  <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
    <div className="flex items-center mb-2">
      <Users className="w-5 h-5 text-blue-500 mr-3" />
      <h4 className="font-semibold text-md text-gray-800">{persona.type}</h4>
    </div>
    <p className="text-sm text-gray-600">Keywords found: {persona.keywords.join(', ')}</p>
  </div>
);

export default function AnalysisResults({ results }) {
  if (!results) {
    return <p>No results to display.</p>;
  }

  const { personas = [], value_drivers = [] } = results;

  return (
    <div className="bg-white rounded-lg shadow-lg p-8 w-full max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Analysis Results</h2>
      
      <div className="mb-8">
        <h3 className="text-xl font-semibold text-gray-700 mb-4 flex items-center">
          <Users className="w-6 h-6 mr-3 text-blue-600" />
          Identified Personas
        </h3>
        {personas.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {personas.map((persona, index) => (
              <PersonaCard key={index} persona={persona} />
            ))}
          </div>
        ) : (
          <p className="text-gray-500">No buyer personas were identified.</p>
        )}
      </div>

      <div>
        <h3 className="text-xl font-semibold text-gray-700 mb-4 flex items-center">
          <DollarSign className="w-6 h-6 mr-3 text-green-600" />
          Value Drivers
        </h3>
        {value_drivers.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {value_drivers.map((driver, index) => (
              <ValueDriverCard key={index} driver={driver} />
            ))}
          </div>
        ) : (
          <p className="text-gray-500">No value drivers were identified.</p>
        )}
      </div>
    </div>
  );
}
