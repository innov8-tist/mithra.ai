import { Home, MessageSquare, FileText, Grid, Globe } from 'lucide-react';

interface SidebarProps {
  activeItem: string;
  onNavigate: (item: string) => void;
}

export default function Sidebar({ activeItem, onNavigate }: SidebarProps) {
  const navItems = [
    { id: 'home', label: 'Home', icon: Home },
    { id: 'assistant', label: 'Assistant', icon: MessageSquare },
    { id: 'documents', label: 'Documents', icon: FileText },
    { id: 'applications', label: 'Applications', icon: Grid },
    { id: 'chrome', label: 'Chrome Sandbox', icon: Globe },
  ];

  return (
    <aside className="w-60 h-screen bg-[#0a0e17] border-r border-white/5 flex flex-col">
      {/* App Header */}
      <div className="p-6 flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center">
          <svg className="w-8 h-8" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
            {/* Circle on top */}
            <circle cx="50" cy="20" r="8" fill="url(#gradient1)" />
            {/* M shape with person silhouette */}
            <path d="M20 40 Q20 35 25 35 L35 35 Q40 35 40 40 L40 80 Q40 85 35 85 L25 85 Q20 85 20 80 Z" fill="url(#gradient2)" />
            <path d="M60 40 Q60 35 65 35 L75 35 Q80 35 80 40 L80 80 Q80 85 75 85 L65 85 Q60 85 60 80 Z" fill="url(#gradient3)" />
            <path d="M35 50 Q50 65 65 50" stroke="url(#gradient4)" strokeWidth="8" fill="none" strokeLinecap="round" />
            <defs>
              <linearGradient id="gradient1" x1="50" y1="12" x2="50" y2="28" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stopColor="#a78bfa" />
                <stop offset="100%" stopColor="#7dd3fc" />
              </linearGradient>
              <linearGradient id="gradient2" x1="20" y1="35" x2="40" y2="85" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stopColor="#8b5cf6" />
                <stop offset="100%" stopColor="#6366f1" />
              </linearGradient>
              <linearGradient id="gradient3" x1="60" y1="35" x2="80" y2="85" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stopColor="#06b6d4" />
                <stop offset="100%" stopColor="#3b82f6" />
              </linearGradient>
              <linearGradient id="gradient4" x1="35" y1="50" x2="65" y2="50" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stopColor="#8b5cf6" />
                <stop offset="50%" stopColor="#6366f1" />
                <stop offset="100%" stopColor="#06b6d4" />
              </linearGradient>
            </defs>
          </svg>
        </div>
        <span className="text-lg font-semibold text-white">Mitra.ai</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeItem === item.id;
          
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl mb-2 transition-all duration-200 ${
                isActive
                  ? 'bg-blue-500/10 text-blue-400 shadow-[0_0_20px_rgba(59,130,246,0.15)]'
                  : 'text-gray-400 hover:text-gray-300 hover:bg-white/5'
              }`}
            >
              <Icon className="w-5 h-5" />
              <span className="font-medium">{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* User Section */}
      <div className="p-4 border-t border-white/5">
        <div className="flex items-center gap-3 px-2 py-2">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gray-600 to-gray-800 flex items-center justify-center text-sm font-semibold text-white">
            U
          </div>
          <span className="text-sm text-gray-300">User</span>
        </div>
      </div>
    </aside>
  );
}
