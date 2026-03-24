import { useState } from 'react';
import Sidebar from './components/Sidebar';
import Home from './components/Home';
import ChromeSandbox from './components/ChromeSandbox';
import Assistant from './components/Assistant';
import Documents from './components/Documents';
import Applications from './components/Applications';

function App() {
  const [activeView, setActiveView] = useState('home');

  return (
    <div className="flex h-screen bg-gradient-to-br from-[#0b0f1a] to-[#0f172a] overflow-hidden">
      <Sidebar activeItem={activeView} onNavigate={setActiveView} />
      
      <main className="flex-1 relative">
        {activeView === 'home' && <Home onNavigate={setActiveView} />}
        {activeView === 'assistant' && <Assistant />}
        {activeView === 'documents' && <Documents />}
        {activeView === 'applications' && <Applications />}
        {activeView === 'chrome' && <ChromeSandbox />}
      </main>
    </div>
  );
}

export default App;
