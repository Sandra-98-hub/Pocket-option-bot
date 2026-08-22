import os
import asyncio
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from pocket_option import PocketOptionClient
from pocket_option.constants import Regions
from pocket_option.models import AuthorizationData


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
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)

    print(f"Health server listening on port {PORT}", flush=True)

    server.serve_forever()


# ==========================================
# POCKET OPTION CONNECTION
# ==========================================

async def main():

    print("==================================", flush=True)
    print("POCKET OPTION BOT", flush=True)
    print("==================================", flush=True)

    session = os.getenv("PO_SESSION")
    uid = os.getenv("PO_UID")

    # --------------------------------------
    # CHECK SESSION
    # --------------------------------------

    if not session:
        print("ERROR: PO_SESSION is missing", flush=True)
        return

    print("PO_SESSION found", flush=True)

    # --------------------------------------
    # CHECK UID
    # --------------------------------------

    if not uid:
        print("ERROR: PO_UID is missing", flush=True)
        return

    print("PO_UID found", flush=True)

    # --------------------------------------
    # CREATE CLIENT
    # --------------------------------------

    try:

        client = PocketOptionClient(
            logger=True
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
    # CREATE AUTHORIZATION
    # --------------------------------------

    try:

        authorization = AuthorizationData.model_validate({

            "session": session,

            # 1 = DEMO
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
    # CONNECTION EVENT
    # --------------------------------------

    @client.on.connect
    async def on_connect(data=None):

        print(
            "==================================",
            flush=True
        )

        print(
            "CONNECTED TO POCKET OPTION",
            flush=True
        )

        print(
            "==================================",
            flush=True
        )

        try:

            await client.emit.auth(
                authorization
            )

            print(
                "AUTHORIZATION SENT",
                flush=True
            )

        except Exception as e:

            print(
                "AUTHORIZATION SEND ERROR:",
                type(e).__name__,
                str(e),
                flush=True
            )


    # --------------------------------------
    # AUTH SUCCESS EVENT
    # --------------------------------------

    @client.on.success_auth
    async def on_success_auth(data):

        print(
            "==================================",
            flush=True
        )

        print(
            "POCKET OPTION AUTHORIZED",
            flush=True
        )

        print(
            "LIVE CONNECTION READY",
            flush=True
        )

        print(
            "==================================",
            flush=True
        )


    # --------------------------------------
    # START CONNECTION
    # --------------------------------------

    print(
        "ABOUT TO CONNECT TO POCKET OPTION",
        flush=True
    )

    try:

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
            "CONNECTION ERROR",
            flush=True
        )

        print(
            type(e).__name__,
            flush=True
        )

        print(
            str(e),
            flush=True
        )

        print(
            "==================================",
            flush=True
        )

        return

    # --------------------------------------
    # KEEP SERVICE RUNNING
    # --------------------------------------

    print(
        "Bot is waiting for Pocket Option events...",
        flush=True
    )

    while True:

        await asyncio.sleep(60)


# ==========================================
# START PROGRAM
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
