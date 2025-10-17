# gx_helpers.py
import random  # Para generar retrasos aleatorios
import time
from datetime import datetime, timedelta

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Funciones auxiliares para login


def completar_login(driver, usuario="INSTALADOR", password="Bancor123"):
    wait = WebDriverWait(driver, 10)

    user_input = wait.until(EC.presence_of_element_located((By.ID, "vUSER")))
    user_input.clear()
    user_input.send_keys(usuario)

    password_input = driver.find_element(By.NAME, "vPASSWORD")
    password_input.clear()
    password_input.send_keys(password)

    login_button = driver.find_element(By.ID, "BTNOPINICIARSESION")
    login_button.click()


def verificar_login_exitoso(driver):
    try:
        # Verificamos que aparezca un elemento del home (ajustar ID si tenés algo más fiable)
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (By.ID, "vNOMBREUSUARIO")
            )  # 👈 ajustar a tu app
        )
        return True
    except:
        return False


# Login reintento
def intentar_con_reintento(funcion, verificador, intentos=3, espera=1):
    for intento in range(1, intentos + 1):
        print(f"Intento {intento} de {intentos}...")
        funcion()
        time.sleep(espera)
        if verificador():
            print(f"Verificación exitosa en intento {intento}.")
            return True
        else:
            print("Verificación fallida.")
    print("Todos los intentos fallaron.")
    return False


# --- Función para elegir nivel educativo aleatorio ---

import random


def nivel_educativo_random():
    niveles = ["1", "2", "3", "4", "5", "6", "999"]
    return random.choice(niveles)


def set_gx_select(driver, field_id, value, desc_event, delay=1000):
    """
    Selecciona un valor en un combo GeneXus y reestablece tras el refresh.
    """
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, field_id)))

    js = f"""
        const sel = document.getElementById('{field_id}');
        sel.focus();
        sel.value = '{value}';
        if (typeof gx !== 'undefined' && gx.evt) {{
            gx.evt.onchange(sel, new Event('change', {{ bubbles: true }}));
            gx.evt.onblur(sel, 220);
        }}
        if (typeof DescartesContainer !== 'undefined' && DescartesContainer.RefreshOnchange) {{
            DescartesContainer.RefreshOnchange('{desc_event}');
        }}

        // Reasignar después del refresh y verificar
        setTimeout(() => {{
            const sel2 = document.getElementById('{field_id}');
            if (sel2) {{
                sel2.value = '{value}';
                if (typeof gx !== 'undefined' && gx.evt) {{
                    gx.evt.onchange(sel2, new Event('change', {{ bubbles: true }}));
                    gx.evt.onblur(sel2, 220);
                }}
                if (sel2.value !== '{value}') {{
                    console.warn('Valor no persistió tras reintento.');
                }} else {{
                    console.log('Nivel educativo seteado post-refresh:', sel2.value);
                }}
            }}
        }}, {delay});
    """
    driver.execute_script(js)
    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.TAB)


#  Esperar y setear combo con lógica de refresco
def esperar_y_setear_combo(
    driver, field_id, value, gx_event, timeout=20, delay_post_refresh=1000
):
    """
    Espera que el combo GX esté presente y lo setea de forma segura con lógica de refresco.
    """
    print(f"Esperando a que aparezca el combo '{field_id}' en el DOM...")
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.ID, field_id))
    )
    print(f"Combo '{field_id}' detectado. Seleccionando valor {value}...")

    set_gx_select(driver, field_id, value, gx_event, delay=delay_post_refresh)

    # Revalidación post-refresh para combos con lógica GX
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, field_id))
        )
        final_combo = driver.find_element(By.ID, field_id)
        print(
            f"Combo '{field_id}' reapareció. Valor final: {final_combo.get_attribute('value')}"
        )
    except Exception:
        print(f"Combo '{field_id}' no reapareció tras el refresh.")


# --- fecha aleatoria mayor a 18 años ---
def completar_fecha_nacimiento(driver, field_id="vPFFNAC", edad_minima=20, timeout=10):
    # Calcular fecha aleatoria entre hace 60 años y edad mínima
    hoy = datetime.today()
    fecha_inicio = hoy - timedelta(days=60 * 365)
    fecha_fin = hoy - timedelta(days=edad_minima * 365)
    fecha_random = fecha_inicio + (fecha_fin - fecha_inicio) * random.random()
    fecha_formateada = fecha_random.strftime("%d/%m/%Y")

    print(f"Completando fecha de nacimiento aleatoria: {fecha_formateada}")

    # Esperar el campo y escribir la fecha
    campo_fecha = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.ID, field_id))
    )
    campo_fecha.clear()
    campo_fecha.send_keys(fecha_formateada)

    # Ejecutar validaciones GX: blur y onchange
    driver.execute_script(
        f"""
        const input = document.getElementById('{field_id}');
        input.dispatchEvent(new Event('change', {{ bubbles: true }}));
        input.dispatchEvent(new Event('blur', {{ bubbles: true }}));
    """
    )


# Completar fecha de nacimiento usando el calendario emergente
def completar_fecha_nacimiento_click(driver, edad_minima=20):
    print("Seleccionando fecha de nacimiento...")

    # 1. Generar fecha aleatoria mayor a edad mínima
    hoy = datetime.now()
    inicio = datetime(1970, 1, 1)
    fin = datetime(hoy.year - edad_minima, hoy.month, hoy.day)
    fecha_random = inicio + timedelta(days=random.randint(0, (fin - inicio).days))
    dia = fecha_random.day
    anio = fecha_random.year
    print(f"Fecha generada: {fecha_random.strftime('%d/%m/%Y')}")

    # 2. Click en el input para abrir el calendario
    input_fecha = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "vPFFNAC"))
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", input_fecha)
    time.sleep(0.3)
    input_fecha.click()
    print("Click realizado sobre el input de fecha.")

    # 3. Esperar a que aparezca el calendario
    try:
        WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "calendartitle"))
        )
    except:
        print("Primer intento fallido. Reintentando click...")
        input_fecha.click()
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "calendartitle"))
        )

    # 4. Retroceder año hasta alcanzar el deseado
    while True:
        titulo = driver.find_element(By.CLASS_NAME, "calendartitle").text.strip()
        print(f"Año actual del calendario: {titulo}")
        if str(anio) in titulo:
            break
        boton_atras = driver.find_element(
            By.XPATH, "//td[@class='calendarbutton' and text()='«']"
        )
        boton_atras.click()
        time.sleep(0.3)

    # 5. Seleccionar el día
    dias = driver.find_elements(By.CSS_SELECTOR, "td.day")
    for d in dias:
        if d.text.strip() == str(dia):
            d.click()
            print(f"Día {dia} seleccionado correctamente.")
            return

    print("No se pudo seleccionar el día.")


# Completar fecha de nacimiento escribiendo en el input
def completar_fecha_nacimiento_input(
    driver, field_id="vPFFNAC", edad_minima=20, timeout=10
):
    print("Completando fecha de nacimiento por input...")

    hoy = datetime.now()
    inicio = datetime(1970, 1, 1)
    fin = datetime(hoy.year - edad_minima, hoy.month, hoy.day)
    fecha_random = inicio + timedelta(days=random.randint(0, (fin - inicio).days))
    fecha_formateada = fecha_random.strftime("%d/%m/%Y")
    print(f"Fecha generada: {fecha_formateada}")

    campo_fecha = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.ID, field_id))
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", campo_fecha)
    campo_fecha.clear()
    campo_fecha.send_keys(fecha_formateada)

    driver.execute_script(
        f"""
        const input = document.getElementById('{field_id}');
        input.dispatchEvent(new Event('change', {{ bubbles: true }}));
        input.dispatchEvent(new Event('blur', {{ bubbles: true }}));
    """
    )

    print("Fecha de nacimiento ingresada correctamente.")


# Forzar clic en el icono del calendario
def forzar_click_en_trigger_fecha(driver, trigger_id="vPFFNAC_dp_trigger", timeout=10):
    try:
        print("Intentando forzar clic en el ícono del calendario...")

        # Esperar que el trigger esté presente en el DOM
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.ID, trigger_id))
        )

        # Ejecutar JS: remover 'gx-disabled' y hacer clic
        driver.execute_script(
            f"""
            const trigger = document.getElementById('{trigger_id}');
            if (trigger) {{
                trigger.classList.remove('gx-disabled');  // Remueve clase que lo deshabilita
                trigger.click();  // Forzar clic
            }}
        """
        )
        print("Click forzado en el ícono de calendario.")

        # Verificar si aparece el calendario
        WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "calendar"))
        )
        print("Calendario detectado correctamente.")

    except Exception as e:
        print(f"No se pudo hacer clic en el trigger del calendario: {e}")


def habilitar_campo_fecha_con_click(driver):
    print("Esperando calendario...")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "calendar"))
    )

    print("Haciendo clic en el trigger de calendario...")
    trigger = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "vPFFNAC_dp_trigger"))
    )
    trigger.click()

    print("Esperando que se libere cualquier overlay...")
    try:
        WebDriverWait(driver, 5).until_not(
            EC.presence_of_element_located(
                (By.XPATH, "//div[contains(@style, 'cursor: wait')]")
            )
        )
    except:
        print("Overlay no detectado, continúo igual...")

    print("Buscando celda del día 8...")
    try:
        dia_8 = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//td[contains(@class, 'day') and normalize-space(text())='8']",
                )
            )
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", dia_8)

        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//td[contains(@class, 'day') and normalize-space(text())='8']",
                )
            )
        )
        dia_8.click()
        print("Día 8 clickeado correctamente.")
    except Exception as e:
        print(f"Click directo falló. Usando JavaScript... Error: {e}")
        try:
            driver.execute_script("arguments[0].click();", dia_8)
            print("Click por JavaScript exitoso.")
        except Exception as e2:
            print(f"También falló con JavaScript: {e2}")


def ingresar_fecha_nacimiento_manual(driver, fecha="07/03/1975"):
    print(f"🗓️ Ingresando fecha manualmente: {fecha}...")

    try:
        campo_fecha = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, "vPFFNAC"))
        )
        campo_fecha.clear()
        campo_fecha.send_keys(fecha)

        # Ejecutar blur y onchange por GX
        driver.execute_script(
            """
            const input = document.getElementById('vPFFNAC');
            input.dispatchEvent(new Event('change', { bubbles: true }));
            input.dispatchEvent(new Event('blur', { bubbles: true }));
        """
        )
        print("Fecha ingresada correctamente.")
    except Exception as e:
        print(f"Error al ingresar la fecha: {e}")
