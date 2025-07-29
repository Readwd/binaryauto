from .estrategias import ma_cross, topbot,momentum, senal_telegram
import os
import sys


def borrar_lineas(n):
    for _ in range(n):
        sys.stdout.write("\033[F")  # Subir una línea
        sys.stdout.write("\033[K")  # Borrar la línea
    sys.stdout.flush()

def cargar_config(ruta):
    ruta_base = os.path.dirname(os.path.abspath(__file__))
    ruta_completa=os.path.join(ruta_base,ruta)
    config = {}
    with open(ruta_completa, "r") as f:
        for linea in f:
            if "=" in linea:
                clave, valor = linea.strip().split("=")
                config[clave.strip()] = valor.strip()
    return config

def get_estrategia():
    m_estrategias = {
        "1": ("Cruce de medias móviles (SMA)", ma_cross.calcular_senal_ma, 60, 5),
        "2": ("TopBot", topbot.calcular_senal_topbot, 60, 2),
        "3": ("Momentum", momentum.calcular_senal_momentum, 60, 2),
        "4": ("Señales Telegram", senal_telegram.calcular_senal, 60, 2),
        "5": "Salir"
    }

    print("\n📊 Estrategias disponibles:\n")
    for clave, valor in m_estrategias.items():
        if clave == "5":
            print(f"   [{clave}] {valor}\n")
        else:
            print(f"   [{clave}] {valor[0]}")

    while True:
        eleccion = input("Seleccione una estrategia (número): ")
        if eleccion in m_estrategias:
            if eleccion == "5":
                print("🚪 Saliendo de la selección de estrategia.")
                return None
            borrar_lineas(len(m_estrategias)+4)
            print(f"✅ Estrategia seleccionada: {m_estrategias[eleccion][0]}\n")
            return m_estrategias[eleccion][1], m_estrategias[eleccion][2], m_estrategias[eleccion][3], eleccion
        else:
            print("❌ Opción no válida. Intente nuevamente.")

def validar_entrada(df, tipo_senal: str, sma_periodo):
    df['SMA'] = calcular_sma(df, sma_periodo)
    vela_actual = df.iloc[-1]
        
    if tipo_senal == "call" and vela_actual["close"] > vela_actual["SMA"]:
        return True
    elif tipo_senal == "put" and vela_actual["close"] < vela_actual["SMA"]:
        return True
    return False
    
def calcular_sma(df, periodos):
    return df['close'].rolling(window = periodos).mean()

def mostrar_tabla(operaciones):
    texto = ""
    ganancia_total = sum(op['lucro'] for op in operaciones)
    for i, op in enumerate(operaciones, start=1):
        if i == len(operaciones):
            if not op['inversion']:
                texto += f"║ {i:^3} ║ {op['hora']:^8} ║ {op['paridad']:^11} ║ {op['direccion']:^9} ║{op['resultado']:^38}║\n"
            else:
                texto += f"║ {i:^3} ║ {op['hora']:^8} ║ {op['paridad']:^11} ║ {op['direccion']:^9} ║{op['resultado']:^10}║{op['mg']:^4}║ {op['inversion']:^9} ║ {op['lucro']:>7.2f} ║\n"
    texto += "╚═════╩══════════╩═════════════╩═══════════╬═══════════╩════╩═══════════╬═════════╣\n"
    texto += f"{' ':>43}║{'Ganancias de la sesion':^28}║ {ganancia_total:>7.2f} ║\n"
    texto += f"{' ':>43}╚════════════════════════════╩═════════╝\n\n"
    borrar_lineas(5)
    print(texto)
    return ganancia_total
