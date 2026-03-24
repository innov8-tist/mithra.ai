use std::process::Command;
use std::path::Path;
use serde_json::{json, Value};
use tokio_tungstenite::{connect_async, tungstenite::Message};
use futures_util::{SinkExt, StreamExt};

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

async fn get_page_ws_url() -> Result<String, String> {
    let client = reqwest::Client::new();
    let res = client
        .get("http://localhost:9222/json")
        .send()
        .await
        .map_err(|e| format!("CDP connection failed: {}", e))?;

    let tabs: Vec<Value> = res.json().await
        .map_err(|e| format!("Failed to parse CDP: {}", e))?;

    tabs.iter()
        .find(|tab| tab.get("type").and_then(|t| t.as_str()) == Some("page"))
        .and_then(|tab| tab.get("webSocketDebuggerUrl"))
        .and_then(|url| url.as_str())
        .map(|s| s.to_string())
        .ok_or_else(|| "No page tab found".to_string())
}

async fn send_cdp_command(ws_url: &str, method: &str, params: Value) -> Result<Value, String> {
    let (mut ws, _) = connect_async(ws_url)
        .await
        .map_err(|e| format!("WebSocket connect failed: {}", e))?;

    let cmd = json!({
        "id": 1,
        "method": method,
        "params": params
    });

    ws.send(Message::Text(cmd.to_string()))
        .await
        .map_err(|e| format!("Send failed: {}", e))?;

    while let Some(msg) = ws.next().await {
        match msg {
            Ok(Message::Text(text)) => {
                let response: Value = serde_json::from_str(&text)
                    .map_err(|e| format!("Parse failed: {}", e))?;
                if response.get("id") == Some(&json!(1)) {
                    if let Some(error) = response.get("error") {
                        return Err(format!("CDP error: {}", error));
                    }
                    return Ok(response.get("result").cloned().unwrap_or(json!({})));
                }
            }
            Err(e) => return Err(format!("WebSocket error: {}", e)),
            _ => {}
        }
    }
    Err("No response from CDP".to_string())
}

#[tauri::command]
async fn capture_screenshot() -> Result<String, String> {
    let ws_url = get_page_ws_url().await?;
    
    let result = send_cdp_command(&ws_url, "Page.captureScreenshot", json!({
        "format": "png",
        "captureBeyondViewport": true
    })).await?;

    result.get("data")
        .and_then(|d| d.as_str())
        .map(|s| s.to_string())
        .ok_or_else(|| "No screenshot data".to_string())
}

#[tauri::command]
async fn extract_form_fields() -> Result<Value, String> {
    let ws_url = get_page_ws_url().await?;

    let js_code = r#"
    (() => {
        return Array.from(document.querySelectorAll("input, select, textarea"))
            .filter(el => {
                const type = (el.getAttribute("type") || "text").toLowerCase();
                if (type === "hidden") return false;
                if (el.disabled) return false;
                const name = (el.name || "").toLowerCase();
                if (name.includes("csrf") || name.includes("token")) return false;
                return true;
            })
            .map((el, index) => {
                const rect = el.getBoundingClientRect();
                return {
                    index,
                    tag: el.tagName,
                    type: el.getAttribute("type") || "text",
                    name: el.getAttribute("name"),
                    id: el.id || null,
                    placeholder: el.getAttribute("placeholder"),
                    required: el.required || false,
                    x: Math.round(rect.x + window.scrollX),
                    y: Math.round(rect.y + window.scrollY),
                    width: Math.round(rect.width),
                    height: Math.round(rect.height),
                    options: el.tagName === "SELECT"
                        ? Array.from(el.options).map(o => ({
                            value: o.value,
                            label: o.innerText.trim(),
                        }))
                        : null,
                };
            });
    })()
    "#;

    let result = send_cdp_command(&ws_url, "Runtime.evaluate", json!({
        "expression": js_code,
        "returnByValue": true
    })).await?;

    result.get("result")
        .and_then(|r| r.get("value"))
        .cloned()
        .ok_or_else(|| "Failed to extract fields".to_string())
}

#[tauri::command]
async fn fill_form_fields(fill_data: Vec<Value>) -> Result<String, String> {
    let ws_url = get_page_ws_url().await?;
    
    let mut filled_count = 0;
    let mut errors: Vec<String> = Vec::new();

    for item in fill_data {
        let id = item.get("id").and_then(|v| v.as_str()).unwrap_or("");
        let action = item.get("action").and_then(|v| v.as_str()).unwrap_or("fill");
        let value = item.get("value").and_then(|v| v.as_str()).unwrap_or("");

        if id.is_empty() {
            continue;
        }

        let js_code = match action {
            "fill" => format!(
                r#"(() => {{
                    const el = document.getElementById('{}');
                    if (el) {{
                        el.focus();
                        el.value = '{}';
                        el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        return true;
                    }}
                    return false;
                }})()"#,
                id, value.replace("'", "\\'")
            ),
            "select" => format!(
                r#"(() => {{
                    const el = document.getElementById('{}');
                    if (el) {{
                        el.value = '{}';
                        el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        return true;
                    }}
                    return false;
                }})()"#,
                id, value.replace("'", "\\'")
            ),
            "click" => format!(
                r#"(() => {{
                    const el = document.getElementById('{}');
                    if (el) {{
                        el.click();
                        return true;
                    }}
                    return false;
                }})()"#,
                id
            ),
            _ => continue,
        };

        match send_cdp_command(&ws_url, "Runtime.evaluate", json!({
            "expression": js_code,
            "returnByValue": true
        })).await {
            Ok(result) => {
                let success = result
                    .get("result")
                    .and_then(|r| r.get("value"))
                    .and_then(|v| v.as_bool())
                    .unwrap_or(false);
                if success {
                    filled_count += 1;
                } else {
                    errors.push(format!("Field '{}' not found", id));
                }
            }
            Err(e) => {
                errors.push(format!("Error filling '{}': {}", id, e));
            }
        }

        // Small delay between fills for stability
        tokio::time::sleep(tokio::time::Duration::from_millis(50)).await;
    }

    if errors.is_empty() {
        Ok(format!("Successfully filled {} fields", filled_count))
    } else {
        Ok(format!("Filled {} fields. Errors: {}", filled_count, errors.join(", ")))
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            greet, 
            launch_chrome_with_cdp, 
            get_current_tab_url, 
            capture_screenshot, 
            extract_form_fields, 
            fill_form_fields
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
