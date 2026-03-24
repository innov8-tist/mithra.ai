interface QuickAction {
  id: string;
  label: string;
  icon: string;
}

const actions: QuickAction[] = [
  { id: 'passport', label: 'Apply for Passport', icon: '🌍' },
  { id: 'password', label: 'Reset Password', icon: '🔒' },
  { id: 'schemes', label: 'Check Schemes', icon: '📋' },
  { id: 'documents', label: 'Ask about Documents', icon: '📄' },
];

export default function QuickActions() {
  return (
    <div className="flex flex-wrap gap-3 justify-center">
      {actions.map((action) => (
        <button
          key={action.id}
          className="px-5 py-2.5 rounded-full bg-white/5 backdrop-blur-sm border border-white/10 text-sm text-gray-300 hover:bg-white/10 hover:border-blue-500/30 hover:text-white hover:scale-105 hover:shadow-[0_0_20px_rgba(59,130,246,0.15)] transition-all duration-200"
        >
          <span className="mr-2">{action.icon}</span>
          {action.label}
        </button>
      ))}
    </div>
  );
}
