import os
import asyncio
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from pocket_option import PocketOptionClient


# ==========================================
# RENDER HEALTH SERVER
# ==========================================

PORT = int(os.getenv("PORT", "10000"))


class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Pocket Option bot is running")

    def log_message(self, format, *args):
        pass


def start_web_server():

    server = HTTPServer(
        ("0.0.0.0", PORT),
        HealthHandler
    )

    print(
        f"Health server listening on port {PORT}",
        flush=True
    )

    server.serve_forever()


# ==========================================
# POCKET OPTION EVENT MONITOR
# ==========================================

async def main():

    print("==================================", flush=True)
    print("POCKET OPTION EVENT MONITOR", flush=True)
    print("==================================", flush=True)

    session = os.getenv("PO_SESSION")
    uid = os.getenv("PO_UID")

    if not session:
        print("ERROR: PO_SESSION is missing", flush=True)
        return

    if not uid:
        print("ERROR: PO_UID is missing", flush=True)
        return

    print("PO_SESSION found", flush=True)
    print("PO_UID found", flush=True)

    try:

        client = PocketOptionClient(
            logger=False
        )

        print(
            "Pocket Option client created",
            flush=True
        )

    except Exception as e:

        print(
            "CLIENT ERROR:",
            type(e).__name__,
            str(e),
            flush=True
        )

        return

    # ======================================
    # CAPTURE EVERY INCOMING EVENT
    # ======================================

    async def event_handler(event_name, data=None):

        print("==================================", flush=True)

        print(
            "POCKET OPTION EVENT:",
            event_name,
            flush=True
        )

        if data is not None:

            try:

                text = str(data)

                # Keep logs manageable
                if len(text) > 2000:
                    text = text[:2000] + "...[truncated]"

                print(
                    "EVENT DATA:",
                    text,
                    flush=True
                )

            except Exception as e:

                print(
                    "DATA DISPLAY ERROR:",
                    type(e).__name__,
                    str(e),
                    flush=True
                )

        print("==================================", flush=True)


    # ======================================
    # REGISTER WILDCARD EVENT LISTENER
    # ======================================

    try:

        client.add_on(
            "*",
            handler=event_handler
        )

        print(
            "Wildcard event listener installed",
            flush=True
        )

    except Exception as e:

        print(
            "EVENT LISTENER ERROR:",
            type(e).__name__,
            str(e),
            flush=True
        )

        return

    # ======================================
    # CONNECT
    # ======================================

    try:

        print(
            "Connecting to Pocket Option...",
            flush=True
        )

        await client.connect(
            "https://api.pocketoption.com",
            wait=True,
            wait_timeout=10,
            retry=True
        )

        print(
            "CONNECT CALL FINISHED",
            flush=True
        )

    except Exception as e:

        print(
            "==================================",
            flush=True
        )

        print(
            "CONNECTION ERROR:",
            type(e).__name__,
            str(e),
            flush=True
        )

        print(
            "==================================",
            flush=True
        )

        return

    print(
        "CONNECTED — LISTENING FOR EVENTS",
        flush=True
    )

    # ======================================
    # KEEP PROCESS ALIVE
    # ======================================

    while True:

        await asyncio.sleep(10)


# ==========================================
# START
# ==========================================

if __name__ == "__main__":

    print(
        "Starting Render health server...",
        flush=True
    )

    threading.Thread(
        target=start_web_server,
        daemon=True
    ).start()

    print(
        "Starting Pocket Option event monitor...",
        flush=True
    )

    asyncio.run(main())
