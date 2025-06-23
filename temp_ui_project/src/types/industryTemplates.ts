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
  metadata?: Record<string, any>;
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
      'Overall Equipment Effectiveness (OEE)',
      'Production yield',
      'Cycle time',
      'Inventory turnover',
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
    'fin',
    'Financial Services',
    'Enhance financial operations and customer experience',
    'financial_services',
    [
      'Reduced operational costs',
      'Improved compliance',
      'Enhanced customer experience',
      'Risk mitigation',
      'Revenue growth'
    ],
    [
      'Customer acquisition cost',
      'Customer lifetime value',
      'Fraud detection rates',
      'Regulatory compliance scores',
      'Transaction processing time'
    ],
    [
      'How can we reduce fraud in financial transactions?',
      'What are best practices for financial data security?',
      'How to improve customer onboarding experience?'
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
    'edu',
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
      'Measurable learning outcomes'
    ]
  )
};
      'Strong executive sponsorship',
      'Cross-functional collaboration',
      'Clear success metrics and KPIs',
      'Ongoing training and support'
    ]
  ),
  manufacturing: createIndustryTemplate(
    'mfg',
    'Manufacturing',
    'Optimize production and supply chain operations',
    'manufacturing',
    [
      'Increased production efficiency',
      'Reduced equipment downtime',
      'Improved quality control',
      'Supply chain optimization',
      'Reduced waste and scrap'
    ],
    [
      'Overall equipment effectiveness (OEE)',
      'Production cycle time',
      'First-pass yield',
      'Inventory turnover',
      'On-time delivery'
    ],
    [
      'How can we reduce production downtime?',
      'What are the best practices for predictive maintenance?',
      'How can we optimize our supply chain for just-in-time delivery?'
    ],
    { min: 30, max: 80, average: 55 },
    'high',
    '6-12 months',
    [
      'High upfront capital investment',
      'Workforce training requirements',
      'Integration with legacy systems'
    ],
    [
      'Strong change management',
      'Employee engagement and training',
      'Clear ROI metrics',
      'Vendor support and partnership'
    ]
  )
    ],
    typicalROIRange: {
      min: 2.5,
      max: 5.0,
      average: 3.8
    },
    implementationComplexity: 'medium',
    timeToValue: '3-6 months',
    commonRisks: [
      'Integration challenges with legacy systems',
      'Skill gaps in new technologies',
      'Resistance to DevOps culture change'
    ],
    successFactors: [
      'Executive sponsorship',
      'Cross-functional collaboration',
      'Iterative implementation approach'
    ]
  },
  // Additional industry templates will be added here
  manufacturing: {
    id: 'mfg',
    name: 'Manufacturing',
    description: 'Enhance production efficiency and supply chain operations',
    commonValueDrivers: [
      'Reduced equipment downtime',
      'Improved production yield',
      'Optimized inventory levels',
      'Enhanced quality control',
      'Supply chain visibility'
    ],
    keyMetrics: [
      'Overall Equipment Effectiveness (OEE)',
      'First-pass yield',
      'Inventory turnover',
      'On-time delivery',
      'Manufacturing cycle time'
    ],
    typicalROIRange: {
      min: 3.0,
      max: 6.0,
      average: 4.2
    },
    implementationComplexity: 'high',
    timeToValue: '6-12 months',
    commonRisks: [
      'Integration with legacy MES/ERP systems',
      'Workforce training requirements',
      'Supply chain disruptions'
    ],
    successFactors: [
      'Clear operational metrics',
      'Stakeholder alignment',
      'Pilot program validation'
    ]
  },
  healthcare: {
    id: 'health',
    name: 'Healthcare',
    description: 'Improve patient outcomes and operational efficiency',
    commonValueDrivers: [
      'Improved patient throughput',
      'Reduced clinical variation',
      'Enhanced care coordination',
      'Regulatory compliance',
      'Staff productivity'
    ],
    keyMetrics: [
      'Average length of stay',
      'Readmission rates',
      'Patient satisfaction scores',
      'Revenue cycle metrics',
      'Clinical outcome measures'
    ],
    typicalROIRange: {
      min: 2.0,
      max: 4.5,
      average: 3.2
    },
    implementationComplexity: 'high',
    timeToValue: '6-12 months',
    commonRisks: [
      'Data privacy and security concerns',
      'Clinical workflow disruption',
      'Staff resistance to technology adoption'
    ],
    successFactors: [
      'Clinical leadership engagement',
      'Change management program',
      'Pilot program with clear metrics'
    ]
  },
  financial_services: {
    id: 'fin',
    name: 'Financial Services',
    description: 'Enhance financial operations and customer experience',
    commonValueDrivers: [
      'Reduced operational risk',
      'Improved regulatory compliance',
      'Enhanced customer experience',
      'Operational efficiency gains',
      'Fraud detection and prevention'
    ],
    keyMetrics: [
      'Cost-income ratio',
      'Customer acquisition cost',
      'Net Promoter Score (NPS)',
      'Time to onboard new customers',
      'Fraud detection rate'
    ],
    typicalROIRange: {
      min: 2.8,
      max: 5.5,
      average: 4.0
    },
    implementationComplexity: 'high',
    timeToValue: '6-9 months',
    commonRisks: [
      'Regulatory compliance requirements',
      'Data security and privacy concerns',
      'Integration with legacy core banking systems'
    ],
    successFactors: [
      'Strong governance framework',
      'Regulatory compliance focus',
      'Phased implementation approach'
    ]
  },
  retail: {
    id: 'retail',
    name: 'Retail',
    description: 'Optimize retail operations and customer engagement',
    commonValueDrivers: [
      'Increased same-store sales',
      'Improved inventory turnover',
      'Enhanced customer experience',
      'Reduced operational costs',
      'Omnichannel integration'
    ],
    keyMetrics: [
      'Sales per square foot',
      'Conversion rate',
      'Average transaction value',
      'Inventory turnover',
      'Customer lifetime value'
    ],
    typicalROIRange: {
      min: 3.5,
      max: 7.0,
      average: 5.0
    },
    implementationComplexity: 'medium',
    timeToValue: '3-6 months',
    commonRisks: [
      'Integration with existing POS systems',
      'Data quality and consistency',
      'Seasonal demand fluctuations'
    ],
    successFactors: [
      'Clear customer journey mapping',
      'Data-driven decision making',
      'Cross-functional collaboration'
    ]
  },
  // Additional industry templates can be added here
  telecom: {
    id: 'telco',
    name: 'Telecommunications',
    description: 'Optimize network operations and customer experience',
    commonValueDrivers: [
      'Network performance improvements',
      'Customer churn reduction',
      'Operational efficiency gains',
      'New revenue streams',
      'Regulatory compliance'
    ],
    keyMetrics: [
      'Network uptime',
      'Customer churn rate',
      'Average revenue per user (ARPU)',
      'Network latency',
      'First call resolution'
    ],
    typicalROIRange: {
      min: 2.0,
      max: 4.5,
      average: 3.2
    },
    implementationComplexity: 'high',
    timeToValue: '6-12 months',
    commonRisks: [
      'Network integration complexity',
      'Regulatory compliance requirements',
      'Legacy system limitations'
    ],
    successFactors: [
      'Strong executive sponsorship',
      'Cross-functional team alignment',
      'Clear success metrics'
    ]
  },
  energy: {
    id: 'energy',
    name: 'Energy',
    description: 'Optimize energy production and distribution',
    commonValueDrivers: [
      'Operational efficiency improvements',
      'Reduced energy waste',
      'Predictive maintenance',
      'Regulatory compliance',
      'Asset performance optimization'
    ],
    keyMetrics: [
      'Energy production efficiency',
      'Unplanned downtime',
      'Maintenance costs',
      'Regulatory compliance status',
      'Asset utilization rates'
    ],
    typicalROIRange: {
      min: 2.5,
      max: 5.5,
      average: 4.0
    },
    implementationComplexity: 'high',
    timeToValue: '6-12 months',
    commonRisks: [
      'Integration with legacy SCADA systems',
      'Cybersecurity vulnerabilities',
      'Regulatory compliance requirements'
    ],
    successFactors: [
      'Clear business case',
      'Stakeholder alignment',
      'Phased implementation approach'
    ]
  },
  education: {
    id: 'edu',
    name: 'Education',
    description: 'Enhance learning outcomes and institutional efficiency',
    commonValueDrivers: [
      'Improved student outcomes',
      'Operational efficiency gains',
      'Enhanced learning experience',
      'Data-driven decision making',
      'Resource optimization'
    ],
    keyMetrics: [
      'Student retention rates',
      'Graduation rates',
      'Learning outcomes assessment',
      'Operational efficiency metrics',
      'Student satisfaction scores'
    ],
    typicalROIRange: {
      min: 2.0,
      max: 4.0,
      average: 3.0
    },
    implementationComplexity: 'medium',
    timeToValue: '6-9 months',
    commonRisks: [
      'Faculty and staff adoption',
      'Data privacy concerns',
      'Integration with existing SIS/LMS systems'
    ],
    successFactors: [
      'Stakeholder engagement',
      'Change management program',
      'Clear success metrics'
    ]
  }
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
