import { useState } from 'react';
import Sidebar from './components/Sidebar';
import Home from './components/Home';
import Assistant from './components/Assistant';

function App() {
  const [activeView, setActiveView] = useState('home');

  return (
    <div className="flex h-screen bg-gradient-to-br from-[#0b0f1a] to-[#0f172a] overflow-hidden">
      <Sidebar activeItem={activeView} onNavigate={setActiveView} />
      
      <main className="flex-1 relative">
        {activeView === 'home' && <Home />}
        {activeView === 'assistant' && <Assistant />}
        {activeView === 'documents' && (
          <div className="flex items-center justify-center h-full">
            <p className="text-gray-400 text-xl">Documents View</p>
          </div>
        )}
        {activeView === 'applications' && (
          <div className="flex items-center justify-center h-full">
            <p className="text-gray-400 text-xl">Applications View</p>
          </div>
        )}
        {activeView === 'chrome' && (
          <div className="flex items-center justify-center h-full">
            <p className="text-gray-400 text-xl">Chrome Sandbox View</p>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
