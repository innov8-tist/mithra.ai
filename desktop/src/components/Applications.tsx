import { useState } from 'react';

interface Application {
  id: string;
  name: string;
  date: string;
  status: 'completed' | 'processing' | 'submitted';
}

export default function Applications() {
  const [applications] = useState<Application[]>([
    { id: '1', name: 'Passport Application', date: 'March 15, 2026', status: 'completed' },
    { id: '2', name: 'PAN Card Correction', date: 'March 18, 2026', status: 'processing' },
    { id: '3', name: 'Driving License Renewal', date: 'March 22, 2026', status: 'submitted' },
    { id: '4', name: 'Voter ID Registration', date: 'March 23, 2026', status: 'processing' },
  ]);

  const statusConfig = {
    completed: {
      color: 'text-green-500',
      bgColor: 'bg-green-500/10',
      label: 'Completed',
    },
    processing: {
      color: 'text-blue-500',
      bgColor: 'bg-blue-500/10',
      label: 'Processing',
    },
    submitted: {
      color: 'text-yellow-500',
      bgColor: 'bg-yellow-500/10',
      label: 'Submitted',
    },
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-8 py-6 border-b border-white/5">
        <h1 className="text-2xl font-bold text-white">Applications</h1>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto px-8 py-8">
        <div className="max-w-5xl mx-auto animate-fadeInUp">
          {/* Table Container */}
          <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl overflow-hidden">
            {/* Table Header */}
            <div className="grid grid-cols-[2fr_1fr_1fr] gap-6 px-6 py-4 border-b border-white/10 bg-white/5">
              <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Application
              </div>
              <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Date
              </div>
              <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Status
              </div>
            </div>

            {/* Table Body */}
            <div>
              {applications.map((app, index) => {
                const status = statusConfig[app.status];
                
                return (
                  <div
                    key={app.id}
                    className="grid grid-cols-[2fr_1fr_1fr] gap-6 px-6 py-5 border-b border-white/5 hover:bg-white/5 transition-all duration-200 animate-fadeInUp"
                    style={{ animationDelay: `${index * 100}ms` }}
                  >
                    {/* Application Name */}
                    <div className="text-white font-medium">{app.name}</div>

                    {/* Date */}
                    <div className="text-gray-400 text-sm">{app.date}</div>

                    {/* Status Badge */}
                    <div>
                      <span className={`inline-flex items-center px-3 py-1.5 rounded-full text-xs font-medium ${status.bgColor} ${status.color}`}>
                        {status.label}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
