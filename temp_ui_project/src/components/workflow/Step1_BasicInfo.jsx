import React, { useState, useEffect } from 'react';
import { Search, Lightbulb, Users, TrendingUp, AlertCircle, CheckCircle2 } from 'lucide-react';
import { b2bValueAPI, DiscoveryResponse, ValueDriverPillar, Persona } from '../../services/b2bValueApi';

interface Step1Props {
  formData: any;
  setFormData: (data: any) => void;
  handleNext: () => void;
  handleBack: () => void;
}

const Step1_BasicInfo: React.FC<Step1Props> = ({ formData, setFormData, handleNext, handleBack }) => {
  const [userQuery, setUserQuery] = useState(formData.userQuery || '');
  const [discoveryResults, setDiscoveryResults] = useState<DiscoveryResponse | null>(formData.discoveryResults || null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedDrivers, setSelectedDrivers] = useState<string[]>(formData.selectedDrivers || []);
  const [selectedPersonas, setSelectedPersonas] = useState<string[]>(formData.selectedPersonas || []);

  // Example queries to guide users
  const exampleQueries = [
    "Implement AI chatbot to reduce customer service costs by 30%",
    "Deploy data analytics platform to increase sales conversion rates",
    "Automate invoice processing to eliminate manual data entry",
    "Modernize legacy systems to improve operational efficiency"
  ];

  const handleDiscoverValue = async () => {
    if (!userQuery.trim()) {
      setError('Please enter a description of your business challenge or investment idea');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const results = await b2bValueAPI.discoverValue(userQuery);
      setDiscoveryResults(results);
      
      // Update form data with discovery results
      setFormData({
        ...formData,
        userQuery,
        discoveryResults: results,
        selectedDrivers: [],
        selectedPersonas: []
      });
    } catch (err) {
      setError('Failed to discover value drivers. Please try again.');
      console.error('Discovery error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleDriverSelection = (pillar: string) => {
    const updated = selectedDrivers.includes(pillar)
      ? selectedDrivers.filter(d => d !== pillar)
      : [...selectedDrivers, pillar];
    
    setSelectedDrivers(updated);
    setFormData({
      ...formData,
      selectedDrivers: updated
    });
  };

  const togglePersonaSelection = (personaName: string) => {
    const updated = selectedPersonas.includes(personaName)
      ? selectedPersonas.filter(p => p !== personaName)
      : [...selectedPersonas, personaName];
    
    setSelectedPersonas(updated);
    setFormData({
      ...formData,
      selectedPersonas: updated
    });
  };

  const canProceed = discoveryResults && selectedDrivers.length > 0 && selectedPersonas.length > 0;

  const handleNextStep = () => {
    if (canProceed) {
      handleNext();
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-800 mb-4">
          <Search className="inline mr-3 text-blue-600" />
          Discovery Phase: Define Your Business Challenge
        </h2>
        <p className="text-lg text-gray-600">
          Describe your business challenge or investment idea, and our AI will suggest relevant value drivers and stakeholder personas.
        </p>
      </div>

      {/* Query Input Section */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h3 className="text-xl font-semibold mb-4 flex items-center">
          <Lightbulb className="mr-2 text-yellow-500" />
          Describe Your Business Challenge
        </h3>
        
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            What business challenge are you trying to solve or investment are you considering?
          </label>
          <textarea
            value={userQuery}
            onChange={(e) => setUserQuery(e.target.value)}
            placeholder="Example: We want to implement an AI-powered customer service chatbot to reduce response times and operational costs while improving customer satisfaction..."
            className="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows={4}
          />
        </div>

        {/* Example Queries */}
        <div className="mb-4">
          <p className="text-sm font-medium text-gray-700 mb-2">Example queries:</p>
          <div className="space-y-2">
            {exampleQueries.map((example, index) => (
              <button
                key={index}
                onClick={() => setUserQuery(example)}
                className="block w-full text-left p-3 bg-gray-50 hover:bg-blue-50 rounded-lg text-sm transition-colors"
              >
                "{example}"
              </button>
            ))}
          </div>
        </div>

        <button
          onClick={handleDiscoverValue}
          disabled={isLoading || !userQuery.trim()}
          className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center"
        >
          {isLoading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Discovering Value Drivers...
            </>
          ) : (
            <>
              <Search className="mr-2" size={16} />
              Discover Value Drivers
            </>
          )}
        </button>

        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center text-red-700">
            <AlertCircle className="mr-2" size={16} />
            {error}
          </div>
        )}
      </div>

      {/* Discovery Results */}
      {discoveryResults && (
        <div className="space-y-6">
          {/* Value Drivers Section */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-semibold mb-4 flex items-center">
              <TrendingUp className="mr-2 text-green-500" />
              Suggested Value Drivers
            </h3>
            <p className="text-gray-600 mb-4">
              Select the value drivers that are most relevant to your business case:
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {discoveryResults.value_drivers.map((driver: ValueDriverPillar) => (
                <div
                  key={driver.pillar}
                  className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                    selectedDrivers.includes(driver.pillar)
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => toggleDriverSelection(driver.pillar)}
                >
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-lg">{driver.pillar}</h4>
                    {selectedDrivers.includes(driver.pillar) && (
                      <CheckCircle2 className="text-blue-500" size={20} />
                    )}
                  </div>
                  <div className="text-sm text-gray-600">
                    <p className="mb-2">Key areas:</p>
                    <ul className="list-disc list-inside space-y-1">
                      {driver.tier_2_drivers.slice(0, 3).map((subDriver, index) => (
                        <li key={index}>{subDriver}</li>
                      ))}
                    </ul>
                    {driver.tier_2_drivers.length > 3 && (
                      <p className="text-xs text-gray-500 mt-1">
                        +{driver.tier_2_drivers.length - 3} more areas
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Personas Section */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-semibold mb-4 flex items-center">
              <Users className="mr-2 text-purple-500" />
              Key Stakeholder Personas
            </h3>
            <p className="text-gray-600 mb-4">
              Select the stakeholder personas who will be most interested in this business case:
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {discoveryResults.personas.map((persona: Persona) => (
                <div
                  key={persona.name}
                  className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                    selectedPersonas.includes(persona.name)
                      ? 'border-purple-500 bg-purple-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => togglePersonaSelection(persona.name)}
                >
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-lg">{persona.name}</h4>
                    {selectedPersonas.includes(persona.name) && (
                      <CheckCircle2 className="text-purple-500" size={20} />
                    )}
                  </div>
                  <p className="text-sm text-gray-600 mb-2">{persona.description}</p>
                  <div className="text-xs text-gray-500">
                    <p className="font-medium">Key priorities:</p>
                    <ul className="list-disc list-inside">
                      {persona.priorities.slice(0, 2).map((priority, index) => (
                        <li key={index}>{priority}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Project Insights */}
          {discoveryResults.project_insights && (
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-6">
              <h3 className="text-xl font-semibold mb-4">AI-Generated Project Insights</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <h4 className="font-medium text-gray-800 mb-2">Industry Context</h4>
                  <p className="text-sm text-gray-600">{discoveryResults.project_insights.industry_context}</p>
                </div>
                <div>
                  <h4 className="font-medium text-gray-800 mb-2">Complexity Assessment</h4>
                  <p className="text-sm text-gray-600">{discoveryResults.project_insights.complexity_assessment}</p>
                </div>
                <div>
                  <h4 className="font-medium text-gray-800 mb-2">Recommended Approach</h4>
                  <p className="text-sm text-gray-600">{discoveryResults.project_insights.recommended_approach}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Navigation */}
      <div className="flex justify-between mt-8">
        <button
          onClick={handleBack}
          className="px-6 py-3 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
          disabled
        >
          Back
        </button>
        
        <button
          onClick={handleNextStep}
          disabled={!canProceed}
          className={`px-6 py-3 rounded-lg flex items-center ${
            canProceed
              ? 'bg-green-600 text-white hover:bg-green-700'
              : 'bg-gray-300 text-gray-500 cursor-not-allowed'
          }`}
        >
          Continue to Quantification
          <TrendingUp className="ml-2" size={16} />
        </button>
      </div>

      {/* Progress Indicator */}
      <div className="mt-6 text-center text-sm text-gray-500">
        Step 1 of 4: Discovery Phase
        {canProceed && (
          <span className="text-green-600 ml-2">
            ✓ Ready to proceed
          </span>
        )}
      </div>
    </div>
  );
};

export default Step1_BasicInfo;
