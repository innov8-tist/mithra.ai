# Browser CDP Setup

## Configuration

The application supports multiple browsers via environment variables.

### Setup

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set your preferred browser:
   ```env
   BROWSER_TYPE=auto
   ```

### Supported Browsers

- `chrome` - Google Chrome
- `chromium` - Chromium browser
- `firefox` - Mozilla Firefox
- `auto` - Auto-detect (tries Chrome → Chromium → Firefox)

### Browser Paths

The application automatically detects browsers at these locations:

#### Linux
- Chrome: `/usr/bin/google-chrome`, `/usr/bin/google-chrome-stable`
- Chromium: `/usr/bin/chromium`, `/usr/bin/chromium-browser`, `/snap/bin/chromium`
- Firefox: `/usr/bin/firefox`, `/snap/bin/firefox`

#### Windows
- Chrome: `C:\Program Files\Google\Chrome\Application\chrome.exe`
- Chromium: `C:\Program Files\Chromium\Application\chromium.exe`
- Firefox: `C:\Program Files\Mozilla Firefox\firefox.exe`

#### macOS
- Chrome: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
- Chromium: `/Applications/Chromium.app/Contents/MacOS/Chromium`
- Firefox: `/Applications/Firefox.app/Contents/MacOS/firefox`

## Features

### URL Monitoring
- Automatically tracks the current tab URL every 2 seconds
- Logs URL changes to both the UI and console
- Check your terminal/console for `Current Tab URL:` logs

### Error Suppression
Chrome/Chromium launches with flags to suppress common errors:
- GCM registration errors
- VAAPI errors
- Shared memory warnings
- Background service warnings

## Usage

1. Click "Open Browser" to launch the browser with CDP enabled
2. Navigate to any website
3. Watch the URL updates in real-time in the UI
4. Check your console/terminal for URL logs

## Troubleshooting

If the browser doesn't launch:
1. Check that your preferred browser is installed
2. Verify the browser path matches your system
3. Try setting `BROWSER_TYPE=auto` to auto-detect
4. Check the error message for specific issues
