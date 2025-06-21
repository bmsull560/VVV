import { useState, useEffect } from 'react';
import { DollarSign, TrendingUp, Calculator, AlertCircle, BarChart3, Target } from 'lucide-react';
import { b2bValueAPI, QuantificationRequest, QuantificationResponse, Tier3Metric, DiscoveryResponse } from '../../services/b2bValueApi';

interface MetricInput {
  name: string;
  value: number;
  unit: string;
  description: string;
}

interface Step2QuantificationData {
  investmentAmount: number;
  metrics: MetricInput[];
  quantificationResults: QuantificationResponse;
}

interface Step2QuantificationProps {
  onNext: (data: Step2QuantificationData) => void;
  onBack: () => void;
  discoveryData: DiscoveryResponse | null;
}

const Step2_Quantification = ({ onNext, onBack, discoveryData }: Step2QuantificationProps) => {
  const [investmentAmount, setInvestmentAmount] = useState<number>(0);
  const [metricInputs, setMetricInputs] = useState<MetricInput[]>([]);
  const [quantificationResults, setQuantificationResults] = useState<QuantificationResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showSensitivityAnalysis, setShowSensitivityAnalysis] = useState(false);
  const [errors, setErrors] = useState<{ [key: string]: string }>({});

  // Initialize metric inputs from discovery data
  useEffect(() => {
    if (discoveryData?.suggested_metrics) {
      const initialMetrics = discoveryData.suggested_metrics.map((metric: Tier3Metric) => ({
        name: metric.name,
        value: metric.suggested_value || 0,
        unit: metric.unit,
        description: metric.description
      }));
      setMetricInputs(initialMetrics);
    }
  }, [discoveryData]);

  // Validate inputs
  const validateInputs = (): boolean => {
    const newErrors: { [key: string]: string } = {};
    
    if (investmentAmount <= 0) {
      newErrors.investment = 'Investment amount must be greater than 0';
    }
    
    metricInputs.forEach((metric, index) => {
      if (metric.value < 0) {
        newErrors[`metric_${index}`] = `${metric.name} cannot be negative`;
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Calculate ROI using backend API
  const calculateROI = async () => {
    if (!validateInputs()) {
      return;
    }

    setIsLoading(true);
    try {
      const metrics: { [key: string]: number } = {};
      metricInputs.forEach(metric => {
        metrics[metric.name] = metric.value;
      });

      const quantificationRequest: QuantificationRequest = {
        investment_amount: investmentAmount,
        metrics,
        time_horizon_years: 3,
        sensitivity_variations: [
          { metric_name: metricInputs[0]?.name || 'productivity_gain', percentage_change: -10 },
          { metric_name: metricInputs[0]?.name || 'productivity_gain', percentage_change: 10 },
          { metric_name: metricInputs[1]?.name || 'cost_reduction', percentage_change: -20 },
          { metric_name: metricInputs[1]?.name || 'cost_reduction', percentage_change: 20 }
        ]
      };

      const response = await b2bValueAPI.quantifyROI(quantificationRequest);
      setQuantificationResults(response);
      setShowSensitivityAnalysis(true);
    } catch (error) {
      console.error('ROI calculation failed:', error);
      setErrors({ api: 'Failed to calculate ROI. Please try again.' });
    } finally {
      setIsLoading(false);
    }
  };

  // Update metric value
  const updateMetricValue = (index: number, value: number) => {
    const updated = [...metricInputs];
    updated[index].value = value;
    setMetricInputs(updated);
    
    // Clear error for this metric
    const newErrors = { ...errors };
    delete newErrors[`metric_${index}`];
    setErrors(newErrors);
  };

  // Format currency
  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  // Format percentage
  const formatPercentage = (value: number): string => {
    return `${(value * 100).toFixed(1)}%`;
  };

  const handleNext = () => {
    if (quantificationResults) {
      onNext({
        investmentAmount,
        metrics: metricInputs,
        quantificationResults
      });
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-800 mb-2">Phase 2: ROI Quantification</h2>
        <p className="text-gray-600">Input your investment amount and refine metric values to calculate comprehensive ROI projections.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Column: Input Section */}
        <div className="space-y-6">
          {/* Investment Amount */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center mb-4">
              <DollarSign className="w-6 h-6 text-green-600 mr-3" />
              <h3 className="text-xl font-semibold text-gray-800">Investment Amount</h3>
            </div>
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">
                Total Investment ($)
                <span className="text-xs text-gray-500 ml-2">Include all costs: software, implementation, training</span>
              </label>
              <input
                type="number"
                value={investmentAmount}
                onChange={(e) => setInvestmentAmount(Number(e.target.value))}
                className={`w-full px-4 py-3 border rounded-lg text-lg font-semibold ${
                  errors.investment ? 'border-red-500' : 'border-gray-300'
                } focus:ring-2 focus:ring-blue-500 focus:border-transparent`}
                placeholder="250000"
                min="0"
              />
              {errors.investment && (
                <p className="text-red-500 text-sm flex items-center">
                  <AlertCircle className="w-4 h-4 mr-1" />
                  {errors.investment}
                </p>
              )}
            </div>
          </div>

          {/* Metric Values */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center mb-4">
              <Target className="w-6 h-6 text-blue-600 mr-3" />
              <h3 className="text-xl font-semibold text-gray-800">Value Metrics</h3>
            </div>
            <div className="space-y-4">
              {metricInputs.map((metric, index) => (
                <div key={index} className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    {metric.name}
                    <span className="text-xs text-gray-500 ml-2">({metric.unit})</span>
                  </label>
                  <p className="text-xs text-gray-500 mb-2">{metric.description}</p>
                  <input
                    type="number"
                    value={metric.value}
                    onChange={(e) => updateMetricValue(index, Number(e.target.value))}
                    className={`w-full px-3 py-2 border rounded-md ${
                      errors[`metric_${index}`] ? 'border-red-500' : 'border-gray-300'
                    } focus:ring-2 focus:ring-blue-500 focus:border-transparent`}
                    min="0"
                    step="0.01"
                  />
                  {errors[`metric_${index}`] && (
                    <p className="text-red-500 text-sm flex items-center">
                      <AlertCircle className="w-4 h-4 mr-1" />
                      {errors[`metric_${index}`]}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Calculate Button */}
          <button
            onClick={calculateROI}
            disabled={isLoading}
            className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-400 flex items-center justify-center"
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                Calculating ROI...
              </>
            ) : (
              <>
                <Calculator className="w-5 h-5 mr-2" />
                Calculate ROI & Projections
              </>
            )}
          </button>

          {errors.api && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-700 flex items-center">
                <AlertCircle className="w-5 h-5 mr-2" />
                {errors.api}
              </p>
            </div>
          )}
        </div>

        {/* Right Column: Results Section */}
        <div className="space-y-6">
          {quantificationResults && (
            <>
              {/* ROI Summary Cards */}
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center mb-4">
                  <TrendingUp className="w-6 h-6 text-green-600 mr-3" />
                  <h3 className="text-xl font-semibold text-gray-800">ROI Summary</h3>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="bg-green-50 rounded-lg p-4 text-center">
                    <p className="text-sm text-green-700 font-medium">Total Annual Value</p>
                    <p className="text-2xl font-bold text-green-800">
                      {formatCurrency(quantificationResults.roi_summary.total_annual_value)}
                    </p>
                  </div>
                  <div className="bg-blue-50 rounded-lg p-4 text-center">
                    <p className="text-sm text-blue-700 font-medium">ROI Percentage</p>
                    <p className="text-2xl font-bold text-blue-800">
                      {formatPercentage(quantificationResults.roi_summary.roi_percentage)}
                    </p>
                  </div>
                  <div className="bg-purple-50 rounded-lg p-4 text-center">
                    <p className="text-sm text-purple-700 font-medium">Payback Period</p>
                    <p className="text-2xl font-bold text-purple-800">
                      {quantificationResults.roi_summary.payback_period_months} months
                    </p>
                  </div>
                </div>
                <div className="mt-4 bg-gray-50 rounded-lg p-4">
                  <p className="text-sm text-gray-700">
                    <span className="font-medium">Confidence Score:</span> 
                    <span className="ml-2 font-bold text-gray-800">
                      {Math.round(quantificationResults.roi_summary.confidence_score * 100)}%
                    </span>
                  </p>
                </div>
              </div>

              {/* Financial Projections */}
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center mb-4">
                  <BarChart3 className="w-6 h-6 text-indigo-600 mr-3" />
                  <h3 className="text-xl font-semibold text-gray-800">3-Year Financial Projections</h3>
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                    <span className="font-medium text-gray-700">Year 1 Benefit:</span>
                    <span className="font-bold text-gray-800">
                      {formatCurrency(quantificationResults.financial_projections.year_1_benefit)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                    <span className="font-medium text-gray-700">Year 2 Benefit:</span>
                    <span className="font-bold text-gray-800">
                      {formatCurrency(quantificationResults.financial_projections.year_2_benefit)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                    <span className="font-medium text-gray-700">Year 3 Benefit:</span>
                    <span className="font-bold text-gray-800">
                      {formatCurrency(quantificationResults.financial_projections.year_3_benefit)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg border border-green-200">
                    <span className="font-medium text-green-700">Total NPV:</span>
                    <span className="font-bold text-green-800">
                      {formatCurrency(quantificationResults.financial_projections.total_npv)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg border border-blue-200">
                    <span className="font-medium text-blue-700">IRR:</span>
                    <span className="font-bold text-blue-800">
                      {formatPercentage(quantificationResults.financial_projections.irr_percentage)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Sensitivity Analysis */}
              {showSensitivityAnalysis && quantificationResults.sensitivity_analysis.length > 0 && (
                <div className="bg-white rounded-lg shadow-md p-6">
                  <h3 className="text-xl font-semibold text-gray-800 mb-4">Sensitivity Analysis</h3>
                  <div className="space-y-3">
                    {quantificationResults.sensitivity_analysis.map((scenario, index) => (
                      <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                        <div>
                          <span className="font-medium text-gray-700">{scenario.scenario_name}</span>
                          <span className={`ml-2 px-2 py-1 rounded-full text-xs font-medium ${
                            scenario.risk_level === 'low' ? 'bg-green-100 text-green-800' :
                            scenario.risk_level === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                            scenario.risk_level === 'high' ? 'bg-orange-100 text-orange-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {scenario.risk_level} risk
                          </span>
                        </div>
                        <div className="text-right">
                          <div className="font-bold text-gray-800">
                            {formatPercentage(scenario.resulting_roi_percentage)}
                          </div>
                          <div className="text-sm text-gray-600">
                            {formatCurrency(scenario.resulting_total_annual_value)}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Navigation */}
      <div className="flex justify-between mt-8 pt-6 border-t border-gray-200">
        <button
          onClick={onBack}
          className="px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
        >
          Back to Discovery
        </button>
        <button
          onClick={handleNext}
          disabled={!quantificationResults}
          className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          Continue to Narrative Generation
        </button>
      </div>
    </div>
  );
};

export default Step2_Quantification;
