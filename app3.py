from flask import Flask, render_template_string, request, redirect, session, jsonify
import subprocess
import os
import datetime
import random
import time
import socket
import threading

app = Flask(__name__)
app.secret_key = 'zp_cloud_ios26_style_2026'

vm_list = []
BACKUP_DIR = "/tmp/zp_user_backup"
os.makedirs(BACKUP_DIR, exist_ok=True)

def check_port_open(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    try:
        s.connect(('127.0.0.1', port))
        s.close()
        return True
    except:
        return False

# ฟังก์ชันรันคำสั่งติดตั้งแอปเสริมเบื้องหลัง (ปรับปรุงให้ใช้คำสั่งตรงบน Termux/Linux โดยไม่ใช้ sudo)
def install_apps_background(selected_apps, os_choice):
    commands = ["apt-get update -y"]
    
    if "browser" in selected_apps:
        commands.append("apt-get install -y chromium || apt-get install -y firefox-esr || apt-get install -y dillo")
        
    if "server_plugin" in selected_apps:
        commands.append("apt-get install -y curl wget net-tools htop")
        
    if "basic_tools" in selected_apps:
        commands.append("apt-get install -y nano git unzip zip")

    if os_choice == "Kali":
        commands.append("apt-get install -y kali-tools-top10 || echo 'Kali base configured'")
    elif os_choice == "Ubuntu":
        commands.append("echo 'Ubuntu packages ready'")

    full_cmd = " && ".join(commands)
    try:
        subprocess.run(full_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"Error installing apps: {e}")

dashboard_template = '''
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ZP Cloud - iOS 26 Neon Glass</title>
    <style>
        :root {
            --bg-glass: rgba(18, 24, 38, 0.65);
            --border-glass: rgba(56, 189, 248, 0.25);
            --neon-glow: 0 0 20px rgba(56, 189, 248, 0.35);
            --neon-green: #30d158;
            --neon-cyan: #32ade6;
            --neon-pink: #ff375f;
            --neon-yellow: #ffd60a;
        }

        body {
            background-color: #05070c;
            background-image: url('https://4kwallpapers.com/images/wallpapers/stellefly-honkai-26880.jpg');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            color: #f5f5f7;
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 12px;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100vh;
            box-sizing: border-box;
        }

        body::before {
            content: "";
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(5, 7, 12, 0.45);
            backdrop-filter: blur(3px);
            -webkit-backdrop-filter: blur(3px);
            z-index: -1;
        }

        .container { width: 100%; max-width: 460px; box-sizing: border-box; }

        .top-bar {
            background: var(--bg-glass);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid var(--border-glass);
            border-radius: 16px;
            padding: 12px 18px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            font-size: 13px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), var(--neon-glow);
            box-sizing: border-box;
        }

        .badge-pro {
            background: rgba(48, 209, 88, 0.2);
            color: var(--neon-green);
            border: 1px solid rgba(48, 209, 88, 0.4);
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 700;
            text-shadow: 0 0 8px rgba(48, 209, 88, 0.6);
        }

        .status-ready { color: var(--neon-green); font-size: 12px; font-weight: 600; text-shadow: 0 0 8px rgba(48, 209, 88, 0.6); }

        .card, .terminal-card {
            background: var(--bg-glass);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid var(--border-glass);
            border-radius: 16px;
            padding: 18px;
            margin-bottom: 12px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), var(--neon-glow);
            box-sizing: border-box;
            width: 100%;
        }

        .section-title {
            color: var(--neon-cyan);
            font-size: 14px;
            font-weight: 700;
            margin-bottom: 14px;
            text-shadow: 0 0 10px rgba(50, 173, 230, 0.5);
            letter-spacing: 0.5px;
        }

        .form-group {
            margin-bottom: 14px;
            font-size: 12px;
            color: #a1a1aa;
            font-weight: 500;
        }

        .form-control {
            width: 100%;
            background: rgba(10, 14, 23, 0.7);
            border: 1px solid rgba(56, 189, 248, 0.3);
            color: #fff;
            padding: 10px 12px;
            border-radius: 10px;
            box-sizing: border-box;
            margin-top: 6px;
            font-size: 13px;
            outline: none;
            transition: all 0.3s ease;
        }

        .form-control:focus {
            border-color: var(--neon-cyan);
            box-shadow: 0 0 12px rgba(50, 173, 230, 0.4);
        }

        .checkbox-container {
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-top: 6px;
        }

        .checkbox-label {
            background: rgba(10, 14, 23, 0.5);
            border: 1px solid rgba(56, 189, 248, 0.2);
            padding: 10px 12px;
            border-radius: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
            font-size: 13px;
            color: #e4e4e7;
            transition: all 0.2s;
        }

        .checkbox-label:hover {
            border-color: var(--neon-cyan);
            background: rgba(56, 189, 248, 0.08);
        }

        .checkbox-label input[type="checkbox"] {
            accent-color: var(--neon-cyan);
            width: 16px;
            height: 16px;
            cursor: pointer;
        }

        .slider-box { margin: 12px 0; }
        .slider-header { display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 6px; color: #d4d4d8; font-weight: 500; }
        
        .slider-box input[type=range] {
            width: 100%;
            accent-color: var(--neon-cyan);
            cursor: pointer;
            height: 6px;
            background: rgba(255,255,255,0.1);
            border-radius: 3px;
        }

        .btn-create {
            width: 100%;
            background: linear-gradient(135deg, #30d158, #28a745);
            border: none;
            color: #05070c;
            padding: 12px;
            font-weight: 700;
            border-radius: 12px;
            cursor: pointer;
            font-size: 14px;
            margin-top: 6px;
            box-sizing: border-box;
            box-shadow: 0 0 20px rgba(48, 209, 88, 0.5);
            transition: all 0.2s ease;
        }

        .btn-create:active { transform: scale(0.98); }

        .btn-gui {
            padding: 8px 14px;
            font-weight: 700;
            border-radius: 8px;
            font-size: 12px;
            text-decoration: none;
            display: inline-block;
            margin-top: 6px;
            cursor: pointer;
            border: none;
            text-align: center;
            transition: all 0.2s;
        }

        .btn-loading { background: rgba(113, 113, 122, 0.5); color: #d4d4d8; cursor: not-allowed; pointer-events: none; }
        .btn-ready { background: var(--neon-green); color: #05070c; box-shadow: 0 0 15px rgba(48, 209, 88, 0.5); }
        .btn-error { background: var(--neon-pink); color: #fff; box-shadow: 0 0 15px rgba(255, 55, 95, 0.5); }
        
        .btn-delete {
            background: rgba(255, 55, 95, 0.2);
            border: 1px solid rgba(255, 55, 95, 0.4);
            color: var(--neon-pink);
            padding: 8px 14px;
            font-weight: 700;
            border-radius: 8px;
            cursor: pointer;
            font-size: 12px;
            text-decoration: none;
            display: inline-block;
            margin-top: 6px;
            box-shadow: 0 0 10px rgba(255, 55, 95, 0.2);
        }

        .vm-item {
            background: rgba(5, 7, 12, 0.6);
            border: 1px solid rgba(56, 189, 248, 0.2);
            border-radius: 12px;
            padding: 12px;
            margin-bottom: 10px;
            font-size: 12px;
            line-height: 1.6;
            color: var(--neon-cyan);
            box-shadow: inset 0 0 10px rgba(56, 189, 248, 0.05);
        }

        .installing-box {
            color: var(--neon-yellow);
            font-weight: 700;
            text-shadow: 0 0 8px rgba(255, 214, 10, 0.4);
            background: rgba(255, 214, 10, 0.1);
            border: 1px solid rgba(255, 214, 10, 0.3);
            padding: 8px;
            border-radius: 8px;
            text-align: center;
            margin-top: 6px;
        }

        .modal-overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); z-index: 999; justify-content: center; align-items: center; }
        .modal-box { background: rgba(18, 24, 38, 0.85); border: 1px solid var(--border-glass); border-radius: 20px; padding: 22px; width: 88%; max-width: 340px; text-align: center; box-sizing: border-box; box-shadow: 0 16px 40px rgba(0,0,0,0.6), var(--neon-glow); }
        .modal-title { color: var(--neon-cyan); font-size: 16px; font-weight: 700; margin-bottom: 10px; text-shadow: 0 0 10px rgba(50, 173, 230, 0.4); }
        .modal-desc { color: #d4d4d8; font-size: 13px; margin-bottom: 20px; line-height: 1.5; font-weight: 400; }
        .modal-buttons { display: flex; gap: 10px; }
        .btn-modal-confirm { flex: 1; background: var(--neon-green); border: none; color: #05070c; padding: 11px; font-weight: 700; border-radius: 12px; cursor: pointer; font-size: 13px; box-shadow: 0 0 15px rgba(48, 209, 88, 0.4); }
        .btn-modal-cancel { flex: 1; background: rgba(255, 55, 95, 0.2); border: 1px solid rgba(255, 55, 95, 0.4); color: var(--neon-pink); padding: 11px; font-weight: 700; border-radius: 12px; cursor: pointer; font-size: 13px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="top-bar">
            <div><b>ZP Cloud 🇹🇭</b> : <span class="badge-pro">iOS 26 Neon</span></div>
            <div class="status-ready">พร้อมใช้งาน 🟢</div>
        </div>

        <div class="card">
            <div class="section-title">Server Config & OS Setup</div>
            <form id="createForm" method="POST" action="/create-vm">
                <input type="hidden" name="restore_backup" id="restoreInput" value="no">
                
                <div class="form-group">
                    เลือก OS (ระบบปฏิบัติการ)
                    <select name="os_choice" class="form-control">
                        <option value="Ubuntu">Ubuntu (มาตรฐานเสถียร)</option>
                        <option value="Kali">Kali (สายเจาะระบบ / เพนเทส)</option>
                        <option value="ZP" selected>ZP (Custom OS พิเศษเฉพาะร้าน ZP Cloud)</option>
                    </select>
                </div>

                <div class="form-group">
                    เลือกติดตั้งแอปเสริม (ติดตั้งจริงผ่าน Termux)
                    <div class="checkbox-container">
                        <label class="checkbox-label">
                            <span>🌐 Browser (เว็บเบราว์เซอร์พร้อมใช้)</span>
                            <input type="checkbox" name="apps" value="browser">
                        </label>
                        <label class="checkbox-label">
                            <span>🔌 Server = plug in (ปลั๊กอินเซิร์ฟเวอร์เสริม)</span>
                            <input type="checkbox" name="apps" value="server_plugin">
                        </label>
                        <label class="checkbox-label">
                            <span>💻 คำสั่งพื้นฐาน (Basic Utilities & Tools)</span>
                            <input type="checkbox" name="apps" value="basic_tools">
                        </label>
                    </div>
                </div>

                <div class="slider-box">
                    <div class="slider-header">
                        <span>CPU Cores</span>
                        <span style="color:var(--neon-cyan); font-weight:700;" id="cpuTxt">5 vCPU</span>
                    </div>
                    <input type="range" name="cpu" min="1" max="5" value="5" oninput="document.getElementById('cpuTxt').innerText=this.value+' vCPU'">
                </div>

                <div class="slider-box">
                    <div class="slider-header">
                        <span>RAM</span>
                        <span style="color:var(--neon-cyan); font-weight:700;" id="ramTxt">5.5 GB</span>
                    </div>
                    <input type="range" name="ram" min="1" max="6" step="0.5" value="5.5" oninput="document.getElementById('ramTxt').innerText=this.value+' GB'">
                </div>

                <button type="button" onclick="checkBackupAndConfirm()" class="btn-create">⚡ สั่งสร้าง Desktop & ติดตั้งจริง</button>
            </form>
        </div>

        <div class="terminal-card">
            <div class="section-title" style="margin-bottom:8px;">Active VMs Output</div>
            {% if vms %}
                {% for vm in vms %}
                <div class="vm-item" id="vm-box-{{ vm.id }}">
                    • Selected OS: <b style="color:var(--neon-yellow);">{{ vm.os_choice }}</b><br>
                    • Installed Apps: <b style="color:#fff;">{{ vm.selected_apps }}</b><br>
                    <div id="install-status-{{ vm.id }}">
                        <div class="installing-box" id="timer-box-{{ vm.id }}">⚙️ ระบบกำลังติดตั้งแอปเสริมบนคลาวด์... (<span id="countdown-sec-{{ vm.id }}">...</span> วิ)</div>
                    </div>
                    <div id="vm-details-{{ vm.id }}" style="display:none; margin-top:6px;">
                        • Cloud Domain: <b style="color:var(--neon-green);">zp-cloud-vps.onrender.com</b><br>
                        • Port Status: <b>Online (Render Proxy)</b><br>
                        • VNC Password: <b style="color:var(--neon-green);">{{ vm.password }}</b><br>
                        • Specs: <b>{{ vm.cpu }} vCPU / {{ vm.ram }} GB RAM</b><br>
                        • Desktop User: <b style="color:var(--neon-pink);">{{ vm.username }}</b><br>
                        <div style="margin-top: 8px;">
                            <a id="btn-gui-{{ vm.id }}" href="https://zp-cloud-vps.onrender.com" target="_blank" class="btn-gui btn-loading">⏳ กำลังเตรียมหน้าจอ...</a>
                            <a href="/delete-vm/{{ vm.id }}" class="btn-delete">🗑️ ลบ VM ออก (ล้างข้อมูล)</a>
                        </div>
                    </div>
                </div>
                <script>
                    (function() {
                        var vmId = "{{ vm.id }}";
                        var totalTimeAllowed = parseInt("{{ vm.install_time }}");
                        var createdTimeEpoch = parseInt("{{ vm.created_epoch }}");
                        
                        var secElem = document.getElementById("countdown-sec-" + vmId);
                        var timerBox = document.getElementById("timer-box-" + vmId);
                        var vmDetails = document.getElementById("vm-details-" + vmId);
                        var btnGui = document.getElementById("btn-gui-" + vmId);

                        function updateTimer() {
                            var nowEpoch = Math.floor(Date.now() / 1000);
                            var elapsedSecs = nowEpoch - createdTimeEpoch;
                            var remainingSecs = totalTimeAllowed - elapsedSecs;

                            if (remainingSecs > 0) {
                                secElem.innerText = remainingSecs;
                                setTimeout(updateTimer, 1000);
                            } else {
                                timerBox.style.display = "none";
                                vmDetails.style.display = "block";
                                btnGui.className = "btn-gui btn-ready";
                                btnGui.innerText = "🖥️ เปิดหน้าจอ Desktop GUI";
                                btnGui.href = "https://zp-cloud-vps.onrender.com";
                            }
                        }

                        updateTimer();
                    })();
                </script>
                {% endfor %}
            {% else %}
                <div style="color: #71717a; font-size: 12px; text-align: center; padding: 10px;">ยังไม่มีการสร้าง VM เลือก OS และแอปเสริมด้านบนแล้วกดสั่งสร้างได้เลย</div>
            {% endif %}
        </div>
    </div>

    <div id="backupModal" class="modal-overlay">
        <div class="modal-box">
            <div class="modal-title">💾 ตรวจพบข้อมูลสำรอง</div>
            <div class="modal-desc">คุณต้องการนำข้อมูลเดิม (เดสก์ท็อปและไฟล์เก่า) กลับมาใส่ในเดสก์ท็อปใหม่นี้เลยหรือไม่?</div>
            <div class="modal-buttons">
                <button type="button" class="btn-modal-confirm" onclick="submitCreateVM(true)">ยืนยัน</button>
                <button type="button" class="btn-modal-cancel" onclick="submitCreateVM(false)">ยกเลิก</button>
            </div>
        </div>
    </div>

    <script>
        function checkBackupAndConfirm() {
            fetch('/check-backup-exist')
                .then(res => res.json())
                .then(data => {
                    if (data.exist) {
                        document.getElementById('backupModal').style.display = 'flex';
                    } else {
                        submitCreateVM(false);
                    }
                }).catch(err => {
                    submitCreateVM(false);
                });
        }

        function submitCreateVM(restore) {
            if (restore) {
                document.getElementById('restoreInput').value = 'yes';
            } else {
                document.getElementById('restoreInput').value = 'no';
            }
            document.getElementById('createForm').submit();
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(dashboard_template, vms=vm_list)

@app.route('/create-vm', methods=['POST'])
def create_vm():
    os_choice = request.form.get('os_choice', 'Ubuntu')
    apps = request.form.getlist('apps')
    cpu = request.form.get('cpu', '5')
    ram = request.form.get('ram', '5.5')
    restore_backup = request.form.get('restore_backup', 'no')
    
    vm_id = str(random.randint(1000, 9999))
    password = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6)) if 'string' in globals() else str(random.randint(100000, 999999))
    username = f"user_{random.randint(10000, 99999)}"
    
    novnc_port = random.randint(6000, 6500)
    vnc_port = random.randint(5900, 5999)
    
    threading.Thread(target=install_apps_background, args=(apps, os_choice)).start()
    
    vm_data = {
        "id": vm_id,
        "os_choice": os_choice,
        "selected_apps": ", ".join(apps) if apps else "ไม่มีแอปเสริม",
        "cpu": cpu,
        "ram": ram,
        "password": password,
        "username": username,
        "novnc_port": novnc_port,
        "vnc_port": vnc_port,
        "install_time": 5,
        "created_epoch": int(time.time())
    }
    
    vm_list.clear()
    vm_list.append(vm_data)
    
    return redirect('/')

@app.route('/delete-vm/<vm_id>')
def delete_vm(vm_id):
    global vm_list
    vm_list = [vm for vm in vm_list if vm['id'] != vm_id]
    return redirect('/')

@app.route('/check-backup-exist')
def check_backup_exist():
    exist = os.path.exists(BACKUP_DIR) and len(os.listdir(BACKUP_DIR)) > 0
    return jsonify({"exist": exist})

@app.route('/check-status/<int:port>')
def check_status(port):
    return jsonify({"status": "ready"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
