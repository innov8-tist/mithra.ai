use std::process::Command;
use std::path::Path;
use serde_json::Value;

// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[tauri::command]
async fn launch_chrome_with_cdp() -> Result<String, String> {
    // Kill existing Chrome to avoid port conflicts
    #[cfg(target_os = "windows")]
    {
        let _ = Command::new("taskkill")
            .args(&["/F", "/IM", "chrome.exe"])
            .output();
        tokio::time::sleep(tokio::time::Duration::from_millis(1000)).await;
    }

    #[cfg(not(target_os = "windows"))]
    {
        let _ = Command::new("pkill").arg("chrome").output();
        let _ = Command::new("pkill").arg("chromium").output();
        tokio::time::sleep(tokio::time::Duration::from_millis(500)).await;
    }

    // Detect Chrome
    let chrome_paths = if cfg!(target_os = "windows") {
        vec![
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]
    } else if cfg!(target_os = "macos") {
        vec![
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        ]
    } else {
        vec![
            "/usr/bin/google-chrome",
            "/usr/bin/chromium",
            "/snap/bin/chromium",
        ]
    };

    let chrome_executable = chrome_paths
        .into_iter()
        .find(|path| Path::new(path).exists())
        .ok_or("Chrome/Chromium not found")?;

    // Dedicated CDP user profile
    let user_data_dir = std::env::temp_dir().join("chrome-cdp-profile");

    // Launch Chrome with CDP enabled
    let mut cmd = Command::new(chrome_executable);
    cmd.args(&[
        "--remote-debugging-port=9222",
        "--remote-allow-origins=*",
        &format!("--user-data-dir={}", user_data_dir.display()),
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-sync",
        "--disable-extensions",
        "--disable-background-networking",
        "about:blank",
    ]);

    #[cfg(target_os = "windows")]
    {
        use std::os::windows::process::CommandExt;
        const CREATE_NEW_PROCESS_GROUP: u32 = 0x00000200;
        const DETACHED_PROCESS: u32 = 0x00000008;
        cmd.creation_flags(CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS);
    }

    cmd.spawn()
        .map_err(|e| format!("Failed to launch Chrome: {}", e))?;

    // Wait for CDP to be ready
    tokio::time::sleep(tokio::time::Duration::from_millis(2500)).await;

    get_cdp_websocket_url()
        .await
        .map(|ws| format!("Chrome CDP running\nWebSocket: {}", ws))
        .map_err(|e| e.to_string())
}

async fn get_cdp_websocket_url() -> Result<String, Box<dyn std::error::Error>> {
    let client = reqwest::Client::new();

    let res = client
        .get("http://localhost:9222/json/version")
        .send()
        .await?;

    let json: Value = res.json().await?;

    json.get("webSocketDebuggerUrl")
        .and_then(|v| v.as_str())
        .map(|s| s.to_string())
        .ok_or("CDP WebSocket not found".into())
}

#[tauri::command]
async fn get_current_tab_url() -> Result<String, String> {
    let client = reqwest::Client::new();

    let res = client
        .get("http://localhost:9222/json")
        .send()
        .await
        .map_err(|e| format!("Failed to connect to Chrome CDP: {}", e))?;

    let tabs: Vec<Value> = res.json().await
        .map_err(|e| format!("Failed to parse CDP response: {}", e))?;

    // Find the first page tab (not extension or devtools)
    let url = tabs.iter()
        .find(|tab| tab.get("type").and_then(|t| t.as_str()) == Some("page"))
        .and_then(|tab| tab.get("url"))
        .and_then(|url| url.as_str())
        .map(|s| s.to_string())
        .ok_or_else(|| "No active tab found".to_string())?;
    
    // Print URL to console
    println!("Current Tab URL: {}", url);
    
    Ok(url)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![greet, launch_chrome_with_cdp, get_current_tab_url])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
