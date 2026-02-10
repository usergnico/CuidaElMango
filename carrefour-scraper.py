import sqlite3
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import os
import re
from datetime import datetime

# ============================================
# CONFIGURACIÓN
# ============================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, 'carrefour.db')

# TODAS las secciones disponibles
SECCIONES = {
    # Alimentos
    'almacen': 'https://www.carrefour.com.ar/almacen',
    'desayuno': 'https://www.carrefour.com.ar/desayuno-y-merienda',
    'bebidas': 'https://www.carrefour.com.ar/bebidas',
    'lacteos': 'https://www.carrefour.com.ar/lacteos-y-productos-frescos',
    'carnes': 'https://www.carrefour.com.ar/carnes-y-pescados',
    'frutas': 'https://www.carrefour.com.ar/frutas-y-verduras',
    'congelados': 'https://www.carrefour.com.ar/congelados',
    'panaderia': 'https://www.carrefour.com.ar/panaderia',
    
    # No alimentación
    'limpieza': 'https://www.carrefour.com.ar/limpieza',
    'perfumeria': 'https://www.carrefour.com.ar/perfumeria-y-farmacia',
    'hogar': 'https://www.carrefour.com.ar/hogar',
    'bazar': 'https://www.carrefour.com.ar/bazar-y-textil',
    'electronica': 'https://www.carrefour.com.ar/electro-y-tecnologia',
    'mascotas': 'https://www.carrefour.com.ar/mascotas',
    'bebe': 'https://www.carrefour.com.ar/mundo-bebe',
}

PROMOTION_KEYWORDS = ['OFF', '%', '2DO', 'PROMO', 'DESCUENTO', 'OFERTA']

# ============================================
# BASE DE DATOS
# ============================================
def inicializar_db():
    """Inicializa la base de datos con schema mejorado"""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    
    # Tabla principal de productos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            categoria TEXT NOT NULL,
            precio_actual REAL NOT NULL,
            promo_actual TEXT,
            url TEXT,
            ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(nombre, categoria)
        )
    ''')
    
    # Tabla de histórico de precios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS precios_historicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER NOT NULL,
            precio REAL NOT NULL,
            promo TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        )
    ''')
    
    # Índices para búsquedas rápidas
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_nombre ON productos(nombre)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_categoria ON productos(categoria)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_precio ON productos(precio_actual)')
    
    conexion.commit()
    conexion.close()
    print(f"🏠 Base de datos lista en: {DB_PATH}")


def guardar_producto(nombre, precio, promo, categoria, url=None):
    """
    Guarda o actualiza un producto en la BD.
    Si el producto existe, actualiza precio y guarda histórico.
    """
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    
    try:
        # Limpiar precio
        if isinstance(precio, str):
            precio = precio.replace('$', '').replace('.', '').replace(',', '.').replace('\xa0', '').strip()
        
        # Validar que el precio no esté vacío
        if not precio or precio == '':
            return  # Saltar este producto
        
        try:
            precio = float(precio)
        except (ValueError, TypeError):
            return  # Saltar si no se puede convertir
        
        # Validar que el precio sea positivo
        if precio <= 0:
            return
        
        # Verificar si el producto existe
        cursor.execute(
            "SELECT id, precio_actual FROM productos WHERE nombre = ? AND categoria = ?",
            (nombre, categoria)
        )
        resultado = cursor.fetchone()
        
        if resultado:
            # Producto existe - actualizar
            producto_id, precio_anterior = resultado
            
            # Solo actualizar si el precio cambió
            if abs(precio - precio_anterior) > 0.01:
                cursor.execute('''
                    UPDATE productos 
                    SET precio_actual = ?, promo_actual = ?, ultima_actualizacion = ?
                    WHERE id = ?
                ''', (precio, promo, datetime.now(), producto_id))
                
                # Guardar en histórico
                cursor.execute('''
                    INSERT INTO precios_historicos (producto_id, precio, promo)
                    VALUES (?, ?, ?)
                ''', (producto_id, precio, promo))
        else:
            # Producto nuevo - insertar
            cursor.execute('''
                INSERT INTO productos (nombre, categoria, precio_actual, promo_actual, url)
                VALUES (?, ?, ?, ?, ?)
            ''', (nombre, categoria, precio, promo, url))
            
            producto_id = cursor.lastrowid
            
            # Guardar primer precio en histórico
            cursor.execute('''
                INSERT INTO precios_historicos (producto_id, precio, promo)
                VALUES (?, ?, ?)
            ''', (producto_id, precio, promo))
        
        conexion.commit()
        
    except Exception as e:
        print(f"❌ Error guardando {nombre}: {e}")
    finally:
        conexion.close()


# ============================================
# EXTRACCIÓN DE DATOS
# ============================================
def limpiar_texto(texto):
    """Normaliza texto removiendo espacios extra"""
    if not texto:
        return ""
    return re.sub(r'\s+', ' ', texto).strip()


def extraer_promocion(item):
    """Extrae la promoción del producto"""
    for tag in item.find_all(['span', 'div']):
        texto = limpiar_texto(tag.text)
        
        if len(texto) > 50:
            continue
        
        if any(keyword in texto.upper() for keyword in PROMOTION_KEYWORDS):
            return texto
    
    return "Precio Regular"


def extraer_datos_producto(item, categoria):
    """
    Extrae nombre, precio y promoción de un elemento de producto.
    Retorna (nombre, precio, promo) o None si hay error.
    """
    try:
        # Nombre del producto
        nombre_elem = item.find('span', class_='vtex-product-summary-2-x-productBrand')
        if not nombre_elem:
            return None
        nombre = limpiar_texto(nombre_elem.text)
        
        # Precio
        precio_elem = item.find('span', class_='valtech-carrefourar-product-price-0-x-currencyContainer')
        if not precio_elem:
            return None
        precio = limpiar_texto(precio_elem.text)
        
        # Validar que el precio no esté vacío
        if not precio or precio == '':
            return None
        
        # Promoción
        promo = extraer_promocion(item)
        
        return (nombre, precio, promo)
        
    except Exception as e:
        return None


def procesar_pagina(page, categoria, num_pagina, url_base):
    """
    Procesa una página de productos.
    Retorna el número de productos encontrados.
    """
    url = f'{url_base}?page={num_pagina}'
    print(f"🔎 [{categoria}] Página {num_pagina}...")
    
    try:
        page.goto(url, wait_until='networkidle', timeout=60000)
        
        # Scroll para cargar lazy content
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)
        
        html = page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        # Verificar si hay productos
        items = soup.find_all('article')
        if not items:
            return 0
        
        productos_encontrados = 0
        for item in items:
            datos = extraer_datos_producto(item, categoria)
            if datos:
                nombre, precio, promo = datos
                guardar_producto(nombre, precio, promo, categoria, url)
                productos_encontrados += 1
        
        if productos_encontrados > 0:
            print(f"  ✅ {productos_encontrados} productos")
        
        return productos_encontrados
        
    except Exception as e:
        print(f"🔥 Error en página {num_pagina}: {e}")
        return -1


def scrapear_seccion(browser, categoria, url_base, max_paginas=None):
    """Scrapea una sección completa"""
    print(f"\n{'='*60}")
    print(f"🛒 Scrapeando sección: {categoria.upper()}")
    print(f"{'='*60}\n")
    
    page = browser.new_page()
    num_pagina = 1
    total_productos = 0
    
    while True:
        if max_paginas and num_pagina > max_paginas:
            print(f"\n⏸️  Límite de páginas alcanzado ({max_paginas})")
            break
        
        productos = procesar_pagina(page, categoria, num_pagina, url_base)
        
        if productos == 0:
            print(f"\n🏁 Fin de la sección {categoria}")
            break
        elif productos == -1:
            print(f"\n🔥 Error. Abortando sección {categoria}")
            break
        
        total_productos += productos
        num_pagina += 1
    
    page.close()
    print(f"✅ Total en {categoria}: {total_productos} productos\n")
    return total_productos


def elegir_secciones():
    """
    Permite al usuario elegir qué secciones scrapear.
    Retorna lista de secciones seleccionadas.
    """
    print("\n" + "="*60)
    print("🎯 SELECCIÓN DE SECCIONES")
    print("="*60)
    print("\n¿Qué secciones querés scrapear?\n")
    
    # Agrupar por categoría
    alimentos = ['almacen', 'desayuno', 'bebidas', 'lacteos', 'carnes', 'frutas', 'congelados', 'panaderia']
    no_alimentos = ['limpieza', 'perfumeria', 'hogar', 'bazar', 'electronica', 'mascotas', 'bebe']
    
    print("🍕 ALIMENTOS:")
    for i, seccion in enumerate(alimentos, 1):
        print(f"  {i}) {seccion}")
    
    print("\n🧹 NO ALIMENTACIÓN:")
    for i, seccion in enumerate(no_alimentos, len(alimentos) + 1):
        print(f"  {i}) {seccion}")
    
    print(f"\n  {len(SECCIONES) + 1}) TODAS las secciones")
    print(f"  {len(SECCIONES) + 2}) Solo ALIMENTOS")
    print(f"  {len(SECCIONES) + 3}) Solo NO ALIMENTACIÓN")
    
    print("\n" + "="*60)
    print("Ingresá los números separados por comas (ej: 1,3,5)")
    print("O presioná Enter para scrapear TODAS")
    print("="*60)
    
    seleccion = input("\nTu selección: ").strip()
    
    if not seleccion:
        return list(SECCIONES.keys())
    
    try:
        numeros = [int(n.strip()) for n in seleccion.split(',')]
        
        # Opciones especiales
        if len(SECCIONES) + 1 in numeros:
            return list(SECCIONES.keys())
        if len(SECCIONES) + 2 in numeros:
            return alimentos
        if len(SECCIONES) + 3 in numeros:
            return no_alimentos
        
        # Selección manual
        todas_secciones = alimentos + no_alimentos
        secciones_elegidas = []
        for num in numeros:
            if 1 <= num <= len(todas_secciones):
                secciones_elegidas.append(todas_secciones[num - 1])
        
        return secciones_elegidas if secciones_elegidas else list(SECCIONES.keys())
        
    except ValueError:
        print("\n⚠️  Entrada inválida. Scrapeando TODAS las secciones.")
        return list(SECCIONES.keys())


# ============================================
# FLUJO PRINCIPAL
# ============================================
def run(secciones=None, max_paginas_por_seccion=None, modo_interactivo=True):
    """
    Ejecuta el scraper de Carrefour.
    
    Args:
        secciones: Lista de secciones a scrapear. Si es None, pregunta al usuario.
        max_paginas_por_seccion: Límite de páginas por sección (útil para testing).
        modo_interactivo: Si True, permite elegir secciones interactivamente.
    """
    inicializar_db()
    
    # Determinar qué secciones scrapear
    if secciones is None and modo_interactivo:
        secciones = elegir_secciones()
    elif secciones is None:
        secciones = list(SECCIONES.keys())
    else:
        # Validar que las secciones existan
        secciones = [s for s in secciones if s in SECCIONES]
        if not secciones:
            print("❌ No se especificaron secciones válidas")
            return
    
    print(f"\n🎯 Secciones a scrapear: {', '.join(secciones)}")
    print(f"🚀 Iniciando scraper de Carrefour...")
    print(f"💾 Base de datos: {DB_PATH}\n")
    
    input("⏸️  Presioná Enter para comenzar (o Ctrl+C para cancelar)...")
    
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        
        total_general = 0
        for i, seccion in enumerate(secciones, 1):
            url = SECCIONES.get(seccion)
            if not url:
                print(f"⚠️  Sección '{seccion}' no encontrada. Saltando...")
                continue
            
            print(f"\n[{i}/{len(secciones)}] Procesando: {seccion}")
            total = scrapear_seccion(browser, seccion, url, max_paginas_por_seccion)
            total_general += total
        
        browser.close()
    
    print(f"\n{'='*60}")
    print(f"🎉 SCRAPING COMPLETO")
    print(f"{'='*60}")
    print(f"✅ Total de productos: {total_general}")
    print(f"📊 Secciones procesadas: {len(secciones)}")
    print(f"💾 Base de datos: {DB_PATH}")


if __name__ == "__main__":
    # Modo interactivo: permite elegir secciones
    run(modo_interactivo=True)
    
    # Para testing: scrapear solo almacén (2 páginas)
    # run(secciones=['almacen'], max_paginas_por_seccion=2, modo_interactivo=False)
    
    # Para automatizar: scrapear secciones específicas
    # run(secciones=['bebidas', 'lacteos'], modo_interactivo=False)
