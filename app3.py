from flask import Flask, render_template_string, request, redirect, session, jsonify
import subprocess
import os
import datetime
import random
import time
import socket
import threading
import string

app = Flask(__name__)
app.secret_key = 'zp_cloud_ios26_style_2026'

vm_list = []
BACKUP_DIR = "/tmp/zp_user_backup"
os.makedirs(BACKUP_DIR, exist_ok=True)

# กำหนดพอร์ตจำลองสำหรับ Linux GUI ทั้งหมด 4 พอร์ต
AVAILABLE_PORTS = [6311, 6312, 6313, 6314]
used_ports = set()

# ฟังก์ชันสั่งรัน VNC และ websockify อัตโนมัติใน Termux
def setup_and_start_vnc(novnc_port):
    vnc_display = ":" + str(novnc_port - 6310)  # แปลงพอร์ตเป็นเลขจอ เช่น 6311 กลายเป็น :1
    
    commands = [
        f"vncserver {vnc_display} -geometry 1280x720 -depth 24 || true",
        f"nohup websockify --web /data/data/com.termux/files/usr/share/novnc {novnc_port} localhost:590{novnc_port - 6310} > /dev/null 2>&1 &"
    ]
    
    full_cmd = " && ".join(commands)
    try:
        subprocess.run(full_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"Error starting VNC/websockify: {e}")

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
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif;
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
            z-index: -1;
        }

        .container { width: 100%; max-width: 460px; box-sizing: border-box; }

        .top-bar {
            background: var(--bg-glass);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border-glass);
            border-radius: 16px;
            padding: 12px 18px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            font-size: 13px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), var(--neon-glow);
        }

        .badge-pro {
            background: rgba(48, 209, 88, 0.2);
            color: var(--neon-green);
            border: 1px solid rgba(48, 209, 88, 0.4);
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 700;
        }

        .status-ready { color: var(--neon-green); font-size: 12px; font-weight: 600; }

        .card, .terminal-card {
            background: var(--bg-glass);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border-glass);
            border-radius: 16px;
            padding: 18px;
            margin-bottom: 12px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), var(--neon-glow);
            width: 100%;
            box-sizing: border-box;
        }

        .section-title {
            color: var(--neon-cyan);
            font-size: 14px;
            font-weight: 700;
            margin-bottom: 14px;
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
            box-shadow: 0 0 20px rgba(48, 209, 88, 0.5);
        }

        .btn-gui {
            padding: 8px 14px;
            font-weight: 700;
            border-radius: 8px;
            font-size: 12px;
            text-decoration: none;
            display: inline-block;
            margin-top: 6px;
            border: none;
            text-align: center;
        }

        .btn-ready { background: var(--neon-green); color: #05070c; box-shadow: 0 0 15px rgba(48, 209, 88, 0.5); }
        .btn-unlimited { background: var(--neon-cyan); color: #05070c; box-shadow: 0 0 15px rgba(50, 173, 230, 0.5); }
        .btn-expired { background: var(--neon-pink); color: #fff; pointer-events: none; }
        
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
        }

        .timer-badge {
            color: var(--neon-yellow);
            font-weight: 700;
            background: rgba(255, 214, 10, 0.1);
            border: 1px solid rgba(255, 214, 10, 0.3);
            padding: 6px;
            border-radius: 6px;
            text-align: center;
            margin-top: 6px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="top-bar">
            <div><b>ZP Cloud 🇹🇭</b> : <span class="badge-pro">iOS 26 Neon</span></div>
            <div class="status-ready">พร้อมใช้งาน 🟢</div>
        </div>

        <div class="card">
            <div class="section-title">Server Config & Package Setup</div>
            <form id="createForm" method="POST" action="/create-vm">
                <div class="form-group">
                    เลือกประเภทแพ็กเกจ
                    <select name="package_type" class="form-control">
                        <option value="daily">รายวัน (จำกัด 4 นาที)</option>
                        <option value="weekly">รายสัปดาห์ (ไม่จำกัดเวลา 🟢)</option>
                        <option value="monthly">รายเดือน (ไม่จำกัดเวลา 🟢)</option>
                    </select>
                </div>

                <div class="form-group">
                    เลือก OS (ระบบปฏิบัติการ)
                    <select name="os_choice" class="form-control">
                        <option value="Ubuntu">Ubuntu (มาตรฐานเสถียร)</option>
                        <option value="Kali">Kali (สายเจาะระบบ)</option>
                        <option value="ZP" selected>ZP (Custom OS พิเศษ)</option>
                    </select>
                </div>

                <button type="submit" class="btn-create">⚡ สั่งสร้าง Desktop อัตโนมัติ</button>
            </form>
        </div>

        <div class="terminal-card">
            <div class="section-title" style="margin-bottom:8px;">Active VMs Output (สูงสุด 4 ช่อง)</div>
            {% if error_msg %}
                <div style="color:var(--neon-pink); font-size:12px; text-align:center; margin-bottom:10px; font-weight:700;">{{ error_msg }}</div>
            {% endif %}
            
            {% if vms %}
                {% for vm in vms %}
                <div class="vm-item" id="vm-box-{{ vm.id }}">
                    • Slot Port: <b style="color:var(--neon-yellow);">127.0.0.1:{{ vm.novnc_port }}</b><br>
                    • Package: <b style="color:var(--neon-yellow);">{{ vm.package_type | upper }}</b><br>
                    • Selected OS: <b style="color:var(--neon-yellow);">{{ vm.os_choice }}</b><br>
                    
                    {% if vm.package_type == 'daily' %}
                        <div class="timer-badge" id="timer-box-{{ vm.id }}">⏳ เวลาใช้งานคงเหลือ: <span id="countdown-sec-{{ vm.id }}">240</span> วินาที</div>
                        <div style="margin-top: 8px;">
                            <a id="btn-gui-{{ vm.id }}" href="http://127.0.0.1:{{ vm.novnc_port }}/vnc.html?host=127.0.0.1&port={{ vm.novnc_port }}" target="_blank" class="btn-gui btn-ready">🖥️ เปิดหน้าจอ Linux GUI</a>
                            <a href="/delete-vm/{{ vm.id }}" class="btn-delete">🗑️ ปิด / ลบสล็อต</a>
                        </div>
                        <script>
                            (function() {
                                var vmId = "{{ vm.id }}";
                                var timeLeft = 240;
                                var secElem = document.getElementById("countdown-sec-" + vmId);
                                var timerBox = document.getElementById("timer-box-" + vmId);
                                var btnGui = document.getElementById("btn-gui-" + vmId);

                                function countdownTimer() {
                                    if (timeLeft > 0) {
                                        timeLeft--;
                                        secElem.innerText = timeLeft;
                                        setTimeout(countdownTimer, 1000);
                                    } else {
                                        timerBox.innerHTML = "❌ หมดเวลาใช้งานรายวัน (4 นาที)";
                                        timerBox.style.background = "rgba(255, 55, 95, 0.1)";
                                        timerBox.style.borderColor = "rgba(255, 55, 95, 0.4)";
                                        timerBox.style.color = "var(--neon-pink)";
                                        btnGui.className = "btn-gui btn-expired";
                                        btnGui.innerText = "🔒 หมดอายุการใช้งาน";
                                        btnGui.removeAttribute("href");
                                    }
                                }
                                setTimeout(countdownTimer, 1000);
                            })();
                        </script>
                    {% else %}
                        <div class="timer-badge" style="color:var(--neon-green); background:rgba(48,209,88,0.1); border-color:rgba(48,209,88,0.3);">♾️ แพ็กเกจ VIP (ใช้งานได้ตลอดเวลา)</div>
                        <div style="margin-top: 8px;">
                            <a href="http://127.0.0.1:{{ vm.novnc_port }}/vnc.html?host=127.0.0.1&port={{ vm.novnc_port }}" target="_blank" class="btn-gui btn-unlimited">🖥️ เปิดหน้าจอ Linux GUI (VIP)</a>
                            <a href="/delete-vm/{{ vm.id }}" class="btn-delete">🗑️ ปิด / ลบสล็อต</a>
                        </div>
                    {% endif %}
                </div>
                {% endfor %}
            {% else %}
                <div style="color: #71717a; font-size: 12px; text-align: center; padding: 10px;">สล็อตว่าง (รองรับสูงสุด 4 พอร์ต)</div>
            {% endif %}
        </div>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(dashboard_template, vms=vm_list)

@app.route('/create-vm', methods=['POST'])
def create_vm():
    global vm_list, used_ports
    
    if len(vm_list) >= 4:
        return render_template_string(dashboard_template, vms=vm_list, error_msg="⚠️ สล็อตเต็ม! (เปิดใช้งานครบ 4 พอร์ตแล้ว)")

    available_slot = None
    for p in AVAILABLE_PORTS:
        if p not in used_ports:
            available_slot = p
            break
            
    if not available_slot:
        return render_template_string(dashboard_template, vms=vm_list, error_msg="⚠️ พอร์ตเต็มทั้ง 4 ช่อง")

    used_ports.add(available_slot)
    os_choice = request.form.get('os_choice', 'Ubuntu')
    package_type = request.form.get('package_type', 'daily')
    vm_id = str(random.randint(1000, 9999))
    
    # สั่งให้ Termux รัน VNC และ websockify ไปที่พอร์ตนั้นๆ ทันทีในเบื้องหลัง
    threading.Thread(target=setup_and_start_vnc, args=(available_slot,)).start()
    
    vm_data = {
        "id": vm_id,
        "os_choice": os_choice,
        "package_type": package_type,
        "novnc_port": available_slot
    }
    
    vm_list.append(vm_data)
    return redirect('/')

@app.route('/delete-vm/<vm_id>')
def delete_vm(vm_id):
    global vm_list, used_ports
    for vm in vm_list:
        if vm['id'] == vm_id:
            used_ports.discard(vm['novnc_port'])
            
    vm_list = [vm for vm in vm_list if vm['id'] != vm_id]
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
