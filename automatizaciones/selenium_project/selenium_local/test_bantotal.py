# Librerías externas
# Ajuste de path para ejecución en Jenkins
import sqlite3
import logging
import os
import random
import sys
import time
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


# Librerías locales (tu código)
from selenium_local.helpers import (
    esperar_y_setear_combo,
    nivel_educativo_random,
    set_gx_select,
)
from selenium_local.helpers.gx_helpers import (
    completar_fecha_nacimiento,
    completar_fecha_nacimiento_click,
    completar_fecha_nacimiento_input,
    habilitar_campo_fecha_con_click,
    ingresar_fecha_nacimiento_manual,
    intentar_con_reintento,
)

HEADLESS = True  # Cambiar a True si querés ocultar el navegador

chrome_options = Options()

# Ignorar errores de certificado (siempre recomendable en entornos de testing)
chrome_options.add_argument("--ignore-certificate-errors")

# Solo si se ejecuta sin interfaz
if HEADLESS:
    chrome_options.add_argument("--headless=new")

# Opciones comunes
# chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Crear driver
driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 20)

print("Driver inicializado correctamente.")


# Ir a la URL de login
driver.get("http://172.17.97.206:8080/btdespri/servlet/com.dlya.bantotal.hlogin")
wait = WebDriverWait(driver, 20)


# LOGIN con validación y reintento en campos
MAX_INTENTOS = 3

try:
    print("Iniciando proceso de login...")

    # Reintentar ingreso de credenciales
    for intento in range(1, MAX_INTENTOS + 1):
        try:
            print(f"Intento de ingreso de credenciales {intento}/{MAX_INTENTOS}")

            # Esperar campo de usuario
            user_input = wait.until(EC.presence_of_element_located((By.ID, "vUSER")))
            user_input.clear()
            user_input.send_keys("INSTALADOR")

            # Esperar campo de contraseña
            password_input = wait.until(
                EC.presence_of_element_located((By.NAME, "vPASSWORD"))
            )
            password_input.clear()
            password_input.send_keys("Bancor123")

            # Validar que ambos campos estén completos
            user_value = user_input.get_attribute("value").strip()
            password_value = password_input.get_attribute("value").strip()

            if not user_value or not password_value:
                raise ValueError("Campo de usuario o contraseña vacío.")

            # Validar formato del usuario
            if not user_value.isalnum():
                raise ValueError(f"Usuario contiene caracteres inválidos: {user_value}")

            print("Campos validados correctamente.")
            break  # ambos campos válidos, salir del ciclo

        except (TimeoutException, ValueError) as e:
            print(f"Error al completar credenciales (intento {intento}): {e}")
            if intento < MAX_INTENTOS:
                print("Reintentando ingreso de credenciales...")
                time.sleep(2)
            else:
                print("No se pudo validar las credenciales tras varios intentos.")

                raise

    # Clic en botón iniciar sesión
    login_button = wait.until(EC.element_to_be_clickable((By.ID, "BTNOPINICIARSESION")))
    login_button.click()
    print("Clic en botón 'Iniciar sesión' ejecutado correctamente.")

    # Esperar apertura de la nueva ventana
    wait.until(EC.number_of_windows_to_be(2))
    driver.switch_to.window(driver.window_handles[-1])
    print("Login exitoso y dentro de RealIndex.")

except TimeoutException:
    print("Timeout: no se encontró algún elemento del login.")
except ValueError as e:
    print(f"Error de validación antes de login: {e}")
except Exception as e:
    print(f"Error inesperado en el login: {e}")


# MENÚ PRINCIPAL
def click_seguro(driver, wait, xpath, descripcion="elemento"):
    try:
        elem = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
        time.sleep(0.3)
        try:
            ActionChains(driver).move_to_element(elem).click().perform()
            print(f"Se hizo clic en {descripcion}.")
        except:
            driver.execute_script("arguments[0].click();", elem)
            print(f"Clic en {descripcion} realizado mediante JavaScript.")
        return True
    except Exception as e:
        print(f"No se pudo hacer clic en {descripcion}: {e}")
        return False


click_seguro(
    driver,
    wait,
    "//a[contains(@class,'menuButton') and normalize-space(text())='Inicio']",
    "Inicio",
)
click_seguro(
    driver,
    wait,
    "//a[contains(@class,'menuItem') and contains(text(),'Menú de Clientes')]",
    "Menú de Clientes",
)
click_seguro(
    driver,
    wait,
    "//a[contains(@class,'menuLeaf') and contains(text(),'Mantenimiento de Personas')]",
    "Mantenimiento de Personas",
)


# BLOQUE PRINCIPAL
try:
    driver.switch_to.default_content()

    # NUEVO BLOQUE: esperar a que el contenedor procContainer se cargue
    print("Esperando que se cargue el iframe principal dentro de procContainer...")
    wait.until(EC.presence_of_element_located((By.ID, "procContainer")))
    iframe_principal = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located(
            (By.XPATH, "//div[@id='procContainer']//iframe[@id='1']")
        )
    )
    driver.switch_to.frame(iframe_principal)
    print("Ingresado al iframe principal (id=1) correctamente.")

    # Esperar a que se inyecte el iframe dinámico process1_stepX -
    print("Esperando a que se cargue el contenido dinámico (process1_stepX)...")
    for i in range(20):
        frames = driver.find_elements(By.TAG_NAME, "iframe")
        visibles = [f for f in frames if "visible" in (f.get_attribute("style") or "")]
        if visibles:
            iframe_inner = visibles[0]
            print(
                f"Se encontró iframe dinámico: name={iframe_inner.get_attribute('name')} style={iframe_inner.get_attribute('style')}"
            )
            driver.switch_to.frame(iframe_inner)
            break
        else:
            time.sleep(1)
    else:
        raise TimeoutException(
            "No se detectó ningún iframe visible dentro del frame principal."
        )

    # Click en botón Agregar
    agregar_btn = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//a[@id='BTNOPAGREGAR' or normalize-space(text())='Agregar']")
        )
    )
    print("Botón 'Agregar' detectado en la pantalla de mantenimiento")

    driver.execute_script(
        """
        var btn = arguments[0];
        if (btn) {
            btn.dispatchEvent(new MouseEvent('mouseover', {bubbles:true}));
            btn.dispatchEvent(new MouseEvent('mousedown', {bubbles:true}));
            btn.dispatchEvent(new MouseEvent('mouseup', {bubbles:true}));
            btn.click();
        }
    """,
        agregar_btn,
    )
    print("Click en botón 'Agregar' realizado correctamente")


except Exception as e:
    print(f"Error inesperado: {e}")

# Volver al frame principal
driver.switch_to.default_content()
iframe_principal = wait.until(
    EC.presence_of_element_located(
        (By.XPATH, "//div[@id='procContainer']//iframe[@id='1']")
    )
)
driver.switch_to.frame(iframe_principal)

# Esperar el iframe del formulario (process1_step2)
print("Esperando el iframe del formulario (nuevo iframe visible tras Agregar)...")

iframe_form = None
iframe_anterior = iframe_inner.get_attribute(
    "name"
)  # recordar el actual (ej: process-1_step0)

for i in range(40):
    frames = driver.find_elements(By.XPATH, "//iframe[starts-with(@name,'process')]")
    for f in frames:
        style = f.get_attribute("style") or ""
        name = f.get_attribute("name") or ""
        if ("visible" in style or "opacity: 1" in style) and name != iframe_anterior:
            iframe_form = f
            driver.switch_to.default_content()
            iframe_principal = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[@id='procContainer']/iframe[@id='1']")
                )
            )
            driver.switch_to.frame(iframe_principal)
            driver.switch_to.frame(iframe_form)
            print(f"Nuevo iframe detectado y activado: {name}")
            break
    if iframe_form:
        break
    time.sleep(1)
else:
    raise TimeoutException(
        "No se detectó un nuevo iframe visible tras hacer clic en Agregar."
    )


# Seleccionar país
print("Buscando selector de país...")
pais_select = wait.until(EC.element_to_be_clickable((By.ID, "vPAIS")))
Select(pais_select).select_by_visible_text("ARGENTINA")
print("País 'PERÚ' seleccionado correctamente")


# Seleccionar tipo de documento
try:
    tipo_doc_select = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.ID, "vTDOCUM"))
    )
    Select(tipo_doc_select).select_by_visible_text("C.U.I.T.")
    print("Tipo de documento seleccionado: C.U.I.T.")
except Exception as e:
    print(f"Error al seleccionar tipo de documento: {e}")


import logging
import os
import sqlite3

# CONFIGURACIÓN DE BASE LOCAL


# Ruta compartida de la base de datos SQLite
DB_PATH = r"C:\Users\aflores\.jenkins\Compartida_con_test_bantotal\dni_tracker.db"

# Crea la carpeta si no existe (evita errores en Jenkins limpio)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Logging (muestra en consola y Jenkins)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

print(f"Usando base de datos en: {DB_PATH}")
logger.info(f"Base de datos SQLite activa en: {DB_PATH}")


def inicializar_db():
    """Crea la base y la tabla tracker si no existen."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tracker (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            dni_actual INTEGER NOT NULL
        )
    """
    )
    # Valor inicial del contador
    cur.execute("INSERT OR IGNORE INTO tracker (id, dni_actual) VALUES (1, 10000250)")
    conn.commit()
    conn.close()


def obtener_y_incrementar_dni():
    """Obtiene el DNI actual y lo incrementa de forma atómica."""
    conn = sqlite3.connect(DB_PATH, isolation_level="EXCLUSIVE")
    cur = conn.cursor()
    cur.execute("BEGIN EXCLUSIVE TRANSACTION")
    cur.execute("SELECT dni_actual FROM tracker WHERE id = 1")
    row = cur.fetchone()
    if not row:
        raise RuntimeError("No se encontró registro en tracker")

    dni_actual = row[0]
    nuevo_valor = dni_actual + 1
    cur.execute("UPDATE tracker SET dni_actual = ? WHERE id = 1", (nuevo_valor,))
    conn.commit()
    conn.close()

    logger.info(f"DNI obtenido: {dni_actual} → incrementado a {nuevo_valor}")
    return dni_actual


def calcular_cuit_sin_guiones(prefijo, dni):
    """Devuelve CUIT sin guiones: PREF(2) + DNI(8) + DV(1)."""
    pref = int(prefijo)
    dni_int = int(dni)
    cuerpo = f"{pref:02d}{dni_int:08d}"
    pesos = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    total = sum(int(d) * w for d, w in zip(cuerpo, pesos))
    resto = total % 11
    dv = 11 - resto
    if dv == 11:
        dv = 0
    elif dv == 10:
        dv = 9
    return f"{cuerpo}{dv}"


def generar_cuit_secuencial(socio="Varones"):
    """Genera un CUIT secuencial único usando la DB local."""
    pref_map = {"Varones": 20, "Mujeres": 27, "Extranjeros": 23}
    pref = pref_map.get(socio, 20)
    dni_usado = obtener_y_incrementar_dni()
    cuit = calcular_cuit_sin_guiones(pref, dni_usado)
    logger.info(f"CUIT generado: {cuit} (DNI: {dni_usado}, prefijo: {pref})")
    return cuit, pref, dni_usado


def inyectar_cuit(driver, cuit_no_guiones):
    """Inyecta el CUIT en el campo vPFNDOC con disparo de eventos GeneXus."""
    try:
        pfndoc = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "vPFNDOC"))
        )

        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'}); arguments[0].focus();",
            pfndoc,
        )
        time.sleep(0.2)

        pfndoc.clear()
        pfndoc.send_keys(cuit_no_guiones)
        time.sleep(0.2)

        # Disparar eventos GX
        driver.execute_script(
            """
            var el = arguments[0];
            el.dispatchEvent(new Event('input', {bubbles:true}));
            el.dispatchEvent(new Event('change', {bubbles:true}));
            el.dispatchEvent(new Event('blur', {bubbles:true}));
        """,
            pfndoc,
        )
        driver.execute_script(
            """
            var el = arguments[0];
            try { if (window.gx && gx.evt && gx.evt.onchange) gx.evt.onchange(el, event); } catch(e) {}
            try { if (window.gx && gx.evt && gx.evt.onblur) gx.evt.onblur(el, event); } catch(e) {}
        """,
            pfndoc,
        )

        pfndoc.send_keys(Keys.TAB)
        time.sleep(0.5)

        val = driver.find_element(By.ID, "vPFNDOC").get_attribute("value")
        logger.info(f"Valor actual en vPFNDOC: {val}")

        return val

    except Exception as e:
        logger.error(f"Error al inyectar CUIT: {e}")
        driver.save_screenshot("error_inyectar_cuit.png")
        raise


# USO PRINCIPAL

try:
    inicializar_db()
    cuit_no_guiones, pref, dni_generado = generar_cuit_secuencial("Varones")
    print(
        f"Generado CUIT (sin guiones): {cuit_no_guiones}  (DNI: {dni_generado}, pref: {pref})"
    )
    valor_final = inyectar_cuit(driver, cuit_no_guiones)
    print("Valor final en campo:", valor_final)
except Exception:
    logger.exception("Error general en generación/inyección de CUIT:")


# Seleccionar tipo de alta
print("Seleccionando tipo de alta 'Normal'...")

try:
    tipo_alta_select = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.ID, "vALTACOD"))
    )
    Select(tipo_alta_select).select_by_visible_text("Normal")
    print("Tipo de alta seleccionado: Normal")
except Exception as e:
    print(f"Error al seleccionar tipo de alta: {e}")


# Seleccionar canal de origen
print("Seleccionando canal de origen 'Sucursal'...")

try:
    canal_origen_select = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.ID, "vDSTCOD"))
    )
    Select(canal_origen_select).select_by_value("1")
    print("Canal de origen seleccionado: Sucursal (value=1)")
except Exception as e:
    print(f"Error al seleccionar canal de origen: {e}")


# Seleccionar categoría comercial
print("Seleccionando categoría comercial 'Comercial'...")

try:
    categoria_select = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.ID, "vPESN03"))
    )
    # Seleccionamos por valor (S = Comercial)
    Select(categoria_select).select_by_value("S")
    print("Categoría seleccionada: Comercial (value='S')")
except Exception as e:
    print(f"Error al seleccionar categoría comercial: {e}")


# Seleccionar tipo de persona
print("Seleccionando tipo de persona 'Física'...")

try:
    tipo_persona_select = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.ID, "vPPETIPO"))
    )
    # Seleccionamos por valor (F = Física)
    Select(tipo_persona_select).select_by_value("F")
    print("Tipo de persona seleccionado: Física (value='F')")
except Exception as e:
    print(f"Error al seleccionar tipo de persona: {e}")


# Confirmar alta
print("Buscando y haciendo clic en el botón 'Confirmar'...")

try:
    confirmar_btn = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//span[@id='BTNOPBTNCONFIRMAR']/a[contains(@class,'OpEnterText') and normalize-space(text())='Confirmar']",
            )
        )
    )

    # Intento 1: click normal
    try:
        confirmar_btn.click()
        print("Click normal en 'Confirmar' ejecutado correctamente.")
    except:
        # Intento 2: click mediante JavaScript (más confiable en GeneXus)
        driver.execute_script(
            """
            var btn = arguments[0];
            if (btn) {
                btn.dispatchEvent(new MouseEvent('mouseover', {bubbles:true}));
                btn.dispatchEvent(new MouseEvent('mousedown', {bubbles:true}));
                btn.dispatchEvent(new MouseEvent('mouseup', {bubbles:true}));
                btn.click();
            }
        """,
            confirmar_btn,
        )
        print("Click forzado por JavaScript en 'Confirmar' ejecutado correctamente.")


except Exception as e:
    print(f"Error al hacer clic en Confirmar: {e}")


# Confirmar acción final (clic en "Sí")
print("Buscando y haciendo clic en el botón 'Sí'...")

try:
    # Esperar a que aparezca el diálogo de confirmación
    boton_si = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//span[@id='BTNCONFIRMATION']/a[normalize-space(text())='Sí']")
        )
    )

    # Intento 1: click normal
    try:
        boton_si.click()
        print("Click normal en 'Sí' ejecutado correctamente.")
    except:
        # Intento 2: click forzado con JavaScript (más confiable)
        driver.execute_script(
            """
            var btn = arguments[0];
            if (btn) {
                btn.dispatchEvent(new MouseEvent('mouseover', {bubbles:true}));
                btn.dispatchEvent(new MouseEvent('mousedown', {bubbles:true}));
                btn.dispatchEvent(new MouseEvent('mouseup', {bubbles:true}));
                btn.click();
            }
        """,
            boton_si,
        )
        print("Click forzado por JavaScript en 'Sí' ejecutado correctamente.")


except Exception as e:
    print(f"Error al hacer clic en 'Sí': {e}")


# Rebuscar específicamente el iframe process1_step3
print("Esperando el iframe visible de 'Datos de Persona' (process1_step3)...")

driver.switch_to.default_content()
iframe_principal = WebDriverWait(driver, 25).until(
    EC.presence_of_element_located(
        (By.XPATH, "//div[@id='procContainer']/iframe[@id='1']")
    )
)
driver.switch_to.frame(iframe_principal)

iframe_visible = None
for i in range(50):
    frames = driver.find_elements(By.XPATH, "//iframe[@name='process1_step3']")
    for f in frames:
        style = f.get_attribute("style") or ""
        if "visibility: visible" in style and "opacity: 1" in style:
            driver.switch_to.frame(f)
            print("Iframe process1_step3 activo y visible.")
            iframe_visible = f
            break
    if iframe_visible:
        break
    time.sleep(1)
else:
    raise TimeoutException("No se detectó iframe visible process1_step3.")


# Ingresando datos personales...
nombres = ["LUIS", "JUAN", "MARÍA", "ANA", "CARLOS", "JORGE", "LAURA"]
apellidos = [
    "GONZÁLEZ",
    "RODRÍGUEZ",
    "FERNÁNDEZ",
    "LÓPEZ",
    "GÓMEZ",
    "MARTÍNEZ",
    "SÁNCHEZ",
]

primer_apellido = random.choice(apellidos)
segundo_apellido = random.choice(apellidos)
primer_nombre = random.choice(nombres)
segundo_nombre = random.choice(nombres)

# Ingresar Primer Apellido
print("Ingresando 'Primer Apellido' dentro del iframe process1_stepX...")
try:
    apellido_input = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.ID, "vPFAPE1"))
    )
    apellido_input.clear()
    apellido_input.send_keys(primer_apellido)
    print(f"Campo 'Primer Apellido' completado: {primer_apellido}")
except Exception as e:
    print(f"Error al completar 'Primer Apellido': {e}")

# Ingresar Segundo Apellido
print("Ingresando 'Segundo Apellido'...")
try:
    segundo_apellido_input = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.ID, "vPFAPE2"))
    )
    segundo_apellido_input.clear()
    segundo_apellido_input.send_keys(segundo_apellido)
    print(f"Campo 'Segundo Apellido' completado: {segundo_apellido}")
except Exception as e:
    print(f"Error al completar 'Segundo Apellido': {e}")

# Ingresar Primer Nombre
print("Ingresando 'Primer Nombre'...")
try:
    nombre1_input = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.ID, "vPFNOM1"))
    )
    nombre1_input.clear()
    nombre1_input.send_keys(primer_nombre)
    print(f"Campo 'Primer Nombre' completado: {primer_nombre}")
except Exception as e:
    print(f"Error al completar 'Primer Nombre': {e}")

# Ingresar Segundo Nombre
print("Ingresando 'Segundo Nombre'...")
try:
    nombre2_input = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.ID, "vPFNOM2"))
    )
    nombre2_input.clear()
    nombre2_input.send_keys(segundo_nombre)
    print(f"Campo 'Segundo Nombre' completado: {segundo_nombre}")
except Exception as e:
    print(f"Error al completar 'Segundo Nombre': {e}")


# tabular para entrar al campo fecha de nacimiento
def tabular_una_vez(driver):
    try:
        print("Enviando tecla TAB para enfocar el siguiente campo...")
        ActionChains(driver).send_keys(Keys.TAB).perform()
        print("TAB enviado correctamente.")
    except Exception as e:
        print(f"Error al enviar TAB: {e}")


# generar fecha aleatoria mayor a 20 años
def generar_fecha_mayor_a_20_anios():
    hoy = datetime.today()
    fecha_limite = hoy - timedelta(days=20 * 365)  # Aprox 20 años
    fecha_inicio = datetime(1900, 1, 1)

    delta_dias = (fecha_limite - fecha_inicio).days
    dias_random = random.randint(0, delta_dias)

    fecha_random = fecha_inicio + timedelta(days=dias_random)
    return fecha_random.strftime("%d/%m/%Y")


# ingresar fecha de nacimiento
def ingresar_fecha_nacimiento(driver):
    try:
        fecha_ddmmaaaa = generar_fecha_mayor_a_20_anios()
        print(f"Ingresando fecha aleatoria '{fecha_ddmmaaaa}' en el campo vPFFNAC...")

        campo_fecha = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "vPFFNAC"))
        )

        campo_fecha.click()
        time.sleep(0.3)

        campo_fecha.send_keys(Keys.CONTROL + "a")
        campo_fecha.send_keys(Keys.DELETE)
        time.sleep(0.3)

        campo_fecha.send_keys(fecha_ddmmaaaa)
        campo_fecha.send_keys(Keys.TAB)  # dispara blur/onchange

        print("Fecha ingresada correctamente.")

    except Exception as e:
        print(f"Error al ingresar fecha: {e}")


# Llamada a las funciones
tabular_una_vez(driver)


# Alternativa: forzar click en trigger calendario y luego ingresar fecha
ingresar_fecha_nacimiento(driver)


# Paso con reintento de facha de nacimiento
intentar_con_reintento(
    funcion=lambda: ingresar_fecha_nacimiento(driver),
    verificador=lambda: driver.find_element(By.ID, "vPFFNAC")
    .get_attribute("value")
    .strip()
    != "",
    intentos=3,
    espera=1,
)


# Email
print("Ingresando email 'aflores@accionpoint.com'...")
try:
    email_input = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.ID, "vEMAIL"))
    )
    email_input.clear()
    email_input.send_keys("aflores@accionpoint.com")
    print("Email ingresado correctamente.")
except Exception as e:
    print(f"Error al completar el email: {e}")


# Seleccionar sexo aleatorio con reintento
def seleccionar_sexo(driver):
    print("Seleccionando sexo aleatorio en vPFCANT...")
    try:
        sexo_select = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "vPFCANT"))
        )
        select_sexo = Select(sexo_select)

        # Opciones disponibles: 1=Masculino, 2=Femenino, 3=No Binario
        sexo_random = random.choice(["1", "2", "3"])
        select_sexo.select_by_value(sexo_random)

        print(f"Sexo seleccionado correctamente: {sexo_random}")
    except Exception as e:
        print(f"Error al seleccionar sexo: {e}")
        raise e  # Importante: relanzar para que el reintento funcione


#  Verificador simple
def verificar_sexo_seleccionado(driver):
    try:
        valor = driver.find_element(By.ID, "vPFCANT").get_attribute("value")
        return valor in ["1", "2", "3"]
    except:
        return False


#  Ejecutar con reintento
intentar_con_reintento(
    funcion=lambda: seleccionar_sexo(driver),
    verificador=lambda: verificar_sexo_seleccionado(driver),
    intentos=3,
    espera=1,
)


# Seleccionar país de nacimiento: Argentina
print("Seleccionando país de nacimiento: Argentina...")
try:
    pais_nac_select = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "vPFPNAC"))
    )
    driver.execute_script(
        """
        const select = document.getElementById('vPFPNAC');
        select.value = '80';  // Argentina
        const event = new Event('change', { bubbles: true });
        select.dispatchEvent(event);
    """
    )
    print("País de nacimiento 'Argentina' seleccionado correctamente.")
except Exception as e:
    print(f"Error al seleccionar país de nacimiento: {e}")


#  Seleccionar estado civil
def seleccionar_estado_civil(driver):
    print("Seleccionando estado civil...")
    set_gx_select(driver, "vPFECIV", "1", "HTMLTXTVLEVENT_ESTCIV")  # 1 = Soltero/a


def verificar_estado_civil(driver):
    try:
        valor = driver.find_element(By.ID, "vPFECIV").get_attribute("value")
        return valor == "1"
    except:
        return False


#  Ejecutar con reintento
intentar_con_reintento(
    funcion=lambda: seleccionar_estado_civil(driver),
    verificador=lambda: verificar_estado_civil(driver),
    intentos=3,
    espera=1,
)


# Seleccionar nacionalidad
print("Seleccionando nacionalidad: Argentina...")
set_gx_select(driver, "vPAISCIU", "80", "HTMLTXTVLEVENT_CPOPAISNAC")


# Seleccionar nivel educativo
def seleccionar_nivel_educativo(driver):
    nivel_random = nivel_educativo_random()
    print(f"Seleccionando nivel educativo aleatorio (valor={nivel_random})...")

    esperar_y_setear_combo(
        driver,
        field_id="vNINSCOD",
        value=nivel_random,
        gx_event="HTMLTXTVLEVENT_NIVELINS",
        delay_post_refresh=2000,
    )


def verificar_nivel_educativo(driver):
    try:
        combo = driver.find_element(By.ID, "vNINSCOD")
        valor = combo.get_attribute("value")
        return valor != "0"
    except:
        return False


#  Ejecutar con reintento
intentar_con_reintento(
    funcion=lambda: seleccionar_nivel_educativo(driver),
    verificador=lambda: verificar_nivel_educativo(driver),
    intentos=3,
    espera=1,
)


# Seleccionar si es residente con reintento
def seleccionar_residente(driver):
    print("Seleccionando residente: Sí (valor=2)...")
    esperar_y_setear_combo(
        driver,
        field_id="vCMBCODAUX4",
        value="2",
        gx_event="HTMLTXTVLEVENT_CMBCMBCODAUX4",
        timeout=30,
        delay_post_refresh=2000,
    )


def verificar_residente(driver):
    try:
        combo = driver.find_element(By.ID, "vCMBCODAUX4")
        valor = combo.get_attribute("value")
        return valor == "2"
    except:
        return False


#  Ejecutar con reintento
intentar_con_reintento(
    funcion=lambda: seleccionar_residente(driver),
    verificador=lambda: verificar_residente(driver),
    intentos=3,
    espera=2,
)


# Ingresar ingreso mensual en pesos
def ingresar_ingreso_mensual(driver, ingreso="900000"):
    print(f"Ingresando ingreso mensual: {ingreso}...")
    campo_ingreso = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "vPEXING"))
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", campo_ingreso)
    time.sleep(0.3)

    campo_ingreso.send_keys(Keys.CONTROL + "a")
    campo_ingreso.send_keys(Keys.DELETE)
    time.sleep(0.3)

    for caracter in ingreso:
        campo_ingreso.send_keys(caracter)
        time.sleep(0.1)  # más realista: tipo humano

    campo_ingreso.send_keys(Keys.TAB)  # activa blur/onchange
    print("Ingreso mensual ingresado correctamente.")


def verificar_ingreso_mensual(driver, ingreso="900000"):
    try:
        campo = driver.find_element(By.ID, "vPEXING")
        valor_actual = (
            campo.get_attribute("value").replace(".", "").replace(",", "").strip()
        )
        return valor_actual.startswith(ingreso)
    except:
        return False


# Ejecutar con reintento automático
intentar_con_reintento(
    funcion=lambda: ingresar_ingreso_mensual(driver, "900000"),
    verificador=lambda: verificar_ingreso_mensual(driver, "900000"),
    intentos=3,
    espera=1,
)


# Seleccionar ocupación
def seleccionar_ocupacion_empleado(driver):
    print("Seleccionando ocupación: Empleado...")
    select_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "vSNGC07COD"))
    )
    select = Select(select_element)
    select.select_by_visible_text("Empleado")  # o .select_by_value("1")
    print("Ocupación 'Empleado' seleccionada correctamente.")


# Verificador
def verificar_ocupacion_empleado(driver):
    try:
        select_element = driver.find_element(By.ID, "vSNGC07COD")
        valor_actual = select_element.get_attribute("value")
        return valor_actual == "1"
    except:
        return False


# Ejecutar reintento automático
intentar_con_reintento(
    funcion=lambda: seleccionar_ocupacion_empleado(driver),
    verificador=lambda: verificar_ocupacion_empleado(driver),
    intentos=3,
    espera=1.5,
)


# Acción: Ingresar datos empleadora
def ingresar_datos_empleadora(driver):
    print("Esperando 2 segundos para que se carguen los campos de empleadora...")
    time.sleep(2)

    print("Ingresando País de Empleadora: 1")
    pais_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "vPAISEMPLEADORAUX"))
    )
    pais_input.click()
    pais_input.send_keys(Keys.CONTROL + "a")
    pais_input.send_keys(Keys.DELETE)
    time.sleep(0.2)
    pais_input.send_keys("1")
    pais_input.send_keys(Keys.TAB)

    print("Ingresando Tipo de Documento de Empleadora: 1")
    tdoc_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "vTDOCEMPLEADORAUX"))
    )
    tdoc_input.click()
    tdoc_input.send_keys(Keys.CONTROL + "a")
    tdoc_input.send_keys(Keys.DELETE)
    time.sleep(0.2)
    tdoc_input.send_keys("1")
    tdoc_input.send_keys(Keys.TAB)

    print("Campos de empleadora completados correctamente.")


# Verificador
def verificar_datos_empleadora(driver):
    try:
        pais = driver.find_element(By.ID, "vPAISEMPLEADORAUX").get_attribute("value")
        tdoc = driver.find_element(By.ID, "vTDOCEMPLEADORAUX").get_attribute("value")
        return pais == "1" and tdoc == "1"
    except:
        return False


# Ejecutar con reintento automático
intentar_con_reintento(
    funcion=lambda: ingresar_datos_empleadora(driver),
    verificador=lambda: verificar_datos_empleadora(driver),
    intentos=3,
    espera=1.5,
)


# Generar CUIT aleatorio del empleador
def generar_cuit_fake():
    """
    Genera un CUIT aleatorio válido en formato sin guiones (XXXXXXXXXXX).
    No verifica el dígito verificador real.
    """
    tipo = random.choice([30, 33, 34])  # Tipos típicos de empresa
    numero = random.randint(10000000, 99999999)
    verificador = random.randint(0, 9)  # No calculamos el dígito real
    return f"{tipo}{numero}{verificador}"


# Acción: Ingresar CUIT empleadora
def ingresar_cuit_empleadora(driver):
    try:
        cuit = generar_cuit_fake()
        print(f"Ingresando CUIT de empleadora: {cuit}")

        cuit_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "vPJNDOC"))
        )
        cuit_input.click()
        cuit_input.send_keys(Keys.CONTROL + "a")
        cuit_input.send_keys(Keys.DELETE)
        time.sleep(0.2)
        cuit_input.send_keys(cuit)
        cuit_input.send_keys(Keys.TAB)

        # Guardar cuit en atributo para verificación posterior
        driver.last_cuit_empleadora = cuit

        print("CUIT ingresado correctamente.")
    except Exception as e:
        print(f"Error al ingresar CUIT: {e}")


# Verificador
def verificar_cuit_empleadora(driver):
    try:
        current_value = driver.find_element(By.ID, "vPJNDOC").get_attribute("value")
        return (
            hasattr(driver, "last_cuit_empleadora")
            and current_value == driver.last_cuit_empleadora
        )
    except:
        return False


# Ejecutar con reintento
intentar_con_reintento(
    funcion=lambda: ingresar_cuit_empleadora(driver),
    verificador=lambda: verificar_cuit_empleadora(driver),
    intentos=3,
    espera=1.5,
)


# Hacer click en Confirmar
def hacer_click_confirmar(driver):
    try:
        print("Haciendo clic en el botón Confirmar...")

        confirmar_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Confirmar"))
        )
        confirmar_btn.click()

        print("Botón Confirmar clickeado correctamente.")
    except Exception as e:
        print(f"Error al hacer clic en Confirmar: {e}")


hacer_click_confirmar(driver)


# Rebuscar específicamente el iframe process1_step4
print("Esperando el iframe visible de 'Datos de Persona' (process1_step4)...")

driver.switch_to.default_content()
iframe_principal = WebDriverWait(driver, 25).until(
    EC.presence_of_element_located(
        (By.XPATH, "//div[@id='procContainer']/iframe[@id='1']")
    )
)
driver.switch_to.frame(iframe_principal)

iframe_visible = None
for i in range(50):
    frames = driver.find_elements(By.XPATH, "//iframe[@name='process1_step4']")
    for f in frames:
        style = f.get_attribute("style") or ""
        if "visibility: visible" in style and "opacity: 1" in style:
            driver.switch_to.frame(f)
            print("Iframe process1_step4 activo y visible.")
            iframe_visible = f
            break
    if iframe_visible:
        break
    time.sleep(1)
else:
    raise TimeoutException("No se detectó iframe visible process1_step4.")


def seleccionar_nacionalidad_no(driver, wait):
    print("Seleccionando nacionalidad: No (valor='N')...")

    try:
        # Esperar que el combo esté visible y clickeable dentro del iframe actual
        combo = wait.until(EC.element_to_be_clickable((By.ID, "vNACIONALIDAD")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", combo)
        time.sleep(0.3)

        # Seleccionar por Selenium (si el combo ya tiene opciones cargadas)
        try:
            select = Select(combo)
            select.select_by_value("N")
            print("Opción 'N' seleccionada mediante Select.")
        except Exception as e:
            print(
                f"No se pudo usar Select directamente: {e}, intentando con JavaScript..."
            )

        # Forzar el cambio manual con eventos GeneXus
        driver.execute_script(
            """
            const select = document.getElementById('vNACIONALIDAD');
            if (select) {
                select.focus();
                select.value = 'N';
                const changeEvent = new Event('change', { bubbles: true });
                select.dispatchEvent(changeEvent);
                const blurEvent = new Event('blur', { bubbles: true });
                select.dispatchEvent(blurEvent);
            }
        """
        )

        # Confirmar que el valor cambió
        valor_final = driver.execute_script(
            "return document.getElementById('vNACIONALIDAD')?.value;"
        )
        if valor_final == "N":
            print("Nacionalidad 'No' seleccionada correctamente.")
        else:
            print(f"Advertencia: el valor final es '{valor_final}' (esperado: 'N').")

    except Exception as e:
        print(f"Error al seleccionar nacionalidad: {e}")


seleccionar_nacionalidad_no(driver, wait)


# Seleccionar residencia: No
def seleccionar_residencia_no(driver, wait):
    """
    Selecciona la opción 'No' (valor='N') en el combo vTIENERESI2.
    Asume que ya estamos dentro del iframe correcto.
    """
    print("Seleccionando 'No' en el campo ¿Tiene residencia? (vTIENERESI2)...")
    try:
        # Esperar que el combo esté visible e interactuable
        combo = wait.until(EC.element_to_be_clickable((By.ID, "vTIENERESI2")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", combo)
        time.sleep(0.3)

        # Intentar selección nativa primero
        try:
            select = Select(combo)
            select.select_by_value("N")
            print("Opción 'N' seleccionada mediante Select.")
        except Exception as e:
            print(
                f"No se pudo usar Select directamente: {e}, intentando con JavaScript..."
            )

        # Forzar evento GeneXus de cambio/blur
        driver.execute_script(
            """
            const select = document.getElementById('vTIENERESI2');
            if (select) {
                select.focus();
                select.value = 'N';
                const changeEvent = new Event('change', { bubbles: true });
                select.dispatchEvent(changeEvent);
                const blurEvent = new Event('blur', { bubbles: true });
                select.dispatchEvent(blurEvent);
            }
        """
        )

        # Validar que el valor cambió realmente
        valor_final = driver.execute_script(
            "return document.getElementById('vTIENERESI2')?.value;"
        )
        if valor_final == "N":
            print("Campo '¿Tiene residencia?' seleccionado correctamente (No).")
        else:
            print(
                f"Advertencia: valor final inesperado '{valor_final}' (esperado 'N')."
            )

    except Exception as e:
        print(f"Error al seleccionar residencia: {e}")


seleccionar_residencia_no(driver, wait)


# Presionar botón Confirmar
def presionar_boton_confirmar(driver):
    print("Haciendo clic en el botón Confirmar...")
    try:
        boton_confirmar = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//a[contains(@class,'OpEnterText') and normalize-space()='Confirmar']",
                )
            )
        )

        driver.execute_script("arguments[0].scrollIntoView(true);", boton_confirmar)
        time.sleep(0.3)
        boton_confirmar.click()
        print("Botón Confirmar clickeado correctamente.")

        # Forzar el evento GeneXus por si el click no lo dispara
        driver.execute_script(
            """
            const btn = document.querySelector("a.OpEnterText");
            if (btn && window.gx && gx.evt) {
                gx.evt.execEvt('', false, btn.getAttribute('data-gx-evt'), btn);
            }
        """
        )

    except Exception as e:
        print(f"Error al presionar Confirmar: {e}")


# llamar al step: Presionar botón Confirmar
presionar_boton_confirmar(driver)


# Esperar hasta que el iframe principal esté presente
print("Esperando iframe principal id='1'...")
driver.switch_to.default_content()
iframe_principal = WebDriverWait(driver, 25).until(
    EC.presence_of_element_located((By.XPATH, "//iframe[@id='1']"))
)
driver.switch_to.frame(iframe_principal)
print("Ingresé al iframe principal id='1'.")

# Esperar hasta que process1_step5 esté visible (con reintento)
print("Esperando a que process1_step5 cambie a visible...")

iframe_visible = None
for i in range(40):  # hasta 40 intentos (unos 40 segundos máx)
    frames = driver.find_elements(By.XPATH, "//iframe[@name='process1_step5']")
    if frames:
        f = frames[0]
        style = f.get_attribute("style") or ""
        if "visibility: visible" in style and "opacity: 1" in style:
            iframe_visible = f
            print(f"Iframe process1_step5 visible tras {i+1} intentos.")
            break
        else:
            print(f"Intento {i+1}: todavía oculto ({style})")
    else:
        print("Aún no se encuentra el iframe process1_step5.")
    time.sleep(1)

if not iframe_visible:
    raise TimeoutException("El iframe process1_step5 nunca se volvió visible.")

driver.switch_to.frame(iframe_visible)
print("Entré correctamente al iframe process1_step5.")


# Presionar botón Agregar
def presionar_boton_agregar(driver):
    """
    Presiona el botón 'Agregar' dentro del iframe actual (GeneXus),
    ejecutando correctamente el evento GX.
    """
    print("Haciendo clic en el botón Agregar...")
    try:
        # Esperar el botón dentro del iframe actual (ya deberías estar en process1_step6 o similar)
        boton_agregar = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//a[normalize-space()='Agregar']"))
        )

        # Hacer scroll si está fuera de vista
        driver.execute_script("arguments[0].scrollIntoView(true);", boton_agregar)
        time.sleep(0.3)

        # Click real
        boton_agregar.click()
        print("Botón Agregar clickeado correctamente.")

        # Forzar evento GeneXus por si el click no lo dispara
        driver.execute_script(
            """
            const btn = document.querySelector("a[href='#'][data-gx-evt][data-gx-evt-condition*='DescartesContainer.BeforeClick']");
            if (btn && window.gx && gx.evt) {
                gx.evt.execEvt('', false, btn.getAttribute('data-gx-evt'), btn);
            }
        """
        )

    except Exception as e:
        print(f"Error al presionar Agregar: {e}")


# llamar al step: Presionar botón Agregar
presionar_boton_agregar(driver)


# Esperar hasta que el iframe principal esté presente
print("Esperando iframe principal id='1'...")
driver.switch_to.default_content()
iframe_principal = WebDriverWait(driver, 25).until(
    EC.presence_of_element_located((By.XPATH, "//iframe[@id='1']"))
)
driver.switch_to.frame(iframe_principal)
print("Ingresé al iframe principal id='1'.")

# Esperar hasta que process1_step6 esté visible (con reintento)
print("Esperando a que process1_step6 cambie a visible...")

iframe_visible = None
for i in range(40):  # hasta 40 intentos (unos 40 segundos máx)
    frames = driver.find_elements(By.XPATH, "//iframe[@name='process1_step6']")
    if frames:
        f = frames[0]
        style = f.get_attribute("style") or ""
        if "visibility: visible" in style and "opacity: 1" in style:
            iframe_visible = f
            print(f"Iframe process1_step6 visible tras {i+1} intentos.")
            break
        else:
            print(f"Intento {i+1}: todavía oculto ({style})")
    else:
        print("⚠️ Aún no se encuentra el iframe process1_step6.")
    time.sleep(1)

if not iframe_visible:
    raise TimeoutException("El iframe process1_step6 nunca se volvió visible.")

driver.switch_to.frame(iframe_visible)
print("Entré correctamente al iframe process1_step6.")


# Seleccionar país URUGUAY
def seleccionar_pais_uruguay(driver):
    """
    Selecciona la opción 'URUGUAY' (value=10) en el campo vDOCPAIS1,
    asegurando compatibilidad con GeneXus (focus, onchange, blur).
    """
    try:
        print("Seleccionando país: URUGUAY (value='10')...")

        # Esperar a que el campo esté presente y habilitado
        select_pais = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "vDOCPAIS1"))
        )

        # Scroll hacia el elemento por si está fuera de vista
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", select_pais
        )
        time.sleep(0.3)

        # Crear objeto Select y elegir valor "10"
        select = Select(select_pais)
        select.select_by_value("10")  # URUGUAY
        time.sleep(0.3)

        # Forzar eventos GeneXus
        driver.execute_script(
            """
            const select = document.getElementById('vDOCPAIS1');
            const changeEvent = new Event('change', { bubbles: true });
            select.dispatchEvent(changeEvent);
            const blurEvent = new Event('blur', { bubbles: true });
            select.dispatchEvent(blurEvent);
        """
        )

        # Disparar GX handlers si existen
        driver.execute_script(
            """
            const el = document.getElementById('vDOCPAIS1');
            try { if (window.gx && gx.evt && gx.evt.onchange) gx.evt.onchange(el, event); } catch(e) {}
            try { if (window.gx && gx.evt && gx.evt.onblur) gx.evt.onblur(el, event); } catch(e) {}
        """
        )

        # Verificar valor final
        valor_final = select_pais.get_attribute("value")
        if valor_final == "10":
            print("País URUGUAY seleccionado correctamente.")
        else:
            print(f"Verificar selección: valor actual = {valor_final}")

    except Exception as e:
        print(f"Error al seleccionar país URUGUAY: {e}")


# llamar al step: Seleccionar país URUGUAY
seleccionar_pais_uruguay(driver)


# Seleccionar tipo de documento CUIT con validación y reintento
def seleccionar_tipo_documento_cuit(driver, max_reintentos=2):
    """
    Selecciona el tipo de documento 'C.U.I.T.' (valor='7') y valida que el cambio se haya aplicado.
    Si al leer el valor se detecta 'PASAPORTE' u otro incorrecto, reintenta hasta max_reintentos.
    """
    print("Seleccionando tipo de documento: C.U.I.T. (valor='7')")
    intentos = 0

    while intentos < max_reintentos:
        try:
            # Esperar que el combo esté presente y visible
            element = WebDriverWait(driver, 25).until(
                EC.presence_of_element_located((By.ID, "vTDOCUM"))
            )
            time.sleep(0.5)

            # Seleccionar la opción '7' (C.U.I.T.)
            select = Select(element)
            select.select_by_value("7")

            # Forzar ciclo completo de eventos GeneXus
            driver.execute_script(
                """
                const select = document.getElementById('vTDOCUM');
                select.focus();
                select.value = '7';
                const changeEvent = new Event('change', { bubbles: true });
                select.dispatchEvent(changeEvent);
                const blurEvent = new Event('blur', { bubbles: true });
                select.dispatchEvent(blurEvent);
            """
            )

            time.sleep(0.5)

            # Validar que el valor actual sea '7' (C.U.I.T.)
            valor_actual = element.get_attribute("value")
            texto_actual = element.find_element(
                By.XPATH, f".//option[@value='{valor_actual}']"
            ).text.strip()

            print(f"Validación: valor={valor_actual} texto='{texto_actual}'")

            if valor_actual == "7" and "CUIT" in texto_actual.upper():
                print("Tipo de documento 'C.U.I.T.' confirmado correctamente.")
                return True

            # Si quedó PASAPORTE u otro valor, reintentar
            print(
                f"Detected '{texto_actual}', reintentando selección (intento {intentos+1}/{max_reintentos})..."
            )
            intentos += 1
            time.sleep(1)

        except Exception as e:
            print(f"Error al seleccionar tipo de documento (intento {intentos+1}): {e}")
            intentos += 1
            time.sleep(1)

    # Si llega hasta acá, no logró dejar CUIT seleccionado
    print("No se pudo confirmar la selección de 'C.U.I.T.' después de varios intentos.")

    return False


# Llamar al step:
seleccionar_tipo_documento_cuit(driver)


# Generar CUIT aleatorio válido
def generar_cuit_sin_guiones():
    """
    Genera un CUIT válido y aleatorio (11 dígitos, sin guiones).
    """
    prefijos_validos = [20, 23, 24, 27, 30, 33, 34]
    prefijo = random.choice(prefijos_validos)
    dni = random.randint(10000000, 99999999)

    # Cálculo del dígito verificador (algoritmo AFIP)
    cuit_base = f"{prefijo}{dni:08d}"
    multiplicadores = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    total = sum(int(cuit_base[i]) * multiplicadores[i] for i in range(10))
    resto = 11 - (total % 11)
    if resto == 11:
        verificador = 0
    elif resto == 10:
        # Ajuste de prefijo según reglas AFIP
        if prefijo in [20, 27]:
            prefijo = 23
        elif prefijo == 30:
            prefijo = 33
        elif prefijo == 33:
            prefijo = 30
        # recalcular
        cuit_base = f"{prefijo}{dni:08d}"
        total = sum(int(cuit_base[i]) * multiplicadores[i] for i in range(10))
        resto = 11 - (total % 11)
        verificador = 0 if resto == 11 else resto
    else:
        verificador = resto

    # CUIT final de 11 dígitos
    cuit = f"{prefijo}{dni:08d}{verificador}"
    return cuit


# Ingresar CUIT en el campo Nro de Documento
def ingresar_cuit(driver):
    """
    Genera un CUIT válido (sin guiones) y lo ingresa correctamente
    en el campo 'vDOCNDOC1' con clic, focus, input y blur.
    """
    try:
        cuit = generar_cuit_sin_guiones()
        print(f"CUIT generado: {cuit}")

        # Esperar el campo y hacer clic real para activar onfocus
        input_field = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "vDOCNDOC1"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", input_field)
        time.sleep(0.2)
        input_field.click()  # 🔹 clic real para disparar gx.evt.onfocus
        time.sleep(0.2)

        # Limpiar y escribir el CUIT
        input_field.clear()
        input_field.send_keys(cuit)
        time.sleep(0.2)

        # Forzar eventos GeneXus (onchange → onblur)
        driver.execute_script(
            """
            const input = document.getElementById('vDOCNDOC1');
            const changeEvent = new Event('change', { bubbles: true });
            input.dispatchEvent(changeEvent);
            const blurEvent = new Event('blur', { bubbles: true });
            input.dispatchEvent(blurEvent);
        """
        )

        # Confirmar visualmente
        value = input_field.get_attribute("value")
        print(f"CUIT ingresado correctamente: {value}")
        return cuit

    except Exception as e:
        print(f"Error al ingresar CUIT: {e}")
        return None


# Ingresar fecha de vencimiento del documento
def generar_fecha_futura_entre_1_y_12_anios():
    """
    Genera una fecha aleatoria hacia el futuro, entre 1 y 12 años desde hoy.
    """
    hoy = datetime.today()
    dias_min = 1 * 365  # mínimo 1 año hacia adelante
    dias_max = 12 * 365  # máximo 12 años hacia adelante
    dias_random = random.randint(dias_min, dias_max)
    fecha_random = hoy + timedelta(days=dias_random)
    return fecha_random.strftime("%d/%m/%Y")


def ingresar_fecha_vencimiento_vDOCFCHVTO(driver):
    """
    Ingresa una fecha aleatoria válida entre 1 y 12 años a futuro
    en el campo vDOCFCHVTO (vencimiento del documento),
    simulando la interacción natural del usuario (TAB, click, input, TAB).
    """
    try:
        # Generar fecha aleatoria futura
        fecha_ddmmaaaa = generar_fecha_futura_entre_1_y_12_anios()
        print(
            f"Ingresando fecha de vencimiento '{fecha_ddmmaaaa}' en el campo vDOCFCHVTO..."
        )

        # Esperar a que el campo esté presente
        campo_fecha = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "vDOCFCHVTO"))
        )

        # 🔹 1: TAB para enfocar naturalmente el campo
        print("Enviando tecla TAB para posicionarse en el campo fecha...")
        ActionChains(driver).send_keys(Keys.TAB).perform()
        time.sleep(0.3)

        # 🔹 2: Click real para activar el evento onfocus de GeneXus
        campo_fecha.click()
        time.sleep(0.3)

        # 🔹 3: Limpiar campo anterior
        campo_fecha.send_keys(Keys.CONTROL + "a")
        campo_fecha.send_keys(Keys.DELETE)
        time.sleep(0.3)

        # 🔹 4: Escribir la nueva fecha y tabular para validar
        campo_fecha.send_keys(fecha_ddmmaaaa)
        campo_fecha.send_keys(Keys.TAB)
        time.sleep(0.3)

        # 🔹 5: Confirmar ingreso
        valor_final = campo_fecha.get_attribute("value").strip()
        if valor_final and valor_final != "  /  /    ":
            print(f"Fecha de vencimiento ingresada correctamente: {valor_final}")
        else:
            print("La fecha parece no haberse cargado, revisar validación GeneXus.")

        return fecha_ddmmaaaa

    except Exception as e:
        print(f"Error al ingresar fecha de vencimiento: {e}")
        return None


# Presionar botón Confirmar
def presionar_boton_confirmar_vDOCFCHVTO(driver):
    """
    Hace clic en el botón 'Confirmar' dentro del formulario actual
    (campo vDOCFCHVTO) y ejecuta correctamente el evento GeneXus.
    """
    print("Haciendo clic en el botón Confirmar...")
    try:
        # Esperar a que el botón esté visible y clickeable
        boton_confirmar = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//a[contains(@class,'OpEnterText') and normalize-space()='Confirmar']",
                )
            )
        )

        # Scroll al botón por si está fuera de vista
        driver.execute_script("arguments[0].scrollIntoView(true);", boton_confirmar)
        time.sleep(0.3)

        # Clic real en el botón
        boton_confirmar.click()
        print("Botón Confirmar clickeado correctamente.")

        # Forzar evento GeneXus (por si el click nativo no dispara gx.evt)
        driver.execute_script(
            """
            const btn = document.querySelector("a.OpEnterText");
            if (btn && window.gx && gx.evt) {
                gx.evt.execEvt('', false, btn.getAttribute('data-gx-evt'), btn);
            }
        """
        )

        # Espera breve para la acción posterior (por ejemplo, carga de nuevo step o mensaje)
        time.sleep(1)

    except Exception as e:
        print(f"Error al presionar Confirmar: {e}")


# Detectar mensaje de documento duplicado
def verificar_mensaje_documento_duplicado(driver):
    """
    Verifica si aparece el mensaje 'Ya existe el Documento con los datos ingresados'.
    Retorna True si aparece, False en caso contrario.
    """
    try:
        mensaje = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//td[contains(normalize-space(), 'Ya existe el Documento con los datos ingresados')]",
                )
            )
        )
        if mensaje.is_displayed():
            print("Mensaje detectado: Ya existe el Documento con los datos ingresados.")
            return True
    except:
        pass
    return False


# Flujo con reintento: CUIT + Fecha + Confirmar
def flujo_cuit_y_fecha_con_reintento(driver, max_reintentos=3):
    """
    Ejecuta el flujo completo:
      1) Ingresar CUIT
      2) Ingresar fecha de vencimiento
      3) Presionar Confirmar
    Si aparece el mensaje de duplicado, reintenta hasta max_reintentos veces.
    """
    for intento in range(1, max_reintentos + 1):
        print(f"\n Intento {intento} de registro de documento...")

        # Ingresar CUIT
        cuit_generado = ingresar_cuit(driver)
        print(f"CUIT ingresado: {cuit_generado}")

        # Ingresar fecha de vencimiento
        fecha_vencimiento = ingresar_fecha_vencimiento_vDOCFCHVTO(driver)
        print(f"Fecha de vencimiento ingresada: {fecha_vencimiento}")

        # Presionar Confirmar
        presionar_boton_confirmar_vDOCFCHVTO(driver)

        # Verificar mensaje de duplicado
        if verificar_mensaje_documento_duplicado(driver):
            print("Documento duplicado. Reintentando con nuevos datos...")
            time.sleep(1)
            continue
        else:
            print("Operación confirmada correctamente (sin duplicado).")
            return cuit_generado, fecha_vencimiento

    print(
        "No se pudo completar la operación: todos los intentos resultaron duplicados."
    )
    return None, None


# Ejecutar el flujo con reintento
cuit_final, fecha_final = flujo_cuit_y_fecha_con_reintento(driver)

if cuit_final:
    print(f"CUIT final utilizado: {cuit_final}")
    print(f"Fecha de vencimiento final: {fecha_final}")
else:
    print("No se pudo completar el alta tras varios intentos.")


# Esperar hasta que el iframe principal esté presente
print("Esperando iframe principal id='1'...")
driver.switch_to.default_content()
iframe_principal = WebDriverWait(driver, 25).until(
    EC.presence_of_element_located((By.XPATH, "//iframe[@id='1']"))
)
driver.switch_to.frame(iframe_principal)
print("Ingresé al iframe principal id='1'.")

# Esperar hasta que process1_step5 esté visible (con reintento)
print("Esperando a que process1_step5 cambie a visible...")

iframe_visible = None
for i in range(40):  # hasta 40 intentos (unos 40 segundos máx)
    frames = driver.find_elements(By.XPATH, "//iframe[@name='process1_step5']")
    if frames:
        f = frames[0]
        style = f.get_attribute("style") or ""
        if "visibility: visible" in style and "opacity: 1" in style:
            iframe_visible = f
            print(f"Iframe process1_step5 visible tras {i+1} intentos.")
            break
        else:
            print(f"Intento {i+1}: todavía oculto ({style})")
    else:
        print("Aún no se encuentra el iframe process1_step5.")
    time.sleep(1)

if not iframe_visible:
    raise TimeoutException("El iframe process1_step5 nunca se volvió visible.")

driver.switch_to.frame(iframe_visible)
print("Entré correctamente al iframe process1_step5.")


# Presionar botón Confirmar
def presionar_boton_confirmar(driver):
    """
    Hace clic en el botón 'Confirmar' del formulario actual.
    Dispara correctamente los eventos GeneXus (BeforeClick, gx.evt).
    """
    print("Haciendo clic en el botón Confirmar...")
    try:
        # Esperar a que el botón sea visible y clickeable
        boton_confirmar = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//a[normalize-space()='Confirmar']"))
        )

        # Scroll hasta el botón por si está fuera de vista
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", boton_confirmar
        )
        time.sleep(0.3)

        # Clic real en el botón
        boton_confirmar.click()
        print("Botón Confirmar clickeado correctamente.")

        # Forzar el evento GeneXus (en caso de que el click nativo no lo dispare)
        driver.execute_script(
            """
            const btn = Array.from(document.querySelectorAll("a"))
                .find(a => a.textContent.trim() === "Confirmar");
            if (btn && window.gx && gx.evt) {
                try {
                    gx.evt.execEvt('', false, btn.getAttribute('data-gx-evt'), btn);
                } catch(e) { console.warn('GX evento no disparado automáticamente:', e); }
            }
        """
        )

        # Espera breve por carga o actualización
        time.sleep(1.5)

    except Exception as e:
        print(f"Error al presionar botón Confirmar: {e}")


# llamar al step: Presionar botón Confirmar
presionar_boton_confirmar(driver)


# Esperar hasta que el iframe principal esté presente
print("Esperando iframe principal id='1'...")
driver.switch_to.default_content()
iframe_principal = WebDriverWait(driver, 25).until(
    EC.presence_of_element_located((By.XPATH, "//iframe[@id='1']"))
)
driver.switch_to.frame(iframe_principal)
print("Ingresé al iframe principal id='1'.")

# Esperar hasta que process1_step8 esté visible (con reintento)
print("Esperando a que process1_step5 cambie a visible...")

iframe_visible = None
for i in range(40):  # hasta 40 intentos (unos 40 segundos máx)
    frames = driver.find_elements(By.XPATH, "//iframe[@name='process1_step8']")
    if frames:
        f = frames[0]
        style = f.get_attribute("style") or ""
        if "visibility: visible" in style and "opacity: 1" in style:
            iframe_visible = f
            print(f"Iframe process1_step8 visible tras {i+1} intentos.")
            break
        else:
            print(f"Intento {i+1}: todavía oculto ({style})")
    else:
        print("Aún no se encuentra el iframe process1_step8.")
    time.sleep(1)

if not iframe_visible:
    raise TimeoutException("El iframe process1_step8 nunca se volvió visible.")

driver.switch_to.frame(iframe_visible)
print("Entré correctamente al iframe process1_step8.")


# Presionar botón Continuar
def presionar_boton_continuar(driver):
    """
    Hace clic en el botón 'Continuar' del formulario actual.
    Dispara correctamente los eventos GeneXus (BeforeClick, gx.evt).
    """
    print("Haciendo clic en el botón Continuar...")
    try:
        # Esperar a que el botón esté visible y clickeable
        boton_continuar = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//a[normalize-space()='Continuar']"))
        )

        # Desplazar hasta el botón por si está fuera del viewport
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", boton_continuar
        )
        time.sleep(0.3)

        # Clic real en el botón
        boton_continuar.click()
        print("Botón Continuar clickeado correctamente.")

        # Forzar el evento GeneXus (en caso de que el click nativo no lo dispare)
        driver.execute_script(
            """
            const btn = Array.from(document.querySelectorAll("a"))
                .find(a => a.textContent.trim() === "Continuar");
            if (btn && window.gx && gx.evt) {
                try {
                    gx.evt.execEvt('', false, btn.getAttribute('data-gx-evt'), btn);
                } catch(e) { console.warn('GX evento no disparado automáticamente:', e); }
            }
        """
        )

        # Espera breve por si hay actualización o carga de nuevo paso
        time.sleep(1.5)

    except Exception as e:
        print(f"Error al presionar botón Continuar: {e}")


# llamar al step: Presionar botón Continuar
presionar_boton_continuar(driver)


# Esperar hasta que el iframe principal esté presente
print("Esperando iframe principal id='1'...")
driver.switch_to.default_content()
iframe_principal = WebDriverWait(driver, 25).until(
    EC.presence_of_element_located((By.XPATH, "//iframe[@id='1']"))
)
driver.switch_to.frame(iframe_principal)
print("Ingresé al iframe principal id='1'.")

# Esperar hasta que process1_step9 esté visible (con reintento)
print("Esperando a que process1_step5 cambie a visible...")

iframe_visible = None
for i in range(40):  # hasta 40 intentos (unos 40 segundos máx)
    frames = driver.find_elements(By.XPATH, "//iframe[@name='process1_step9']")
    if frames:
        f = frames[0]
        style = f.get_attribute("style") or ""
        if "visibility: visible" in style and "opacity: 1" in style:
            iframe_visible = f
            print(f"Iframe process1_step9 visible tras {i+1} intentos.")
            break
        else:
            print(f"Intento {i+1}: todavía oculto ({style})")
    else:
        print("Aún no se encuentra el iframe process1_step9.")
    time.sleep(1)

if not iframe_visible:
    raise TimeoutException("El iframe process1_step9 nunca se volvió visible.")

driver.switch_to.frame(iframe_visible)
print("Entré correctamente al iframe process1_step9.")


# Presionar botón Confirmar
def presionar_boton_confirmar_openter(driver):
    """
    Hace clic en el botón 'Confirmar' con clase 'OpEnterText'.
    Dispara correctamente los eventos GeneXus (BeforeClick, gx.evt.execEvt).
    """
    print("Haciendo clic en el botón Confirmar (OpEnterText)...")
    try:
        # Esperar que el botón sea visible y clickeable
        boton_confirmar = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//a[contains(@class, 'OpEnterText') and normalize-space()='Confirmar']",
                )
            )
        )

        # Scroll hasta el botón por si está fuera de la vista
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", boton_confirmar
        )
        time.sleep(0.3)

        # Clic real en el botón
        boton_confirmar.click()
        print("Botón Confirmar clickeado correctamente.")

        # Forzar el evento GeneXus (si el click nativo no lo dispara)
        driver.execute_script(
            """
            const btn = document.querySelector("a.OpEnterText");
            if (btn && window.gx && gx.evt) {
                try {
                    gx.evt.execEvt('', false, btn.getAttribute('data-gx-evt'), btn);
                } catch (e) {
                    console.warn('gx.evt.execEvt no se ejecutó automáticamente:', e);
                }
            }
        """
        )

        # Pausa breve para permitir la actualización del DOM o el cambio de paso
        time.sleep(1.5)

    except Exception as e:
        print(f"Error al presionar botón Confirmar (OpEnterText): {e}")


# llamar al step: Presionar botón Confirmar
presionar_boton_confirmar_openter(driver)


# Esperar hasta que el iframe principal esté presente
print("Esperando iframe principal id='1'...")
driver.switch_to.default_content()
iframe_principal = WebDriverWait(driver, 25).until(
    EC.presence_of_element_located((By.XPATH, "//iframe[@id='1']"))
)
driver.switch_to.frame(iframe_principal)
print("Ingresé al iframe principal id='1'.")

# Esperar hasta que process1_step10 esté visible (con reintento)
print("Esperando a que process1_step10 cambie a visible...")

iframe_visible = None
for i in range(40):  # hasta 40 intentos (unos 40 segundos máx)
    frames = driver.find_elements(By.XPATH, "//iframe[@name='process1_step10']")
    if frames:
        f = frames[0]
        style = f.get_attribute("style") or ""
        if "visibility: visible" in style and "opacity: 1" in style:
            iframe_visible = f
            print(f"Iframe process1_step10 visible tras {i+1} intentos.")
            break
        else:
            print(f"Intento {i+1}: todavía oculto ({style})")
    else:
        print("Aún no se encuentra el iframe process1_step10.")
    time.sleep(1)

if not iframe_visible:
    raise TimeoutException("El iframe process1_step10 nunca se volvió visible.")

driver.switch_to.frame(iframe_visible)
print("Entré correctamente al iframe process1_step10.")

# llamar al step: Presionar botón Confirmar
presionar_boton_confirmar(driver)

# Esperar hasta que el iframe principal esté presente
print("Esperando iframe principal id='1'...")
driver.switch_to.default_content()
iframe_principal = WebDriverWait(driver, 25).until(
    EC.presence_of_element_located((By.XPATH, "//iframe[@id='1']"))
)
driver.switch_to.frame(iframe_principal)
print("Ingresé al iframe principal id='1'.")

# Esperar hasta que process1_step11 esté visible (con reintento)
print("Esperando a que process1_step11 cambie a visible...")

iframe_visible = None
for i in range(40):  # hasta 40 intentos (unos 40 segundos máx)
    frames = driver.find_elements(By.XPATH, "//iframe[@name='process1_step11']")
    if frames:
        f = frames[0]
        style = f.get_attribute("style") or ""
        if "visibility: visible" in style and "opacity: 1" in style:
            iframe_visible = f
            print(f"Iframe process1_step11 visible tras {i+1} intentos.")
            break
        else:
            print(f"Intento {i+1}: todavía oculto ({style})")
    else:
        print("Aún no se encuentra el iframe process1_step11.")
    time.sleep(1)

if not iframe_visible:
    raise TimeoutException("El iframe process1_step11 nunca se volvió visible.")

driver.switch_to.frame(iframe_visible)
print("Entré correctamente al iframe process1_step11.")


# llamar al step: Presionar botón Continuar
presionar_boton_continuar(driver)


# Esperar hasta que el iframe principal esté presente
print("Esperando iframe principal id='1'...")
driver.switch_to.default_content()
iframe_principal = WebDriverWait(driver, 25).until(
    EC.presence_of_element_located((By.XPATH, "//iframe[@id='1']"))
)
driver.switch_to.frame(iframe_principal)
print("Ingresé al iframe principal id='1'.")

# Esperar hasta que process1_step12 esté visible (con reintento)
print("Esperando a que process1_step12 cambie a visible...")

iframe_visible = None
for i in range(40):  # hasta 40 intentos (unos 40 segundos máx)
    frames = driver.find_elements(By.XPATH, "//iframe[@name='process1_step12']")
    if frames:
        f = frames[0]
        style = f.get_attribute("style") or ""
        if "visibility: visible" in style and "opacity: 1" in style:
            iframe_visible = f
            print(f"Iframe process1_step12 visible tras {i+1} intentos.")
            break
        else:
            print(f"Intento {i+1}: todavía oculto ({style})")
    else:
        print("Aún no se encuentra el iframe process1_step12.")
    time.sleep(1)

if not iframe_visible:
    raise TimeoutException("El iframe process1_step12 nunca se volvió visible.")

driver.switch_to.frame(iframe_visible)
print("Entré correctamente al iframe process1_step12.")


# Paso previo: ya estás dentro de process1_step12
print("Entré correctamente al iframe process1_step12.")


def presionar_boton_agregar_domicilio(driver):
    """
    Hace clic en el botón 'Agregar' de la sección 'Domicilios' dentro del iframe process1_step12,
    asumiendo que el driver ya está dentro de ese iframe.
    No espera el iframe process1_step13 (se manejará por separado).
    """
    print("Buscando botón 'Agregar' dentro del iframe process1_step12...")

    try:
        # XPath acotado a la sección Domicilios (solo el botón correcto)
        xpath_agregar_domicilios = (
            "(//*[self::td or self::div or self::span][normalize-space(.)='Domicilios'])[1]"
            "/following::a[normalize-space()='Agregar'][1]"
        )

        # Esperar a que sea clickeable, hacer scroll y clic
        boton_objetivo = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, xpath_agregar_domicilios))
        )
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", boton_objetivo
        )
        time.sleep(0.2)
        boton_objetivo.click()
        print(
            "Botón 'Agregar' (Domicilios) clickeado correctamente dentro del iframe 12."
        )

        # Forzar ejecución del evento GeneXus por JS (por si hace falta)
        driver.execute_script(
            """
            const btn = arguments[0];
            if (btn && window.gx && gx.evt) {
                try { gx.evt.execEvt('', false, btn.getAttribute('data-gx-evt'), btn); } catch(e) {}
            }
        """,
            boton_objetivo,
        )

    except Exception as e:
        print(f"Error al presionar botón 'Agregar' dentro del iframe 12: {e}")


# Ejecutar el paso
presionar_boton_agregar_domicilio(driver)


# Esperar hasta que el iframe principal esté presente
print("Esperando iframe principal id='1'...")
driver.switch_to.default_content()
iframe_principal = WebDriverWait(driver, 25).until(
    EC.presence_of_element_located((By.XPATH, "//iframe[@id='1']"))
)
driver.switch_to.frame(iframe_principal)
print("Ingresé al iframe principal id='1'.")

# Esperar hasta que process1_step13 esté visible (con reintento)
print("Esperando a que process1_step13 cambie a visible...")

iframe_visible = None
for i in range(40):  # hasta 40 intentos (unos 40 segundos máx)
    frames = driver.find_elements(By.XPATH, "//iframe[@name='process1_step13']")
    if frames:
        f = frames[0]
        style = f.get_attribute("style") or ""
        if "visibility: visible" in style and "opacity: 1" in style:
            iframe_visible = f
            print(f"Iframe process1_step13 visible tras {i+1} intentos.")
            break
        else:
            print(f"Intento {i+1}: todavía oculto ({style})")
    else:
        print("Aún no se encuentra el iframe process1_step13.")
    time.sleep(1)

if not iframe_visible:
    raise TimeoutException("El iframe process1_step13 nunca se volvió visible.")

driver.switch_to.frame(iframe_visible)
print("Entré correctamente al iframe process1_step13.")


# Ingresar un nombre de avenida aleatorio


def ingresar_nombre_avenida(driver):
    """
    Genera e ingresa un nombre de avenida aleatorio en el campo vNOM1.
    Dispara los eventos GeneXus correspondientes (focus, change, blur).
    """
    try:
        # Lista base de avenidas posibles
        avenidas = [
            "AV. SAN MARTÍN",
            "AV. BELGRANO",
            "AV. SARMIENTO",
            "AV. CORRIENTES",
            "AV. RIVADAVIA",
            "AV. MITRE",
            "AV. LAS HERAS",
            "AV. 9 DE JULIO",
            "AV. DEL LIBERTADOR",
            "AV. COLÓN",
            "AV. PELLEGRINI",
            "AV. JUAN B. JUSTO",
            "AV. ENTRE RÍOS",
            "AV. INDEPENDENCIA",
            "AV. GAONA",
            "AV. PUEYRREDÓN",
            "AV. LAVALLE",
            "AV. SCALABRINI ORTIZ",
            "AV. CABILDO",
        ]

        # Elegir una al azar
        avenida_elegida = random.choice(avenidas)
        print(f"Ingresando nombre de avenida aleatorio: '{avenida_elegida}'...")

        # Esperar que el campo esté presente y listo para interactuar
        campo_nombre = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "vNOM1"))
        )

        # Scroll y focus al campo
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", campo_nombre
        )
        time.sleep(0.3)
        campo_nombre.click()
        time.sleep(0.2)

        # Limpiar campo y escribir el nombre
        campo_nombre.clear()
        campo_nombre.send_keys(avenida_elegida)
        time.sleep(0.3)

        # Disparar eventos nativos y GeneXus
        driver.execute_script(
            """
            const el = document.getElementById('vNOM1');
            el.dispatchEvent(new Event('input', {bubbles:true}));
            el.dispatchEvent(new Event('change', {bubbles:true}));
            el.dispatchEvent(new Event('blur', {bubbles:true}));
            try {
                if (window.gx && gx.evt && gx.evt.onchange) gx.evt.onchange(el, event);
                if (window.gx && gx.evt && gx.evt.onblur) gx.evt.onblur(el, event);
            } catch(e) {}
        """
        )

        # Validar valor final
        valor_final = campo_nombre.get_attribute("value").strip()
        if valor_final:
            print(f"Nombre de avenida ingresado correctamente: {valor_final}")
        else:
            print("El campo vNOM1 quedó vacío, revisar validación GeneXus.")

    except Exception as e:
        print(f"Error al ingresar nombre de avenida: {e}")


# llamar al step: Ingresar un nombre de avenida aleatorio
ingresar_nombre_avenida(driver)


# Ingresar número aleatorio de 4 dígitos (altura de la avenida)
import random


def ingresar_numero_altura(driver):
    """
    Genera un número aleatorio de 4 dígitos (1000–9999)
    y lo ingresa en el campo vNOM2, respetando los eventos GeneXus.
    """
    try:
        # Generar número aleatorio
        numero = random.randint(1000, 9999)
        print(f"Ingresando número de altura aleatorio: {numero}")

        # Esperar a que el campo esté listo
        campo_numero = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "vNOM2"))
        )

        # Scroll y focus
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", campo_numero
        )
        time.sleep(0.3)
        campo_numero.click()
        time.sleep(0.2)

        # Limpiar campo anterior
        campo_numero.clear()
        campo_numero.send_keys(str(numero))
        time.sleep(0.3)

        # Disparar eventos nativos y GeneXus
        driver.execute_script(
            """
            const el = document.getElementById('vNOM2');
            el.dispatchEvent(new Event('input', {bubbles:true}));
            el.dispatchEvent(new Event('change', {bubbles:true}));
            el.dispatchEvent(new Event('blur', {bubbles:true}));
            try {
                if (window.gx && gx.evt && gx.evt.onchange) gx.evt.onchange(el, event);
                if (window.gx && gx.evt && gx.evt.onblur) gx.evt.onblur(el, event);
            } catch(e) {}
        """
        )

        # Validar que se haya ingresado correctamente
        valor_final = campo_numero.get_attribute("value").strip()
        if valor_final:
            print(f"Número ingresado correctamente: {valor_final}")
        else:
            print("El campo vNOM2 quedó vacío, revisar validación GeneXus.")

    except Exception as e:
        print(f"Error al ingresar número de altura: {e}")


# llamar al step: Ingresar número aleatorio de 4 dígitos (altura de la avenida)
ingresar_numero_altura(driver)


# Ingresar valor 1 en el campo vNOM3
def ingresar_valor_uno_vNOM3(driver):
    """
    Ingresa el valor '1' en el campo vNOM3,
    simulando la interacción natural del usuario y disparando eventos GeneXus.
    """
    try:
        print("Ingresando valor '1' en el campo vNOM3...")

        # Esperar a que el campo esté presente y listo
        campo_vnom3 = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "vNOM3"))
        )

        # Scroll hasta el campo y foco
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", campo_vnom3
        )
        time.sleep(0.3)
        campo_vnom3.click()
        time.sleep(0.2)

        # Limpiar el campo y escribir "1"
        campo_vnom3.clear()
        campo_vnom3.send_keys("1")
        time.sleep(0.3)

        # Disparar eventos nativos y GeneXus
        driver.execute_script(
            """
            const el = document.getElementById('vNOM3');
            el.dispatchEvent(new Event('input', {bubbles:true}));
            el.dispatchEvent(new Event('change', {bubbles:true}));
            el.dispatchEvent(new Event('blur', {bubbles:true}));
            try {
                if (window.gx && gx.evt && gx.evt.onchange) gx.evt.onchange(el, event);
                if (window.gx && gx.evt && gx.evt.onblur) gx.evt.onblur(el, event);
            } catch(e) {}
        """
        )

        # Validar valor final
        valor_final = campo_vnom3.get_attribute("value").strip()
        if valor_final == "1":
            print("Valor '1' ingresado correctamente en vNOM3.")
        else:
            print(
                f"El campo vNOM3 no contiene el valor esperado. Valor actual: '{valor_final}'"
            )

    except Exception as e:
        print(f"Error al ingresar valor en vNOM3: {e}")


# llamar al step: Ingresar valor 1 en el campo vNOM3
ingresar_valor_uno_vNOM3(driver)


# Ingresar valor 202 en el campo vNOM4
def ingresar_valor_202_vNOM4(driver):
    """
    Ingresa el valor '202' en el campo vNOM4,
    respetando los eventos GeneXus (focus, change, blur).
    """
    try:
        print("Ingresando valor '202' en el campo vNOM4...")

        # Esperar que el campo esté visible y clickeable
        campo_vnom4 = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "vNOM4"))
        )

        # Scroll y focus en el campo
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", campo_vnom4
        )
        time.sleep(0.3)
        campo_vnom4.click()
        time.sleep(0.2)

        # Limpiar campo previo y escribir "202"
        campo_vnom4.clear()
        campo_vnom4.send_keys("202")
        time.sleep(0.3)

        # Disparar eventos nativos + GeneXus
        driver.execute_script(
            """
            const el = document.getElementById('vNOM4');
            el.dispatchEvent(new Event('input', {bubbles:true}));
            el.dispatchEvent(new Event('change', {bubbles:true}));
            el.dispatchEvent(new Event('blur', {bubbles:true}));
            try {
                if (window.gx && gx.evt && gx.evt.onchange) gx.evt.onchange(el, event);
                if (window.gx && gx.evt && gx.evt.onblur) gx.evt.onblur(el, event);
            } catch(e) {}
        """
        )

        # Validar resultado
        valor_final = campo_vnom4.get_attribute("value").strip()
        if valor_final == "202":
            print("Valor '202' ingresado correctamente en vNOM4.")
        else:
            print(f"El valor en vNOM4 no coincide. Valor actual: '{valor_final}'")

    except Exception as e:
        print(f"Error al ingresar valor en vNOM4: {e}")


# llamar al step: Ingresar valor 202 en el campo vNOM4
ingresar_valor_202_vNOM4(driver)


# Ingresar valor 1 en el campo vNOM5
def ingresar_valor_uno_vNOM5(driver):
    """
    Ingresa el valor '1' en el campo vNOM5,
    simulando la interacción natural del usuario y disparando los eventos GeneXus.
    """
    try:
        print("Ingresando valor '1' en el campo vNOM5...")

        # Esperar que el campo esté presente y clickeable
        campo_vnom5 = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "vNOM5"))
        )

        # Scroll y focus sobre el campo
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", campo_vnom5
        )
        time.sleep(0.3)
        campo_vnom5.click()
        time.sleep(0.2)

        # Limpiar campo y escribir "1"
        campo_vnom5.clear()
        campo_vnom5.send_keys("1")
        time.sleep(0.3)

        # Disparar eventos nativos y GeneXus
        driver.execute_script(
            """
            const el = document.getElementById('vNOM5');
            el.dispatchEvent(new Event('input', {bubbles:true}));
            el.dispatchEvent(new Event('change', {bubbles:true}));
            el.dispatchEvent(new Event('blur', {bubbles:true}));
            try {
                if (window.gx && gx.evt && gx.evt.onchange) gx.evt.onchange(el, event);
                if (window.gx && gx.evt && gx.evt.onblur) gx.evt.onblur(el, event);
            } catch(e) {}
        """
        )

        # Verificar valor final
        valor_final = campo_vnom5.get_attribute("value").strip()
        if valor_final == "1":
            print("Valor '1' ingresado correctamente en vNOM5.")
        else:
            print(f"El valor en vNOM5 no coincide. Valor actual: '{valor_final}'")

    except Exception as e:
        print(f"Error al ingresar valor en vNOM5: {e}")


# llamar al step: Ingresar valor 1 en el campo vNOM5
ingresar_valor_uno_vNOM5(driver)


# Ingresar valor 1 en el campo vNOM6
def ingresar_valor_uno_vNOM6(driver):
    """
    Ingresa el valor '1' en el campo vNOM6,
    respetando los eventos GeneXus (focus, change, blur).
    """
    try:
        print("Ingresando valor '1' en el campo vNOM6...")

        # Esperar a que el campo esté presente y clickeable
        campo_vnom6 = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "vNOM6"))
        )

        # Scroll y foco sobre el campo
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", campo_vnom6
        )
        time.sleep(0.3)
        campo_vnom6.click()
        time.sleep(0.2)

        # Limpiar campo y escribir "1"
        campo_vnom6.clear()
        campo_vnom6.send_keys("1")
        time.sleep(0.3)

        # Disparar eventos nativos y GeneXus
        driver.execute_script(
            """
            const el = document.getElementById('vNOM6');
            el.dispatchEvent(new Event('input', {bubbles:true}));
            el.dispatchEvent(new Event('change', {bubbles:true}));
            el.dispatchEvent(new Event('blur', {bubbles:true}));
            try {
                if (window.gx && gx.evt && gx.evt.onchange) gx.evt.onchange(el, event);
                if (window.gx && gx.evt && gx.evt.onblur) gx.evt.onblur(el, event);
            } catch(e) {}
        """
        )

        # Validar el valor final
        valor_final = campo_vnom6.get_attribute("value").strip()
        if valor_final == "1":
            print("Valor '1' ingresado correctamente en vNOM6.")
        else:
            print(f"El valor en vNOM6 no coincide. Valor actual: '{valor_final}'")

    except Exception as e:
        print(f"Error al ingresar valor en vNOM6: {e}")


# llamar al step: Ingresar valor 1 en el campo vNOM6
ingresar_valor_uno_vNOM6(driver)


# Seleccionar provincia BUENOS AIRES (valor = 1)
def seleccionar_provincia_buenos_aires(driver):
    """
    Despliega el combo 'vDODEPCODP' y selecciona la opción con valor '1' (BUENOS AIRES),
    disparando los eventos GeneXus correspondientes.
    """
    try:
        print("Seleccionando provincia: BUENOS AIRES (valor='1')...")

        # Esperar a que el combo esté visible y clickeable
        combo_provincia = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "vDODEPCODP"))
        )

        # Scroll y click para abrir el desplegable
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", combo_provincia
        )
        time.sleep(0.3)
        combo_provincia.click()
        time.sleep(0.3)

        # Seleccionar opción por valor
        select = Select(combo_provincia)
        select.select_by_value("1")
        time.sleep(0.4)

        # Disparar eventos GeneXus manualmente (onchange y onblur)
        driver.execute_script(
            """
            const el = document.getElementById('vDODEPCODP');
            el.dispatchEvent(new Event('change', {bubbles:true}));
            el.dispatchEvent(new Event('blur', {bubbles:true}));
            try {
                if (window.gx && gx.evt && gx.evt.onchange) gx.evt.onchange(el, event);
                if (window.gx && gx.evt && gx.evt.onblur) gx.evt.onblur(el, event);
            } catch(e) {}
        """
        )

        # Verificar selección final
        opcion_seleccionada = select.first_selected_option.text.strip()
        if "BUENOS AIRES" in opcion_seleccionada.upper():
            print(f"Provincia seleccionada correctamente: {opcion_seleccionada}")
        else:
            print(f"Verificar selección, opción actual: {opcion_seleccionada}")

    except Exception as e:
        print(f"Error al seleccionar provincia BUENOS AIRES: {e}")


# llamar al step: Seleccionar provincia BUENOS AIRES
seleccionar_provincia_buenos_aires(driver)


# Seleccionar localidad VALERIA DEL MAR
def seleccionar_localidad_valeria_del_mar(driver):
    """
    Despliega el combo 'vXLOCCOD' y selecciona la opción con valor '1833' (VALERIA DEL MAR),
    disparando los eventos GeneXus correspondientes (onchange, onblur).
    """
    try:
        print("Seleccionando localidad: VALERIA DEL MAR (valor='1833')...")

        # Esperar que el combo sea visible y clickeable
        combo_localidad = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "vXLOCCOD"))
        )

        # Hacer scroll hasta el elemento y desplegar
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", combo_localidad
        )
        time.sleep(0.3)
        combo_localidad.click()
        time.sleep(0.3)

        # Seleccionar la opción por valor
        select = Select(combo_localidad)
        select.select_by_value("1833")
        time.sleep(0.4)

        # Disparar manualmente los eventos GeneXus
        driver.execute_script(
            """
            const el = document.getElementById('vXLOCCOD');
            el.dispatchEvent(new Event('change', {bubbles:true}));
            el.dispatchEvent(new Event('blur', {bubbles:true}));
            try {
                if (window.gx && gx.evt && gx.evt.onchange) gx.evt.onchange(el, event);
                if (window.gx && gx.evt && gx.evt.onblur) gx.evt.onblur(el, event);
            } catch(e) {}
        """
        )

        # Confirmar la selección
        opcion = select.first_selected_option.text.strip()
        if "VALERIA DEL MAR" in opcion.upper():
            print(f"Localidad seleccionada correctamente: {opcion}")
        else:
            print(f"Verificar selección. Opción actual: {opcion}")

    except Exception as e:
        print(f"Error al seleccionar localidad VALERIA DEL MAR: {e}")


# llamar al step: Seleccionar localidad VALERIA DEL MAR
seleccionar_localidad_valeria_del_mar(driver)


# Seleccionar opción "OTRO"
def seleccionar_otro_vFSE005COL(driver):
    """
    Despliega el combo 'vFSE005COL' y selecciona la opción con valor '25500' (OTRO),
    ejecutando los eventos GeneXus correspondientes.
    """
    try:
        print("Seleccionando opción 'OTRO' (valor='25500') en vFSE005COL...")

        # Esperar a que el combo sea visible y clickeable
        combo_otro = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "vFSE005COL"))
        )

        # Hacer scroll hasta el elemento y click para abrirlo
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", combo_otro
        )
        time.sleep(0.3)
        combo_otro.click()
        time.sleep(0.3)

        # Seleccionar la opción "OTRO" (valor 25500)
        select = Select(combo_otro)
        select.select_by_value("25500")
        time.sleep(0.4)

        # Disparar manualmente eventos GeneXus
        driver.execute_script(
            """
            const el = document.getElementById('vFSE005COL');
            el.dispatchEvent(new Event('change', {bubbles:true}));
            el.dispatchEvent(new Event('blur', {bubbles:true}));
            try {
                if (window.gx && gx.evt && gx.evt.onchange) gx.evt.onchange(el, event);
                if (window.gx && gx.evt && gx.evt.onblur) gx.evt.onblur(el, event);
            } catch(e) {}
        """
        )

        # Verificar la opción seleccionada
        opcion_final = select.first_selected_option.text.strip()
        if "OTRO" in opcion_final.upper():
            print(f"Opción seleccionada correctamente: {opcion_final}")
        else:
            print(f"Verificar selección. Opción actual: {opcion_final}")

    except Exception as e:
        print(f"Error al seleccionar opción 'OTRO' en vFSE005COL: {e}")


# llamar al step: Seleccionar opción "OTRO"
seleccionar_otro_vFSE005COL(driver)


# Ingresar código postal 7166 con validación, reintento y reubicación


def ingresar_codigo_postal(driver, codigo_postal="7166", max_reintentos=3):
    """
    Ingresa el código postal (por defecto 7166) en el campo 'vCODPOS'.
    Reintenta si el valor no se aplica correctamente o el campo se recarga.
    """
    print(f"Iniciando ingreso de código postal: {codigo_postal}")
    intentos = 0

    while intentos < max_reintentos:
        try:
            # Buscar nuevamente el campo en cada intento (por si GeneXus refrescó el DOM)
            campo_cp = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "vCODPOS"))
            )
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "vCODPOS"))
            )
            time.sleep(0.3)

            # Scroll para centrar el campo visible
            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", campo_cp
            )
            time.sleep(0.3)
            campo_cp.click()
            time.sleep(0.3)

            # Limpiar contenido anterior
            campo_cp.send_keys(Keys.CONTROL + "a")
            campo_cp.send_keys(Keys.DELETE)
            time.sleep(0.2)

            # Escribir código postal
            campo_cp.send_keys(codigo_postal)
            time.sleep(0.2)

            # Disparar eventos GeneXus (onchange y onblur)
            driver.execute_script(
                """
                const el = document.getElementById('vCODPOS');
                el.dispatchEvent(new Event('change', {bubbles:true}));
                el.dispatchEvent(new Event('blur', {bubbles:true}));
                try {
                    if (window.gx && gx.evt && gx.evt.onchange) gx.evt.onchange(el, event);
                    if (window.gx && gx.evt && gx.evt.onblur) gx.evt.onblur(el, event);
                } catch(e) {}
                """
            )

            time.sleep(0.6)

            # Leer valor final del campo
            valor_final = campo_cp.get_attribute("value").strip()

            if valor_final == codigo_postal:
                print(f"Código postal confirmado correctamente: {valor_final}")
                return True
            else:
                print(
                    f"Valor leído: '{valor_final}'. Reintentando ({intentos+1}/{max_reintentos})..."
                )
                intentos += 1
                time.sleep(1.0)

        except Exception as e:
            print(f"Error en intento {intentos+1}: {e}")
            intentos += 1
            time.sleep(1.0)

    # Si no se pudo confirmar después de varios intentos
    print(
        "No se pudo ingresar el código postal correctamente después de varios intentos."
    )
    driver.save_screenshot("error_codigo_postal.png")
    return False


# Llamar al step

ingresar_codigo_postal(driver)


# Hacer clic en botón Confirmar
def presionar_boton_confirmar(driver):
    """
    Hace clic en el botón 'Confirmar' (GeneXus) visible en pantalla.
    Aplica scroll, validación de visibilidad y ejecución del evento GX.
    """
    print("Buscando botón 'Confirmar' en la pantalla actual...")

    try:
        # Esperar el botón clickeable
        boton_confirmar = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//a[normalize-space()='Confirmar']"))
        )

        # Desplazar al centro y hacer clic real
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", boton_confirmar
        )
        time.sleep(0.3)
        boton_confirmar.click()
        print("Botón 'Confirmar' clickeado correctamente.")

        # Forzar evento GeneXus si es necesario
        driver.execute_script(
            """
            const btn = arguments[0];
            if (btn && window.gx && gx.evt) {
                try { gx.evt.execEvt('', false, btn.getAttribute('data-gx-evt'), btn); } catch(e) {}
            }
        """,
            boton_confirmar,
        )

        time.sleep(1)

    except Exception as e:
        print(f"Error al presionar el botón 'Confirmar': {e}")


# Ejecutar el paso
presionar_boton_confirmar(driver)


# Esperar hasta que el iframe principal esté presente
print("Esperando iframe principal id='1'...")
driver.switch_to.default_content()
iframe_principal = WebDriverWait(driver, 25).until(
    EC.presence_of_element_located((By.XPATH, "//iframe[@id='1']"))
)
driver.switch_to.frame(iframe_principal)
print("Ingresé al iframe principal id='1'.")

# Esperar hasta que process1_step12 esté visible (con reintento)
print("Esperando a que process1_step12 cambie a visible...")

iframe_visible = None
for i in range(40):  # hasta 40 intentos (unos 40 segundos máx)
    frames = driver.find_elements(By.XPATH, "//iframe[@name='process1_step12']")
    if frames:
        f = frames[0]
        style = f.get_attribute("style") or ""
        if "visibility: visible" in style and "opacity: 1" in style:
            iframe_visible = f
            print(f"Iframe process1_step12 visible tras {i+1} intentos.")
            break
        else:
            print(f"Intento {i+1}: todavía oculto ({style})")
    else:
        print("Aún no se encuentra el iframe process1_step12.")
    time.sleep(1)

if not iframe_visible:
    raise TimeoutException("El iframe process1_step12 nunca se volvió visible.")

driver.switch_to.frame(iframe_visible)
print("Entré correctamente al iframe process1_step12.")


# Seleccionar fila "Particular/Social" sin forzar execEvt por defecto
def seleccionar_registro_particular_social(driver, forzar_evento=False):
    """
    Selecciona la fila 'Particular/Social' en grilla GeneXus.
    Evita llamar execEvt por defecto para no dejar la UI bloqueada.
    Espera a que terminen overlays/AJAX de GX.
    Si forzar_evento=True, dispara el evento una única vez como plan B.
    """

    def esperar_fin_ajax_gx(timeout=8):
        """Espera a que no haya overlays ni AJAX en progreso (best-effort)."""
        fin = time.time() + timeout
        while time.time() < fin:
            try:
                # Si existe gx.ajax.iscallinprogress y está en progreso, esperamos
                en_progreso = driver.execute_script(
                    """
                    try {
                        if (window.gx && gx.ajax && typeof gx.ajax.iscallinprogress === 'function') {
                            return gx.ajax.iscallinprogress();
                        }
                        return false;
                    } catch(e){ return false; }
                """
                )
            except Exception:
                en_progreso = False

            # Overlays comunes
            overlays = driver.find_elements(
                By.CSS_SELECTOR,
                ".modal-backdrop, .loading, .loader, .gx-mask, .blockUI, .waitoverlay",
            )
            visibles = [o for o in overlays if o.is_displayed()]
            if not en_progreso and not visibles:
                return True
            time.sleep(0.2)
        return False

    print("Buscando registro 'Particular/Social' en la tabla...")

    try:
        # 1) Localizar y llevar al centro
        registro = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (By.XPATH, "//span[normalize-space(text())='Particular/Social']")
            )
        )
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", registro
        )
        time.sleep(0.2)

        # 2) Intento de click normal; si no responde, click JS
        try:
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//span[normalize-space(text())='Particular/Social']")
                )
            )
            registro.click()
            print("Click normal sobre 'Particular/Social'.")
        except Exception as e:
            driver.execute_script(
                "arguments[0].dispatchEvent(new MouseEvent('click', {bubbles:true}));",
                registro,
            )
            print(
                f"Click forzado (dispatchEvent) sobre 'Particular/Social'. Detalle: {e}"
            )

        # 3) Esperar a que GX termine de procesar y libere la UI
        if esperar_fin_ajax_gx(timeout=10):
            print("UI liberada tras la selección (sin execEvt).")
        else:
            print("Timeout esperando fin de AJAX/overlay.")

        # 4) PLAN B (opcional y una sola vez): forzar evento correcto
        if forzar_evento:
            driver.execute_script(
                """
                const el = arguments[0];
                try {
                    if (window.gx && gx.evt) {
                        const rowId = (el.id && el.id.split('_').pop()) || '0001';
                        // Evento típico de la grilla de domicilios:
                        gx.evt.execEvt('EGRIDDOMICILIOS.CLICK.', false, 'EGRIDDOMICILIOS.CLICK.' + rowId, el);
                    }
                } catch(e) { console.warn('execEvt plan B falló:', e); }
            """,
                registro,
            )
            # Espera corta posterior
            esperar_fin_ajax_gx(timeout=8)
            print("execEvt plan B ejecutado.")

        time.sleep(0.5)

    except Exception as e:
        print(f"Error al seleccionar registro 'Particular/Social': {e}")


# Ejecutar el paso (sin forzar evento)
seleccionar_registro_particular_social(driver)


# seleccionar registro
def esperar_sin_overlay(driver, timeout=20):
    # Espera a que no haya overlays comunes de GeneXus
    fin = time.time() + timeout
    while time.time() < fin:
        overlays = driver.find_elements(
            By.CSS_SELECTOR,
            "#gx-mask, .gx-mask, .gx-ui-disabled, .gx-pending, .K2BToolsModalBackground",
        )
        vis = [o for o in overlays if o.is_displayed()]
        if not vis:
            return True
        time.sleep(0.2)
    return False


def presionar_boton_telefonos(driver, esperar_iframe_name=None, timeout_iframe=40):
    print("Intentando abrir 'Teléfonos' (control GX BTNOPTELEF)...")
    try:
        # 0) Asegurar que no haya overlay bloqueando
        esperar_sin_overlay(driver, 20)

        # 1) Tomar span contenedor y su <a>
        span = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "BTNOPTELEF"))
        )
        WebDriverWait(driver, 10).until(EC.visibility_of(span))

        # Puede estar dentro: <span id="BTNOPTELEF"><a>Teléfonos</a></span>
        link = span.find_element(By.XPATH, ".//a[normalize-space()='Teléfonos']")

        # 2) Scroll y clic normal
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", span)
        time.sleep(0.2)
        try:
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable(
                    (By.XPATH, ".//a[normalize-space()='Teléfonos']")
                )
            )
            link.click()
            print("Clic normal en <a> 'Teléfonos'.")
        except (
            ElementClickInterceptedException,
            StaleElementReferenceException,
            TimeoutException,
        ):
            # 3) Actions
            try:
                ActionChains(driver).move_to_element(link).pause(0.1).click().perform()
                print("Clic con Actions en 'Teléfonos'.")
            except Exception:
                # 4) JS click + MouseEvent
                try:
                    driver.execute_script("arguments[0].click();", link)
                    print("JS click en 'Teléfonos'.")
                except Exception:
                    driver.execute_script(
                        """
                        const el = arguments[0];
                        el.dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, composed:true}));
                    """,
                        link,
                    )
                    print("MouseEvent('click') disparado en 'Teléfonos'.")

        # 5) Forzar eventos GeneXus sobre el control (span) y/o el <a>
        try:
            driver.execute_script(
                """
                (function(){
                    const span = document.getElementById('BTNOPTELEF');
                    const a = span ? span.querySelector('a') : null;

                    // Disparos genéricos
                    if (a) {
                        a.dispatchEvent(new Event('focus', {bubbles:true}));
                        a.dispatchEvent(new Event('click', {bubbles:true, cancelable:true}));
                        a.dispatchEvent(new Event('blur',  {bubbles:true}));
                    }

                    if (window.gx && gx.evt) {
                        // 1) Usar data-gx-evt del <a> si existe
                        const evtCode = a ? (a.getAttribute('data-gx-evt') || '5') : '5';
                        try { gx.evt.execEvt('', false, evtCode, a || span); } catch(e) {}

                        // 2) Probar firmas típicas de eventos GX por nombre del control
                        const tries = [
                            "E'BTNOPTELEF'.",
                            "E\\'BTNOPTELEF\\'.",
                            "E_BTNOPTELEF.",
                            "EENTER."  // por si el botón mappea Enter
                        ];
                        for (const t of tries) { try { gx.evt.execEvt('', false, t, a || span); } catch(e) {} }

                        // 3) linkClick auxiliar
                        try { if (a && gx.evt.linkClick) gx.evt.linkClick(a); } catch(e) {}
                    }
                })();
            """
            )
            print("Handlers GeneXus forzados (best-effort).")
        except Exception:
            pass

        # 6) Espera breve a navegación/render
        esperar_sin_overlay(driver, 10)
        time.sleep(0.8)

        # 7) (OPCIONAL) Esperar iframe siguiente si te sirve verificar acá
        if esperar_iframe_name:
            print(f"Esperando iframe '{esperar_iframe_name}' visible...")
            ok = False
            for i in range(timeout_iframe):
                driver.switch_to.default_content()
                frames = driver.find_elements(
                    By.XPATH, f"//iframe[@name='{esperar_iframe_name}']"
                )
                visible = False
                for f in frames:
                    style = f.get_attribute("style") or ""
                    if "visibility: visible" in style and (
                        "opacity: 1" in style or "opacity:1" in style
                    ):
                        visible = True
                        break
                if visible:
                    print(
                        f"Iframe '{esperar_iframe_name}' visible tras {i+1} intentos."
                    )
                    ok = True
                    break
                time.sleep(1)
            if not ok:
                raise TimeoutException(
                    f"No apareció iframe '{esperar_iframe_name}' tras el clic en 'Teléfonos'."
                )

        print("Paso 'Teléfonos' procesado.")
    except Exception as e:
        print(f"Error al presionar 'Teléfonos': {e}")


# Ejecutar el paso
presionar_boton_telefonos(driver)


# Click "Agregar" dentro de process1_step15 y esperar
def click_agregar_en_telefonos(driver, next_iframe="process1_step16", max_reintentos=3):

    from selenium.common.exceptions import (
        ElementClickInterceptedException,
        StaleElementReferenceException,
        TimeoutException,
    )

    def esperar_sin_overlay(timeout=10):
        fin = time.time() + timeout
        while time.time() < fin:
            try:
                overlays = driver.find_elements(
                    By.CSS_SELECTOR,
                    ".modal-backdrop, .loading, .loader, .gx-mask, .blockUI, .waitoverlay",
                )
                visibles = [o for o in overlays if o.is_displayed()]
                if not visibles:
                    # si hay API GX, chequear ajax en progreso
                    en_ajax = driver.execute_script(
                        """
                        try {
                            return (window.gx && gx.ajax && typeof gx.ajax.iscallinprogress==='function')
                                   ? gx.ajax.iscallinprogress() : false;
                        } catch(e){ return false; }
                    """
                    )
                    if not en_ajax:
                        return True
            except Exception:
                return True
            time.sleep(0.2)
        return False

    def entrar_a_step(nombre):
        # Estamos en id='1' (contenedor principal)
        driver.switch_to.default_content()
        # entrar al iframe principal id='1'
        root = WebDriverWait(driver, 25).until(
            EC.presence_of_element_located((By.XPATH, "//iframe[@id='1']"))
        )
        driver.switch_to.frame(root)
        # esperar a que el step esté visible
        for _ in range(40):
            frames = driver.find_elements(By.XPATH, f"//iframe[@name='{nombre}']")
            if frames:
                f = frames[0]
                style = (f.get_attribute("style") or "").replace(" ", "").lower()
                # GeneXus suele usar visibility + opacity
                if "visibility:visible" in style and ("opacity:1" in style):
                    driver.switch_to.frame(f)
                    return True
            time.sleep(1)
        return False

    for intento in range(1, max_reintentos + 1):
        print(f"[Intento {intento}] Click en 'Agregar' dentro de process1_step15...")

        # 1) Entrar al step15 (contexto correcto para el botón)
        if not entrar_a_step("process1_step15"):
            print("No pude entrar a process1_step15.")
            continue

        esperar_sin_overlay(8)

        # 2) Buscar botón 'Agregar' visible dentro del step15
        try:
            # menos restrictivo: por texto; a veces no está @data-gx-evt
            boton = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//a[normalize-space(.)='Agregar']")
                )
            )
        except TimeoutException:
            # fallback: primer <a> con texto 'Agregar' visible por JS
            boton = driver.execute_script(
                """
                const cand = Array.from(document.querySelectorAll('a'))
                  .filter(a => a.textContent && a.textContent.trim()==='Agregar' && a.offsetParent!==null);
                return cand.length ? cand[0] : null;
            """
            )
            if not boton:
                print("No encontré botón 'Agregar' dentro de process1_step15.")
                continue

        # 3) Scroll + click (normal, luego fallback JS si hace falta)
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", boton)
        time.sleep(0.2)
        try:
            boton.click()
            print("Click normal en 'Agregar'.")
        except (
            ElementClickInterceptedException,
            StaleElementReferenceException,
            TimeoutException,
        ) as e:
            driver.execute_script("arguments[0].click();", boton)
            print(f"Click JS en 'Agregar'. Detalle: {e}")

        # (Opcional) empujón GX con prudencia (sin romper estados)
        try:
            driver.execute_script(
                """
                const el = arguments[0];
                if (window.gx && gx.evt) {
                    try { gx.evt.execEvt('', false, el.id || '', el); } catch(e){}
                }
            """,
                boton,
            )
        except Exception:
            pass

        # 4) Salir a root y esperar que aparezca el siguiente step (process1_step16)
        driver.switch_to.default_content()
        # re-entrar al iframe id='1' para ver sus hijos
        try:
            root = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//iframe[@id='1']"))
            )
            driver.switch_to.frame(root)
        except TimeoutException:
            print("No pude reingresar al iframe id='1' para validar step siguiente.")
            continue

        print(f"Esperando '{next_iframe}' visible...")
        ok = False
        for i in range(20):
            frames = driver.find_elements(By.XPATH, f"//iframe[@name='{next_iframe}']")
            if frames:
                f = frames[0]
                style = (f.get_attribute("style") or "").replace(" ", "").lower()
                if "visibility:visible" in style and ("opacity:1" in style):
                    ok = True
                    print(f"'{next_iframe}' visible en {i+1} intentos.")
                    break
            time.sleep(1)

        if ok:
            # entrar al step16 para continuar tu flujo
            driver.switch_to.frame(
                driver.find_element(By.XPATH, f"//iframe[@name='{next_iframe}']")
            )
            return True
        else:
            print("No apareció el step siguiente; reintentamos el click en Agregar.")

    # Si agotó reintentos:
    driver.switch_to.default_content()
    print(
        "No se pudo abrir el formulario de Alta ('process1_step16'). Evidencia: error_boton_agregar.png"
    )
    return False


# invocar el paso
click_agregar_en_telefonos(driver, next_iframe="process1_step16", max_reintentos=3)


# Ingresar '11' en el campo vPREFIJOAUX dentro del iframe process1_step16
def ingresar_prefijo_aux(driver, valor="11", intentos=3):
    """
    Ingresa un valor en el campo vPREFIJOAUX dentro del iframe process1_step16.
    Incluye reintento y disparo de eventos GeneXus (focus/change/blur).
    """

    print(f"Intentando ingresar '{valor}' en el campo vPREFIJOAUX...")

    for intento in range(1, intentos + 1):
        try:
            # Asegurar contexto correcto
            driver.switch_to.default_content()
            iframe_principal = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//iframe[@id='1']"))
            )
            driver.switch_to.frame(iframe_principal)
            iframe_form = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.NAME, "process1_step16"))
            )
            driver.switch_to.frame(iframe_form)

            # Esperar campo visible
            campo = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "vPREFIJOAUX"))
            )
            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", campo
            )
            time.sleep(0.2)

            campo.clear()
            campo.send_keys(valor)
            print(f"Valor '{valor}' ingresado (intento {intento}).")

            # Disparar eventos GeneXus
            driver.execute_script(
                """
                const el = arguments[0];
                if (window.gx && gx.evt) {
                    try {
                        gx.evt.onfocus(el, 117,'',false,'0001',0);
                        gx.evt.onchange(el, null);
                        gx.evt.onblur(el,117);
                    } catch(e){}
                }
            """,
                campo,
            )

            # Confirmar valor
            if campo.get_attribute("value").strip() == valor:
                print(f"Verificación OK: '{valor}' seteado correctamente.")
                return
            else:
                raise Exception("Valor no seteado correctamente")

        except Exception as e:
            print(f"Intento {intento} falló: {e}")
            time.sleep(1)

    print("No se pudo ingresar el valor tras múltiples intentos.")


# Ejecutar el paso
ingresar_prefijo_aux(driver)


# Ingresar '12345678' en el campo vTELEFONOAUX
def ingresar_telefono_aux(driver, valor="12345678", intentos=3):
    """
    Ingresa un número de teléfono dentro del iframe process1_step16.
    Incluye reintento y disparo de eventos GeneXus.
    """

    print(f"Intentando ingresar '{valor}' en el campo vTELEFONOAUX...")

    for intento in range(1, intentos + 1):
        try:
            # Asegurar contexto correcto
            driver.switch_to.default_content()
            iframe_principal = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//iframe[@id='1']"))
            )
            driver.switch_to.frame(iframe_principal)
            iframe_form = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.NAME, "process1_step16"))
            )
            driver.switch_to.frame(iframe_form)

            campo = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "vTELEFONOAUX"))
            )
            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", campo
            )
            time.sleep(0.2)

            campo.clear()
            campo.send_keys(valor)
            print(f"Valor '{valor}' ingresado (intento {intento}).")

            driver.execute_script(
                """
                const el = arguments[0];
                if (window.gx && gx.evt) {
                    try {
                        gx.evt.onfocus(el, 120,'',false,'0001',0);
                        gx.evt.onchange(el, null);
                        gx.evt.onblur(el,120);
                    } catch(e){}
                }
            """,
                campo,
            )

            if campo.get_attribute("value").strip() == valor:
                print(f"Verificación OK: '{valor}' seteado correctamente.")
                return
            else:
                raise Exception("Valor no seteado correctamente")

        except Exception as e:
            print(f"Intento {intento} falló: {e}")
            time.sleep(1)

    print("No se pudo ingresar el número tras múltiples intentos.")


# Ejecutar el paso
ingresar_telefono_aux(driver)


# Ingresar '1' en el campo vDOTLEXP dentro del iframe process1_step16
def ingresar_dotlexp(driver, valor="1", intentos=3):
    """
    Ingresa un valor en el campo vDOTLEXP dentro del iframe process1_step16.
    Incluye reintento y disparo de eventos GeneXus (focus/change/blur).
    """

    print(f"Intentando ingresar '{valor}' en el campo vDOTLEXP...")

    for intento in range(1, intentos + 1):
        try:
            # Asegurar contexto correcto
            driver.switch_to.default_content()
            iframe_principal = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//iframe[@id='1']"))
            )
            driver.switch_to.frame(iframe_principal)
            iframe_form = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.NAME, "process1_step16"))
            )
            driver.switch_to.frame(iframe_form)

            # Esperar que el campo esté visible y habilitado
            campo = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "vDOTLEXP"))
            )
            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", campo
            )
            time.sleep(0.2)

            campo.clear()
            campo.send_keys(valor)
            print(f"Valor '{valor}' ingresado (intento {intento}).")

            # Disparar eventos GeneXus
            driver.execute_script(
                """
                const el = arguments[0];
                if (window.gx && gx.evt) {
                    try {
                        gx.evt.onfocus(el, 137,'',false,'0001',0);
                        gx.evt.onchange(el, null);
                        gx.evt.onblur(el,137);
                    } catch(e){}
                }
            """,
                campo,
            )

            # Verificar el valor
            if campo.get_attribute("value").strip() == valor:
                print(f"Verificación OK: '{valor}' seteado correctamente.")
                return
            else:
                raise Exception("Valor no seteado correctamente")

        except Exception as e:
            print(f"Intento {intento} falló: {e}")
            time.sleep(1)

    print("No se pudo ingresar el valor tras múltiples intentos.")


# Ejecutar el paso
ingresar_dotlexp(driver)


# Ingresar 'AUTOMATION' en el campo vDOFAXP
def ingresar_dofaxp(driver, valor="AUTOMATION", intentos=3):
    """
    Ingresa un texto en el campo vDOFAXP dentro del iframe process1_step16.
    Incluye reintento, mayúsculas automáticas y eventos GeneXus.
    """

    print(f"Intentando ingresar '{valor}' en el campo vDOFAXP...")

    for intento in range(1, intentos + 1):
        try:
            # Asegurar contexto correcto
            driver.switch_to.default_content()
            iframe_principal = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//iframe[@id='1']"))
            )
            driver.switch_to.frame(iframe_principal)
            iframe_form = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.NAME, "process1_step16"))
            )
            driver.switch_to.frame(iframe_form)

            # Esperar campo visible
            campo = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "vDOFAXP"))
            )
            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", campo
            )
            time.sleep(0.2)

            campo.clear()
            campo.send_keys(valor)
            print(f"Valor '{valor}' ingresado (intento {intento}).")

            # Disparar eventos GeneXus
            driver.execute_script(
                """
                const el = arguments[0];
                if (window.gx && gx.evt) {
                    try {
                        gx.evt.onfocus(el, 141,'',false,'0001',0);
                        gx.evt.onchange(el, null);
                        gx.evt.onblur(el,141);
                    } catch(e){}
                }
            """,
                campo,
            )

            # Confirmar valor en mayúsculas
            current_value = campo.get_attribute("value").strip()
            if current_value == valor.upper():
                print(f"Verificación OK: '{current_value}' seteado correctamente.")
                return
            else:
                raise Exception(
                    f"Valor leído '{current_value}' distinto de '{valor.upper()}'."
                )

        except Exception as e:
            print(f"Intento {intento} falló: {e}")
            time.sleep(1)

    print("No se pudo ingresar el texto tras múltiples intentos.")


# Ejecutar el paso
ingresar_dofaxp(driver)


# Hacer clic en botón "Confirmar" dentro del iframe process1_step16
def presionar_boton_confirmar(driver):
    """
    Hace clic en el botón 'Confirmar' dentro del iframe process1_step16 (GeneXus).
    Asegura contexto correcto y dispara el evento GX correspondiente.
    """

    print("Buscando botón 'Confirmar' dentro del iframe process1_step16...")

    try:
        # Asegurar que estamos en el contexto correcto
        driver.switch_to.default_content()

        # Ingresar al iframe principal id="1"
        iframe_principal = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//iframe[@id='1']"))
        )
        driver.switch_to.frame(iframe_principal)

        # Ingresar al iframe del formulario actual (process1_step16)
        iframe_form = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.NAME, "process1_step16"))
        )
        driver.switch_to.frame(iframe_form)

        # Esperar el botón Confirmar visible
        boton = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//a[normalize-space(text())='Confirmar']")
            )
        )

        # Desplazarlo y hacer clic real
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", boton)
        time.sleep(0.3)
        boton.click()
        print("Click normal realizado sobre 'Confirmar'.")

        # Disparar evento GeneXus (por seguridad)
        driver.execute_script(
            """
            const el = arguments[0];
            if (window.gx && gx.evt) {
                try {
                    gx.evt.execEvt('', false, el.id || '', el);
                    console.log('Evento GeneXus ejecutado correctamente (Confirmar).');
                } catch (err) {
                    console.warn('gx.evt.execEvt no se ejecutó automáticamente:', err);
                }
            }
        """,
            boton,
        )

        # Pequeña espera por si la interfaz refresca
        time.sleep(1.5)

    except Exception as e:
        print(f"Error al presionar el botón 'Confirmar': {e}")

    finally:
        print("click_boton_confirmar")


# Ejecutar el paso
presionar_boton_confirmar(driver)


# Hacer clic en botón "Sí" de confirmación (maneja modales GX internos o globales)
def presionar_boton_si(driver):
    """
    Hace clic en el botón 'Sí' del cuadro de confirmación GeneXus.
    Detecta automáticamente si está en el modal del iframe actual o en el nivel global.
    Ejecuta el evento GX correspondiente y espera la transición posterior.
    """

    print("Buscando botón 'Sí' en el cuadro de confirmación...")

    try:
        boton_si = None

        # Opción A: intentar encontrarlo en el iframe process1_step16
        try:
            driver.switch_to.default_content()
            iframe_principal = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//iframe[@id='1']"))
            )
            driver.switch_to.frame(iframe_principal)

            iframe_form = driver.find_elements(By.NAME, "process1_step16")
            if iframe_form:
                driver.switch_to.frame(iframe_form[0])
                boton_si = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//a[normalize-space(text())='Sí']")
                    )
                )
                print("Botón 'Sí' encontrado dentro del iframe process1_step16.")
        except Exception:
            # Si no está en el iframe, seguimos con el plan B
            pass

        # Opción B: si no lo encontró dentro del iframe, buscarlo en default_content
        if not boton_si:
            driver.switch_to.default_content()
            boton_si = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//a[normalize-space(text())='Sí']")
                )
            )
            print("Botón 'Sí' encontrado en el nivel global (default_content).")

        # Desplazarlo al centro
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", boton_si
        )
        time.sleep(0.3)

        # Click real
        boton_si.click()
        print("Click normal realizado sobre el botón 'Sí'.")

        # Disparar evento GeneXus (por seguridad)
        driver.execute_script(
            """
            const el = arguments[0];
            if (window.gx && gx.evt) {
                try {
                    gx.evt.execEvt('', false, el.id || '', el);
                    console.log('Evento GeneXus ejecutado correctamente (botón Sí).');
                } catch (err) {
                    console.warn('gx.evt.execEvt no se ejecutó automáticamente:', err);
                }
            }
        """,
            boton_si,
        )

        # Esperar que desaparezca el modal (común en GX)
        WebDriverWait(driver, 10).until_not(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//a[normalize-space(text())='Sí']")
            )
        )
        print("Modal de confirmación cerrado correctamente.")

    except Exception as e:
        print(f"Error al presionar el botón 'Sí': {e}")

    finally:
        print("click_boton_si")


# Ejecutar el paso
presionar_boton_si(driver)


# Esperar hasta que el iframe principal esté presente
print("Esperando iframe principal id='1'...")
driver.switch_to.default_content()
iframe_principal = WebDriverWait(driver, 25).until(
    EC.presence_of_element_located((By.XPATH, "//iframe[@id='1']"))
)
driver.switch_to.frame(iframe_principal)
print("Ingresé al iframe principal id='1'.")

# Esperar hasta que process1_step15 esté visible (con reintento)
print("Esperando a que process1_step15 cambie a visible...")

iframe_visible = None
for i in range(40):  # hasta 40 intentos (unos 40 segundos máx)
    frames = driver.find_elements(By.XPATH, "//iframe[@name='process1_step15']")
    if frames:
        f = frames[0]
        style = f.get_attribute("style") or ""
        if "visibility: visible" in style and "opacity: 1" in style:
            iframe_visible = f
            print(f"Iframe process1_step15 visible tras {i+1} intentos.")
            break
        else:
            print(f"Intento {i+1}: todavía oculto ({style})")
    else:
        print("Aún no se encuentra el iframe process1_step15.")
    time.sleep(1)

if not iframe_visible:
    raise TimeoutException("El iframe process1_step15 nunca se volvió visible.")

driver.switch_to.frame(iframe_visible)
print("Entré correctamente al iframe process1_step15.")


# Hacer clic en botón "Finalizar" (ya dentro del iframe process1_step15)
def presionar_boton_finalizar(driver):
    """
    Hace clic en el botón 'Finalizar' en una pantalla GeneXus,
    asumiendo que ya estamos dentro del iframe process1_step15.
    Dispara el evento GX por seguridad.
    """

    print("Buscando botón 'Finalizar' dentro del iframe actual...")

    try:
        # Esperar el enlace <a> con texto 'Finalizar'
        boton_finalizar = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//a[normalize-space(text())='Finalizar']")
            )
        )

        # Scroll al centro y click real
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", boton_finalizar
        )
        time.sleep(0.3)
        boton_finalizar.click()
        print("Click normal realizado sobre el botón 'Finalizar'.")

        # Disparar evento GeneXus (por seguridad)
        driver.execute_script(
            """
            const el = arguments[0];
            if (window.gx && gx.evt) {
                try {
                    gx.evt.execEvt('', false, el.id || '', el);
                    console.log('Evento GeneXus ejecutado correctamente (Finalizar).');
                } catch (err) {
                    console.warn('gx.evt.execEvt no se ejecutó automáticamente:', err);
                }
            }
        """,
            boton_finalizar,
        )

        # Esperar un momento por postback o navegación
        time.sleep(1.5)

    except Exception as e:
        print(f"Error al presionar el botón 'Finalizar': {e}")

    finally:
        print("click_boton_finalizar")


# Ejecutar el paso
presionar_boton_finalizar(driver)


# Esperar hasta que el iframe principal esté presente
print("Esperando iframe principal id='1'...")
driver.switch_to.default_content()
iframe_principal = WebDriverWait(driver, 25).until(
    EC.presence_of_element_located((By.XPATH, "//iframe[@id='1']"))
)
driver.switch_to.frame(iframe_principal)
print("Ingresé al iframe principal id='1'.")

# Esperar hasta que process1_step12 esté visible (con reintento)
print("Esperando a que process1_step12 cambie a visible...")

iframe_visible = None
for i in range(40):  # hasta 40 intentos (unos 40 segundos máx)
    frames = driver.find_elements(By.XPATH, "//iframe[@name='process1_step12']")
    if frames:
        f = frames[0]
        style = f.get_attribute("style") or ""
        if "visibility: visible" in style and "opacity: 1" in style:
            iframe_visible = f
            print(f"Iframe process1_step15 visible tras {i+1} intentos.")
            break
        else:
            print(f"Intento {i+1}: todavía oculto ({style})")
    else:
        print("Aún no se encuentra el iframe process1_step12.")
    time.sleep(1)

if not iframe_visible:
    raise TimeoutException("El iframe process1_step12 nunca se volvió visible.")

driver.switch_to.frame(iframe_visible)
print("Entré correctamente al iframe process1_step12.")


# Hacer clic en botón "Confirmar" (ya dentro del iframe activo)
def presionar_boton_confirmar(driver):
    """
    Hace clic en el botón 'Confirmar' dentro del iframe actual.
    Ejecuta también el evento GeneXus correspondiente.
    """

    print("Buscando botón 'Confirmar' dentro del iframe actual...")

    try:
        # Esperar el enlace <a> con texto 'Confirmar'
        boton_confirmar = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//a[normalize-space(text())='Confirmar']")
            )
        )

        # Scroll al centro
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", boton_confirmar
        )
        time.sleep(0.3)

        # Click real
        boton_confirmar.click()
        print("Click normal realizado sobre el botón 'Confirmar'.")

        # Disparar evento GeneXus (por seguridad)
        driver.execute_script(
            """
            const el = arguments[0];
            if (window.gx && gx.evt) {
                try {
                    gx.evt.execEvt('', false, el.id || '', el);
                    console.log('Evento GeneXus ejecutado correctamente (botón Confirmar).');
                } catch (err) {
                    console.warn('gx.evt.execEvt no se ejecutó automáticamente:', err);
                }
            }
        """,
            boton_confirmar,
        )

        # Espera postback o navegación
        time.sleep(1.5)

    except Exception as e:
        print(f"Error al presionar el botón 'Confirmar': {e}")

    finally:
        print("click_boton_confirmar")


# Ejecutar el paso
presionar_boton_confirmar(driver)

# Esperar hasta que el iframe principal esté presente
print("Esperando iframe principal id='1'...")
driver.switch_to.default_content()
iframe_principal = WebDriverWait(driver, 25).until(
    EC.presence_of_element_located((By.XPATH, "//iframe[@id='1']"))
)
driver.switch_to.frame(iframe_principal)
print("Ingresé al iframe principal id='1'.")

# Esperar hasta que process1_step19 esté visible (con reintento)
print("Esperando a que process1_step19 cambie a visible...")

iframe_visible = None
for i in range(40):  # hasta 40 intentos (unos 40 segundos máx)
    frames = driver.find_elements(By.XPATH, "//iframe[@name='process1_step19']")
    if frames:
        f = frames[0]
        style = f.get_attribute("style") or ""
        if "visibility: visible" in style and "opacity: 1" in style:
            iframe_visible = f
            print(f"Iframe process1_step19 visible tras {i+1} intentos.")
            break
        else:
            print(f"Intento {i+1}: todavía oculto ({style})")
    else:
        print("Aún no se encuentra el iframe process1_step19.")
    time.sleep(1)

if not iframe_visible:
    raise TimeoutException("El iframe process1_step19 nunca se volvió visible.")

driver.switch_to.frame(iframe_visible)
print("Entré correctamente al iframe process1_step19.")


# Hacer clic en botón "Confirmar" (GX data-gx-evt=5)
def presionar_boton_confirmar(driver):
    """
    Hace clic en el botón 'Confirmar' identificado por data-gx-evt="5" y clase 'OpEnterText'.
    Se asume que ya estamos dentro del iframe correcto.
    Ejecuta click real y dispara el evento GeneXus para garantizar la acción.
    """

    print("Buscando botón 'Confirmar' (GeneXus)...")

    try:
        # Esperar el botón <a> con texto 'Confirmar' y atributo data-gx-evt="5"
        boton_confirmar = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//a[normalize-space(text())='Confirmar' and @data-gx-evt='5']",
                )
            )
        )

        # Asegurar visibilidad
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", boton_confirmar
        )
        time.sleep(0.3)

        # Click real
        boton_confirmar.click()
        print("Click normal realizado sobre el botón 'Confirmar'.")

        # Disparar evento GeneXus manualmente (por seguridad)
        driver.execute_script(
            """
            const el = arguments[0];
            if (window.gx && gx.evt) {
                try {
                    gx.evt.execEvt('', false, el.id || '', el);
                    console.log('Evento GeneXus ejecutado correctamente (Confirmar).');
                } catch (err) {
                    console.warn('gx.evt.execEvt no se ejecutó automáticamente:', err);
                }
            }
        """,
            boton_confirmar,
        )

        # Esperar un momento por postback o recarga
        time.sleep(1.5)

    except Exception as e:
        print(f"Error al presionar el botón 'Confirmar': {e}")

    finally:
        print("click_boton_confirmar")


presionar_boton_confirmar(driver)


# Esperar hasta que el iframe principal esté presente
print("Esperando iframe principal id='1'...")
driver.switch_to.default_content()
iframe_principal = WebDriverWait(driver, 25).until(
    EC.presence_of_element_located((By.XPATH, "//iframe[@id='1']"))
)
driver.switch_to.frame(iframe_principal)
print("Ingresé al iframe principal id='1'.")

# Esperar hasta que process1_step20 esté visible (con reintento)
print("Esperando a que process1_step19 cambie a visible...")

iframe_visible = None
for i in range(40):  # hasta 40 intentos (unos 40 segundos máx)
    frames = driver.find_elements(By.XPATH, "//iframe[@name='process1_step20']")
    if frames:
        f = frames[0]
        style = f.get_attribute("style") or ""
        if "visibility: visible" in style and "opacity: 1" in style:
            iframe_visible = f
            print(f"Iframe process1_step20 visible tras {i+1} intentos.")
            break
        else:
            print(f"Intento {i+1}: todavía oculto ({style})")
    else:
        print("Aún no se encuentra el iframe process1_step20.")
    time.sleep(1)

if not iframe_visible:
    raise TimeoutException("El iframe process1_step20 nunca se volvió visible.")

driver.switch_to.frame(iframe_visible)
print("Entré correctamente al iframe process1_step20.")


# Hacer clic en botón "Sí" (BTNOPSI) dentro del iframe process1_step20
def presionar_boton_si_en_step20(driver):
    """
    Entra al iframe process1_step20 y hace clic en el botón 'Sí' (BTNOPSI).
    Usa click real + fallbacks JS y dispara eventos GeneXus.
    """

    def entrar_a_step20():
        driver.switch_to.default_content()
        root = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//iframe[@id='1']"))
        )
        driver.switch_to.frame(root)
        step = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.NAME, "process1_step20"))
        )
        driver.switch_to.frame(step)

    try:
        print("Entrando a process1_step20…")
        entrar_a_step20()

        print("Buscando botón 'Sí' (BTNOPSI)…")
        # Preferimos el <a> dentro del span BTNOPSI
        a_si = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#BTNOPSI > a"))
        )

        # Asegurar visibilidad
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", a_si)
        time.sleep(0.2)

        # Click normal con fallback JS
        try:
            a_si.click()
            print("Click normal sobre 'Sí'.")
        except Exception as e:
            driver.execute_script("arguments[0].click();", a_si)
            print(f"Click JS sobre 'Sí'. Detalle: {e}")

        # Empujón GeneXus: linkClick + execEvt
        try:
            driver.execute_script(
                """
                const a = arguments[0];
                const span = a.closest('#BTNOPSI');
                if (window.gx && gx.evt) {
                    try { gx.evt.linkClick(a); } catch(e){}
                    try {
                        // usar el control name cuando está disponible
                        const ctrl = span ? (span.getAttribute('data-gx-evt-control') || 'BTNOPSI') : 'BTNOPSI';
                        // variantes típicas de GX
                        const tries = [
                            ctrl,                      // "BTNOPSI"
                            "E'"+ctrl+"'.",           // "E'BTNOPSI'."
                            "E_"+ctrl+".",            // "E_BTNOPSI." (por si cambia prefijo)
                            (a.getAttribute('data-gx-evt') || '5') // "5"
                        ];
                        for (const t of tries) { try { gx.evt.execEvt('', false, t, a); } catch(e){} }
                    } catch(e){}
                }
            """,
                a_si,
            )
            print("Eventos GeneXus disparados (best-effort).")
        except Exception:
            pass

        # Pequeña espera por si hay navegación/postback
        time.sleep(1.2)

    except Exception as e:
        print(f"Error al presionar 'Sí' (BTNOPSI): {e}")
    finally:
        print("click_boton_si_step20")


presionar_boton_si_en_step20(driver)


# Esperar hasta que el iframe principal esté presente
print("Esperando iframe principal id='1'...")
driver.switch_to.default_content()
iframe_principal = WebDriverWait(driver, 25).until(
    EC.presence_of_element_located((By.XPATH, "//iframe[@id='1']"))
)
driver.switch_to.frame(iframe_principal)
print("Ingresé al iframe principal id='1'.")

# Esperar hasta que process1_step21 esté visible (con reintento)
print("Esperando a que process1_step21 cambie a visible...")

iframe_visible = None
for i in range(40):  # hasta 40 intentos (unos 40 segundos máx)
    frames = driver.find_elements(By.XPATH, "//iframe[@name='process1_step21']")
    if frames:
        f = frames[0]
        style = f.get_attribute("style") or ""
        if "visibility: visible" in style and "opacity: 1" in style:
            iframe_visible = f
            print(f"Iframe process1_step21 visible tras {i+1} intentos.")
            break
        else:
            print(f"Intento {i+1}: todavía oculto ({style})")
    else:
        print("Aún no se encuentra el iframe process1_step21.")
    time.sleep(1)

if not iframe_visible:
    raise TimeoutException("El iframe process1_step21 nunca se volvió visible.")

driver.switch_to.frame(iframe_visible)
print("Entré correctamente al iframe process1_step21.")





# LOG DE DATOS DE CUENTA Y DOCUMENTO EN SQLITE


def inicializar_tabla_logs():
    """Crea la tabla logs_cuentas si no existe."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS logs_cuentas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            numero_cuenta TEXT NOT NULL,
            numero_documento TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()
    logger.info("Tabla 'logs_cuentas' lista en la base SQLite.")


def registrar_datos_cuenta(numero_cuenta, numero_documento):
    """Inserta un registro en logs_cuentas."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO logs_cuentas (numero_cuenta, numero_documento) VALUES (?, ?)",
            (numero_cuenta, numero_documento),
        )
        conn.commit()
        conn.close()
        logger.info(f"Registro insertado: Cuenta={numero_cuenta}, Documento={numero_documento}")
    except Exception as e:
        logger.error(f"Error al registrar datos en logs_cuentas: {e}")



# Crear tabla si no existe
inicializar_tabla_logs()



# Obtener y registrar datos de la cuenta creada

def obtener_datos_cuenta_y_documento(driver):
    """
    Obtiene el número de cuenta (span_vCTNRO) y el número de documento (span_vNUMDOC_0001)
    dentro del iframe actual, y los guarda en la tabla logs_cuentas de la base SQLite.
    """
    logger.info("Obteniendo datos de la cuenta y del documento...")

    try:
        cuenta_elem = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "span_vCTNRO"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", cuenta_elem)
        numero_cuenta = cuenta_elem.text.strip()
        logger.info(f"Número de cuenta detectado: {numero_cuenta}")

        documento_elem = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "span_vNUMDOC_0001"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", documento_elem)
        numero_documento = documento_elem.text.strip()
        logger.info(f"Número de documento detectado: {numero_documento}")

        # Guardar en la base
        registrar_datos_cuenta(numero_cuenta, numero_documento)
        return numero_cuenta, numero_documento

    except Exception as e:
        logger.error(f"Error al obtener datos de cuenta/documento: {e}")
        return None, None


# invoca el paso anterior
cuenta, documento = obtener_datos_cuenta_y_documento(driver)


# Hacer clic en botón "Finalizar" (ya dentro del iframe)
def presionar_boton_finalizar(driver):
    """
    Hace clic en el botón 'Finalizar' dentro del iframe actual (GeneXus).
    Ejecuta click real y dispara los eventos GX necesarios.
    """

    print("Buscando botón 'Finalizar' dentro del iframe actual...")

    try:
        # Esperar el enlace <a> con texto Finalizar
        boton_finalizar = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//a[normalize-space(text())='Finalizar']")
            )
        )

        # Desplazarlo al centro para asegurar visibilidad
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", boton_finalizar
        )
        time.sleep(0.3)

        # Intentar click normal con fallback JS
        try:
            boton_finalizar.click()
            print("Click normal realizado sobre 'Finalizar'.")
        except Exception as e:
            driver.execute_script("arguments[0].click();", boton_finalizar)
            print(f"Click JS alternativo ejecutado. Detalle: {e}")

        # Disparar los eventos GeneXus (por seguridad)
        driver.execute_script(
            """
            const el = arguments[0];
            if (window.gx && gx.evt) {
                try { gx.evt.linkClick(el); } catch(e){}
                const evt = el.getAttribute('data-gx-evt') || '5';
                const posibles = [
                    evt,
                    "E'BTNFINALIZAR'.",
                    "E_BTNFINALIZAR.",
                    "E'FINALIZAR'.",
                    "E_FINALIZAR."
                ];
                for (const t of posibles) {
                    try { gx.evt.execEvt('', false, t, el); } catch(e){}
                }
                console.log("Eventos GeneXus disparados para 'Finalizar'.");
            }
        """,
            boton_finalizar,
        )

        # Pequeña espera por postback o transición
        time.sleep(1.5)

    except Exception as e:
        print(f"Error al presionar el botón 'Finalizar': {e}")

    finally:
        print("click_boton_finalizar")


# Ejecutar el paso
presionar_boton_finalizar(driver)


# Esperar hasta que el iframe principal esté presente
print("Esperando iframe principal id='1'...")
driver.switch_to.default_content()
iframe_principal = WebDriverWait(driver, 25).until(
    EC.presence_of_element_located((By.XPATH, "//iframe[@id='1']"))
)
driver.switch_to.frame(iframe_principal)
print("Ingresé al iframe principal id='1'.")

# Esperar hasta que process1_step22 esté visible (con reintento)
print("Esperando a que process1_step22 cambie a visible...")

iframe_visible = None
for i in range(40):  # hasta 40 intentos (unos 40 segundos máx)
    frames = driver.find_elements(By.XPATH, "//iframe[@name='process1_step22']")
    if frames:
        f = frames[0]
        style = f.get_attribute("style") or ""
        if "visibility: visible" in style and "opacity: 1" in style:
            iframe_visible = f
            print(f"Iframe process1_step22 visible tras {i+1} intentos.")
            break
        else:
            print(f"Intento {i+1}: todavía oculto ({style})")
    else:
        print("Aún no se encuentra el iframe process1_step22.")
    time.sleep(1)

if not iframe_visible:
    raise TimeoutException("El iframe process1_step22 nunca se volvió visible.")

driver.switch_to.frame(iframe_visible)
print("Entré correctamente al iframe process1_step22.")


# Hacer clic en botón "Confirmar" (ya dentro del iframe)
def presionar_boton_confirmar(driver):
    """
    Hace clic en el botón 'Confirmar' dentro del iframe actual.
    Realiza clic real con fallback JS y dispara los eventos GeneXus (gx.evt).
    """

    print("Buscando botón 'Confirmar' dentro del iframe actual...")

    try:
        # Esperar el enlace <a> con texto Confirmar
        boton_confirmar = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//a[normalize-space(text())='Confirmar']")
            )
        )

        # Asegurar visibilidad desplazándolo al centro
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", boton_confirmar
        )
        time.sleep(0.3)

        # Click normal con fallback JS si falla
        try:
            boton_confirmar.click()
            print("Click normal realizado sobre 'Confirmar'.")
        except Exception as e:
            driver.execute_script("arguments[0].click();", boton_confirmar)
            print(f"Click JS alternativo ejecutado. Detalle: {e}")

        # Ejecutar los eventos GeneXus por seguridad
        driver.execute_script(
            """
            const el = arguments[0];
            if (window.gx && gx.evt) {
                try { gx.evt.linkClick(el); } catch(e){}
                const evt = el.getAttribute('data-gx-evt') || '5';
                const posibles = [
                    evt,
                    "E'BTNCONFIRMAR'.",
                    "E_BTNCONFIRMAR.",
                    "E'CONFIRMAR'.",
                    "E_CONFIRMAR."
                ];
                for (const t of posibles) {
                    try { gx.evt.execEvt('', false, t, el); } catch(e){}
                }
                console.log("Eventos GeneXus disparados para 'Confirmar'.");
            }
        """,
            boton_confirmar,
        )

        # Espera breve por postback o navegación
        time.sleep(1.5)

    except Exception as e:
        print(f"Error al presionar el botón 'Confirmar': {e}")

    finally:
        print("FINALIZO EL FLUJO OK PORFINNNNN")


# Ejecutar el paso
presionar_boton_confirmar(driver)
