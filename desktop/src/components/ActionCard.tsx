interface ActionCardProps {
  icon: string;
  title: string;
  description: string;
  onClick?: () => void;
}

export default function ActionCard({ icon, title, description, onClick }: ActionCardProps) {
  return (
    <button
      onClick={onClick}
      className="group relative bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-5 hover:bg-white/8 hover:shadow-[0_4px_20px_rgba(59,130,246,0.2)] hover:border-blue-500/30 transition-all duration-200 text-left"
    >
      {/* Icon */}
      <div className="text-3xl mb-3 flex items-center justify-center w-12 h-12">
        <span className="group-hover:scale-110 transition-transform duration-200 inline-block">
          {icon}
        </span>
      </div>

      {/* Content */}
      <h4 className="text-base font-semibold text-white mb-1">{title}</h4>
      <p className="text-xs text-gray-400">{description}</p>
    </button>
  );
}
