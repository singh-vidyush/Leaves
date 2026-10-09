use tauri::{
    image::Image,
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    Manager, WindowEvent,
};

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
        .setup(|app| {
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
        .run(tauri::generate_context!())
        .expect("error while running Leaves");
}
