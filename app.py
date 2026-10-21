import os
import subprocess
from flask import Flask, render_template_string, jsonify

app = Flask(__name__)

# Helper function to trigger our container sandbox and return metrics
def run_sandbox_telemetry():
    seccomp_profile = "seccomp-profile.json"
    binary_path = "/src/test_binary"

    docker_cmd = [
        "docker", "run", "--rm",
        "--user", "65534:65534",
        "--security-opt", f"seccomp={seccomp_profile}",
        "-v", f"{os.getcwd()}/untrusted_code:/src",
        "alpine",
        binary_path
    ]

    try:
        result = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=5)
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        exit_code = result.returncode
        
        # Calculate scoring logic for web state
        if "Access denied" in stdout or "Permission denied" in stderr:
            score = 100
            status = "SECURE - Threat Intercepted"
            badge = "bg-success"
        elif "Exploit Success" in stdout:
            score = 0
            status = "COMPROMISED - Privilege Leak"
            badge = "bg-danger"
        else:
            score = 90
            status = "NORMAL - Closed Cleanly"
            badge = "bg-primary"
            
        return {
            "score": score,
            "status": status,
            "badge": badge,
            "stdout": stdout if stdout else "None",
            "stderr": stderr if stderr else "None",
            "exit_code": exit_code
        }
    except Exception as e:
        return {"score": 0, "status": f"Error: {str(e)}", "badge": "bg-warning", "stdout": "", "stderr": "", "exit_code": -1}

# UI HTML Layout Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HPS Security Dashboard</title>
    <link href="https://jsdelivr.net" rel="stylesheet">
    <style>
        body { background-color: #0f172a; color: #e2e8f0; font-family: sans-serif; }
        .card { background-color: #1e293b; border: 1px solid #334155; color: #f8fafc; }
        pre { background-color: #020617; color: #38bdf8; padding: 15px; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container my-5">
        <div class="d-flex justify-content-between align-items-center mb-4 pb-2 border-bottom border-secondary">
            <h2>🛡️ Hardened Polyglot Sandbox (HPS) Telemetry</h2>
            <a href="/" class="btn btn-outline-info btn-sm">🔄 Refresh Metrics</a>
        </div>

        <div class="row g-4">
            <!-- Score Card -->
            <div class="col-md-4">
                <div class="card p-4 text-center">
                    <h5>Security Compliance Score</h5>
                    <h1 class="display-2 my-3 font-monospace text-warning">{{ metrics.score }}/100</h1>
                    <span class="badge {{ metrics.badge }} p-2 fs-6">{{ metrics.status }}</span>
                </div>
            </div>

            <!-- Profile Parameters -->
            <div class="col-md-8">
                <div class="card p-4 h-100">
                    <h5>Active Container Restrictions</h5>
                    <ul class="list-group list-group-flush mt-3">
                        <li class="list-group-item bg-transparent text-light border-secondary">👤 <strong>User Execution Context:</strong> Non-Root (UID 65534 / nobody)</li>
                        <li class="list-group-item bg-transparent text-light border-secondary">📄 <strong>Seccomp Boundary State:</strong> Custom Whitelist (Active)</li>
                        <li class="list-group-item bg-transparent text-light border-secondary">🚪 <strong>Exit Termination State:</strong> Code {{ metrics.exit_code }}</li>
                    </ul>
                </div>
            </div>

            <!-- Log Panels -->
            <div class="col-12">
                <div class="card p-4">
                    <h5>Live Sandbox Console Output</h5>
                    <div class="mt-3">
                        <h6>Standard Output (stdout):</h6>
                        <pre><code>{{ metrics.stdout }}</code></pre>
                    </div>
                    <div class="mt-3">
                        <h6>Standard Error (stderr):</h6>
                        <pre style="color: #f87171;"><code>{{ metrics.stderr }}</code></pre>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    metrics = run_sandbox_telemetry()
    return render_template_string(HTML_TEMPLATE, metrics=metrics)

if __name__ == '__main__':
    # Running on 0.0.0.0 allowing GitHub Codespaces to forward it instantly
    app.run(host='0.0.0.0', port=5000, debug=True)
