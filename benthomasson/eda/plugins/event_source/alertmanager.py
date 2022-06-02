"""
alertmanager.py

An ansible-events event source module for receiving events via a webhook from alertmanager.

Arguments:
    host: The hostname to listen to. Set to 0.0.0.0 to listen on all interfaces. Defaults to 127.0.0.1
    port: The TCP port to listen to.  Defaults to 5000

Example:

    - benthomasson.eda.alertmanager:
        host: 0.0.0.0
        port: 8000

"""

from flask import Flask, request
from gevent.pywsgi import WSGIServer
import dpath


def clean_host(host):
    if ":" in host:
        return host.split(":")[0]
    else:
        return host


def main(queue, args):

    app = Flask(__name__)

    @app.route("/", methods=["GET"])
    def status():
        return "up", 200

    @app.route("/<path:endpoint>", methods=["POST", "PUT", "DELETE", "PATCH"])
    def webhook(endpoint):
        payload = (request.json,)
        queue.put(
            dict(
                payload=payload,
                meta=dict(endpoint=endpoint, headers=dict(request.headers)),
            )
        )
        for item in payload:
            for alert in item.get("alerts"):
                host = dpath.util.get(alert, 'labels.instance', separator=".")
                host = clean_host(host)
                hosts = []
                if host is not None:
                    hosts.append(host)
                queue.put(
                    dict(
                        alert=alert,
                        meta=dict(endpoint=endpoint,
                                  headers=dict(request.headers),
                                  hosts=hosts),
                    )
                )
        return "Received", 202

    http_server = WSGIServer(
        (args.get("host") or "127.0.0.1", args.get("port") or 5000), app
    )
    http_server.serve_forever()
