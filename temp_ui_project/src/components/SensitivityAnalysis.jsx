import React, { useState } from 'react';
import { SlidersHorizontal, TrendingUp, TrendingDown } from 'lucide-react';

const SensitivityAnalysis = () => {
  const [baseInvestment, setBaseInvestment] = useState(100000);
  const [baseGain, setBaseGain] = useState(150000);
  const [investmentVariation, setInvestmentVariation] = useState(10);
  const [gainVariation, setGainVariation] = useState(15);
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleRunAnalysis = async () => {
    setIsLoading(true);
    setError(null);
    setResults([]);

    const variations = {
      investment: [-investmentVariation / 100, 0, investmentVariation / 100],
      gain: [-gainVariation / 100, 0, gainVariation / 100],
    };

    try {
      const response = await fetch('http://localhost:5001/api/run-sensitivity-analysis', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          base_investment: parseFloat(baseInvestment),
          base_gain: parseFloat(baseGain),
          variations 
        }),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.error || 'Failed to run analysis');
      }

      const data = await response.json();
      setResults(data.scenarios || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const getRowClass = (roi) => {
    if (roi > 50) return 'bg-green-100 dark:bg-green-900/50';
    if (roi < 0) return 'bg-red-100 dark:bg-red-900/50';
    return 'bg-gray-50 dark:bg-gray-800/50';
  };

  return (
    <div className="bg-white dark:bg-gray-900 p-6 rounded-lg shadow-md w-full max-w-4xl mx-auto">
      <div className="flex items-center mb-6">
        <SlidersHorizontal className="w-8 h-8 text-blue-500 mr-3" />
        <h2 className="text-2xl font-bold text-gray-800 dark:text-white">What-if: Sensitivity Analysis</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
          <label htmlFor="baseInvestment" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Base Investment ($)</label>
          <input
            type="number"
            id="baseInvestment"
            value={baseInvestment}
            onChange={(e) => setBaseInvestment(e.target.value)}
            className="mt-1 block w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
          <label htmlFor="baseGain" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Base Gain ($)</label>
          <input
            type="number"
            id="baseGain"
            value={baseGain}
            onChange={(e) => setBaseGain(e.target.value)}
            className="mt-1 block w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
          <label htmlFor="investmentVar" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Investment Variation (%)</label>
          <input
            type="number"
            id="investmentVar"
            value={investmentVariation}
            onChange={(e) => setInvestmentVariation(e.target.value)}
            className="mt-1 block w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
          <label htmlFor="gainVar" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Gain Variation (%)</label>
          <input
            type="number"
            id="gainVar"
            value={gainVariation}
            onChange={(e) => setGainVariation(e.target.value)}
            className="mt-1 block w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      <div className="text-center mb-6">
        <button
          onClick={handleRunAnalysis}
          disabled={isLoading}
          className="px-6 py-2 bg-blue-600 text-white font-semibold rounded-lg shadow-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-75 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Running Analysis...' : 'Run Analysis'}
        </button>
      </div>

      {error && <div className="text-red-500 text-center p-4 bg-red-100 dark:bg-red-900/50 rounded-lg">Error: {error}</div>}

      {results.length > 0 && (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-100 dark:bg-gray-800">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Variable Changed</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Change</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Resulting ROI (%)</th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
              {results.map((result, index) => (
                <tr key={index} className={getRowClass(result.roi_percentage)}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white capitalize">{result.variable_changed}</td>
                  <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${result.percentage_change > 0 ? 'text-green-600' : result.percentage_change < 0 ? 'text-red-600' : 'text-gray-500'}`}>
                    <div className="flex items-center">
                      {result.percentage_change > 0 && <TrendingUp className="w-4 h-4 mr-1" />}
                      {result.percentage_change < 0 && <TrendingDown className="w-4 h-4 mr-1" />}
                      {result.percentage_change}%
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-800 dark:text-gray-200 font-bold">{result.roi_percentage}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default SensitivityAnalysis;
