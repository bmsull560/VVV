declare module './components/AnalysisForm' {
  import React from 'react';
  const AnalysisForm: React.FC<{ onAnalysisStarted: (id: string) => void }>;
  export default AnalysisForm;
}

declare module './components/AnalysisResults' {
  import React from 'react';
  const AnalysisResults: React.FC<{ analysisId: string | null }>;
  export default AnalysisResults;
}
