import { useState, useEffect, useCallback } from 'react';
import { FileText, Bot, Loader, CheckCircle, AlertCircle, ArrowLeft, ArrowRight } from 'lucide-react';
import { NarrativeResponse, DiscoveryResponse, QuantificationResponse, b2bValueAPI } from '../../services/b2bValueApi';
import styles from './Step3_NarrativeGeneration.module.css';

interface Step3NarrativeGenerationProps {
  discoveryData: DiscoveryResponse;
  quantificationData: QuantificationResponse;
  onNavigate: (step: number) => void;
  onNarrativeComplete: (narrativeData: NarrativeResponse, userFeedback: { approved: boolean; comments?: string }) => void;
}

const Step3_NarrativeGeneration = ({ 
  discoveryData, 
  quantificationData, 
  onNavigate, 
  onNarrativeComplete 
}: Step3NarrativeGenerationProps) => {
  const [narrative, setNarrative] = useState<NarrativeResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [userApproved, setUserApproved] = useState<boolean | null>(null);
  const [feedbackComments, setFeedbackComments] = useState<string>('');
  const [showFeedbackForm, setShowFeedbackForm] = useState(false);

  // Helper functions for confidence display
  const getConfidenceColor = (score: number): string => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getConfidenceLabel = (score: number): string => {
    if (score >= 0.8) return 'High Confidence';
    if (score >= 0.6) return 'Moderate Confidence';
    return 'Low Confidence';
  };

  // Generate narrative
  const handleGenerateNarrative = useCallback(async () => {
    if (!discoveryData || !quantificationData) {
      setError('Missing required data for narrative generation');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const narrativeData = await b2bValueAPI.generateNarrative({
        discovery_data: discoveryData,
        quantification_data: quantificationData,
        target_audience: ['executives', 'finance'],
        narrative_style: 'executive'
      });
      
      setNarrative(narrativeData);
    } catch (err) {
      console.error('Error generating narrative:', err);
      setError(err instanceof Error ? err.message : 'Failed to generate narrative');
    } finally {
      setIsLoading(false);
    }
  }, [discoveryData, quantificationData]);

  // Approve narrative
  const handleApproveNarrative = () => {
    setUserApproved(true);
    setShowFeedbackForm(false);
    
    if (narrative) {
      onNarrativeComplete(narrative, { 
        approved: true, 
        comments: feedbackComments || undefined 
      });
    }
  };

  // Reject narrative and show feedback form
  const handleRejectNarrative = () => {
    setUserApproved(false);
    setShowFeedbackForm(true);
  };

  // Submit feedback and request regeneration
  const handleSubmitFeedback = () => {
    setShowFeedbackForm(false);
    setUserApproved(null);
    // Could trigger regeneration with feedback here
    handleGenerateNarrative();
  };

  // Generate narrative on component mount
  useEffect(() => {
    if (discoveryData && quantificationData && !narrative && !isLoading) {
      handleGenerateNarrative();
    }
  }, [discoveryData, quantificationData, narrative, isLoading, handleGenerateNarrative]);

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center mb-4">
          <FileText className="h-8 w-8 text-blue-600 mr-3" />
          <h2 className="text-2xl font-bold text-gray-900">Phase 3: Narrative Generation</h2>
        </div>
        <p className="text-gray-600 text-lg">
          AI-powered narrative creation to transform your data into a compelling business story.
        </p>
      </div>

      {/* Development Mode Indicator */}
      {import.meta.env.DEV && (
        <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
          <div className="flex items-center">
            <AlertCircle className="h-5 w-5 text-amber-600 mr-2" />
            <span className="text-amber-800 text-sm font-medium">
              Development Mode: Using mock narrative data
            </span>
          </div>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="text-center py-12">
          <Loader className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Generating Narrative</h3>
          <p className="text-gray-600">AI is crafting your business case narrative...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center">
            <AlertCircle className="h-5 w-5 text-red-600 mr-2" />
            <span className="text-red-800">{error}</span>
          </div>
          <button
            onClick={handleGenerateNarrative}
            className="mt-3 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
          >
            Retry Generation
          </button>
        </div>
      )}

      {/* Generated Narrative */}
      {narrative && (
        <div className="space-y-6">
          {/* Narrative Content */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Generated Narrative</h3>
              <div className="flex items-center space-x-2">
                <Bot className="h-5 w-5 text-blue-600" />
                <span className="text-sm text-gray-500">AI Generated</span>
                <button
                  onClick={handleGenerateNarrative}
                  disabled={isLoading}
                  className="text-sm bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-md disabled:opacity-50"
                >
                  Regenerate
                </button>
              </div>
            </div>
            
            <div className="prose max-w-none mb-6">
              <p className="text-gray-700 leading-relaxed whitespace-pre-line">
                {narrative.narrative_text}
              </p>
            </div>

            {/* Key Points */}
            <div className="mb-6">
              <h4 className="text-sm font-medium text-gray-900 mb-3">Key Points</h4>
              <ul className="space-y-2">
                {narrative.key_points.map((point: string, index: number) => (
                  <li key={index} className="flex items-start">
                    <CheckCircle className="h-5 w-5 text-green-500 mr-2 mt-0.5" />
                    <span className="text-gray-700">{point}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* AI Critique Panel */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">AI Analysis & Critique</h3>
            
            <div className="space-y-6">
              {/* Confidence Score */}
              <div className="mb-6">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Confidence Score</span>
                  <span className={`text-sm font-semibold ${getConfidenceColor(narrative.ai_critique.confidence_score)}`}>
                    {Math.round(narrative.ai_critique.confidence_score * 100)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={styles.progressBar}
                    style={{ '--progress-width': `${narrative.ai_critique.confidence_score * 100}%` } as React.CSSProperties}
                  />
                </div>
                <p className={`text-xs mt-1 ${getConfidenceColor(narrative.ai_critique.confidence_score)}`}>
                  {getConfidenceLabel(narrative.ai_critique.confidence_score)}
                </p>
              </div>

              {/* Critique Summary */}
              <div className="mb-6">
                <h4 className="text-sm font-medium text-gray-900 mb-2">Summary</h4>
                <p className="text-sm text-gray-600 leading-relaxed">
                  {narrative.ai_critique.critique_summary}
                </p>
              </div>

              {/* Strengths */}
              <div className="mb-6">
                <h4 className="text-sm font-medium text-gray-900 mb-2">Strengths</h4>
                <ul className="space-y-1">
                  {narrative.ai_critique.strengths.map((strength: string, index: number) => (
                    <li key={index} className="flex items-start">
                      <CheckCircle className="h-4 w-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                      <span className="text-sm text-gray-600">{strength}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Areas for Improvement */}
              <div className="mb-6">
                <h4 className="text-sm font-medium text-gray-900 mb-2">Areas for Improvement</h4>
                <ul className="space-y-1">
                  {narrative.ai_critique.areas_for_improvement.map((area: string, index: number) => (
                    <li key={index} className="flex items-start">
                      <AlertCircle className="h-4 w-4 text-amber-500 mr-2 mt-0.5 flex-shrink-0" />
                      <span className="text-sm text-gray-600">{area}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Suggestions */}
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-2">Suggestions</h4>
                <ul className="space-y-1">
                  {narrative.ai_critique.suggestions.map((suggestion: string, index: number) => (
                    <li key={index} className="flex items-start">
                      <Bot className="h-4 w-4 text-blue-500 mr-2 mt-0.5 flex-shrink-0" />
                      <span className="text-sm text-gray-600">{suggestion}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          {/* User Feedback Form */}
          {showFeedbackForm && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Provide Feedback</h3>
              <div className="space-y-4">
                <div>
                  <label htmlFor="feedback" className="block text-sm font-medium text-gray-700 mb-2">
                    What would you like to improve in the narrative?
                  </label>
                  <textarea
                    id="feedback"
                    rows={4}
                    value={feedbackComments}
                    onChange={(e) => setFeedbackComments(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Share your thoughts on how to improve the narrative..."
                  />
                </div>
                <div className="flex space-x-3">
                  <button
                    onClick={handleSubmitFeedback}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    Submit Feedback & Regenerate
                  </button>
                  <button
                    onClick={() => setShowFeedbackForm(false)}
                    className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Approval Actions */}
          {!showFeedbackForm && userApproved === null && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Review & Approve</h3>
              <p className="text-gray-600 mb-4">
                Please review the generated narrative and provide your feedback.
              </p>
              <div className="flex space-x-3">
                <button
                  onClick={handleApproveNarrative}
                  className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                >
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Approve Narrative
                </button>
                <button
                  onClick={handleRejectNarrative}
                  className="flex items-center px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
                >
                  <AlertCircle className="h-4 w-4 mr-2" />
                  Request Changes
                </button>
              </div>
            </div>
          )}

          {/* Approval Confirmation */}
          {userApproved === true && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-6">
              <div className="flex items-center">
                <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
                <span className="text-green-800 font-medium">Narrative approved and ready for composition!</span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Navigation */}
      <div className="flex justify-between mt-8 pt-6 border-t border-gray-200">
        <button
          onClick={() => onNavigate(2)}
          className="flex items-center px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Quantification
        </button>
        
        {narrative && userApproved === true && (
          <button
            onClick={() => onNavigate(4)}
            className="flex items-center px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Continue to Composition
            <ArrowRight className="h-4 w-4 ml-2" />
          </button>
        )}
      </div>

      {/* Summary Card for other phases */}
      {narrative && userApproved !== true && (
        <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-800">
            <Bot className="h-4 w-4 inline mr-1" />
            AI Confidence: <span className={getConfidenceColor(narrative.ai_critique.confidence_score)}>
              {Math.round(narrative.ai_critique.confidence_score * 100)}%
            </span>
            {narrative.ai_critique.critique_summary && (
              <span> • {narrative.ai_critique.critique_summary.slice(0, 100)}...</span>
            )}
          </p>
        </div>
      )}
    </div>
  );
};

export default Step3_NarrativeGeneration;
