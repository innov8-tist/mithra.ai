import { MessageSquare, FileText, Grid } from 'lucide-react';
import Card from './Card';
import QuickActions from './QuickActions';

interface HomeProps {
  onNavigate: (view: string) => void;
}

export default function Home({ onNavigate }: HomeProps) {
  return (
    <div className="flex-1 flex items-center justify-center p-8">
      {/* Radial Glow Background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-blue-500/10 rounded-full blur-[120px]" />
      </div>

      {/* Main Content */}
      <div className="relative z-10 max-w-4xl w-full animate-fadeInUp">
        {/* Hero Section */}
        <div className="flex flex-col items-center mb-12">
          {/* Hero Icon */}
          <div className="mb-6 animate-pulse-glow">
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-[0_0_40px_rgba(99,102,241,0.4)]">
              <svg className="w-10 h-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
          </div>

          {/* Heading */}
          <h1 className="text-4xl font-bold text-white mb-3">Welcome back</h1>
          <p className="text-gray-400 text-lg">What would you like to do today?</p>
        </div>

        {/* Action Cards */}
        <div className="grid grid-cols-3 gap-6 mb-8">
          <Card
            icon={MessageSquare}
            title="Talk to Assistant"
            description="Ask questions or get things done"
            onClick={() => onNavigate('assistant')}
          />
          <Card
            icon={FileText}
            title="My Documents"
            description="Upload and manage your documents"
            onClick={() => onNavigate('documents')}
          />
          <Card
            icon={Grid}
            title="My Applications"
            description="Track your submissions"
            onClick={() => onNavigate('applications')}
          />
        </div>

        {/* Quick Actions */}
        <QuickActions />
      </div>
    </div>
  );
}
