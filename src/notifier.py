import os
import json
import urllib.request
import urllib.error
from typing import List, Dict, Any

def send_telegram_notification(jobs_summary: List[Dict[str, Any]]) -> bool:
    """
    Envía una alerta estructurada a Telegram con el resumen de vacantes y enlaces directos.
    Usa la librería estándar urllib para no requerir dependencias externas.
    Requiere las variables de entorno:
      - TELEGRAM_BOT_TOKEN
      - TELEGRAM_CHAT_ID
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("ℹ️ Telegram: TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID no configurados. Saltando notificación.")
        return False
        
    if not jobs_summary:
        return False

    message_lines = [
        "🎯 *Nuevas Vacantes Detectadas en Berlín (Indeed)*",
        f"📅 _Revisión programada: {len(jobs_summary)} vacantes compatibles encontradas_\n"
    ]
    
    for job in jobs_summary:
        score = job.get("score", 0)
        company = job.get("company", "Empresa")
        title = job.get("title", "Cargo")
        url = job.get("url", "#")
        folder = job.get("folder", "")
        
        message_lines.append(
            f"🏢 *{company}* ({score}% match)\n"
            f"💼 _{title}_\n"
            f"🔗 [Postular en Indeed]({url})\n"
            f"📁 Borrador listo en: `{folder}`\n"
        )
        
    message_lines.append("⚡ _Revisa tu carpeta `vacantes_para_enviar/` para ver tu CV adaptado y Cover Letter._")
    
    payload = {
        "chat_id": chat_id,
        "text": "\n".join(message_lines),
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    
    api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(api_url, data=data, headers={"Content-Type": "application/json"})
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                print("✅ Notificación enviada con éxito a Telegram.")
                return True
            else:
                print(f"⚠️ Error al enviar a Telegram (status {response.status})")
                return False
    except urllib.error.URLError as e:
        print(f"⚠️ Error de conexión con Telegram: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Excepción en notificación Telegram: {e}")
        return False
