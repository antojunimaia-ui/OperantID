import os
import json
import asyncio
import threading
import sys
import io
from flask import Flask, render_template_string, request, jsonify
from .agent import Agent

# Premium UI template with Tabs
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OperantID Playground 🤖</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #4f46e5;
            --bg: #0f172a;
            --card-bg: transparent;
            --text: #f8fafc;
            --accent: #9333ea;
            --border: #1e293b;
            --input-bg: #1e293b;
        }
        body {
            font-family: 'Outfit', sans-serif;
            background-color: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 40px;
            display: flex;
            justify-content: center;
        }
        .container {
            width: 96%;
            max-width: 1800px;
            background: transparent;
            padding: 0;
            border: none;
            box-shadow: none;
        }
        .header { text-align: left; margin-bottom: 40px; border-bottom: 2px solid var(--border); padding-bottom: 20px; }
        h1 { font-size: 3rem; margin: 0; font-weight: 700; color: white; }
        .subtitle { color: #94a3b8; font-size: 1.1rem; margin-top: 10px; }

        /* Tabs Styling */
        .tabs-nav {
            display: flex;
            gap: 20px;
            margin-bottom: 30px;
            border-bottom: 1px solid var(--border);
            padding: 0;
            background: transparent;
        }
        .tab-btn {
            padding: 12px 24px;
            border: none;
            background: transparent;
            color: #64748b;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            border-radius: 0;
            transition: all 0.2s;
            border-bottom: 2px solid transparent;
        }
        .tab-btn.active {
            color: white;
            border-bottom: 2px solid var(--primary);
        }
        .tab-content { display: none; }
        .tab-content.active { display: block; }

        .form-group { margin-bottom: 25px; }
        .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; }
        label { display: block; margin-bottom: 10px; font-size: 0.95rem; color: #94a3b8; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
        input, select, textarea {
            width: 100%;
            padding: 14px;
            background: var(--input-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: white;
            font-size: 1rem;
            box-sizing: border-box;
            transition: border-color 0.2s;
        }
        input:focus, select:focus, textarea:focus { outline: none; border-color: var(--primary); }
        
        button#runBtn {
            width: auto;
            min-width: 200px;
            padding: 16px 32px;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1.1rem;
            font-weight: 700;
            cursor: pointer;
            transition: background 0.2s;
        }
        button#runBtn:hover:not(:disabled) { background: #4338ca; }
        button#runBtn:disabled { opacity: 0.5; cursor: not-allowed; }

        #logs {
            margin-top: 10px;
            background: #020617;
            border-radius: 4px;
            padding: 15px;
            height: calc(100vh - 450px);
            overflow-y: auto;
            font-family: 'JetBrains Mono', 'Consolas', monospace;
            font-size: 0.8rem;
            line-height: 1.4;
            border: 1px solid rgba(255,255,255,0.05);
            color: #d1d5db;
            white-space: pre-wrap;
            word-break: break-all;
        }
        .log-line { margin-bottom: 2px; }
        .log-info { color: #38bdf8; }
        .log-action { color: #a855f7; }
        .log-success { color: #4ade80; }
        .log-warning { color: #fbbf24; }
        .log-error { color: #f87171; }
        .log-reasoning { color: #94a3b8; font-style: italic; opacity: 0.8; margin-bottom: 10px; }
        .log-terminal { color: #64748b; font-size: 0.75rem; border-bottom: 1px solid rgba(255,255,255,0.02); padding-bottom: 2px; }
        
        .status-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
        .status-badge { padding: 6px 14px; border-radius: 30px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
        .status-idle { background: #1e293b; color: #94a3b8; }
        .status-running { background: #064e3b; color: #34d399; animation: pulse 2s infinite; }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.7; } 100% { opacity: 1; } }
        
        .switch-group { display: flex; align-items: center; gap: 12px; background: rgba(255,255,255,0.03); padding: 12px 18px; border-radius: 14px; }
        .switch-group input[type="checkbox"] { width: auto; cursor: pointer; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>OperantID</h1>
            <p class="subtitle">Nexus de Agentes Autônomos</p>
        </div>

        <div class="tabs-nav">
            <button class="tab-btn active" onclick="switchTab('config', event)">⚙️ Config</button>
            <button class="tab-btn" onclick="switchTab('params', event)">🎛️ Parameters</button>
            <button class="tab-btn" onclick="switchTab('browser_settings', event)">🌐 Browser Settings</button>
            <button class="tab-btn" onclick="switchTab('agent', event)">🤖 Agent</button>
        </div>

        <!-- Tab: Config -->
        <div id="config" class="tab-content active">
            <div class="grid-2">
                <div class="form-group">
                    <label>Provedor de IA</label>
                    <select id="provider">
                        <option value="gemini">Google Gemini</option>
                        <option value="openai">OpenAI / Compatíveis</option>
                        <option value="mistral">Mistral AI</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Modelo (Opcional)</label>
                    <input type="text" id="model" placeholder="Ex: gemini-1.5-flash">
                </div>
            </div>
            <div class="form-group">
                <label>API Key</label>
                <input type="password" id="apiKey" placeholder="Insira sua chave aqui...">
            </div>
            <div class="form-group">
                <label>Custom Base URL (OpenAI API Compatible)</label>
                <input type="text" id="baseUrl" placeholder="Ex: https://openrouter.ai/api/v1">
            </div>
        </div>

        <!-- Tab: Parameters -->
        <div id="params" class="tab-content">
            <div class="grid-2">
                <div class="form-group">
                    <label>Max Steps</label>
                    <input type="number" id="maxSteps" value="25">
                </div>
                <div class="form-group">
                    <label>Wait Delay (ms)</label>
                    <input type="number" id="waitMs" value="1000">
                </div>
            </div>
            <div class="grid-2">
                <div class="switch-group">
                    <input type="checkbox" id="headless">
                    <label for="headless" style="margin-bottom:0">Modo Headless (Ocultar Navegador)</label>
                </div>
                <div class="switch-group">
                    <input type="checkbox" id="streaming" checked>
                    <label for="streaming" style="margin-bottom:0">Habilitar Streaming (Beta)</label>
                </div>
            </div>
            <div class="grid-2" style="margin-top:20px">
                <div class="form-group">
                    <label>Email (Login Automático)</label>
                    <input type="text" id="email" placeholder="email@exemplo.com">
                </div>
                <div class="form-group">
                    <label>Senha (Login Automático)</label>
                    <input type="password" id="password" placeholder="********">
                </div>
            </div>
        </div>

        <!-- Tab: Browser Settings -->
        <div id="browser_settings" class="tab-content">
            <div class="grid-2">
                <div class="form-group">
                    <label>Browser Engine</label>
                    <select id="browserType">
                        <option value="chromium">Chromium (Recommended)</option>
                        <option value="firefox">Firefox</option>
                        <option value="webkit">Safari (Webkit)</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>User Agent (Opcional)</label>
                    <input type="text" id="userAgent" placeholder="Deixe em branco para padrão...">
                </div>
            </div>
            <div class="grid-2">
                <div class="form-group">
                    <label>Viewport Width</label>
                    <input type="number" id="viewportWidth" value="1280">
                </div>
                <div class="form-group">
                    <label>Viewport Height</label>
                    <input type="number" id="viewportHeight" value="720">
                </div>
            </div>
            <div class="grid-2">
                <div class="form-group">
                    <label>Locale</label>
                    <input type="text" id="locale" value="pt-BR">
                </div>
                <div class="form-group">
                    <label>Timezone</label>
                    <input type="text" id="timezone" value="America/Sao_Paulo">
                </div>
            </div>
        </div>

        <!-- Tab: Agent -->
        <div id="agent" class="tab-content">
            <div class="status-header">
                <label style="margin:0">Defina a Missão do seu Agente</label>
                <div id="status" class="status-badge status-idle">IDLE</div>
            </div>
            
            <div class="grid-2" style="grid-template-columns: 1fr 480px; gap: 40px; align-items: stretch;">
                <!-- Left: Browser Stream -->
                <div id="streamContainer" style="display: flex; flex-direction: column;">
                    <label style="font-size: 0.75rem; letter-spacing: 0.2em; opacity: 0.6; margin-bottom: 15px;">OPERANT.VISION / LIVE_STREAM</label>
                    <div style="background: #020617; border: 1px solid var(--border); border-radius: 4px; overflow: hidden; width: 100%; aspect-ratio: 16 / 9; display: flex; align-items: center; justify-content: center; box-shadow: 0 20px 40px rgba(0,0,0,0.6);">
                        <img id="browserStream" src="" style="width: 100%; height: 100%; object-fit: cover; display: none;">
                        <div id="streamPlaceholder" style="color: #475569; text-align: center; padding: 20px;">
                            <div style="font-size: 3rem; margin-bottom: 10px; opacity: 0.3;">📡</div>
                            <div style="font-family: monospace; font-size: 0.8rem; letter-spacing: 0.1em;">Awaiting Uplink...</div>
                        </div>
                    </div>
                </div>

                <!-- Right: Control & Logs -->
                <div style="display: flex; flex-direction: column; height: 100%;">
                    <div class="status-header">
                        <label style="margin:0; font-size: 0.75rem; letter-spacing: 0.2em; opacity: 0.6;">MISSION_CONTROL</label>
                        <div id="status" class="status-badge status-idle">IDLE</div>
                    </div>
                    
                    <div style="background: var(--input-bg); border: 1px solid var(--border); padding: 5px; border-radius: 8px; margin-bottom: 15px;">
                        <textarea id="command" rows="3" style="background: transparent; border: none; font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; resize: none;" placeholder="Defina a missão..."></textarea>
                    </div>
                    <button id="runBtn" onclick="runAgent()" style="width: 100%; margin-bottom: 25px;">LAUNCH_OPERATIONS</button>
                    
                    <label style="font-size: 0.75rem; letter-spacing: 0.2em; opacity: 0.6; margin-bottom: 10px;">TELEMETRY_LOGS</label>
                    <div id="logs" style="flex-grow: 1; height: 0; min-height: 200px; margin-top: 0;">
                        <div class="log-line" style="color: #4b5563;">[SYS] Initialising telemetry uplink...</div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let isRunning = false;

        function switchTab(tabId, event) {
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.currentTarget.classList.add('active');
        }
        
        async function runAgent() {
            if (isRunning) return;
            
            const btn = document.getElementById('runBtn');
            const status = document.getElementById('status');
            const logs = document.getElementById('logs');
            
            // Collect all inputs
            const config = {
                apiKey: document.getElementById('apiKey').value,
                provider: document.getElementById('provider').value,
                model: document.getElementById('model').value,
                baseUrl: document.getElementById('baseUrl').value,
                maxSteps: document.getElementById('maxSteps').value,
                headless: document.getElementById('headless').checked,
                streaming: document.getElementById('streaming').checked,
                email: document.getElementById('email').value,
                password: document.getElementById('password').value,
                command: document.getElementById('command').value,
                browser: {
                    browser_type: document.getElementById('browserType').value,
                    user_agent: document.getElementById('userAgent').value,
                    viewport: {
                        width: parseInt(document.getElementById('viewportWidth').value),
                        height: parseInt(document.getElementById('viewportHeight').value)
                    },
                    locale: document.getElementById('locale').value,
                    timezone: document.getElementById('timezone').value
                }
            };

            if (!config.apiKey || !config.command) {
                alert('Por favor, preencha a API Key e a Missão.');
                switchTab('config');
                return;
            }

            isRunning = true;
            btn.disabled = true;
            btn.innerText = '🤖 EM CAMPO...';
            status.innerText = 'RUNNING';
            status.className = 'status-badge status-running';
            logs.innerHTML = '';
            
            if (config.streaming) {
                document.getElementById('browserStream').style.display = 'block';
                document.getElementById('streamPlaceholder').style.display = 'none';
                startStreaming();
            }

            try {
                await fetch('/run', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(config)
                });
                pollLogs();
            } catch (e) {
                addLog('Erro de conexão: ' + e, 'error');
                stopSession();
            }
        }

        async function pollLogs() {
            const interval = setInterval(async () => {
                try {
                    const res = await fetch('/logs');
                    const data = await res.json();
                    
                    if (data.logs && data.logs.length > 0) {
                        data.logs.forEach(log => {
                            addLog(log.msg, log.type, log.reasoning);
                        });
                    }

                    if (data.status === 'completed') {
                        clearInterval(interval);
                        stopStreaming();
                        stopSession();
                    }
                } catch (e) {
                    clearInterval(interval);
                    stopSession();
                }
            }, 800);
        }

        let streamInterval = null;
        function startStreaming() {
            const img = document.getElementById('browserStream');
            streamInterval = setInterval(async () => {
                try {
                    const res = await fetch('/screenshot');
                    const data = await res.json();
                    if (data.image) {
                        img.src = 'data:image/jpeg;base64,' + data.image;
                    }
                } catch (e) {}
            }, 1000);
        }

        function stopStreaming() {
            if (streamInterval) clearInterval(streamInterval);
        }

        function addLog(msg, type, reasoning = null) {
            const logsDiv = document.getElementById('logs');
            const line = document.createElement('div');
            line.className = 'log-line';
            
            // Basic ANSI color stripping for clean WebUI (optional, but good for readability)
            let cleanMsg = msg.replace(/\033\[[0-9;]*m/g, '');
            line.innerText = cleanMsg;
            
            if (cleanMsg.includes('ℹ️')) line.classList.add('log-info');
            if (cleanMsg.includes('⚡')) line.classList.add('log-action');
            if (cleanMsg.includes('✅')) line.classList.add('log-success');
            if (cleanMsg.includes('⚠️')) line.classList.add('log-warning');
            if (cleanMsg.includes('❌')) line.classList.add('log-error');
            
            if (type === 'terminal') {
                line.classList.add('log-terminal');
            }
            
            logsDiv.appendChild(line);
            
            if (reasoning) {
                const reasonLine = document.createElement('div');
                reasonLine.className = 'log-line log-reasoning';
                reasonLine.innerText = ' > reasoning: ' + reasoning;
                logsDiv.appendChild(reasonLine);
            }
            
            logsDiv.scrollTop = logsDiv.scrollHeight;
        }

        function stopSession() {
            isRunning = false;
            const btn = document.getElementById('runBtn');
            const status = document.getElementById('status');
            btn.disabled = false;
            btn.innerText = '🚀 REINICIAR MISSÃO';
            status.innerText = 'IDLE';
            status.className = 'status-badge status-idle';
        }
    </script>
</body>
</html>
"""

app = Flask(__name__)
session_data = {
    "logs": [],
    "status": "idle",
    "agent": None,
    "last_screenshot": ""
}

# Terminal Output Redirection
class TerminalStream(io.TextIOBase):
    def __init__(self, original_stream):
        self.original_stream = original_stream

    def write(self, s):
        if s.strip():
            session_data["logs"].append({"msg": s.strip(), "type": "terminal"})
        self.original_stream.write(s)
        return len(s)

    def flush(self):
        self.original_stream.flush()

sys.stdout = TerminalStream(sys.stdout)
sys.stderr = TerminalStream(sys.stderr)

async def log_collector(data):
    agent = session_data.get("agent")
    if agent and agent.browser:
        try:
            session_data["last_screenshot"] = await agent.browser.get_screenshot()
        except:
            pass
    
    # Reasoning is already captured via Stdout redirection because Logger prints it
    # But we can add extra structure if needed
    pass

def run_agent_sync(config):
    global session_data
    session_data["status"] = "running"
    session_data["logs"] = []
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    agent_model = config.get("model") if config.get("model") and config.get("model").strip() else None
    
    agent = Agent(
        api_key=config.get("apiKey"),
        provider=config.get("provider"),
        model=agent_model,
        base_url=config.get("baseUrl"),
        headless=config.get("headless"),
        email=config.get("email"),
        password=config.get("password"),
        browser_config=config.get("browser")
    )
    session_data["agent"] = agent
    
    # Override max_steps if provided
    if config.get("maxSteps"):
        try: agent.max_steps = int(config.get("maxSteps"))
        except: pass

    try:
        loop.run_until_complete(agent.execute(config.get("command"), on_step=log_collector))
    except Exception as e:
        session_data["logs"].append({"msg": f"Erro: {str(e)}", "type": "error"})
    finally:
        session_data["status"] = "completed"
        session_data["agent"] = None
        loop.close()

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/run", methods=["POST"])
def run():
    config = request.json
    thread = threading.Thread(target=run_agent_sync, args=(config,))
    thread.start()
    return jsonify({"status": "started"})

@app.route("/logs")
def get_logs():
    logs = session_data["logs"]
    session_data["logs"] = [] 
    return jsonify({"logs": logs, "status": session_data["status"]})

@app.route("/screenshot")
def get_screenshot():
    # Retorna o último screenshot capturado sem bloquear o loop principal
    return jsonify({"image": session_data.get("last_screenshot", "")})

def launch_ui(port=5000):
    print(f"\n🚀 OperantID Playground subindo em: http://127.0.0.1:{port}")
    app.run(port=port)
