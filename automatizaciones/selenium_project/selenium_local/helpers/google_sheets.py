import logging
import os

import gspread
from google.oauth2.service_account import Credentials

# Nombre de tu planilla
SHEET_NAME = "Alta_Personas_1_Caso"

# Logging opcional
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def conectar_google_sheets():
    """Conecta con Google Sheets usando el archivo de credenciales del mismo directorio."""
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    # Ruta absoluta al archivo de credenciales
    current_dir = os.path.dirname(os.path.abspath(__file__))
    credentials_path = os.path.join(current_dir, "credentials.json")

    if not os.path.exists(credentials_path):
        raise FileNotFoundError(
            f"No se encontró el archivo de credenciales en: {credentials_path}"
        )

    creds = Credentials.from_service_account_file(credentials_path, scopes=scope)
    client = gspread.authorize(creds)
    logger.info(
        f"Conectado correctamente a Google Sheets con credenciales: {credentials_path}"
    )
    return client.open(SHEET_NAME).sheet1


def obtener_cuit_pendiente():
    """Devuelve (fila, cuit) del primer registro pendiente o con error."""
    sheet = conectar_google_sheets()
    data = sheet.get_all_records()

    for i, row in enumerate(data, start=2):  # salta encabezado
        leido = str(row.get("Leido", "")).strip().upper()
        cuit = str(row.get("CUIT", "")).strip()

        if leido in ("", "ERROR") and cuit:
            logger.info(f"CUIT pendiente encontrado: {cuit} (fila {i})")
            return i, cuit

    logger.warning("No se encontraron CUITs pendientes o con error.")
    return None, None


def marcar_leido(fila, estado, mensaje=""):
    """Marca el registro como leído o error en la planilla."""
    sheet = conectar_google_sheets()
    sheet.update_acell(f"AD{fila}", estado)  # Columna 'Leido'
    sheet.update_acell(f"AE{fila}", mensaje)  # Columna 'Mensaje'
    logger.info(f"Fila {fila} actualizada en planilla: {estado} - {mensaje}")


import logging

import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1Nqoawsr2SxF-1kmPDI6B8nUi5kRgmaPkYzcgQDsocSg/edit?gid=0"

def conectar_hoja():
    """Devuelve una instancia del worksheet."""
    credentials = Credentials.from_service_account_file(
        r"C:\Users\aflores\mi-proyecto-cypress\automatizaciones\selenium_project\selenium_local\helpers\credentials.json",
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    gc = gspread.authorize(credentials)
    sheet = gc.open_by_url(SPREADSHEET_URL).sheet1
    return sheet


def actualizar_datos_cuenta(fila_index, numero_cuenta, numero_documento):
    """
    Inserta el número de cuenta y documento en las columnas correspondientes
    dentro de la misma fila del CUIT procesado.
    """
    try:
        sheet = conectar_hoja()
        registros = sheet.row_values(1)
        # Buscar columnas destino
        col_cuenta = None
        col_doc = None
        for i, col in enumerate(registros, start=1):
            if col.strip().lower() == "numerocuenta":
                col_cuenta = i
            elif col.strip().lower() == "numerodocumento":
                col_doc = i

        if not col_cuenta or not col_doc:
            logger.warning("No se encontraron columnas NumeroCuenta o NumeroDocumento en la hoja.")
            return

        # Actualizar valores
        sheet.update_cell(fila_index, col_cuenta, numero_cuenta)
        sheet.update_cell(fila_index, col_doc, numero_documento)
        logger.info(f"Datos actualizados en fila {fila_index}: Cuenta={numero_cuenta}, Documento={numero_documento}")
    except Exception as e:
        logger.error(f"Error al actualizar datos de cuenta/documento en planilla: {e}")
