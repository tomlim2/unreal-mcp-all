use std::{env, fs, io::Write, path::PathBuf};

fn ensure_windows_icon() {
    // Create a minimal 1x1 transparent ICO if icons/icon.ico is missing.
    let manifest_dir = env::var("CARGO_MANIFEST_DIR").unwrap_or_else(|_| ".".into());
    let mut ico_path = PathBuf::from(manifest_dir);
    ico_path.push("icons");
    ico_path.push("icon.ico");

    if ico_path.exists() {
        return;
    }

    if let Some(parent) = ico_path.parent() {
        let _ = fs::create_dir_all(parent);
    }

    // Minimal valid ICO bytes for a 1x1 pixel, 32-bit BGRA, with AND mask.
    // Header (ICONDIR) + Directory (ICONDIRENTRY) + BITMAPINFOHEADER + pixel + mask
    let ico_bytes: [u8; 70] = [
        // ICONDIR
        0x00, 0x00, // reserved
        0x01, 0x00, // image type (icon)
        0x01, 0x00, // number of images
        // ICONDIRENTRY
        0x01, // width
        0x01, // height
        0x00, // color count
        0x00, // reserved
        0x01, 0x00, // color planes
        0x20, 0x00, // bits per pixel (32)
        0x30, 0x00, 0x00, 0x00, // size of BMP data (48 bytes)
        0x16, 0x00, 0x00, 0x00, // offset to BMP data (22 bytes)
        // BITMAPINFOHEADER (40 bytes)
        0x28, 0x00, 0x00, 0x00, // header size (40)
        0x01, 0x00, 0x00, 0x00, // width = 1
        0x02, 0x00, 0x00, 0x00, // height = 2 (image + mask)
        0x01, 0x00, // planes = 1
        0x20, 0x00, // bitcount = 32
        0x00, 0x00, 0x00, 0x00, // compression = BI_RGB
        0x00, 0x00, 0x00, 0x00, // size image = 0 (can be 0 for BI_RGB)
        0x00, 0x00, 0x00, 0x00, // x pixels per meter
        0x00, 0x00, 0x00, 0x00, // y pixels per meter
        0x00, 0x00, 0x00, 0x00, // colors used
        0x00, 0x00, 0x00, 0x00, // important colors
        // Pixel data (BGRA) 1x1: transparent
        0x00, 0x00, 0x00, 0x00,
        // AND mask (padded to 32 bits)
        0x00, 0x00, 0x00, 0x00,
    ];

    if let Ok(mut f) = fs::File::create(&ico_path) {
        let _ = f.write_all(&ico_bytes);
    }
}

fn main() {
    // Ensure Windows build has an .ico available
    #[cfg(target_os = "windows")]
    ensure_windows_icon();

    tauri_build::build()
}
