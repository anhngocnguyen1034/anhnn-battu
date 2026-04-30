"""
FOR-BAZI Windows Launcher
用于 PyInstaller 打包为 .exe 后启动 Streamlit 应用。
"""
import subprocess
import sys
import os
import webbrowser
import time
import socket


def find_free_port(start=8501, end=8600):
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return start


def main():
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    app_path = os.path.join(base_dir, "streamlit_app.py")
    if not os.path.exists(app_path):
        print(f"[ERROR] streamlit_app.py not found at {app_path}")
        input("Press Enter to exit...")
        sys.exit(1)

    port = find_free_port()
    url = f"http://localhost:{port}"

    print(f"""
╔══════════════════════════════════════════╗
║   玄冥 | MING MATRIX - 命理架构终端     ║
║   Bazi Destiny Architecture Terminal     ║
╠══════════════════════════════════════════╣
║   Starting server on port {port}...        ║
║   Browser will open automatically.       ║
║   Press Ctrl+C to stop.                  ║
╚══════════════════════════════════════════╝
""")

    time.sleep(1)
    webbrowser.open(url)

    proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", app_path,
         f"--server.port={port}", "--server.headless=true",
         "--browser.gatherUsageStats=false"],
        cwd=base_dir,
    )

    try:
        proc.wait()
    except KeyboardInterrupt:
        print("\nShutting down...")
        proc.terminate()
        proc.wait(timeout=5)


if __name__ == "__main__":
    main()
