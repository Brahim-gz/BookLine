import os
import sys
import uvicorn

def main() -> None:
    host = "127.0.0.1"
    ports_to_try = (
        [int(os.environ["PORT"])] if os.environ.get("PORT") else [5001, 9001, 8001]
    )
    for port in ports_to_try:
        try:
            print(f"Starting backend on http://{host}:{port}")
            uvicorn.run(
                "app.main:app",
                host=host,
                port=port,
                reload=True,
            )
            break
        except OSError as e:
            if getattr(e, "winerror", None) == 10013 or getattr(e, "errno", None) == 10013:
                print(f"Port {port} blocked, trying next...", file=sys.stderr)
                continue
            raise
    else:
        print("No port available. Set PORT=your_port in env.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
