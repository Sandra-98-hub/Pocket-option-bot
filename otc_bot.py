import os
import asyncio
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from pocket_option import PocketOptionClient
from pocket_option.constants import Regions
from pocket_option.models import AuthorizationData


# ==========================================
# VERSION TEST
# ==========================================

print("NEW SOCKET TEST VERSION", flush=True)
print("SOCKET TEST READY", flush=True)


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
# MAIN BOT
# ==========================================

async def main():

    print("==================================", flush=True)
    print("POCKET OPTION SOCKET TEST", flush=True)
    print("==================================", flush=True)

    # --------------------------------------
    # ENVIRONMENT VARIABLES
    # --------------------------------------

    session = os.getenv("PO_SESSION")
    uid = os.getenv("PO_UID")

    if not session:

        print(
            "ERROR: PO_SESSION is missing",
            flush=True
        )

        return

    if not uid:

        print(
            "ERROR: PO_UID is missing",
            flush=True
        )

        return

    print(
        "PO_SESSION found",
        flush=True
    )

    print(
        "PO_UID found",
        flush=True
    )


    # --------------------------------------
    # CREATE CLIENT
    # --------------------------------------

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
            "CLIENT CREATION ERROR:",
            type(e).__name__,
            str(e),
            flush=True
        )

        return


    # --------------------------------------
    # WILDCARD EVENT LISTENER
    # --------------------------------------

    async def on_any_event(
        event_name,
        data=None
    ):

        print(
            "==================================",
            flush=True
        )

        print(
            "POCKET OPTION EVENT:",
            event_name,
            flush=True
        )

        if data is not None:

            try:

                text = str(data)

                if len(text) > 3000:

                    text = (
                        text[:3000]
                        + "...[truncated]"
                    )

                print(
                    "EVENT DATA:",
                    text,
                    flush=True
                )

            except Exception as e:

                print(
                    "EVENT DATA ERROR:",
                    type(e).__name__,
                    str(e),
                    flush=True
                )

        print(
            "==================================",
            flush=True
        )


    try:

        client.add_on(
            "*",
            handler=on_any_event
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


    # --------------------------------------
    # AUTHORIZATION
    # --------------------------------------

    try:

        authorization = AuthorizationData.model_validate({

            "session": session,

            "isDemo": 1,

            "uid": int(uid),

            "platform": 2,

            "isFastHistory": True,

            "isOptimized": True

        })

        print(
            "Authorization created",
            flush=True
        )

    except Exception as e:

        print(
            "AUTHORIZATION ERROR:",
            type(e).__name__,
            str(e),
            flush=True
        )

        return


    # --------------------------------------
    # CONNECT
    # --------------------------------------

    print(
        "ABOUT TO CONNECT TO POCKET OPTION",
        flush=True
    )

    try:

        # This is the same connection
        # method that previously succeeded.

        await client.connect(
            Regions.DEMO
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


    # --------------------------------------
    # CONNECTED
    # --------------------------------------

    print(
        "CONNECTED — LISTENING FOR EVENTS",
        flush=True
    )

    print(
        "Bot is waiting for Pocket Option events...",
        flush=True
    )


    # --------------------------------------
    # KEEP RENDER SERVICE ALIVE
    # --------------------------------------

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
        "Starting Pocket Option connection...",
        flush=True
    )

    asyncio.run(main())
