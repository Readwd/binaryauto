import re
import time
from datetime import datetime
from telethon import TelegramClient, events
from zoneinfo import ZoneInfo
from .estrategias import senal_telegram
from quotexbot import utils
import asyncio


class TelegramSignalHandler:
    def __init__(self, telegram_path="telegram.txt", zona_local="Asia/Kolkata", bot=None):
        telegram = utils.cargar_config(telegram_path)
        self.api_id = int(telegram.get("api_id"))
        self.api_hash = telegram.get("api_hash")
        self.canal = telegram.get("canal")
        #self.canal = "@mysignal72_bot"
        self.zona_local = zona_local
        self.bot = bot
        self.client_tele = TelegramClient('sesion_senales', self.api_id, self.api_hash)
        self.activo_callback = None

    def normalizar_asset(self, raw_asset: str) -> str:
        return raw_asset.replace("-OTC", "_otc")

    def convertir_a_local(self, hora_str):
        try:
            ahora = datetime.now(ZoneInfo(self.zona_local))
            hora_local = datetime.strptime(hora_str, "%H:%M:%S").replace(
                year=ahora.year,
                month=ahora.month,
                day=ahora.day,
                tzinfo=ZoneInfo(self.zona_local)
            )
            return hora_local
        except Exception as e:
            print(f"⚠️ Error al convertir hora: {e}")
            return None

    async def esperar_y_ejecutar_senal(self, asset, tipo, hora_objetivo):
        try:
            await asyncio.sleep((hora_objetivo - datetime.now(ZoneInfo(self.zona_local))).total_seconds())
            senal_telegram.set_senal_externa(tipo)
            if self.activo_callback:
                self.activo_callback(asset)
        except Exception as e:
            utils.borrar_lineas(1)
            print(f"❌ Error durante la ejecución de señal para {asset}: {e}")

    async def iniciar(self):
        async def manejar_mensaje(event):
            mensaje = event.raw_text
            print("Received message:", mensaje)  # For debugging

            # Improved regex patterns
            asset_match = re.search(r'Active Pair\s*[-»]*\s*([A-Z0-9\- ]+(?:\(OTC\)|-OTC)?)', mensaje, re.IGNORECASE)
            action_match = re.search(r'Direction\s*[-»]*\s*(CALL|PUT)', mensaje, re.IGNORECASE)
            hora_match = re.search(r'Timetable\s*[-»]*\s*(\d{2}:\d{2}(?::\d{2})?)', mensaje)

            if asset_match and action_match and hora_match:
                asset_bruto = asset_match.group(1).replace(" ", "").replace("(OTC)", "-OTC")
                tipo = action_match.group(1).lower()
                hora_raw = hora_match.group(1)
                if len(hora_raw) == 5:
                    hora_raw += ":00"  # Add seconds if missing

                par = self.normalizar_asset(asset_bruto)
                hora_local = self.convertir_a_local(hora_raw)
                if not hora_local:
                    utils.borrar_lineas(1)
                    print("⚠️ Invalid time, signal discarded.")
                    return

                ahora = datetime.now(ZoneInfo(self.zona_local))
                delta = (hora_local - ahora).total_seconds()
                if delta < -5:
                    utils.borrar_lineas(1)
                    print(f"⚠️ Signal time ({hora_local.strftime('%H:%M:%S')}) already passed. Ignored.")
                    return
                utils.borrar_lineas(1)
                print(f"📌 Signal scheduled: {tipo.upper()} on {par}, waiting until {hora_local.strftime('%H:%M:%S')}...⏳")
                asyncio.create_task(self.esperar_y_ejecutar_senal(par, tipo, hora_local))
            else:
                utils.borrar_lineas(1)
                print("⚠️ Could not extract signal from message.")

        self.client_tele.add_event_handler(manejar_mensaje, events.NewMessage(chats=self.canal))
        print("🤖 Escuchando señales de Telegram...\n")
        await self.client_tele.start()