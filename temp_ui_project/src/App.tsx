import React, { useState } from 'react';
import { LayoutDashboard, FilePlus, BrainCircuit, Calculator, Briefcase, FileText, BarChart2, Settings } from 'lucide-react';
import AnalysisForm from './components/AnalysisForm';
import AnalysisResults from './components/AnalysisResults';

// Placeholder components for views that are not yet fully implemented
const PlaceholderView = ({ title }: { title: string }) => (
  <div className="p-6">
    <h1 className="text-3xl font-bold">{title}</h1>
    <p className="mt-4 text-gray-600">This feature is under construction.</p>
  </div>
);

const DashboardView = () => (
    <div className="p-6">
        <h1 className="text-3xl font-bold text-gray-800 mb-6">Welcome back, John!</h1>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-white p-6 rounded-lg shadow-md">
                <h3 className="font-semibold text-lg mb-2">Create Business Case</h3>
                <p className="text-sm text-gray-600 mb-4">Start a new value analysis.</p>
                <button className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700">Create Case</button>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-md">
                <h3 className="font-semibold text-lg mb-2">Use a Template</h3>
                <p className="text-sm text-gray-600 mb-4">Jumpstart analysis with templates.</p>
                <button className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700">Use Template</button>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-md">
                <h3 className="font-semibold text-lg mb-2">View Recent</h3>
                <p className="text-sm text-gray-600 mb-4">Access your recent analyses.</p>
                <button className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700">View Recent</button>
            </div>
        </div>
    </div>
);

const AiAnalysisView = () => {
  const [analysisResults, setAnalysisResults] = useState(null);

  return (
    <div className="p-6">
      {!analysisResults ? (
        <AnalysisForm onAnalysisComplete={setAnalysisResults} />
      ) : (
        <AnalysisResults results={analysisResults} />
      )}
    </div>
  );
};

const NavItem = ({ icon, label, active, onClick }: { icon: React.ElementType, label: string, active: boolean, onClick: () => void }) => (
  <button
    onClick={onClick}
    className={`flex items-center w-full text-left px-4 py-2.5 rounded-md text-sm font-medium transition-colors ${
      active ? 'bg-green-200 text-green-800' : 'text-gray-600 hover:bg-gray-100'
    }`}
  >
    {React.createElement(icon, { className: 'w-5 h-5 mr-3' })}
    {label}
  </button>
);

function App() {
  const [activeView, setActiveView] = useState('dashboard');

  const renderView = () => {
    switch (activeView) {
      case 'dashboard': return <DashboardView />;
      case 'analysis': return <AiAnalysisView />;
      // Using placeholders for other views
      case 'intake': return <PlaceholderView title="Project Intake" />;
      case 'roi': return <PlaceholderView title="ROI Calculator" />;
      case 'builder': return <PlaceholderView title="Business Case Builder" />;
      case 'templates': return <PlaceholderView title="Templates" />;
      case 'reports': return <PlaceholderView title="Reports" />;
      case 'settings': return <PlaceholderView title="Settings" />;
      default: return <DashboardView />;
    }
  };

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'intake', label: 'Project Intake', icon: FilePlus },
    { id: 'analysis', label: 'AI Analysis Results', icon: BrainCircuit },
    { id: 'roi', label: 'ROI Calculator', icon: Calculator },
    { id: 'builder', label: 'Business Case Builder', icon: Briefcase },
    { id: 'templates', label: 'Templates', icon: FileText },
    { id: 'reports', label: 'Reports', icon: BarChart2 },
  ];

  return (
    <div className="flex h-screen bg-gray-50 font-sans">
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="px-6 py-4">
          <h1 className="text-xl font-bold text-gray-800">B2BValue GTM Interface</h1>
        </div>
        <nav className="flex-1 px-4 py-2 space-y-1">
          {navItems.map(item => (
            <NavItem
              key={item.id}
              icon={item.icon}
              label={item.label}
              active={activeView === item.id}
              onClick={() => setActiveView(item.id)}
            />
          ))}
        </nav>
        <div className="px-4 py-2">
           <NavItem
              icon={Settings}
              label="Settings"
              active={activeView === 'settings'}
              onClick={() => setActiveView('settings')}
            />
        </div>
      </aside>

      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="bg-white border-b border-gray-200">
          <div className="flex items-center justify-between h-16 px-6">
            <div />
            <div className="flex items-center">
              <span className="text-sm mr-4 text-gray-600">Welcome, GTM Team!</span>
              <div className="w-9 h-9 bg-gray-300 rounded-full flex items-center justify-center font-bold text-gray-600">J</div>
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-50">
          {renderView()}
        </main>
      </div>
    </div>
  );
}

export default App;
