import { ArrowRight, LucideIcon } from 'lucide-react';

interface CardProps {
  icon: LucideIcon;
  title: string;
  description: string;
  onClick?: () => void;
}

export default function Card({ icon: Icon, title, description, onClick }: CardProps) {
  return (
    <button
      onClick={onClick}
      className="group relative bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-6 hover:bg-white/8 hover:shadow-[0_8px_30px_rgba(59,130,246,0.2)] hover:border-blue-500/30 transition-all duration-200 text-left w-full"
    >
      {/* Icon */}
      <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-600/20 flex items-center justify-center mb-4 group-hover:shadow-[0_0_20px_rgba(99,102,241,0.3)] transition-all duration-200">
        <Icon className="w-6 h-6 text-blue-400 group-hover:scale-110 transition-transform duration-200" />
      </div>

      {/* Content */}
      <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
      <p className="text-sm text-gray-400 mb-4">{description}</p>

      {/* Arrow */}
      <div className="absolute bottom-6 right-6 text-gray-500 group-hover:text-blue-400 transition-colors">
        <ArrowRight className="w-5 h-5" />
      </div>
    </button>
  );
}
