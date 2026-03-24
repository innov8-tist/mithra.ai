import { FileText, CheckCircle, Loader, AlertCircle, MoreVertical } from 'lucide-react';

interface Document {
  id: string;
  name: string;
  type: string;
  status: 'ready' | 'processing' | 'error';
}

interface DocumentCardProps {
  document: Document;
  index: number;
}

export default function DocumentCard({ document, index }: DocumentCardProps) {
  const statusConfig = {
    ready: {
      icon: CheckCircle,
      color: 'text-green-500',
      bgColor: 'bg-green-500/10',
      label: 'Ready',
    },
    processing: {
      icon: Loader,
      color: 'text-blue-500',
      bgColor: 'bg-blue-500/10',
      label: 'Processing',
    },
    error: {
      icon: AlertCircle,
      color: 'text-red-500',
      bgColor: 'bg-red-500/10',
      label: 'Error',
    },
  };

  const status = statusConfig[document.status];
  const StatusIcon = status.icon;

  return (
    <div
      className="group relative bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-6 hover:bg-white/8 hover:shadow-[0_8px_30px_rgba(59,130,246,0.2)] hover:border-blue-500/30 transition-all duration-300 animate-fadeInUp"
      style={{ animationDelay: `${index * 100}ms` }}
    >
      {/* Icon Container */}
      <div className="mb-4 flex items-center justify-center w-14 h-14">
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-600/20 flex items-center justify-center group-hover:shadow-[0_0_20px_rgba(99,102,241,0.3)] transition-all duration-200">
          <FileText className="w-6 h-6 text-blue-400 group-hover:scale-110 transition-transform duration-200" />
        </div>
      </div>

      {/* Document Info */}
      <h4 className="text-base font-semibold text-white mb-1 truncate">{document.name}</h4>
      <p className="text-xs text-gray-400 mb-4">{document.type}</p>

      {/* Status Badge */}
      <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full ${status.bgColor} ${status.color}`}>
        <StatusIcon className={`w-3.5 h-3.5 ${document.status === 'processing' ? 'animate-spin' : ''}`} />
        <span className="text-xs font-medium">{status.label}</span>
      </div>

      {/* More Options */}
      <button className="absolute top-4 right-4 p-2 rounded-lg text-gray-500 opacity-0 group-hover:opacity-100 hover:bg-white/10 hover:text-gray-300 transition-all duration-200">
        <MoreVertical className="w-4 h-4" />
      </button>
    </div>
  );
}
