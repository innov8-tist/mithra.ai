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
              <svg className="w-12 h-12" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                {/* Circle on top */}
                <circle cx="50" cy="20" r="8" fill="white" />
                {/* M shape with person silhouette */}
                <path d="M20 40 Q20 35 25 35 L35 35 Q40 35 40 40 L40 80 Q40 85 35 85 L25 85 Q20 85 20 80 Z" fill="white" opacity="0.9" />
                <path d="M60 40 Q60 35 65 35 L75 35 Q80 35 80 40 L80 80 Q80 85 75 85 L65 85 Q60 85 60 80 Z" fill="white" opacity="0.9" />
                <path d="M35 50 Q50 65 65 50" stroke="white" strokeWidth="8" fill="none" strokeLinecap="round" />
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
