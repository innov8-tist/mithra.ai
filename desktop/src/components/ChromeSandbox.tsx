import { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/core';

function ChromeSandbox() {
  const [chromeMsg, setChromeMsg] = useState('');
  const [isLaunchingChrome, setIsLaunchingChrome] = useState(false);
  const [currentTabUrl, setCurrentTabUrl] = useState('');
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [isMagicFilling, setIsMagicFilling] = useState(false);
  const [magicFillStatus, setMagicFillStatus] = useState<string | null>(null);
  const [formFieldCount, setFormFieldCount] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [liveQueryStatus, setLiveQueryStatus] = useState<string | null>(null);

  async function launchChrome() {
    setIsLaunchingChrome(true);
    setChromeMsg('Launching Chrome with CDP...');

    try {
      const result = await invoke('launch_chrome_with_cdp');
      setChromeMsg(result as string);
      setIsMonitoring(true);
      console.log('Chrome launched, monitoring started');
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

  async function injectMagicFillButton() {
    try {
      const result = await invoke<string>('inject_magic_fill_button');
      const data = JSON.parse(result);
      if (data.injected) {
        console.log(`Magic Fill button injected - ${data.fieldCount} fields detected`);
        setFormFieldCount(data.fieldCount);
      } else {
        console.log('No forms detected, button not injected');
        setFormFieldCount(0);
      }
    } catch (error) {
      console.log('Button injection error:', error);
    }
  }

  async function injectVoiceButton() {
    try {
      const result = await invoke<string>('inject_voice_button');
      const data = JSON.parse(result);
      if (data.injected) {
        console.log('Voice button injected');
      }
    } catch (error) {
      console.log('Voice button injection error:', error);
    }
  }

  async function handleMagicFill() {
    setIsMagicFilling(true);
    setMagicFillStatus('Capturing screenshot...');

    try {
      // Step 1: Capture screenshot via CDP
      const screenshotB64 = await invoke<string>('capture_screenshot');
      setMagicFillStatus('Extracting form fields...');

      // Step 2: Extract DOM fields via CDP
      const fields = await invoke<any[]>('extract_form_fields');
      setMagicFillStatus(`Found ${fields.length} fields. Analyzing with AI...`);

      // Step 3: Send to backend for Gemini Vision + RAG lookup
      const response = await fetch('http://localhost:8000/vision-magicfill', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          screenshot_b64: screenshotB64,
          fields: fields,
          url: currentTabUrl,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.error) {
          setMagicFillStatus(`Error: ${data.error}`);
        } else if (data.fill_data && data.fill_data.length > 0) {
          setMagicFillStatus(`Filling ${data.fill_data.length} fields...`);

          // Step 4: Fill the form via CDP
          const fillResult = await invoke<string>('fill_form_fields', {
            fillData: data.fill_data,
          });

          setMagicFillStatus(`✅ ${fillResult}`);
        } else {
          setMagicFillStatus('No matching data found in your documents');
        }
      } else {
        setMagicFillStatus(`Failed: ${response.statusText}`);
      }
    } catch (error) {
      setMagicFillStatus(`Error: ${error}`);
    } finally {
      setIsMagicFilling(false);
    }
  }

  useEffect(() => {
    let urlInterval: number | undefined;
    let clickInterval: number | undefined;
    let voiceInterval: number | undefined;

    if (isMonitoring) {
      console.log('Starting monitoring intervals...');
      getCurrentTab();
      injectMagicFillButton();
      injectVoiceButton();

      urlInterval = window.setInterval(() => {
        getCurrentTab();
        injectMagicFillButton();
        injectVoiceButton();
      }, 2000);

      // Start checking for button clicks
      clickInterval = window.setInterval(async () => {
        try {
          const clicked = await invoke<boolean>('check_magic_fill_clicked');
          if (clicked && !isMagicFilling) {
            console.log('Magic Fill button clicked in webpage! Triggering fill...');
            handleMagicFill();
          }
        } catch (error) {
          // Silently ignore errors when button not injected yet
        }
      }, 500);

      // Monitor voice recording state
      voiceInterval = window.setInterval(async () => {
        try {
          const recording = await invoke<boolean>('check_voice_recording_state');

          // Detect when recording stops
          if (isRecording && !recording) {
            console.log('Recording stopped, retrieving audio...');
            setIsRecording(false);
            setLiveQueryStatus('🎤 Processing voice...');

            // Wait a bit for audio to be ready
            await new Promise(resolve => setTimeout(resolve, 500));

            try {
              const audioBase64 = await invoke<string>('get_recorded_audio');

              if (audioBase64) {
                console.log('Transcribing...');
                setLiveQueryStatus('🔄 Transcribing audio...');

                // Send to backend for transcription
                const response = await fetch('http://localhost:8000/voice-transcribe', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({
                    audio_base64: audioBase64,
                    language_code: 'auto'  // Auto-detect Malayalam or English
                  })
                });

                if (response.ok) {
                  const data = await response.json();
                  if (data.success) {
                    console.log('✅ Transcription successful!');
                    console.log('Language:', data.language);
                    console.log('Original:', data.transcribed_text);
                    if (data.translated_text !== data.transcribed_text) {
                      console.log('English:', data.translated_text);
                    }

                    setLiveQueryStatus(`📝 "${data.translated_text}"`);

                    // Now capture screenshot and send to live-query endpoint
                    console.log('📸 Capturing screenshot for live query...');
                    setLiveQueryStatus('📸 Analyzing page...');
                    const screenshotB64 = await invoke<string>('capture_screenshot');

                    // Extract form fields for better matching
                    const formFields = await invoke<any[]>('extract_form_fields');
                    console.log('Extracted form fields for live query:', formFields.length);

                    // Send to live-query endpoint
                    console.log('\n' + '='.repeat(60));
                    console.log('SENDING TO LIVE QUERY ENDPOINT');
                    console.log('='.repeat(60));
                    console.log('Query:', data.translated_text);
                    console.log('Screenshot length:', screenshotB64.length, 'chars');
                    console.log('Form fields:', formFields.length);
                    
                    const liveQueryResponse = await fetch('http://localhost:8000/live-query', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        screenshot_b64: screenshotB64,
                        query: data.translated_text,
                        fields: formFields  // Send extracted fields
                      })
                    });

                    if (liveQueryResponse.ok) {
                      const liveData = await liveQueryResponse.json();
                      
                      console.log('\n' + '='.repeat(60));
                      console.log('LIVE QUERY RESPONSE RECEIVED');
                      console.log('='.repeat(60));
                      console.log('Full Response:', JSON.stringify(liveData, null, 2));
                      console.log('='.repeat(60));
                      
                      if (liveData.success) {
                        console.log('🤖 Live Agent Response:', liveData.text);
                        console.log('📊 Decision:', liveData.decision);

                        // If decision is "inject", auto-fill the form via CDP
                        if (liveData.decision === 'inject' && liveData.fields && liveData.fields.length > 0) {
                          console.log('💉 Injecting form data via CDP...');
                          console.log('Fields to inject:', JSON.stringify(liveData.fields, null, 2));
                          setLiveQueryStatus(`💉 Injecting ${liveData.fields.length} fields via CDP...`);
                          
                          try {
                            // Build fill data from returned fields (already have IDs from backend)
                            const fillData: any[] = [];
                            
                            for (const field of liveData.fields) {
                              if (field.id) {
                                // Backend already matched and provided ID
                                let action = 'fill';
                                let finalValue = field.value;
                                
                                if (field.tag === 'SELECT' && field.options) {
                                  action = 'select';
                                  // Find matching option
                                  const valueLower = field.value.toLowerCase();
                                  const matchingOption = field.options.find((opt: any) => {
                                    const optLabel = (opt.label || '').toLowerCase();
                                    const optValue = (opt.value || '').toLowerCase();
                                    return optLabel.includes(valueLower) || 
                                           valueLower.includes(optLabel) ||
                                           optValue.includes(valueLower);
                                  });
                                  
                                  if (matchingOption) {
                                    finalValue = matchingOption.value;
                                    console.log(`SELECT: ${field.label} → ${matchingOption.label} (${finalValue})`);
                                  }
                                } else if (field.type === 'radio') {
                                  action = 'click';
                                }
                                
                                fillData.push({
                                  id: field.id,
                                  value: finalValue,
                                  action: action
                                });
                              }
                            }
                            
                            if (fillData.length > 0) {
                              console.log('CDP Fill data:', JSON.stringify(fillData, null, 2));
                              
                              // Fill the form using existing command
                              const fillResult = await invoke<string>('fill_form_fields', {
                                fillData: fillData
                              });

                              console.log('✅', fillResult);
                              setLiveQueryStatus(`✅ ${fillResult}`);
                            } else {
                              console.error('No matching fields found');
                              setLiveQueryStatus('❌ Could not match any fields to fill');
                            }
                          } catch (error) {
                            console.error('Form filling failed:', error);
                            setLiveQueryStatus(`❌ Error: ${error}`);
                          }
                        } else {
                          // Just show the response (normal query)
                          console.log('ℹ️ Information response (no injection needed)');
                          setLiveQueryStatus(`ℹ️ ${liveData.text}`);
                        }
                      } else {
                        console.error('❌ Live query error:', liveData.error);
                        setLiveQueryStatus(`❌ ${liveData.error}`);
                      }
                    } else {
                      console.error('❌ Live query failed:', liveQueryResponse.statusText);
                      setLiveQueryStatus(`❌ Failed to analyze: ${liveQueryResponse.statusText}`);
                    }
                  } else {
                    console.error('❌ Error:', data.error);
                    setLiveQueryStatus(`❌ Transcription failed: ${data.error}`);
                  }
                } else {
                  console.error('❌ Failed:', response.statusText);
                  setLiveQueryStatus(`❌ Failed: ${response.statusText}`);
                }
              }
            } catch (error) {
              console.error('Audio retrieval error:', error);
              setLiveQueryStatus(`❌ Error: ${error}`);
            }
          } else if (!isRecording && recording) {
            // Recording started
            setIsRecording(true);
            setLiveQueryStatus('🎤 Recording...');
            console.log('🎤 Recording started...');
          }
        } catch (error) {
          // Silently ignore errors
        }
      }, 500);
    }

    return () => {
      if (urlInterval) {
        clearInterval(urlInterval);
      }
      if (clickInterval) {
        clearInterval(clickInterval);
      }
      if (voiceInterval) {
        clearInterval(voiceInterval);
      }
    };
  }, [isMonitoring, isMagicFilling, isRecording]);

  return (
    <div className="h-full flex flex-col items-center pt-12 px-8">
      <h1 className="text-3xl font-bold text-white mb-2">Chrome Sandbox</h1>
      <p className="text-gray-400 mb-10">Launch browser with CDP and auto-fill forms</p>

      <div className="flex gap-6 mb-8">
        <div
          onClick={!isLaunchingChrome ? launchChrome : undefined}
          className={`w-64 p-6 bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl hover:shadow-2xl transition-all cursor-pointer ${isLaunchingChrome ? 'opacity-50 cursor-not-allowed' : 'hover:scale-105'
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

        {isMonitoring && (
          <div
            onClick={!isMagicFilling ? handleMagicFill : undefined}
            className={`w-64 p-6 bg-gradient-to-br from-purple-600 to-purple-700 rounded-xl hover:shadow-2xl transition-all cursor-pointer ${isMagicFilling ? 'opacity-50 cursor-not-allowed' : 'hover:scale-105'
              }`}
          >
            <div className="w-14 h-14 bg-white/20 rounded-xl flex items-center justify-center text-white mb-4">
              <MagicIcon />
            </div>
            <h3 className="font-semibold text-white mb-2">Magic Fill</h3>
            <p className="text-sm text-purple-100">
              {isMagicFilling ? 'Processing...' : formFieldCount > 0 ? `${formFieldCount} fields detected` : 'AI-powered form filling'}
            </p>
          </div>
        )}
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
            <p className="mt-3 text-sm text-gray-400 italic">
              Auto-refreshing every 2 seconds...
              {formFieldCount > 0 && ` | Magic Fill button injected (${formFieldCount} fields)`}
            </p>
          )}
        </div>
      )}

      {magicFillStatus && (
        <div className={`w-full max-w-2xl mt-4 p-5 rounded-2xl border-2 backdrop-blur-sm ${magicFillStatus.includes('✅')
          ? 'bg-green-900/30 border-green-500/50'
          : magicFillStatus.includes('Error')
            ? 'bg-red-900/30 border-red-500/50'
            : 'bg-yellow-900/30 border-yellow-500/50'
          }`}>
          <p className="font-semibold text-white mb-2">Magic Fill Status:</p>
          <p className="text-gray-300">{magicFillStatus}</p>
        </div>
      )}

      {liveQueryStatus && (
        <div className={`w-full max-w-2xl mt-4 p-5 rounded-2xl border-2 backdrop-blur-sm ${liveQueryStatus.includes('✅')
          ? 'bg-green-900/30 border-green-500/50'
          : liveQueryStatus.includes('❌')
            ? 'bg-red-900/30 border-red-500/50'
            : liveQueryStatus.includes('🎤')
              ? 'bg-purple-900/30 border-purple-500/50'
              : 'bg-blue-900/30 border-blue-500/50'
          }`}>
          <p className="font-semibold text-white mb-2">Voice Query Status:</p>
          <p className="text-gray-300 whitespace-pre-wrap">{liveQueryStatus}</p>
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
