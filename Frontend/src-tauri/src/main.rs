// Prevents additional console window on Windows in release builds
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::{Child, Command};
use std::sync::Mutex;
use tauri::{Manager, State};

// Backend process state
struct BackendProcess(Mutex<Option<Child>>);

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_store::Builder::default().build())
        .setup(|app| {
            // Start backend process
            let backend_process = start_backend_process(app);
            app.manage(BackendProcess(Mutex::new(backend_process)));

            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event {
                // Clean up backend process before closing
                if let Some(backend_state) = window.app_handle().try_state::<BackendProcess>() {
                    if let Ok(mut backend) = backend_state.0.lock() {
                        if let Some(mut child) = backend.take() {
                            let _ = child.kill();
                            println!("Backend process terminated");
                        }
                    }
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

fn start_backend_process(app: &tauri::App) -> Option<Child> {
    // Get the resource directory where sidecar binaries are located
    let resource_dir = app
        .path()
        .resource_dir()
        .expect("Failed to get resource directory");

    // Path to the backend executable (will be bundled as sidecar)
    let backend_exe = resource_dir.join("MegaMelangeBackend.exe");

    println!("Starting backend from: {:?}", backend_exe);

    // Start the backend process
    match Command::new(&backend_exe)
        .current_dir(&resource_dir)
        .spawn()
    {
        Ok(child) => {
            println!("Backend started with PID: {}", child.id());
            Some(child)
        }
        Err(e) => {
            eprintln!("Failed to start backend: {}", e);
            eprintln!("Tried to run: {:?}", backend_exe);
            None
        }
    }
}
