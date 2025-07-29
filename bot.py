import asyncio
import pandas as pd
import time
from datetime import datetime
from .telegram_signal_handler import TelegramSignalHandler
from quotexbot import utils
from pyquotex.stable_api import Quotex


class BotModular:
    def __init__(self, login_path="login.txt", config_path="config.txt"):
        self.config = utils.cargar_config(config_path)
        login = utils.cargar_config(login_path)

        self.client = Quotex(email=login.get("email"), password=login.get("password"), lang="es")
        
        self.telegram_handler = TelegramSignalHandler(bot=self)
        self.telegram_handler.activo_callback = self.actualizar_activo
        
        self.asset = self.config.get("asset")
        self.expiration_time = int(self.config.get("expiration_time"))
        self.entrada_actual = float(self.config.get("valor_entrada"))
        self.use_mg = self.config.get("usar_martingale") == "S"
        self.nivel_mg = int(self.config.get("niveles_martingala"))
        self.factor_mg = float(self.config.get("factor_martingale"))
        self.use_stop_win = self.config.get("use_stop_win") == "S"
        self.stop_win = int(self.config.get("stop_win"))
        self.use_stop_loss = self.config.get("use_stop_loss") == "S"
        self.stop_loss = float(self.config.get("stop_loss"))
        self.use_media_movil = self.config.get("use_media_movil") == "S"
        self.periodo_medias = int(self.config.get("periodo_medias", 5))

        self.operaciones = []
        self.nivel_actual = 0

    async def conectar(self, reintentos=5):
        for intento in range(reintentos):
            print(f">> Intentando conectar... intento {intento + 1}")
            try:
                conectado, _ = await self.client.connect()
                if conectado:
                    utils.borrar_lineas(1)
                    print("✅ Conectado correctamente.\n")
                    return True
            except Exception as e:
                print(f"Error al conectar: {e}")
            await asyncio.sleep(5)
        print("❌ No se pudo conectar después de varios intentos.")
        return False

    async def set_account(self):
        profile = await self.client.get_profile()
        balances = [("REAL", profile.live_balance) , ("PRACTICE", profile.demo_balance), ("TOURNAMENT", 0)]
        print("📊 BALANCES DISPONIBLES:\n")
        opciones_disponibles = []
        for i, balance in enumerate(balances, start=1):
            tipo, monto = balance
            print(f"   [{i}] {tipo:<10}: {monto:>8.2f}")
            opciones_disponibles.append(tipo)

        while True:
            eleccion = input("\n>> Ingresa el número de la cuenta: ").strip()
            if eleccion.isdigit() and 1 <= int(eleccion) <= len(opciones_disponibles):
                if eleccion == "3":
                    self.seleccionar_torneo()
                seleccion = opciones_disponibles[int(eleccion) - 1]
                self.client.change_account(seleccion.upper())
                break
            else:
                print("❌ Opción inválida. Por favor, elige 1 o 2.")    

        utils.borrar_lineas(len(opciones_disponibles)+4)
        print(f"{"Bienvenido/a":<17}:{profile.nick_name}\n")
        print(f"{"Tipo de cuenta":<17}:{seleccion} ${await self.client.get_balance()}")
        print(f"{'Valor entrada':<17}:{str(self.config.get('porcentaje_entrada')) + '%' + ' de la cuenta' if self.config.get('usar_porcentaje') == 'S' else self.entrada_actual}")
        if self.use_stop_win:
            print(f"{"Stop Win":<17}:{self.stop_win}")
        if self.use_stop_loss:
            print(f"{"Stop Loss":<17}:-{self.stop_loss}")
        if self.use_mg:
            print(f"{"Niveles MG":<17}:{self.nivel_mg}")
        if self.use_media_movil:
            print(f"{"Periodo":<17}:{self.periodo_medias}")

        return True

    def seleccionar_torneo(self):
        tournaments = self.client.api.account_balance.get("tournamentsBalances", {})
        
        if not tournaments:
            print("❌ No estás inscrito en ningún torneo.")
            return None

        print("\n🎯 Torneos disponibles:")
        for tournament_id, balance in tournaments.items():
            print(f"ID Torneo: {tournament_id} | Saldo: ${balance}")

        while True:
            seleccion = input("👉 Ingresa el ID del torneo que quieres usar: ").strip()
            
            if seleccion in tournaments:
                self.client.api.tournament_id = int(seleccion)
                print(f"✅ Torneo seleccionado: ID {seleccion} | Saldo: ${tournaments[seleccion]}")
                return tournaments[seleccion]
            else:
                print("⚠️ ID de torneo inválido. Intenta nuevamente.")


    async def actualizar_entrada(self):
        balance = await self.client.get_balance()
        if self.config.get("usar_porcentaje") == "S":
            porcentaje = float(self.config.get("porcentaje_entrada", 1))  # default 1%
            self.entrada_actual = max(round(balance * (porcentaje / 100), 0), 1)
        else:
            self.entrada = int(self.config.get("valor_entrada", 1))
    
    def actualizar_activo(self, nuevo_activo):
        self.asset = nuevo_activo

    async def seleccionar_activo_abierto(self, limite=20):
        print("🕵️‍♂️ Iniciando búsqueda de activos abiertos en la plataforma...")
        activos = await self.client.check_asset_open_v2()
        activos_abiertos = [
            (symbol, data['name'], data['profit'])
            for symbol, data in activos.items() if data.get('is_open', False)
        ]
        if not activos_abiertos:
            print("⚠️ No hay activos binarios abiertos.")
            return None

        activos_ordenados = sorted(activos_abiertos, key=lambda x: x[2], reverse=True)[:limite]

        utils.borrar_lineas(1)
        print("📈 Activos binarios abiertos disponibles:\n")
        col_width = 28
        text=""
        for i, (sym, name, prof) in enumerate(activos_ordenados, 1):
            text += f"[{i:^2}] {sym:^11}:{prof}%"
            if i % 4 == 0:
                text += "\n"
            else:
                text.ljust(col_width)
           
        if len(activos_ordenados) % 4 != 0:
            text += "\n"  # Salto final si no termina justo en múltiplo de 4
        print(text)

        while True:
            try:
                choice = int(input("Seleccione un activo (número): "))
                if 1 <= choice <= len(activos_ordenados):
                    utils.borrar_lineas(len(activos_ordenados)//4+4)
                    return activos_ordenados[choice - 1][0]
                else:
                    print("Número fuera de rango.")
            except ValueError:
                print("Entrada inválida, ingrese un número.")
                
    async def obtener_candles(self, asset, end_time, offset, period):
        candles = await self.client.get_candles(asset, end_time, offset, period)
        df = pd.DataFrame(candles)
        df['date'] = pd.to_datetime(df['time'], unit='s', utc=True).dt.tz_convert("America/Santiago")
        df = df[['date', 'open', 'high', 'low', 'close']]
        df = df.sort_values('date').reset_index(drop=True)
        return df

    async def ejecutar_operacion(self, signal, message_check, hora_op=None):
        nivel = 0
        entrada = self.entrada_actual
        hora = hora_op if hora_op else datetime.now().strftime('%H:%M:%S')
        total_profit = 0
        resultado_final = "❌ LOSS"

        while True:
            utils.borrar_lineas(1)
            print(message_check)
            status, buy_info = await self.client.buy(entrada, self.asset, signal, self.expiration_time)
            if not status:
                print("❌ No se pudo ejecutar la operación.")
                return
                
            resultado, profit = await self.client.check_winv2(buy_info["id"])
            total_profit += profit

            if profit > 0:
                resultado_final = "✅ WIN"
                break
            elif profit == 0:
                if self.nivel_actual == 0:
                    resultado_final = "🤝 DRAW"
                    break
                else:
                    pass
            elif not self.use_mg or nivel >= self.nivel_mg:
                resultado_final = "❌ LOSS"
                break
            else:
                nivel += 1
                entrada = round(entrada * self.factor_mg, 0)
                message_check = f">>🔁 Nivel MG {nivel} activado, nueva entrada: {entrada}, esperando resultado...⏳ "
                await asyncio.sleep(1)

        self.operaciones.append({
            "hora": hora,
            "paridad": self.asset,
            "direccion": signal.upper(),
            "inversion": self.entrada_actual,
            "resultado": resultado_final,
            "mg": nivel,
            "lucro": total_profit
        })

        ganancia_total = utils.mostrar_tabla(self.operaciones)

        if self.use_stop_win and ganancia_total >= self.stop_win:
            print("🎯 Stop Win alcanzado. Deteniendo operaciones.")
            return

        if self.use_stop_loss and ganancia_total <= -self.stop_loss:
            print("🛑 Stop Loss alcanzado. Deteniendo operaciones.")
            return

        self.nivel_actual = 0
        await self.actualizar_entrada()
        await asyncio.sleep(1)

    async def esperar_proxima_vela(self, espera, message):
        segundos = int(time.time()) % 60
        tiempo_espera = (60 - segundos + espera - 1) if segundos > espera else (espera - 1 - segundos)
        while tiempo_espera > 0:
            tiempo_espera -= 1
            utils.borrar_lineas(1)
            print(f">>{message}esperando próxima vela en {tiempo_espera} segundos...⏳")
            await asyncio.sleep(1)

    async def validar_senal(self, signal, precio_entrada, duracion=30):
        df = await self.obtener_candles(self.asset, int(time.time()), offset=60, period=60)
        if len(df) < 15:
           return False, "⚠️ No hay suficientes velas para calcular SMA"
           
        
        if self.use_media_movil:
            if not utils.validar_entrada(df, signal, self.periodo_medias):
                return False, "❌ Condición de SMA no cumplida"

        if not precio_entrada:
            return True, None
        tiempo_limite = time.time() + duracion
        
        while time.time() < tiempo_limite:
            vela = await self.client.get_candles(self.asset, int(time.time()), 60, 1)
            if not vela:
                utils.borrar_lineas(1)
                print("❌ Error al obtener precio actual.")
                await asyncio.sleep(1)
                continue
            precio_actual = vela[0]["close"]
            if (signal == "call" and precio_actual <= precio_entrada) or (signal == "put" and precio_actual >= precio_entrada):
                return True, None
            utils.borrar_lineas(1)
            print(f"Esperando mejor precio ({signal.upper()}): actual={precio_actual:.5f}, apertura={precio_entrada:.5f}...⏳")
            await asyncio.sleep(0.5)
        return False, f"⚠️ No alcanzó precio favorable en {duracion}s"

    async def trading_loop(self):
        try:
            await self.actualizar_entrada()
            strategy, _, espera_segundos, opcion = utils.get_estrategia()
    
            if opcion == "4":
                await self.telegram_handler.iniciar()
            else:
                if self.config.get("set_asset") == "S":
                    self.asset = await self.seleccionar_activo_abierto()
                    if not self.asset:
                        print("No se seleccionó activo válido. Abortando.")
                        return
                print(f"Bot iniciado con activo {self.asset}. esperando señales...\n")
    
            print("╔═════╦══════════╦═════════════╦═══════════╦═══════════╦════╦═══════════╦═════════╗")
            print("║ CTD ║   HORA   ║   PARIDAD   ║ DIRECCION ║ RESULTADO ║ MG ║ INVERSION ║  LUCRO  ║")
            print("╠═════╬══════════╬═════════════╬═══════════╬═══════════╬════╬═══════════╬═════════╣")
            print("╚═════╩══════════╩═════════════╩═══════════╬═══════════╩════╩═══════════╬═════════╣")
            print(f"{' ':>43}║{'Ganancias de la sesion':^28}║ {0.0:>7} ║")
            print(f"{' ':>43}╚════════════════════════════╩═════════╝\n\n")
    
            message = ""
            while True:
                df = None
                if opcion != "4":
                    await self.esperar_proxima_vela(espera_segundos, message) 
                    df = await self.obtener_candles(self.asset, int(time.time()) // 60 * 60, 60, 60)
                    utils.borrar_lineas(1)
                    print(">> Analizando Velas, porfavor espera...⏳")
                    
                senal = strategy(df)
                if senal:
                    precio_entrada = 0 if df is None else df.iloc[-1]["open"]
                    isValida, info = await self.validar_senal(senal, precio_entrada)
                    if isValida:
                        msg = f">>🔔 Señal de {'COMPRA' if senal == 'call' else 'VENTA'} detectada, esperando resultado...⏳ "
                        await self.ejecutar_operacion(senal, msg, hora_op=datetime.fromtimestamp(int(time.time()) // 60 * 60).strftime('%H:%M:%S'))
                    else:
                        self.operaciones.append({
                            "hora": datetime.fromtimestamp(int(time.time()) // 60 * 60).strftime('%H:%M:%S'),
                            "paridad": self.asset,
                            "direccion": senal.upper(),
                            "inversion": 0,
                            "resultado": info,
                            "mg": None,
                            "lucro": 0
                        })
    
                        ganancia_total = utils.mostrar_tabla(self.operaciones)    
                else:
                    if opcion == "4":
                        await asyncio.sleep(1)
                    else:
                        message = f"{datetime.fromtimestamp(int(time.time()) // 60 * 60).strftime('%H:%M:%S')} - No hay señal en esta vela, "
        except (KeyboardInterrupt, asyncio.CancelledError):
            print("\n🛑 Programa detenido por el usuario.")
        finally:
            print(">>Cerrando bot...")
            await self.client.close()
