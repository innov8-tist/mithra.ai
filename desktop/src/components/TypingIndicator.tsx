export default function TypingIndicator() {
  return (
    <div className="flex justify-start animate-fadeInUp">
      <div className="bg-white/5 backdrop-blur-sm border border-white/10 text-gray-200 px-5 py-3 rounded-2xl">
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
          <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
          <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
      </div>
    </div>
  );
}
