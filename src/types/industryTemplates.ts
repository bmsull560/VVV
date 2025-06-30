export type IndustryVertical = 
  | 'technology' 
  | 'manufacturing' 
  | 'healthcare' 
  | 'financial_services' 
  | 'retail' 
  | 'telecom' 
  | 'energy' 
  | 'education';

export interface IndustryTemplate {
  id: string;
  name: string;
  description: string;
  industry: string;
  commonValueDrivers: string[];
  keyMetrics: string[];
  suggestedQueries: string[];
  typicalROIRange: {
    min: number;
    max: number;
    average: number;
  };
  implementationComplexity: 'low' | 'medium' | 'high';
  timeToValue: string;
  commonRisks: string[];
  successFactors: string[];
  metadata?: Record<string, unknown>;
  caseStudy?: {
    title: string;
    description: string;
    results: string;
  };
}

// Helper function to create consistent template structure
const createIndustryTemplate = (
  id: string,
  name: string,
  description: string,
  industry: IndustryVertical,
  valueDrivers: string[],
  metrics: string[],
  suggestedQueries: string[],
  roiRange: { min: number; max: number; average: number },
  complexity: 'low' | 'medium' | 'high',
  ttv: string,
  risks: string[],
  successFactors: string[],
  caseStudy?: { title: string; description: string; results: string }
): IndustryTemplate => ({
  id,
  name,
  description,
  industry,
  commonValueDrivers: valueDrivers,
  keyMetrics: metrics,
  suggestedQueries,
  typicalROIRange: roiRange,
  implementationComplexity: complexity,
  timeToValue: ttv,
  commonRisks: risks,
  successFactors,
  metadata: {},
  ...(caseStudy ? { caseStudy } : {})
});

export const industryTemplates: Record<IndustryVertical, IndustryTemplate> = {
  technology: createIndustryTemplate(
    'tech',
    'Technology',
    'Optimize software development and IT operations',
    'technology',
    [
      'Developer productivity improvements',
      'Cloud cost optimization',
      'Reduced time-to-market',
      'Improved system reliability',
      'Enhanced security posture'
    ],
    [
      'Deployment frequency',
      'Lead time for changes',
      'Mean time to recover',
      'Change failure rate',
      'Infrastructure cost per deployment'
    ],
    [
      'How can we reduce cloud costs while maintaining performance?',
      'What are the best practices for CI/CD pipeline optimization?',
      'How can we improve developer productivity with better tooling?'
    ],
    { min: 25, max: 75, average: 45 },
    'medium',
    '3-6 months',
    [
      'Integration complexity with existing systems',
      'Talent acquisition and retention',
      'Security and compliance requirements'
    ],
    [
      'Executive sponsorship',
      'Cross-functional collaboration',
      'Clear success metrics',
      'User adoption'
    ]
  ),
  manufacturing: createIndustryTemplate(
    'mfg',
    'Manufacturing',
    'Optimize manufacturing operations and supply chain',
    'manufacturing',
    [
      'Production efficiency improvements',
      'Reduced downtime',
      'Supply chain optimization',
      'Quality improvement',
      'Labor productivity'
    ],
    [
      'Production efficiency',
      'Supply chain lead time',
      'Inventory turnover',
      'Defect rate',
      'On-time delivery'
    ],
    [
      'How can we reduce manufacturing defects?',
      'What are best practices for predictive maintenance?',
      'How to optimize our supply chain?'
    ],
    { min: 20, max: 60, average: 35 },
    'high',
    '6-12 months',
    [
      'Equipment integration challenges',
      'Workforce training requirements',
      'Supply chain disruptions'
    ],
    [
      'Operator buy-in',
      'Data quality and availability',
      'Cross-department collaboration'
    ]
  ),
  healthcare: createIndustryTemplate(
    'healthcare',
    'Healthcare',
    'Improve patient care and healthcare operations',
    'healthcare',
    [
      'Improved patient outcomes',
      'Reduced operational costs',
      'Enhanced patient experience',
      'Regulatory compliance',
      'Staff efficiency'
    ],
    [
      'Patient wait times',
      'Treatment success rates',
      'Readmission rates',
      'Staff productivity',
      'Compliance scores'
    ],
    [
      'How can we reduce patient wait times?',
      'What are best practices for healthcare data security?',
      'How to improve staff efficiency in healthcare?'
    ],
    { min: 30, max: 80, average: 50 },
    'high',
    '6-12 months',
    [
      'Data privacy concerns',
      'Regulatory compliance requirements',
      'Integration with existing healthcare systems'
    ],
    [
      'Clinical staff involvement',
      'Executive sponsorship',
      'Clear compliance framework'
    ]
  ),
  financial_services: createIndustryTemplate(
    'financial_services',
    'Financial Services',
    'Enhance financial performance and regulatory compliance',
    'financial_services',
    [
      'Cost reduction in operations',
      'Revenue growth from new services',
      'Improved risk management',
      'Enhanced customer experience'
    ],
    [
      'Customer acquisition cost',
      'Customer lifetime value',
      'Risk exposure',
      'Regulatory compliance rate'
    ],
    [
      'How to improve fraud detection?',
      'What are strategies for digital customer engagement?',
      'How to optimize investment portfolio performance?'
    ],
    { min: 25, max: 70, average: 45 },
    'high',
    '4-8 months',
    [
      'Regulatory compliance',
      'Data security concerns',
      'System integration challenges'
    ],
    [
      'Strong governance framework',
      'Regulatory expertise',
      'Customer-centric approach'
    ]
  ),
  retail: createIndustryTemplate(
    'retail',
    'Retail',
    'Enhance retail operations and customer experience',
    'retail',
    [
      'Increased sales',
      'Improved customer experience',
      'Inventory optimization',
      'Reduced operational costs',
      'Omnichannel integration'
    ],
    [
      'Sales per square foot',
      'Customer conversion rates',
      'Average transaction value',
      'Inventory turnover',
      'Customer satisfaction scores'
    ],
    [
      'How can we improve in-store customer experience?',
      'What are best practices for inventory optimization?',
      'How to increase online conversion rates?'
    ],
    { min: 20, max: 65, average: 40 },
    'medium',
    '3-6 months',
    [
      'Integration with existing systems',
      'Data privacy concerns',
      'Change management'
    ],
    [
      'Customer journey mapping',
      'Data-driven decision making',
      'Seamless omnichannel experience'
    ]
  ),
  telecom: createIndustryTemplate(
    'telecom',
    'Telecommunications',
    'Optimize network operations and customer service',
    'telecom',
    [
      'Network performance',
      'Customer satisfaction',
      'Operational efficiency',
      'Service reliability',
      'New revenue streams'
    ],
    [
      'Network uptime',
      'Mean time to repair',
      'Customer churn rate',
      'Average revenue per user',
      'Service activation time'
    ],
    [
      'How can we reduce network downtime?',
      'What are best practices for customer churn reduction?',
      'How to improve service activation processes?'
    ],
    { min: 15, max: 50, average: 30 },
    'high',
    '6-12 months',
    [
      'Legacy system integration',
      'Network complexity',
      'Regulatory requirements'
    ],
    [
      'Network reliability',
      'Customer experience focus',
      'Operational efficiency'
    ]
  ),
  energy: createIndustryTemplate(
    'energy',
    'Energy',
    'Optimize energy production and distribution',
    'energy',
    [
      'Operational efficiency',
      'Cost reduction',
      'Sustainability',
      'Asset performance',
      'Regulatory compliance'
    ],
    [
      'Energy production efficiency',
      'Maintenance costs',
      'Equipment uptime',
      'Safety incident rate',
      'Regulatory compliance score'
    ],
    [
      'How can we improve energy production efficiency?',
      'What are best practices for predictive maintenance?',
      'How to reduce operational costs in energy production?'
    ],
    { min: 20, max: 60, average: 40 },
    'high',
    '6-18 months',
    [
      'High capital requirements',
      'Regulatory changes',
      'Technology integration challenges'
    ],
    [
      'Strong project management',
      'Stakeholder alignment',
      'Clear ROI metrics'
    ]
  ),
  education: createIndustryTemplate(
    'education',
    'Education',
    'Enhance learning outcomes and institutional efficiency',
    'education',
    [
      'Improved learning outcomes',
      'Operational efficiency',
      'Student engagement',
      'Cost reduction',
      'Accessibility'
    ],
    [
      'Student performance',
      'Graduation rates',
      'Student satisfaction',
      'Operational costs',
      'Technology adoption rates'
    ],
    [
      'How can we improve student engagement in online learning?',
      'What are best practices for educational technology integration?',
      'How to measure the impact of educational technology?'
    ],
    { min: 15, max: 50, average: 30 },
    'medium',
    '4-8 months',
    [
      'Resistance to change',
      'Budget constraints',
      'Technology adoption challenges'
    ],
    [
      'Faculty and staff buy-in',
      'Student-centered design',
      'Measurable learning outcomes',
      'Strong executive sponsorship',
      'Cross-functional collaboration',
      'Clear success metrics and KPIs',
      'Ongoing training and support'
    ]
  )
};

export const getIndustryTemplate = (industry: IndustryVertical): IndustryTemplate => {
  return industryTemplates[industry] || industryTemplates.technology; // Default to technology
};

export const getIndustryTemplateById = (id: string): IndustryTemplate | undefined => {
  return Object.values(industryTemplates).find(template => template.id === id);
};

export const getIndustryTemplateOptions = () => {
  return Object.entries(industryTemplates).map(([key, template]) => ({
    value: key,
    label: template.name,
    description: template.description
  }));
};