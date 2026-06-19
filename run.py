"""
run.py — Starts FastAPI (uvicorn) and Streamlit simultaneously.
Usage: python run.py
"""

import subprocess
import sys
import time
import signal
import os

BACKEND_CMD  = [sys.executable, "-m", "uvicorn", "backend:app",
                "--host", "0.0.0.0", "--port", "8000", "--reload"]
FRONTEND_CMD = [sys.executable, "-m", "streamlit", "run", "frontend.py",
                "--server.port", "8501", "--server.headless", "true"]


def main():
    # print("=" * 55)
    # print("  🚀  Starting RAG Chatbot")
    # print("  Backend  → http://localhost:8000")
    # print("  Frontend → http://localhost:8501")
    # print("  Press Ctrl+C to stop both servers.")
    # print("=" * 55)

    backend  = subprocess.Popen(BACKEND_CMD)
    time.sleep(2)                          # give FastAPI a head-start
    frontend = subprocess.Popen(FRONTEND_CMD)

    def shutdown(sig, frame):
        print("\n[run.py] Shutting down…")
        backend.terminate()
        frontend.terminate()
        backend.wait()
        frontend.wait()
        print("[run.py] All processes stopped.")
        sys.exit(0)

    signal.signal(signal.SIGINT,  shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Block until either process exits
    while True:
        if backend.poll() is not None:
            print("[run.py] Backend exited unexpectedly.")
            frontend.terminate()
            break
        if frontend.poll() is not None:
            print("[run.py] Frontend exited unexpectedly.")
            backend.terminate()
            break
        time.sleep(1)


if __name__ == "__main__":
    main()
