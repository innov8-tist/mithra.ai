import { useState, useEffect } from 'react';
import { Upload } from 'lucide-react';
import DocumentCard from './DocumentCard';
import Toast from './Toast';

interface Document {
  id: string;
  name: string;
  type: string;
  status: 'ready' | 'processing' | 'error';
  size: number;
}

interface ToastState {
  show: boolean;
  message: string;
  type: 'success' | 'downloading';
}

const API_BASE_URL = 'http://localhost:8000';

export default function Documents() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [toast, setToast] = useState<ToastState>({ show: false, message: '', type: 'success' });

  const showToast = (message: string, type: 'success' | 'downloading') => {
    setToast({ show: true, message, type });
    if (type === 'success') {
      setTimeout(() => setToast({ show: false, message: '', type: 'success' }), 3000);
    }
  };

  // Fetch documents on mount
  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/files`);
      const data = await response.json();
      
      const mappedDocs: Document[] = data.files.map((file: any, index: number) => ({
        id: `${index}`,
        name: file.name,
        type: getDocumentType(file.name),
        status: 'ready' as const,
        size: file.size,
      }));
      
      setDocuments(mappedDocs);
    } catch (error) {
      console.error('Failed to fetch documents:', error);
    }
  };

  const getDocumentType = (filename: string): string => {
    const lower = filename.toLowerCase();
    if (lower.includes('aadhaar') || lower.includes('aadhar')) return 'Aadhaar';
    if (lower.includes('pan')) return 'PAN';
    if (lower.includes('passport')) return 'Passport';
    if (lower.includes('license') || lower.includes('licence')) return 'License';
    if (lower.includes('voter')) return 'Voter ID';
    return 'Document';
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = Array.from(e.dataTransfer.files);
    await uploadFiles(files);
  };

  const uploadFiles = async (files: File[]) => {
    if (files.length === 0) return;
    
    setIsUploading(true);
    const formData = new FormData();
    
    files.forEach((file) => {
      formData.append('files', file);
    });

    try {
      const response = await fetch(`${API_BASE_URL}/upload`, {
        method: 'POST',
        body: formData,
      });
      
      if (response.ok) {
        await fetchDocuments();
        showToast('Files uploaded successfully!', 'success');
      }
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDownload = async (filename: string) => {
    showToast(`Downloading ${filename}...`, 'downloading');
    
    try {
      const encodedFilename = encodeURIComponent(filename);
      const response = await fetch(`${API_BASE_URL}/files/${encodedFilename}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const blob = await response.blob();
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      
      // Cleanup
      setTimeout(() => {
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      }, 100);
      
      showToast(`${filename} downloaded successfully!`, 'success');
    } catch (error) {
      console.error('Download failed:', error);
      showToast(`Failed to download ${filename}`, 'success');
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files) {
      uploadFiles(Array.from(files));
    }
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
            onClick={() => document.getElementById('file-input')?.click()}
            className={`mb-8 border-2 border-dashed rounded-2xl p-12 transition-all duration-300 cursor-pointer ${
              isDragging
                ? 'border-blue-500 bg-blue-500/10 shadow-[0_0_40px_rgba(59,130,246,0.3)]'
                : 'border-white/10 bg-white/5 hover:border-blue-500/50 hover:bg-white/8'
            }`}
          >
            <input
              id="file-input"
              type="file"
              multiple
              onChange={handleFileSelect}
              className="hidden"
              accept=".pdf,.jpg,.jpeg,.png,.bmp,.tiff,.gif,.txt,.md"
            />
            <div className="flex flex-col items-center">
              {/* Upload Icon */}
              <div className="mb-4 relative">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500/20 to-purple-600/20 flex items-center justify-center">
                  <Upload className={`w-8 h-8 text-blue-400 transition-transform duration-300 ${isDragging || isUploading ? 'scale-110' : ''} ${isUploading ? 'animate-pulse' : ''}`} />
                </div>
                {isDragging && (
                  <div className="absolute inset-0 rounded-2xl bg-blue-500/20 animate-pulse" />
                )}
              </div>

              {/* Text */}
              <h3 className="text-lg font-semibold text-white mb-2">
                {isUploading ? 'Uploading...' : 'Drop files here to upload'}
              </h3>
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
                  onDownload={handleDownload}
                />
              ))}
            </div>
          )}
        </div>
      </div>
      
      {/* Toast Notification */}
      {toast.show && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast({ show: false, message: '', type: 'success' })}
        />
      )}
    </div>
  );
}
