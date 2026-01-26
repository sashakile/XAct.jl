"""Flask HTTP server for Wolfram Engine evaluation with persistent kernel."""

import time

from flask import Flask, jsonify, request

from kernel_manager import KernelManager

app = Flask(__name__)
km = KernelManager()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/evaluate", methods=["POST"])
def evaluate():
    """Evaluate a Wolfram expression (without xAct)."""
    data = request.get_json()
    if not data or "expr" not in data:
        return jsonify({"status": "error", "error": "Missing 'expr' field"}), 400

    expr = data["expr"]
    timeout = int(data.get("timeout", 30))

    start = time.time()
    ok, result, error = km.evaluate(expr, timeout, with_xact=False)
    elapsed_ms = int((time.time() - start) * 1000)

    if ok:
        return jsonify({"status": "ok", "result": result, "timing_ms": elapsed_ms})
    else:
        status = "timeout" if error and "timed out" in error else "error"
        return jsonify({"status": status, "error": error, "timing_ms": elapsed_ms})


@app.route("/evaluate-with-init", methods=["POST"])
def evaluate_with_init():
    """Evaluate expression with xAct pre-loaded."""
    data = request.get_json()
    if not data or "expr" not in data:
        return jsonify({"status": "error", "error": "Missing 'expr' field"}), 400

    expr = data["expr"]
    timeout = int(data.get("timeout", 60))
    context_id = data.get("context_id")  # Optional context isolation

    start = time.time()
    ok, result, error = km.evaluate(expr, timeout, with_xact=True, context_id=context_id)
    elapsed_ms = int((time.time() - start) * 1000)

    if ok:
        return jsonify({"status": "ok", "result": result, "timing_ms": elapsed_ms})
    else:
        status = "timeout" if error and "timed out" in error else "error"
        return jsonify({"status": status, "error": error, "timing_ms": elapsed_ms})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8765)
