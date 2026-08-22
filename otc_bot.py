import os
import asyncio
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from pocket_option import PocketOptionClient
from pocket_option.constants import Regions
from pocket_option.models import AuthorizationData


PORT = int(os.getenv("PORT", "10000"))


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Pocket Option bot is running")

    def log_message(self, format, *args):
        pass


def start_web_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    print(f"Health server listening on port {PORT}")
    server.serve_forever()


async def main():

    session = os.getenv("PO_SESSION")
    uid = os.getenv("PO_UID")

    if not session:
        print("ERROR: PO_SESSION is missing")
        return

    if not uid:
        print("ERROR: PO_UID is missing")
        return

    print("PO_SESSION found")
    print("PO_UID found")

    client = PocketOptionClient(logger=True)

    authorization = AuthorizationData.model_validate({
        "session": session,
        "isDemo": 1,
        "uid": int(uid),
        "platform": 2,
        "isFastHistory": True,
        "isOptimized": True,
    })

    print("Authorization created")
    print("Connecting to Pocket Option...")

    @client.on.connect
    async def on_connect(data=None):
        print("CONNECTED TO POCKET OPTION")
        await client.emit.auth(authorization)

    @client.on.success_auth
    async def on_success_auth(data):
        print("POCKET OPTION AUTHORIZED")

    await client.connect(Regions.DEMO)

    print("Connection test running...")

    while True:
        await asyncio.sleep(60)


if __name__ == "__main__":
    threading.Thread(
        target=start_web_server,
        daemon=True
    ).start()

    asyncio.run(main())
