import { CheckCircle, Download, X } from 'lucide-react';

interface ToastProps {
  message: string;
  type: 'success' | 'downloading';
  onClose: () => void;
}

export default function Toast({ message, type, onClose }: ToastProps) {
  return (
    <div className="fixed bottom-6 right-6 z-50 animate-fadeInUp">
      <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-xl px-5 py-4 shadow-[0_8px_30px_rgba(0,0,0,0.4)] flex items-center gap-3 min-w-[300px]">
        {type === 'downloading' && (
          <div className="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center">
            <Download className="w-5 h-5 text-blue-400 animate-pulse" />
          </div>
        )}
        {type === 'success' && (
          <div className="w-10 h-10 rounded-full bg-green-500/20 flex items-center justify-center">
            <CheckCircle className="w-5 h-5 text-green-400" />
          </div>
        )}
        
        <p className="flex-1 text-white text-sm font-medium">{message}</p>
        
        <button
          onClick={onClose}
          className="p-1 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-all duration-200"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
