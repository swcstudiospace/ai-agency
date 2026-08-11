#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![platform_info, open_external])
        .setup(|_app| {
            #[cfg(debug_assertions)]
            {
                // dev-only hooks
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running Agency Cockpit");
}

#[tauri::command]
fn platform_info() -> serde_json::Value {
    serde_json::json!({
        "os": std::env::consts::OS,
        "arch": std::env::consts::ARCH,
        "family": std::env::consts::FAMILY,
        "shell": "tauri",
    })
}

#[tauri::command]
fn open_external(url: String) -> Result<(), String> {
    // Prefer plugin from frontend; this is a fallback stub
    let _ = url;
    Ok(())
}
