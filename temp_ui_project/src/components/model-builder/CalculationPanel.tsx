import React, { useState, useMemo } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Progress } from '../ui/progress';
import {
  Calculator,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Info,
  RefreshCw,
  Zap,
  BarChart3
} from 'lucide-react';
import { ModelComponent, CalculationResult } from '../../utils/calculationEngine';

interface CalculationPanelProps {
  model: { components: ModelComponent[]; connections: any[] } | null;
  calculations: Record<string, CalculationResult>;
  getFormattedValue: (id: string) => string;
  recalculate: () => void;
  isCalculating: boolean;
  isGenerating?: boolean;
  generateScenarios?: () => void;
}

const CalculationPanel: React.FC<CalculationPanelProps> = ({
  model,
  calculations,
  getFormattedValue,
  recalculate,
  isCalculating,
  isGenerating,
  generateScenarios
}) => {
  const [showDetails, setShowDetails] = useState(false);
  const [selectedTab, setSelectedTab] = useState('results');

  // Process calculations into structured results
  const getCalculationResults = (): CalculationResult[] => {
    if (!model || !calculations) return [];

    return model.components.map(component => {
      const calc = calculations[component.id] || {};
      const value = calc.result || 0;
      const formattedValue = getFormattedValue(component.id);
      
      // Determine status based on calculation validity
      let status: 'valid' | 'warning' | 'error' = 'valid';
      if (calc.error) status = 'error';
      else if (calc.warning || value === 0) status = 'warning';

      // Calculate confidence based on component type and data quality
      const confidence = calculateConfidence(component, calc);

      return {
        id: component.id,
        name: component.properties.name || component.type.replace('-', ' ').toUpperCase(),
        value,
        formattedValue,
        type: component.type,
        status,
        confidence,
        dependencies: component.connections || []
      };
    });
  };

  // Calculate confidence score for a component
  const calculateConfidence = (component: ModelComponent, calc: any): number => {
    let confidence = 100;

    // Reduce confidence for missing required properties
    const requiredProps = getRequiredProperties(component.type);
    const missingProps = requiredProps.filter(prop => !component.properties[prop]);
    confidence -= missingProps.length * 15;

    // Reduce confidence for calculation errors
    if (calc.error) confidence = Math.min(confidence, 30);
    else if (calc.warning) confidence -= 20;

    // Reduce confidence for zero values (might indicate missing data)
    if (calc.result === 0) confidence -= 10;

    // Reduce confidence for components with many dependencies
    const depCount = component.connections?.length || 0;
    if (depCount > 3) confidence -= depCount * 5;

    return Math.max(confidence, 0);
  };

  // Get required properties for component type
  const getRequiredProperties = (type: string): string[] => {
    const required: Record<string, string[]> = {
      'revenue-stream': ['unitPrice', 'quantity'],
      'cost-center': ['monthlyCost'],
      'roi-calculator': ['investment', 'annualBenefit'],
      'npv-calculator': ['discountRate', 'cashFlows'],
      'payback-calculator': ['investment', 'annualCashFlow'],
      'sensitivity-analysis': ['baseCase'],
      'variable': ['value'],
      'formula': ['formula']
    };
    return required[type] || [];
  };

  // Get summary statistics
  const getSummaryStats = () => {
    const results = getCalculationResults();
    const total = results.length;
    const valid = results.filter(r => r.status === 'valid').length;
    const warnings = results.filter(r => r.status === 'warning').length;
    const errors = results.filter(r => r.status === 'error').length;
    const avgConfidence = total > 0 
      ? results.reduce((sum, r) => sum + r.confidence, 0) / total 
      : 0;

    return { total, valid, warnings, errors, avgConfidence };
  };

  // Get financial summary
  const getFinancialSummary = () => {
    const results = getCalculationResults();
    
    const revenues = results
      .filter(r => r.type === 'revenue-stream')
      .reduce((sum, r) => sum + r.value, 0);
    
    const costs = results
      .filter(r => r.type === 'cost-center')
      .reduce((sum, r) => sum + r.value, 0);
    
    const investments = results
      .filter(r => ['roi-calculator', 'npv-calculator', 'payback-calculator'].includes(r.type))
      .reduce((sum, r) => sum + (calculations[r.id]?.investment || 0), 0);

    const netBenefit = revenues - costs;
    const roi = investments > 0 ? (netBenefit / investments) * 100 : 0;

    return { revenues, costs, investments, netBenefit, roi };
  };

  const results = getCalculationResults();
  const stats = getSummaryStats();
  const financial = getFinancialSummary();

  // Get status icon
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'valid': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'warning': return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      case 'error': return <AlertCircle className="h-4 w-4 text-red-500" />;
      default: return <Calculator className="h-4 w-4 text-gray-500" />;
    }
  };

  // Get confidence color
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return 'text-green-600';
    if (confidence >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <Card className="w-80 h-full flex flex-col">
      <CardHeader className="flex-shrink-0">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Calculator className="h-5 w-5" />
            Calculations
          </CardTitle>
          <div className="flex gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowDetails(!showDetails)}
            >
              {showDetails ? <Info className="h-4 w-4" /> : <Info className="h-4 w-4" />}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={recalculate}
              disabled={isCalculating}
            >
              <RefreshCw className={`h-4 w-4 ${isCalculating ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </div>
        
        {/* Summary Stats */}
        <div className="grid grid-cols-2 gap-2 mt-3">
          <div className="text-center p-2 bg-gray-50 rounded">
            <div className="text-lg font-bold text-green-600">{stats.valid}</div>
            <div className="text-xs text-gray-600">Valid</div>
          </div>
          <div className="text-center p-2 bg-gray-50 rounded">
            <div className="text-lg font-bold text-yellow-600">{stats.warnings}</div>
            <div className="text-xs text-gray-600">Warnings</div>
          </div>
        </div>
        
        {stats.errors > 0 && (
          <div className="text-center p-2 bg-red-50 rounded mt-2">
            <div className="text-lg font-bold text-red-600">{stats.errors}</div>
            <div className="text-xs text-red-600">Errors</div>
          </div>
        )}
      </CardHeader>

      <CardContent className="flex-1 overflow-y-auto">
        <Tabs value={selectedTab} onValueChange={setSelectedTab}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="results">Results</TabsTrigger>
            <TabsTrigger value="financial">Financial</TabsTrigger>
            <TabsTrigger value="confidence">Quality</TabsTrigger>
          </TabsList>

          <TabsContent value="results" className="space-y-3 mt-4">
            {results.length === 0 ? (
              <div className="text-center text-gray-500 py-8">
                <Calculator className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                <p>No components to calculate</p>
              </div>
            ) : (
              results.map(result => (
                <Card key={result.id} className="p-3">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(result.status)}
                      <span className="font-medium text-sm truncate">
                        {result.name}
                      </span>
                    </div>
                    <Badge variant="outline" className="text-xs">
                      {result.type}
                    </Badge>
                  </div>
                  
                  <div className="text-lg font-semibold text-gray-900">
                    {result.formattedValue}
                  </div>
                  
                  {showDetails && (
                    <div className="mt-2 pt-2 border-t space-y-1">
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-600">Confidence:</span>
                        <span className={getConfidenceColor(result.confidence)}>
                          {result.confidence.toFixed(0)}%
                        </span>
                      </div>
                      {result.dependencies.length > 0 && (
                        <div className="text-xs text-gray-600">
                          Dependencies: {result.dependencies.length}
                        </div>
                      )}
                    </div>
                  )}
                </Card>
              ))
            )}
          </TabsContent>

          <TabsContent value="financial" className="space-y-4 mt-4">
            <div className="space-y-3">
              <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-green-600" />
                  <span className="text-sm font-medium">Total Revenue</span>
                </div>
                <span className="font-semibold text-green-700">
                  ${financial.revenues.toLocaleString()}
                </span>
              </div>

              <div className="flex justify-between items-center p-3 bg-red-50 rounded-lg">
                <div className="flex items-center gap-2">
                  <BarChart3 className="h-4 w-4 text-red-600" />
                  <span className="text-sm font-medium">Total Costs</span>
                </div>
                <span className="font-semibold text-red-700">
                  ${financial.costs.toLocaleString()}
                </span>
              </div>

              <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-2">
                  <Calculator className="h-4 w-4 text-gray-600" />
                  <span className="text-sm font-medium">Investment</span>
                </div>
                <span className="font-semibold text-gray-700">
                  ${financial.investments.toLocaleString()}
                </span>
              </div>

              <div className="border-t pt-3">
                <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="h-4 w-4 text-blue-600" />
                    <span className="text-sm font-medium">Net Benefit</span>
                  </div>
                  <span className={`font-semibold ${financial.netBenefit >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                    ${financial.netBenefit.toLocaleString()}
                  </span>
                </div>

                <div className="flex justify-between items-center p-3 bg-purple-50 rounded-lg mt-2">
                  <div className="flex items-center gap-2">
                    <Zap className="h-4 w-4 text-purple-600" />
                    <span className="text-sm font-medium">ROI</span>
                  </div>
                  <span className={`font-semibold ${financial.roi >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                    {financial.roi.toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="confidence" className="space-y-4 mt-4">
            <div className="space-y-3">
              <div className="p-3 bg-gray-50 rounded-lg">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium">Overall Quality</span>
                  <span className={`font-semibold ${getConfidenceColor(stats.avgConfidence)}`}>
                    {stats.avgConfidence.toFixed(0)}%
                  </span>
                </div>
                <Progress value={stats.avgConfidence} className="h-2" />
              </div>

              {results.map(result => (
                <div key={result.id} className="p-3 border rounded-lg">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium truncate">
                      {result.name}
                    </span>
                    <span className={`text-sm font-semibold ${getConfidenceColor(result.confidence)}`}>
                      {result.confidence.toFixed(0)}%
                    </span>
                  </div>
                  <Progress value={result.confidence} className="h-1" />
                  {showDetails && result.confidence < 80 && (
                    <div className="mt-2 text-xs text-gray-600">
                      {result.confidence < 50 && "Low confidence - check inputs"}
                      {result.confidence >= 50 && result.confidence < 80 && "Medium confidence - consider validation"}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default CalculationPanel;
