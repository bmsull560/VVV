import React from 'react';
import { useDrag } from 'react-dnd';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { 
  Calculator, 
  TrendingUp, 
  DollarSign, 
  Percent, 
  Calendar,
  Hash,
  FormInput,
  Target,
  BarChart3,
  PieChart,
  Zap,
  Plus
} from 'lucide-react';

interface ComponentType {
  id: string;
  name: string;
  category: string;
  description: string;
  icon: React.ComponentType<any>;
  color: string;
  isPopular?: boolean;
  isPremium?: boolean;
}

interface DraggableComponentProps {
  component: ComponentType;
  onAddComponent?: (type: string) => void;
}

interface ComponentLibraryProps {
  onAddComponent?: (type: string) => void;
}

const DraggableComponent: React.FC<DraggableComponentProps> = ({ 
  component, 
  onAddComponent 
}) => {
  const [{ isDragging }, drag] = useDrag({
    type: 'component',
    item: { type: 'component', componentType: component.id },
    collect: (monitor) => ({
      isDragging: monitor.isDragging()
    })
  });

  const Icon = component.icon;

  return (
    <div
      ref={drag}
      className={`
        p-3 border rounded-lg cursor-move transition-all
        ${isDragging ? 'opacity-50 scale-95' : 'hover:shadow-md hover:scale-105'}
        ${component.isPremium ? 'border-yellow-300 bg-yellow-50' : 'border-gray-200 bg-white'}
      `}
      onClick={() => onAddComponent?.(component.id)}
    >
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${component.color}`}>
          <Icon className="h-4 w-4" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h4 className="text-sm font-medium truncate">{component.name}</h4>
            {component.isPopular && (
              <Badge variant="secondary" className="text-xs">Popular</Badge>
            )}
            {component.isPremium && (
              <Badge variant="outline" className="text-xs border-yellow-400 text-yellow-700">
                Pro
              </Badge>
            )}
          </div>
          <p className="text-xs text-gray-600 mt-1 line-clamp-2">
            {component.description}
          </p>
        </div>
      </div>
    </div>
  );
};

const ComponentLibrary: React.FC<ComponentLibraryProps> = ({ onAddComponent }) => {
  const componentTypes: ComponentType[] = [
    // Financial Inputs
    {
      id: 'revenue-stream',
      name: 'Revenue Stream',
      category: 'Financial Inputs',
      description: 'Track income sources with growth rates and forecasting',
      icon: TrendingUp,
      color: 'bg-green-100 text-green-700',
      isPopular: true
    },
    {
      id: 'cost-center',
      name: 'Cost Center',
      category: 'Financial Inputs',
      description: 'Monitor expenses with escalation and categorization',
      icon: DollarSign,
      color: 'bg-red-100 text-red-700',
      isPopular: true
    },
    {
      id: 'investment',
      name: 'Investment',
      category: 'Financial Inputs',
      description: 'Capital expenditures and initial investments',
      icon: Target,
      color: 'bg-purple-100 text-purple-700'
    },
    {
      id: 'benefit',
      name: 'Benefit',
      category: 'Financial Inputs',
      description: 'Quantifiable business benefits and value drivers',
      icon: Zap,
      color: 'bg-blue-100 text-blue-700'
    },

    // Calculations
    {
      id: 'roi-calculator',
      name: 'ROI Calculator',
      category: 'Calculations',
      description: 'Return on Investment analysis with risk adjustments',
      icon: Calculator,
      color: 'bg-blue-100 text-blue-700',
      isPopular: true
    },
    {
      id: 'npv-calculator',
      name: 'NPV Calculator',
      category: 'Calculations',
      description: 'Net Present Value with discount rate modeling',
      icon: BarChart3,
      color: 'bg-purple-100 text-purple-700',
      isPremium: true
    },
    {
      id: 'payback-calculator',
      name: 'Payback Period',
      category: 'Calculations',
      description: 'Simple and discounted payback period analysis',
      icon: Calendar,
      color: 'bg-yellow-100 text-yellow-700'
    },
    {
      id: 'sensitivity-analysis',
      name: 'Sensitivity Analysis',
      category: 'Calculations',
      description: 'Risk modeling with scenario testing and Monte Carlo',
      icon: PieChart,
      color: 'bg-cyan-100 text-cyan-700',
      isPremium: true
    },

    // Variables & Logic
    {
      id: 'variable',
      name: 'Variable',
      category: 'Variables & Logic',
      description: 'Store values, constants, and parameters',
      icon: Hash,
      color: 'bg-gray-100 text-gray-700'
    },
    {
      id: 'formula',
      name: 'Custom Formula',
      category: 'Variables & Logic',
      description: 'Create custom calculations and business logic',
      icon: FormInput,
      color: 'bg-pink-100 text-pink-700',
      isPremium: true
    }
  ];

  // Group components by category
  const groupedComponents = componentTypes.reduce((groups, component) => {
    const category = component.category;
    if (!groups[category]) {
      groups[category] = [];
    }
    groups[category].push(component);
    return groups;
  }, {} as Record<string, ComponentType[]>);

  return (
    <Card className="w-80 h-full">
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <Plus className="h-5 w-5" />
          Component Library
        </CardTitle>
        <p className="text-sm text-gray-600">
          Drag components to the canvas or click to add
        </p>
      </CardHeader>

      <CardContent className="overflow-y-auto">
        <div className="space-y-6">
          {Object.entries(groupedComponents).map(([category, components]) => (
            <div key={category}>
              <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                {category}
                <Badge variant="outline" className="text-xs">
                  {components.length}
                </Badge>
              </h3>
              
              <div className="space-y-2">
                {components.map(component => (
                  <DraggableComponent
                    key={component.id}
                    component={component}
                    onAddComponent={onAddComponent}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Quick Actions */}
        <div className="mt-6 pt-4 border-t">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Quick Start</h3>
          <div className="space-y-2">
            <Button 
              variant="outline" 
              size="sm" 
              className="w-full justify-start"
              onClick={() => {
                // Add basic ROI template
                onAddComponent?.('investment');
                setTimeout(() => onAddComponent?.('benefit'), 100);
                setTimeout(() => onAddComponent?.('roi-calculator'), 200);
              }}
            >
              <Calculator className="h-4 w-4 mr-2" />
              Basic ROI Template
            </Button>
            
            <Button 
              variant="outline" 
              size="sm" 
              className="w-full justify-start"
              onClick={() => {
                // Add revenue model template
                onAddComponent?.('revenue-stream');
                setTimeout(() => onAddComponent?.('cost-center'), 100);
                setTimeout(() => onAddComponent?.('variable'), 200);
              }}
            >
              <TrendingUp className="h-4 w-4 mr-2" />
              Revenue Model
            </Button>
            
            <Button 
              variant="outline" 
              size="sm" 
              className="w-full justify-start"
              onClick={() => {
                // Add advanced analysis template
                onAddComponent?.('npv-calculator');
                setTimeout(() => onAddComponent?.('sensitivity-analysis'), 100);
                setTimeout(() => onAddComponent?.('payback-calculator'), 200);
              }}
            >
              <BarChart3 className="h-4 w-4 mr-2" />
              Advanced Analysis
            </Button>
          </div>
        </div>

        {/* Help Section */}
        <div className="mt-6 pt-4 border-t">
          <div className="p-3 bg-blue-50 rounded-lg">
            <h4 className="text-sm font-medium text-blue-800 mb-1">
              💡 Pro Tips
            </h4>
            <ul className="text-xs text-blue-700 space-y-1">
              <li>• Drag components to the canvas to add them</li>
              <li>• Connect components to create relationships</li>
              <li>• Use variables for reusable values</li>
              <li>• Start with templates for common scenarios</li>
            </ul>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default ComponentLibrary;
