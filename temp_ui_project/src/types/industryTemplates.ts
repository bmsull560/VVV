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

export const industryTemplates: Record<IndustryVertical, IndustryTemplate> = {
  technology: {
    id: 'tech',
    name: 'Technology',
    description: 'Optimize software development and IT operations',
    commonValueDrivers: [
      'Developer productivity improvements',
      'Cloud cost optimization',
      'Reduced time-to-market',
      'Improved system reliability',
      'Enhanced security posture'
    ],
    keyMetrics: [
      'Deployment frequency',
      'Lead time for changes',
      'Mean time to recover',
      'Change failure rate',
      'Infrastructure cost per deployment'
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
