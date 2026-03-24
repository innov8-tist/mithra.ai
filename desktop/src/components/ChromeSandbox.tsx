import { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/core';

function ChromeSandbox() {
  const [chromeMsg, setChromeMsg] = useState('');
  const [isLaunchingChrome, setIsLaunchingChrome] = useState(false);
  const [currentTabUrl, setCurrentTabUrl] = useState('');
  const [isMonitoring, setIsMonitoring] = useState(false);

  async function launchChrome() {
    setIsLaunchingChrome(true);
    setChromeMsg('Launching Chrome with CDP...');

    try {
      const result = await invoke('launch_chrome_with_cdp');
      setChromeMsg(result as string);
      setIsMonitoring(true);
    } catch (error) {
      setChromeMsg(`Error: ${error}`);
    } finally {
      setIsLaunchingChrome(false);
    }
  }

  async function getCurrentTab() {
    try {
      const result = await invoke('get_current_tab_url');
      const url = result as string;
      setCurrentTabUrl(url);
      console.log('Current Tab URL:', url);
    } catch (error) {
      setCurrentTabUrl(`Error: ${error}`);
    }
  }

  useEffect(() => {
    let interval: number | undefined;

    if (isMonitoring) {
      getCurrentTab();
      interval = window.setInterval(() => {
        getCurrentTab();
      }, 2000);
    }

    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [isMonitoring]);

  return (
    <div className="h-full flex flex-col items-center pt-12 px-8">
      <h1 className="text-3xl font-bold text-white mb-2">Chrome Sandbox</h1>
      <p className="text-gray-400 mb-10">Launch browser with CDP and auto-fill forms</p>

      <div className="flex gap-6 mb-8">
        <div
          onClick={!isLaunchingChrome ? launchChrome : undefined}
          className={`w-64 p-6 bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl hover:shadow-2xl transition-all cursor-pointer ${
            isLaunchingChrome ? 'opacity-50 cursor-not-allowed' : 'hover:scale-105'
          }`}
        >
          <div className="w-14 h-14 bg-white/20 rounded-xl flex items-center justify-center text-white mb-4">
            <GlobeIcon />
          </div>
          <h3 className="font-semibold text-white mb-2">Open Browser</h3>
          <p className="text-sm text-blue-100">
            {isLaunchingChrome ? 'Launching...' : 'Launch web browser with CDP'}
          </p>
        </div>

        <div className="w-64 p-6 bg-gradient-to-br from-purple-600 to-purple-700 rounded-xl hover:shadow-2xl transition-all cursor-pointer hover:scale-105">
          <div className="w-14 h-14 bg-white/20 rounded-xl flex items-center justify-center text-white mb-4">
            <MagicIcon />
          </div>
          <h3 className="font-semibold text-white mb-2">Magic Fill</h3>
          <p className="text-sm text-purple-100">Launch browser first</p>
        </div>
      </div>

      {chromeMsg && (
        <div className="w-full max-w-2xl mt-4 p-5 bg-blue-900/30 rounded-2xl border-2 border-blue-500/50 backdrop-blur-sm">
          <p className="font-semibold text-white mb-2">Chrome CDP Status:</p>
          <p className="text-gray-300 break-all whitespace-pre-wrap">{chromeMsg}</p>
        </div>
      )}

      {currentTabUrl && (
        <div className="w-full max-w-2xl mt-4 p-5 bg-blue-900/30 rounded-2xl border-2 border-blue-500/50 backdrop-blur-sm">
          <p className="font-semibold text-white mb-2">Current Active Tab:</p>
          <p className="text-gray-300 break-all">{currentTabUrl}</p>
          {isMonitoring && (
            <p className="mt-3 text-sm text-gray-400 italic flex items-center gap-2">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
              Live monitoring via CDP events
            </p>
          )}
        </div>
      )}
    </div>
  );
}

const GlobeIcon = () => (
  <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
  </svg>
);

const MagicIcon = () => (
  <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
  </svg>
);

export default ChromeSandbox;
