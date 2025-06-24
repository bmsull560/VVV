import React, { useState, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Select } from '../ui/select';
import { Badge } from '../ui/badge';
import { IndustryTemplate, getIndustryTemplate, getIndustryTemplateOptions } from '../../types/industryTemplates';
import { Check, ChevronDown, Info } from 'lucide-react';

import type { IndustryVertical } from '../../types/industryTemplates';

interface IndustryTemplateSelectorProps {
  onSelectTemplate: (template: IndustryTemplate) => void;
  onCancel: () => void;
  initialIndustry?: IndustryVertical;
}

const IndustryTemplateSelector: React.FC<IndustryTemplateSelectorProps> = ({
  onSelectTemplate,
  onCancel,
  initialIndustry = 'technology',
}) => {
  const industryOptions = getIndustryTemplateOptions();
  const [selectedIndustry, setSelectedIndustry] = useState<IndustryVertical>(initialIndustry);
  const [selectedTemplate, setSelectedTemplate] = useState<IndustryTemplate>(
    getIndustryTemplate(initialIndustry)
  );
  const [isExpanded, setIsExpanded] = useState<boolean>(false);

  const handleIndustryChange = useCallback((value: string) => {
    const industry = value as IndustryVertical;
    const template = getIndustryTemplate(industry);
    setSelectedIndustry(industry);
    setSelectedTemplate(template);
  }, []);

  const handleApplyTemplate = useCallback(() => {
    onSelectTemplate(selectedTemplate);
  }, [onSelectTemplate, selectedTemplate]);

  const toggleExpand = useCallback(() => {
    setIsExpanded(prev => !prev);
  }, []);

  const renderComplexityBadge = (complexity: string) => {
    switch (complexity) {
      case 'low':
        return <Badge variant="outline" className="bg-green-100 text-green-800">Low Complexity</Badge>;
      case 'medium':
        return <Badge variant="outline" className="bg-yellow-100 text-yellow-800">Medium Complexity</Badge>;
      case 'high':
        return <Badge variant="outline" className="bg-red-100 text-red-800">High Complexity</Badge>;
      default:
        return null;
    }
  };

  return (
    <Card className="w-full max-w-3xl mx-auto">
      <CardHeader>
        <div className="flex justify-between items-start">
          <div>
            <CardTitle>Select Industry Template</CardTitle>
            <div className="mt-1 text-muted-foreground text-sm">
              Choose an industry template to pre-populate common value drivers and metrics.
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="text-muted-foreground"
            onClick={onCancel}
          >
            Skip Template
          </Button>
        </div>
      </CardHeader>
      
      <CardContent>
        <div className="space-y-6">
          <div className="space-y-2">
            <label htmlFor="industry-select" className="text-sm font-medium leading-none">
              Industry
            </label>
            <Select
              id="industry-select"
              label="Industry"
              value={selectedIndustry}
              options={industryOptions.map(option => ({ value: option.value, label: option.label }))}
              onChange={e => handleIndustryChange(e.target.value)}
              className="w-full"
              data-testid="industry-select-trigger"
            />
          </div>

          <div className="border rounded-lg overflow-hidden">
            <div className="p-4 bg-muted/50 border-b">
              <div className="flex justify-between items-center">
                <h3 className="font-medium">{selectedTemplate.name} Template</h3>
                <div className="flex items-center gap-2">
                  {renderComplexityBadge(selectedTemplate.implementationComplexity)}
                  <Badge variant="outline" className="bg-blue-50 text-blue-700">
                    ROI: {selectedTemplate.typicalROIRange.average}x
                  </Badge>
                  <Badge variant="outline" className="bg-purple-50 text-purple-700">
                    TTV: {selectedTemplate.timeToValue}
                  </Badge>
                </div>
              </div>
              <p className="text-sm text-muted-foreground mt-1">
                {selectedTemplate.description}
              </p>
            </div>

            <div className="p-4 space-y-4">
              <div>
                <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                  Common Value Drivers
                  <Info className="h-4 w-4 text-muted-foreground" />
                </h4>
                <div className="space-y-2">
                  {selectedTemplate.commonValueDrivers.map((driver, index) => (
                    <div key={index} className="flex items-start gap-2">
                      <Check className="h-4 w-4 mt-0.5 text-green-500 flex-shrink-0" />
                      <span className="text-sm">{driver}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                  Key Metrics
                  <Info className="h-4 w-4 text-muted-foreground" />
                </h4>
                <div className="space-y-2">
                  {selectedTemplate.keyMetrics.map((metric, index) => (
                    <div key={index} className="flex items-start gap-2">
                      <div className="h-2 w-2 rounded-full bg-primary mt-2 flex-shrink-0" />
                      <span className="text-sm">{metric}</span>
                    </div>
                  ))}
                </div>
              </div>

              {isExpanded && (
                <div className="space-y-4 pt-2 border-t">
                  <div>
                    <h4 className="text-sm font-medium mb-2">Success Factors</h4>
                    <div className="space-y-2">
                      {selectedTemplate.successFactors.map((factor, index) => (
                        <div key={index} className="flex items-start gap-2">
                          <div className="h-2 w-2 rounded-full bg-green-500 mt-2 flex-shrink-0" />
                          <span className="text-sm">{factor}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h4 className="text-sm font-medium mb-2">Common Risks</h4>
                    <div className="space-y-2">
                      {selectedTemplate.commonRisks.map((risk, index) => (
                        <div key={index} className="flex items-start gap-2">
                          <div className="h-2 w-2 rounded-full bg-red-500 mt-2 flex-shrink-0" />
                          <span className="text-sm">{risk}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              <button
                onClick={toggleExpand}
                className="text-sm text-primary hover:underline flex items-center gap-1"
              >
                {isExpanded ? 'Show less' : 'Show more details'}
                <ChevronDown
                  className={`h-4 w-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                />
              </button>
            </div>
          </div>
        </div>
      </CardContent>

      <div className="flex justify-end gap-2 p-6 border-t">
        <Button variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button onClick={handleApplyTemplate}>
          Apply Template
        </Button>
      </div>
    </Card>
  );
};

export default IndustryTemplateSelector;
