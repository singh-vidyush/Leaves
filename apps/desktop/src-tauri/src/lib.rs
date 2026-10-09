use std::net::TcpListener;
use std::sync::Mutex;
use tauri::{
    image::Image,
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    Manager, RunEvent, WindowEvent,
};
use tauri_plugin_shell::{process::CommandChild, ShellExt};

struct BackendProcess {
    child: Mutex<Option<CommandChild>>,
    port: u16,
}

#[tauri::command]
fn backend_api_port(state: tauri::State<'_, BackendProcess>) -> u16 {
    state.port
}

fn leaves_tray_image() -> Image<'static> {
    let mut rgba = Vec::with_capacity(16 * 16 * 4);
    for y in 0..16 {
        for x in 0..16 {
            let xf = (x as f32 - 7.5) / 6.0;
            let yf = (y as f32 - 7.5) / 6.0;
            let rotated_x = xf * 0.82 + yf * 0.57;
            let rotated_y = -xf * 0.57 + yf * 0.82;
            let inside_leaf = rotated_x * rotated_x / 0.95 + rotated_y * rotated_y / 0.42 <= 1.0;
            let vein = (x as i32 - y as i32).abs() <= 1 && inside_leaf;
            if inside_leaf {
                if vein {
                    rgba.extend_from_slice(&[247, 246, 239, 255]);
                } else {
                    rgba.extend_from_slice(&[75, 103, 80, 255]);
                }
            } else {
                rgba.extend_from_slice(&[0, 0, 0, 0]);
            }
        }
    }
    Image::new_owned(rgba, 16, 16)
}

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_opener::init())
        .setup(|app| {
            // In development, scripts/dev.sh owns the API process. Installed apps
            // launch the bundled Python sidecar and stop it when Leaves exits.
            if !cfg!(debug_assertions) {
                let port = TcpListener::bind(("127.0.0.1", 0))?.local_addr()?.port();
                let data_dir = app.path().app_data_dir()?;
                std::fs::create_dir_all(&data_dir)?;
                let (mut events, child) = app
                    .shell()
                    .sidecar("leaves-api")?
                    .env("LEAVES_DATA_DIR", data_dir.to_string_lossy())
                    .env("LEAVES_API_PORT", port.to_string())
                    .spawn()?;
                app.manage(BackendProcess {
                    child: Mutex::new(Some(child)),
                    port,
                });
                tauri::async_runtime::spawn(async move {
                    while let Some(event) = events.recv().await {
                        match event {
                            tauri_plugin_shell::process::CommandEvent::Stderr(bytes) => {
                                eprintln!("Leaves backend: {}", String::from_utf8_lossy(&bytes));
                            }
                            tauri_plugin_shell::process::CommandEvent::Error(error) => {
                                eprintln!("Leaves backend process error: {error}");
                            }
                            tauri_plugin_shell::process::CommandEvent::Terminated(status) => {
                                eprintln!("Leaves backend exited: {status:?}");
                            }
                            _ => {}
                        }
                    }
                });
            } else {
                // The development script runs uvicorn on the documented port.
                app.manage(BackendProcess {
                    child: Mutex::new(None),
                    port: 8000,
                });
            }

            let open_item = MenuItem::with_id(app, "open", "Open Leaves", true, None::<&str>)?;
            let quit_item = MenuItem::with_id(app, "quit", "Quit Leaves", true, None::<&str>)?;
            let menu = Menu::with_items(app, &[&open_item, &quit_item])?;

            TrayIconBuilder::new()
                .icon(leaves_tray_image())
                .icon_as_template(false)
                .tooltip("Leaves")
                .menu(&menu)
                .show_menu_on_left_click(false)
                .on_menu_event(|app, event| match event.id.as_ref() {
                    "open" => {
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.set_focus();
                        }
                    }
                    "quit" => app.exit(0),
                    _ => {}
                })
                .on_tray_icon_event(|tray, event| {
                    if let TrayIconEvent::Click {
                        button: MouseButton::Left,
                        button_state: MouseButtonState::Up,
                        ..
                    } = event
                    {
                        if let Some(window) = tray.app_handle().get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.set_focus();
                        }
                    }
                })
                .build(app)?;

            Ok(())
        })
        .on_window_event(|window, event| {
            if let WindowEvent::CloseRequested { api, .. } = event {
                api.prevent_close();
                let _ = window.hide();
            }
        })
        .on_event(|app, event| {
            if matches!(event, RunEvent::Exit) {
                if let Some(state) = app.try_state::<BackendProcess>() {
                    if let Ok(mut child) = state.child.lock() {
                        if let Some(child) = child.take() {
                            let _ = child.kill();
                        }
                    }
                }
            }
        })
        .invoke_handler(tauri::generate_handler![backend_api_port])
        .run(tauri::generate_context!())
        .expect("error while running Leaves");
}
