"""
Browser Automation Service
Launches Chrome with CDP and navigates to the service link
"""

import subprocess
import time
import os
from typing import Dict, Any, Optional


class BrowserAutomation:
    """Handles browser automation with CDP"""
    
    def __init__(self):
        self.chrome_process = None
        self.cdp_port = 9222
    
    def find_chrome_path(self) -> Optional[str]:
        """Find Chrome executable path on Windows"""
        possible_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def launch_browser(self, url: str, headless: bool = False) -> Dict[str, Any]:
        """
        Launch Chrome browser with CDP and navigate to URL
        """
        try:
            chrome_path = self.find_chrome_path()
            
            if not chrome_path:
                return {
                    "success": False,
                    "error": "Chrome not found. Please install Google Chrome."
                }
            
            # Chrome arguments
            chrome_args = [
                chrome_path,
                f"--remote-debugging-port={self.cdp_port}",
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check",
                f"--user-data-dir={os.path.expandvars('%TEMP%')}\\chrome_cdp_profile",
                url
            ]
            
            if headless:
                chrome_args.append("--headless")
            
            # Launch Chrome
            self.chrome_process = subprocess.Popen(
                chrome_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            
            # Wait for Chrome to start
            time.sleep(3)
            
            # Check if process is running
            if self.chrome_process.poll() is None:
                return {
                    "success": True,
                    "message": "Browser launched and navigated successfully",
                    "url": url,
                    "cdp_port": self.cdp_port,
                    "pid": self.chrome_process.pid
                }
            else:
                return {
                    "success": False,
                    "error": "Chrome process terminated unexpectedly"
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def close_browser(self) -> Dict[str, Any]:
        """
        Close the browser
        """
        try:
            if self.chrome_process:
                # Try graceful termination first
                self.chrome_process.terminate()
                time.sleep(1)
                
                # Force kill if still running
                if self.chrome_process.poll() is None:
                    self.chrome_process.kill()
                
                self.chrome_process = None
                
                return {
                    "success": True,
                    "message": "Browser closed successfully"
                }
            else:
                return {
                    "success": True,
                    "message": "No browser instance to close"
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def is_running(self) -> bool:
        """Check if browser is still running"""
        if self.chrome_process:
            return self.chrome_process.poll() is None
        return False


# Global browser instance
_browser_instance: Optional[BrowserAutomation] = None


def get_browser_instance() -> BrowserAutomation:
    """
    Get or create browser instance
    """
    global _browser_instance
    
    if _browser_instance is None:
        _browser_instance = BrowserAutomation()
    
    return _browser_instance


def launch_and_navigate(url: str, headless: bool = False) -> Dict[str, Any]:
    """
    Main function: Launch browser and navigate to URL
    
    Args:
        url: URL to navigate to
        headless: Run browser in headless mode
    
    Returns:
        Dictionary with navigation result
    """
    browser = get_browser_instance()
    result = browser.launch_browser(url, headless=headless)
    return result


def close_browser_instance() -> Dict[str, Any]:
    """
    Close the global browser instance
    """
    global _browser_instance
    
    if _browser_instance:
        result = _browser_instance.close_browser()
        _browser_instance = None
        return result
    
    return {"success": True, "message": "No browser instance to close"}
