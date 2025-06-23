import { useState, useEffect, useCallback } from 'react';
import { FileDown, Eye, ArrowLeft, Download, BookOpen, FileText, Presentation, Check, AlertCircle, Loader } from 'lucide-react';
import { ComposedBusinessCase, DiscoveryResponse, QuantificationResponse, NarrativeResponse, b2bValueAPI } from '../../services/b2bValueApi';
import styles from './Step4_Composition.module.css';

interface Step4CompositionProps {
  discoveryData: DiscoveryResponse;
  quantificationData: QuantificationResponse;
  narrativeData: NarrativeResponse;
  userFeedback: { approved: boolean; comments?: string };
  onNavigate: (step: number) => void;
  onCompositionComplete: (compositionData: ComposedBusinessCase) => void;
}

const Step4_Composition = ({
  discoveryData,
  quantificationData,
  narrativeData,
  userFeedback,
  onNavigate,
  onCompositionComplete
}: Step4CompositionProps) => {
  const [businessCase, setBusinessCase] = useState<ComposedBusinessCase | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedExportFormat, setSelectedExportFormat] = useState<'pdf' | 'docx' | 'presentation'>('pdf');
  const [isExporting, setIsExporting] = useState(false);
  const [activeSection, setActiveSection] = useState<string>('executive_summary');
  const [isPreviewMode, setIsPreviewMode] = useState(false);

  // Export format options
  const exportFormats = [
    { id: 'pdf', label: 'PDF Document', icon: FileText, description: 'Professional business case document' },
    { id: 'docx', label: 'Word Document', icon: FileDown, description: 'Editable Microsoft Word format' },
    { id: 'presentation', label: 'PowerPoint', icon: Presentation, description: 'Executive presentation slides' }
  ] as const;

  // Generate business case composition
  const handleGenerateBusinessCase = useCallback(async () => {
    if (!discoveryData || !quantificationData || !narrativeData) {
      setError('Missing required data for business case composition');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const composedCase = await b2bValueAPI.composeBusinessCase({
        discovery_data: discoveryData,
        quantification_data: quantificationData,
        narrative_data: narrativeData,
        document_template: 'enterprise_standard',
        export_format: selectedExportFormat,
        user_feedback: userFeedback // Include user feedback in composition
      });
      
      setBusinessCase(composedCase);
      onCompositionComplete(composedCase);
    } catch (err) {
      console.error('Error composing business case:', err);
      setError(err instanceof Error ? err.message : 'Failed to compose business case');
    } finally {
      setIsLoading(false);
    }
  }, [discoveryData, quantificationData, narrativeData, selectedExportFormat, userFeedback, onCompositionComplete]);

  // Export business case
  const handleExportBusinessCase = async () => {
    if (!businessCase) return;

    setIsExporting(true);
    try {
      // In a real implementation, this would trigger a download
      console.log('Exporting business case as:', selectedExportFormat);
      
      // Simulate export process
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Create a blob URL for download simulation
      const content = `${businessCase.title}\n\n${businessCase.executive_summary}\n\n${businessCase.introduction}`;
      const blob = new Blob([content], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = url;
      a.download = `business-case-${Date.now()}.${selectedExportFormat === 'presentation' ? 'pptx' : selectedExportFormat}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
    } catch (err) {
      console.error('Export error:', err);
      setError('Failed to export business case');
    } finally {
      setIsExporting(false);
    }
  };

  // Navigate to section
  const handleSectionNavigation = (sectionId: string) => {
    setActiveSection(sectionId);
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  // Generate business case on component mount
  useEffect(() => {
    if (!businessCase && !isLoading) {
      handleGenerateBusinessCase();
    }
  }, [businessCase, isLoading, handleGenerateBusinessCase]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader className="h-12 w-12 animate-spin text-blue-600 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Composing Your Business Case</h2>
          <p className="text-gray-600">Creating a comprehensive document with all your insights...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-600 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Composition Error</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={handleGenerateBusinessCase}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!businessCase) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">No Business Case Available</h2>
          <p className="text-gray-600">Unable to load the composed business case.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Business Case Composition</h1>
              <p className="text-gray-600 mt-1">Review and export your complete business case</p>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Preview Toggle */}
              <button
                onClick={() => setIsPreviewMode(!isPreviewMode)}
                className={`px-4 py-2 rounded-lg border transition-colors ${
                  isPreviewMode
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                <Eye className="h-4 w-4 inline mr-2" />
                {isPreviewMode ? 'Edit View' : 'Preview'}
              </button>

              {/* Export Button */}
              <button
                onClick={handleExportBusinessCase}
                disabled={isExporting}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isExporting ? (
                  <>
                    <Loader className="h-4 w-4 animate-spin inline mr-2" />
                    Exporting...
                  </>
                ) : (
                  <>
                    <Download className="h-4 w-4 inline mr-2" />
                    Export {selectedExportFormat.toUpperCase()}
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Table of Contents Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 sticky top-24">
              <h3 className="font-semibold text-gray-900 mb-4">Table of Contents</h3>
              <nav className="space-y-2">
                {businessCase.table_of_contents.map((section, index) => (
                  <button
                    key={index}
                    onClick={() => handleSectionNavigation(section.toLowerCase().replace(/\s+/g, '_'))}
                    className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                      activeSection === section.toLowerCase().replace(/\s+/g, '_')
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    {section}
                  </button>
                ))}
              </nav>

              {/* Export Format Selection */}
              <div className="mt-8 pt-6 border-t border-gray-200">
                <h4 className="font-medium text-gray-900 mb-3">Export Format</h4>
                <div className="space-y-2">
                  {exportFormats.map((format) => (
                    <label key={format.id} className="flex items-center">
                      <input
                        type="radio"
                        name="exportFormat"
                        value={format.id}
                        checked={selectedExportFormat === format.id}
                        onChange={(e) => setSelectedExportFormat(e.target.value as 'pdf' | 'docx' | 'presentation')}
                        className="h-4 w-4 text-blue-600"
                      />
                      <div className="ml-3">
                        <div className="flex items-center">
                          <format.icon className="h-4 w-4 text-gray-500 mr-2" />
                          <span className="text-sm font-medium text-gray-700">{format.label}</span>
                        </div>
                        <p className="text-xs text-gray-500 mt-1">{format.description}</p>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200">
              {/* Document Header */}
              <div className="p-8 border-b border-gray-200">
                <div className="text-center">
                  <h1 className="text-3xl font-bold text-gray-900 mb-4">{businessCase.title}</h1>
                  <div className="flex items-center justify-center space-x-6 text-sm text-gray-600">
                    <span>Created: {businessCase.metadata.created_date}</span>
                    <span>Version: {businessCase.metadata.version}</span>
                    <span>Pages: {businessCase.metadata.total_pages}</span>
                    <div className="flex items-center">
                      <span>Confidence: </span>
                      <div className={`ml-2 px-2 py-1 rounded-full text-xs ${
                        businessCase.metadata.confidence_score >= 0.8
                          ? 'bg-green-100 text-green-800'
                          : businessCase.metadata.confidence_score >= 0.6
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {Math.round(businessCase.metadata.confidence_score * 100)}%
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Document Sections */}
              <div className="p-8 space-y-8">
                {/* Executive Summary */}
                <section id="executive_summary" className={styles.documentSection}>
                  <h2 className="text-2xl font-bold text-gray-900 mb-4">Executive Summary</h2>
                  <div className="prose max-w-none">
                    {businessCase.executive_summary.split('\n').map((paragraph, index) => (
                      paragraph.trim() && (
                        <p key={index} className="mb-4 text-gray-700 leading-relaxed">
                          {paragraph}
                        </p>
                      )
                    ))}
                  </div>
                </section>

                {/* Introduction */}
                <section id="introduction" className={styles.documentSection}>
                  <h2 className="text-2xl font-bold text-gray-900 mb-4">Introduction</h2>
                  <div className="prose max-w-none">
                    {businessCase.introduction.split('\n').map((paragraph, index) => (
                      paragraph.trim() && (
                        <p key={index} className="mb-4 text-gray-700 leading-relaxed">
                          {paragraph}
                        </p>
                      )
                    ))}
                  </div>
                </section>

                {/* Value Drivers */}
                <section id="value_drivers_section" className={styles.documentSection}>
                  <h2 className="text-2xl font-bold text-gray-900 mb-4">Value Drivers</h2>
                  <div className="prose max-w-none">
                    {businessCase.value_drivers_section.split('\n').map((paragraph, index) => (
                      paragraph.trim() && (
                        <p key={index} className="mb-4 text-gray-700 leading-relaxed">
                          {paragraph}
                        </p>
                      )
                    ))}
                  </div>
                </section>

                {/* Financial Projections */}
                <section id="financial_projections_section" className={styles.documentSection}>
                  <h2 className="text-2xl font-bold text-gray-900 mb-4">Financial Projections</h2>
                  <div className="prose max-w-none">
                    {businessCase.financial_projections_section.split('\n').map((paragraph, index) => (
                      paragraph.trim() && (
                        <p key={index} className="mb-4 text-gray-700 leading-relaxed">
                          {paragraph}
                        </p>
                      )
                    ))}
                  </div>
                </section>

                {/* Risk Assessment */}
                <section id="risk_assessment_section" className={styles.documentSection}>
                  <h2 className="text-2xl font-bold text-gray-900 mb-4">Risk Assessment</h2>
                  <div className="prose max-w-none">
                    {businessCase.risk_assessment_section.split('\n').map((paragraph, index) => (
                      paragraph.trim() && (
                        <p key={index} className="mb-4 text-gray-700 leading-relaxed">
                          {paragraph}
                        </p>
                      )
                    ))}
                  </div>
                </section>

                {/* Implementation Roadmap */}
                <section id="implementation_roadmap" className={styles.documentSection}>
                  <h2 className="text-2xl font-bold text-gray-900 mb-4">Implementation Roadmap</h2>
                  <div className="prose max-w-none">
                    {businessCase.implementation_roadmap.split('\n').map((paragraph, index) => (
                      paragraph.trim() && (
                        <p key={index} className="mb-4 text-gray-700 leading-relaxed">
                          {paragraph}
                        </p>
                      )
                    ))}
                  </div>
                </section>

                {/* Conclusion */}
                <section id="conclusion" className={styles.documentSection}>
                  <h2 className="text-2xl font-bold text-gray-900 mb-4">Conclusion</h2>
                  <div className="prose max-w-none">
                    {businessCase.conclusion.split('\n').map((paragraph, index) => (
                      paragraph.trim() && (
                        <p key={index} className="mb-4 text-gray-700 leading-relaxed">
                          {paragraph}
                        </p>
                      )
                    ))}
                  </div>
                </section>

                {/* Appendices */}
                {businessCase.appendices.length > 0 && (
                  <section id="appendices" className={styles.documentSection}>
                    <h2 className="text-2xl font-bold text-gray-900 mb-4">Appendices</h2>
                    <div className="space-y-6">
                      {businessCase.appendices.map((appendix, index) => (
                        <div key={index} className="border-l-4 border-blue-500 pl-4">
                          <h3 className="font-semibold text-gray-900 mb-2">Appendix {String.fromCharCode(65 + index)}</h3>
                          <div className="prose max-w-none">
                            {appendix.split('\n').map((paragraph, pIndex) => (
                              paragraph.trim() && (
                                <p key={pIndex} className="mb-2 text-gray-700 leading-relaxed">
                                  {paragraph}
                                </p>
                              )
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </section>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Footer */}
      <div className="bg-white border-t border-gray-200 sticky bottom-0">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <button
              onClick={() => onNavigate(3)}
              className="flex items-center text-gray-600 hover:text-gray-900 transition-colors"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Narrative
            </button>

            <div className="flex items-center space-x-4">
              <div className="flex items-center text-green-600">
                <Check className="h-5 w-5 mr-2" />
                <span className="font-medium">Business Case Complete</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Step4_Composition;
