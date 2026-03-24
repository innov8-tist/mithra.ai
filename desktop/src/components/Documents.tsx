import { useState } from 'react';
import { Upload } from 'lucide-react';
import DocumentCard from './DocumentCard';

interface Document {
  id: string;
  name: string;
  type: string;
  status: 'ready' | 'processing' | 'error';
}

export default function Documents() {
  const [documents, setDocuments] = useState<Document[]>([
    { id: '1', name: 'Aadhaar_Card.pdf', type: 'Aadhaar', status: 'ready' },
    { id: '2', name: 'PAN_Card.jpg', type: 'PAN', status: 'ready' },
    { id: '3', name: 'Passport_Scan.pdf', type: 'Passport', status: 'processing' },
  ]);
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    // Handle file upload logic here
    console.log('Files dropped:', e.dataTransfer.files);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-8 py-6 border-b border-white/5">
        <h1 className="text-2xl font-bold text-white">Documents</h1>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto px-8 py-8">
        <div className="max-w-6xl mx-auto animate-fadeInUp">
          {/* Upload Area */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`mb-8 border-2 border-dashed rounded-2xl p-12 transition-all duration-300 ${
              isDragging
                ? 'border-blue-500 bg-blue-500/10 shadow-[0_0_40px_rgba(59,130,246,0.3)]'
                : 'border-white/10 bg-white/5 hover:border-blue-500/50 hover:bg-white/8'
            }`}
          >
            <div className="flex flex-col items-center">
              {/* Upload Icon */}
              <div className="mb-4 relative">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500/20 to-purple-600/20 flex items-center justify-center">
                  <Upload className={`w-8 h-8 text-blue-400 transition-transform duration-300 ${isDragging ? 'scale-110' : ''}`} />
                </div>
                {isDragging && (
                  <div className="absolute inset-0 rounded-2xl bg-blue-500/20 animate-pulse" />
                )}
              </div>

              {/* Text */}
              <h3 className="text-lg font-semibold text-white mb-2">Drop files here to upload</h3>
              <p className="text-sm text-gray-400">
                Supports PDF, JPG, PNG — Aadhaar, PAN, Passport, and more
              </p>
            </div>
          </div>

          {/* Documents Grid */}
          {documents.length > 0 && (
            <div className="grid grid-cols-3 gap-6">
              {documents.map((doc, index) => (
                <DocumentCard
                  key={doc.id}
                  document={doc}
                  index={index}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
