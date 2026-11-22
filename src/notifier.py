import os
import requests
from typing import List, Dict, Any

def send_telegram_notification(jobs_summary: List[Dict[str, Any]]) -> bool:
    """
    Envía una alerta estructurada a Telegram con el resumen de vacantes y enlaces directos.
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
    
    text = "\n".join(message_lines)
    api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    try:
        response = requests.post(
            api_url,
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": False
            },
            timeout=10
        )
        if response.status_code == 200:
            print("✅ Notificación enviada con éxito a Telegram.")
            return True
        else:
            print(f"⚠️ Error al enviar a Telegram ({response.status_code}): {response.text}")
            return False
    except Exception as e:
        print(f"⚠️ Excepción al conectar con Telegram: {e}")
        return False
