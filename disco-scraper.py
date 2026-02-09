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
os.makedirs(DATA_DIR, exist_ok=True)  # Crear carpeta data si no existe
DB_PATH = os.path.join(DATA_DIR, 'disco.db')

# TODAS las secciones disponibles
SECCIONES = {
    # Alimentos
    'almacen': 'https://www.disco.com.ar/almacen',
    'bebidas': 'https://www.disco.com.ar/bebidas',
    'lacteos': 'https://www.disco.com.ar/lacteos',
    'carnes': 'https://www.disco.com.ar/carnes',
    'quesos y fiambres': 'https://www.disco.com.ar/quesos-y-fiambres',
    'frutas': 'https://www.disco.com.ar/frutas-y-verduras',
    'congelados': 'https://www.disco.com.ar/congelados',
    'panaderia': 'https://www.disco.com.ar/panaderia-y-pasteleria',
    'pastas frescas': 'https://www.disco.com.ar/pastas-frescas',
    
    # No alimentación
    'limpieza': 'https://www.disco.com.ar/limpieza',
    'perfumeria': 'https://www.disco.com.ar/perfumeria',
    'bazar': 'https://www.disco.com.ar/hogar-y-textil',
    'mascotas': 'https://www.disco.com.ar/mascotas',
    'bebe': 'https://www.disco.com.ar/mundo-bebe',
    'electronica': 'https://www.disco.com.ar/electro',
    'tiempo libre': 'https://www.disco.com.ar/tiempo-libre',
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
        precio = float(precio)
        
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
        precio_elem = item.find('div', class_='discoargentina-store-theme-1dCOMij_MzTzZOCohX1K7w')
        if not precio_elem:
            return None
        precio = limpiar_texto(precio_elem.text)
        
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
        page.goto(url, wait_until='domcontentloaded', timeout=60000)
        page.wait_for_selector('article', timeout=20000)
        
        # Scroll progresivo (clave para cargar contenido en Disco)
        for i in range(5):
            page.evaluate(f"window.scrollBy(0, {i * 500})")
            page.wait_for_timeout(500)
        
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


# ============================================
# FLUJO PRINCIPAL
# ============================================
def run(secciones=None, max_paginas_por_seccion=None):
    """
    Ejecuta el scraper de Disco.
    
    Args:
        secciones: Lista de secciones a scrapear. Si es None, scrapea todas.
        max_paginas_por_seccion: Límite de páginas por sección (útil para testing).
    """
    inicializar_db()
    
    # Determinar qué secciones scrapear
    if secciones is None:
        secciones = list(SECCIONES.keys())
    else:
        # Validar que las secciones existan
        secciones = [s for s in secciones if s in SECCIONES]
        if not secciones:
            print("❌ No se especificaron secciones válidas")
            return
    
    print(f"\n🎯 Secciones a scrapear: {', '.join(secciones)}")
    print(f"🚀 Iniciando scraper de Disco...")
    print(f"💾 Base de datos: {DB_PATH}\n")
    
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        page.close()  # Cerramos la página inicial
        
        total_general = 0
        for seccion in secciones:
            url = SECCIONES[seccion]
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
    # Para testing: scrapear solo almacén (2 páginas)
    # run(secciones=['almacen'], max_paginas_por_seccion=2)
    
    # Para producción: scrapear TODAS las secciones
    run()
