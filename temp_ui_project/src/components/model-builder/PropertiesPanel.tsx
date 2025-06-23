import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Button } from '../ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Textarea } from '../ui/textarea';
import { Switch } from '../ui/switch';
import { Badge } from '../ui/badge';
import { Calculator, TrendingUp, DollarSign, Percent, Hash, Calendar } from 'lucide-react';
import { ModelComponent } from '../../utils/calculationEngine';

interface PropertiesPanelProps {
  model: { components: ModelComponent[] } | null;
  setModel: (model: { components: ModelComponent[] }) => void;
  selectedComponent: string | null;
  calculations: Record<string, any>;
  getFormattedValue: (id: string) => string;
}

const PropertiesPanel: React.FC<PropertiesPanelProps> = ({
  model,
  setModel,
  selectedComponent,
  calculations,
  getFormattedValue
}) => {
  const [localProperties, setLocalProperties] = useState<Record<string, any>>({});
  const [hasChanges, setHasChanges] = useState(false);

  const component = selectedComponent 
    ? model?.components.find(c => c.id === selectedComponent)
    : null;

  // Update local properties when component changes
  useEffect(() => {
    if (component) {
      setLocalProperties({ ...component.properties });
      setHasChanges(false);
    } else {
      setLocalProperties({});
      setHasChanges(false);
    }
  }, [component]);

  // Update property value
  const updateProperty = (key: string, value: any) => {
    const newProperties = { ...localProperties, [key]: value };
    setLocalProperties(newProperties);
    setHasChanges(true);
  };

  // Save changes to model
  const saveChanges = () => {
    if (!component || !model) return;

    const updatedComponents = model.components.map(c => 
      c.id === component.id 
        ? { ...c, properties: { ...localProperties } }
        : c
    );

    setModel({ components: updatedComponents });
    setHasChanges(false);
  };

  // Reset changes
  const resetChanges = () => {
    if (component) {
      setLocalProperties({ ...component.properties });
      setHasChanges(false);
    }
  };

  // Get component type configuration
  const getComponentConfig = (type: string) => {
    const configs: Record<string, any> = {
      'revenue-stream': {
        icon: TrendingUp,
        title: 'Revenue Stream',
        color: 'bg-green-100 text-green-800',
        fields: [
          { key: 'name', label: 'Stream Name', type: 'text', placeholder: 'Enter revenue stream name' },
          { key: 'unitPrice', label: 'Unit Price ($)', type: 'number', min: 0, step: 0.01 },
          { key: 'quantity', label: 'Quantity', type: 'number', min: 0 },
          { key: 'growthRate', label: 'Growth Rate (%)', type: 'number', min: -100, max: 1000, step: 0.1 },
          { key: 'periods', label: 'Periods', type: 'number', min: 1, max: 240 },
          { key: 'startPeriod', label: 'Start Period', type: 'number', min: 1, default: 1 }
        ]
      },
      'cost-center': {
        icon: DollarSign,
        title: 'Cost Center',
        color: 'bg-red-100 text-red-800',
        fields: [
          { key: 'name', label: 'Cost Name', type: 'text', placeholder: 'Enter cost description' },
          { key: 'monthlyCost', label: 'Monthly Cost ($)', type: 'number', min: 0, step: 0.01 },
          { key: 'periods', label: 'Periods', type: 'number', min: 1, max: 240 },
          { key: 'escalationRate', label: 'Escalation Rate (%)', type: 'number', min: -50, max: 100, step: 0.1 },
          { key: 'costType', label: 'Cost Type', type: 'select', options: ['Fixed', 'Variable', 'Semi-Variable'] },
          { key: 'startPeriod', label: 'Start Period', type: 'number', min: 1, default: 1 }
        ]
      },
      'roi-calculator': {
        icon: Calculator,
        title: 'ROI Calculator',
        color: 'bg-blue-100 text-blue-800',
        fields: [
          { key: 'name', label: 'Investment Name', type: 'text', placeholder: 'Enter investment description' },
          { key: 'investment', label: 'Initial Investment ($)', type: 'number', min: 0, step: 0.01 },
          { key: 'annualBenefit', label: 'Annual Benefit ($)', type: 'number', step: 0.01 },
          { key: 'periods', label: 'Time Horizon (Years)', type: 'number', min: 1, max: 20 },
          { key: 'riskAdjustment', label: 'Risk Adjustment (%)', type: 'number', min: 0, max: 100, step: 0.1, default: 0 }
        ]
      },
      'npv-calculator': {
        icon: TrendingUp,
        title: 'NPV Calculator',
        color: 'bg-purple-100 text-purple-800',
        fields: [
          { key: 'name', label: 'NPV Analysis Name', type: 'text', placeholder: 'Enter NPV analysis name' },
          { key: 'discountRate', label: 'Discount Rate (%)', type: 'number', min: 0, max: 50, step: 0.1 },
          { key: 'cashFlows', label: 'Cash Flows ($)', type: 'textarea', placeholder: 'Enter cash flows separated by commas (e.g., -10000, 3000, 4000, 5000)' },
          { key: 'includeTerminalValue', label: 'Include Terminal Value', type: 'boolean', default: false },
          { key: 'terminalGrowthRate', label: 'Terminal Growth Rate (%)', type: 'number', min: 0, max: 10, step: 0.1, condition: 'includeTerminalValue' }
        ]
      },
      'payback-calculator': {
        icon: Calendar,
        title: 'Payback Calculator',
        color: 'bg-yellow-100 text-yellow-800',
        fields: [
          { key: 'name', label: 'Payback Analysis Name', type: 'text', placeholder: 'Enter payback analysis name' },
          { key: 'investment', label: 'Initial Investment ($)', type: 'number', min: 0, step: 0.01 },
          { key: 'annualCashFlow', label: 'Annual Cash Flow ($)', type: 'number', step: 0.01 },
          { key: 'useDiscounting', label: 'Use Discounted Payback', type: 'boolean', default: false },
          { key: 'discountRate', label: 'Discount Rate (%)', type: 'number', min: 0, max: 50, step: 0.1, condition: 'useDiscounting' }
        ]
      },
      'sensitivity-analysis': {
        icon: TrendingUp,
        title: 'Sensitivity Analysis',
        color: 'bg-cyan-100 text-cyan-800',
        fields: [
          { key: 'name', label: 'Analysis Name', type: 'text', placeholder: 'Enter sensitivity analysis name' },
          { key: 'baseCase', label: 'Base Case Value', type: 'number', step: 0.01 },
          { key: 'variationPercent', label: 'Variation (±%)', type: 'number', min: 1, max: 100, default: 20 },
          { key: 'steps', label: 'Number of Steps', type: 'number', min: 3, max: 21, default: 5 },
          { key: 'analysisType', label: 'Analysis Type', type: 'select', options: ['Linear', 'Optimistic/Pessimistic', 'Monte Carlo'] }
        ]
      },
      'variable': {
        icon: Hash,
        title: 'Variable',
        color: 'bg-gray-100 text-gray-800',
        fields: [
          { key: 'name', label: 'Variable Name', type: 'text', placeholder: 'Enter variable name' },
          { key: 'value', label: 'Value', type: 'number', step: 0.01 },
          { key: 'units', label: 'Units', type: 'text', placeholder: 'e.g., $, %, units' },
          { key: 'description', label: 'Description', type: 'textarea', placeholder: 'Describe this variable' }
        ]
      },
      'formula': {
        icon: Calculator,
        title: 'Formula',
        color: 'bg-pink-100 text-pink-800',
        fields: [
          { key: 'name', label: 'Formula Name', type: 'text', placeholder: 'Enter formula name' },
          { key: 'formula', label: 'Formula', type: 'textarea', placeholder: 'Enter formula (e.g., A1 * B1 + C1)' },
          { key: 'description', label: 'Description', type: 'textarea', placeholder: 'Describe this formula' }
        ]
      }
    };
    return configs[type] || { icon: Calculator, title: type, color: 'bg-gray-100 text-gray-800', fields: [] };
  };

  // Render field based on type
  const renderField = (field: any) => {
    const value = localProperties[field.key] ?? field.default ?? '';
    
    // Check condition if present
    if (field.condition && !localProperties[field.condition]) {
      return null;
    }

    switch (field.type) {
      case 'text':
        return (
          <Input
            value={value}
            onChange={(e) => updateProperty(field.key, e.target.value)}
            placeholder={field.placeholder}
            className="mt-1"
          />
        );
      
      case 'number':
        return (
          <Input
            type="number"
            value={value}
            onChange={(e) => updateProperty(field.key, parseFloat(e.target.value) || 0)}
            min={field.min}
            max={field.max}
            step={field.step || 1}
            className="mt-1"
          />
        );
      
      case 'textarea':
        return (
          <Textarea
            value={value}
            onChange={(e) => updateProperty(field.key, e.target.value)}
            placeholder={field.placeholder}
            rows={3}
            className="mt-1"
          />
        );
      
      case 'select':
        return (
          <Select
            value={value}
            onValueChange={(newValue) => updateProperty(field.key, newValue)}
          >
            <SelectTrigger className="mt-1">
              <SelectValue placeholder="Select option" />
            </SelectTrigger>
            <SelectContent>
              {field.options?.map((option: string) => (
                <SelectItem key={option} value={option}>{option}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        );
      
      case 'boolean':
        return (
          <div className="flex items-center space-x-2 mt-1">
            <Switch
              checked={value}
              onCheckedChange={(checked) => updateProperty(field.key, checked)}
            />
            <span className="text-sm text-gray-600">
              {value ? 'Enabled' : 'Disabled'}
            </span>
          </div>
        );
      
      default:
        return (
          <Input
            value={value}
            onChange={(e) => updateProperty(field.key, e.target.value)}
            className="mt-1"
          />
        );
    }
  };

  if (!component) {
    return (
      <Card className="w-80 h-full">
        <CardHeader>
          <CardTitle className="text-lg">Properties</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center text-gray-500 py-8">
            <Calculator className="h-12 w-12 mx-auto mb-3 text-gray-300" />
            <p>Select a component to edit its properties</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const config = getComponentConfig(component.type);
  const Icon = config.icon;
  const calculatedValue = getFormattedValue(component.id);

  return (
    <Card className="w-80 h-full flex flex-col">
      <CardHeader className="flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${config.color}`}>
            <Icon className="h-5 w-5" />
          </div>
          <div>
            <CardTitle className="text-lg">{config.title}</CardTitle>
            <Badge variant="outline" className="mt-1">
              {calculatedValue}
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex-1 overflow-y-auto">
        <div className="space-y-4">
          {config.fields.map((field: any) => (
            <div key={field.key}>
              <Label htmlFor={field.key} className="text-sm font-medium">
                {field.label}
              </Label>
              {renderField(field)}
            </div>
          ))}
        </div>

        {/* Action buttons */}
        {hasChanges && (
          <div className="flex gap-2 mt-6 pt-4 border-t">
            <Button onClick={saveChanges} className="flex-1">
              Save Changes
            </Button>
            <Button variant="outline" onClick={resetChanges}>
              Reset
            </Button>
          </div>
        )}

        {/* Calculation result */}
        {calculatedValue && (
          <div className="mt-6 p-3 bg-gray-50 rounded-lg">
            <Label className="text-sm font-medium text-gray-700">
              Calculated Value
            </Label>
            <div className="text-lg font-semibold text-gray-900 mt-1">
              {calculatedValue}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default PropertiesPanel;
