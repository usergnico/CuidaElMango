"""
Configuración centralizada para todos los scrapers.
Modificá acá para agregar nuevas secciones o supermercados.
"""

import os

# ============================================
# CONFIGURACIÓN GENERAL
# ============================================

# Directorio base del proyecto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Directorio de datos
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# Bases de datos
DB_CONFIG = {
    'carrefour': os.path.join(DATA_DIR, 'carrefour.db'),
    'disco': os.path.join(DATA_DIR, 'disco.db'),
    'dia': os.path.join(DATA_DIR, 'dia.db'),
    'coto': os.path.join(DATA_DIR, 'coto.db'),
}

# ============================================
# CONFIGURACIÓN DE SCRAPING
# ============================================

# Timeouts (en milisegundos)
TIMEOUT_NAVIGATION = 60000  # 60 segundos
TIMEOUT_SELECTOR = 20000    # 20 segundos

# Delays (en milisegundos)
DELAY_SCROLL = 2000         # 2 segundos después de scroll
DELAY_BETWEEN_PAGES = 1000  # 1 segundo entre páginas

# Navegador
BROWSER_CONFIG = {
    'headless': False,  # Cambiar a True para producción
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# ============================================
# URLS Y SECCIONES POR SUPERMERCADO
# ============================================

CARREFOUR_SECCIONES = {
    # Alimentos
    'almacen': 'https://www.carrefour.com.ar/almacen',
    'bebidas': 'https://www.carrefour.com.ar/bebidas',
    'lacteos': 'https://www.carrefour.com.ar/lacteos-productos-frescos-y-huevos',
    'carnes': 'https://www.carrefour.com.ar/carnes-y-pescados',
    'frutas': 'https://www.carrefour.com.ar/frutas-y-verduras',
    'congelados': 'https://www.carrefour.com.ar/congelados',
    'panaderia': 'https://www.carrefour.com.ar/panaderia-y-reposteria',
    
    # No alimentación
    'limpieza': 'https://www.carrefour.com.ar/limpieza',
    'perfumeria': 'https://www.carrefour.com.ar/perfumeria-y-cuidado-personal',
    'bazar': 'https://www.carrefour.com.ar/bazar-y-textil',
    'electronica': 'https://www.carrefour.com.ar/electronica-y-tecnologia',
    'mascotas': 'https://www.carrefour.com.ar/mascotas',
    'bebe': 'https://www.carrefour.com.ar/mundo-bebe',
}

DISCO_SECCIONES = {
    # Alimentos
    'almacen': 'https://www.disco.com.ar/almacen',
    'bebidas': 'https://www.disco.com.ar/bebidas',
    'lacteos': 'https://www.disco.com.ar/lacteos-productos-frescos-y-huevos',
    'carnes': 'https://www.disco.com.ar/carnes-y-pescados',
    'frutas': 'https://www.disco.com.ar/frutas-y-verduras',
    'congelados': 'https://www.disco.com.ar/congelados',
    'panaderia': 'https://www.disco.com.ar/panaderia-y-reposteria',
    
    # No alimentación
    'limpieza': 'https://www.disco.com.ar/limpieza',
    'perfumeria': 'https://www.disco.com.ar/perfumeria-y-cuidado-personal',
    'bazar': 'https://www.disco.com.ar/bazar-y-textil',
    'mascotas': 'https://www.disco.com.ar/mascotas',
    'bebe': 'https://www.disco.com.ar/mundo-bebe',
}

# Día (URLs aproximadas - verificar)
DIA_SECCIONES = {
    'almacen': 'https://diaonline.supermercadosdia.com.ar/almacen',
    'bebidas': 'https://diaonline.supermercadosdia.com.ar/bebidas',
    'lacteos': 'https://diaonline.supermercadosdia.com.ar/lacteos',
    # ... agregar más
}

# Coto (URLs aproximadas - verificar)
COTO_SECCIONES = {
    'almacen': 'https://www.cotodigital3.com.ar/sitios/cdigi/browse/catalogo-almac%C3%A9n',
    'bebidas': 'https://www.cotodigital3.com.ar/sitios/cdigi/browse/catalogo-bebidas',
    # ... agregar más
}

# ============================================
# SELECTORES CSS POR SUPERMERCADO
# ============================================

# Estos selectores pueden cambiar si los sitios actualizan su HTML
# Usá verificar_selectores.py para encontrar los correctos

CARREFOUR_SELECTORES = {
    'producto_container': 'article',
    'nombre': 'span.vtex-product-summary-2-x-productBrand',
    'precio': 'span.valtech-carrefourar-product-price-0-x-currencyContainer',
    'promo': None,  # Se busca dinámicamente
}

DISCO_SELECTORES = {
    'producto_container': 'article',
    'nombre': 'span.vtex-product-summary-2-x-productBrand',
    'precio': 'div.discoargentina-store-theme-1dCOMij_MzTzZOCohX1K7w',
    'promo': None,  # Se busca dinámicamente
}

# ============================================
# DETECCIÓN DE PROMOCIONES
# ============================================

# Palabras clave que indican promoción
PROMOTION_KEYWORDS = [
    'OFF',
    '%',
    '2DO',
    'SEGUNDO',
    'DESCUENTO',
    'PROMO',
    'OFERTA',
    '2X1',
    '3X2',
    'LLEVANDO',
]

# Longitud máxima de texto de promoción (para filtrar descripciones largas)
MAX_PROMO_LENGTH = 50

# ============================================
# CONFIGURACIÓN DE LOGGING
# ============================================

LOGGING_CONFIG = {
    'level': 'INFO',  # DEBUG, INFO, WARNING, ERROR
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': os.path.join(DATA_DIR, 'scraper.log'),
}

# ============================================
# CONFIGURACIÓN DE BASE DE DATOS
# ============================================

# Schema SQL para las tablas
DB_SCHEMA = {
    'productos': '''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            categoria TEXT NOT NULL,
            precio_actual REAL NOT NULL,
            promo_actual TEXT,
            url TEXT,
            tienda TEXT NOT NULL,
            ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(nombre, categoria, tienda)
        )
    ''',
    'precios_historicos': '''
        CREATE TABLE IF NOT EXISTS precios_historicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER NOT NULL,
            precio REAL NOT NULL,
            promo TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        )
    ''',
}

DB_INDICES = [
    'CREATE INDEX IF NOT EXISTS idx_nombre ON productos(nombre)',
    'CREATE INDEX IF NOT EXISTS idx_categoria ON productos(categoria)',
    'CREATE INDEX IF NOT EXISTS idx_precio ON productos(precio_actual)',
    'CREATE INDEX IF NOT EXISTS idx_tienda ON productos(tienda)',
    'CREATE INDEX IF NOT EXISTS idx_fecha ON precios_historicos(fecha)',
]

# ============================================
# FUNCIONES HELPER
# ============================================

def get_db_path(tienda: str) -> str:
    """Retorna el path de la DB para una tienda"""
    return DB_CONFIG.get(tienda.lower())


def get_secciones(tienda: str) -> dict:
    """Retorna el diccionario de secciones para una tienda"""
    tienda_lower = tienda.lower()
    
    if tienda_lower == 'carrefour':
        return CARREFOUR_SECCIONES
    elif tienda_lower == 'disco':
        return DISCO_SECCIONES
    elif tienda_lower == 'dia':
        return DIA_SECCIONES
    elif tienda_lower == 'coto':
        return COTO_SECCIONES
    else:
        return {}


def get_selectores(tienda: str) -> dict:
    """Retorna los selectores CSS para una tienda"""
    tienda_lower = tienda.lower()
    
    if tienda_lower == 'carrefour':
        return CARREFOUR_SELECTORES
    elif tienda_lower == 'disco':
        return DISCO_SELECTORES
    else:
        return {}


# ============================================
# VALIDACIÓN
# ============================================

def validar_config():
    """Valida que la configuración sea correcta"""
    errores = []
    
    # Verificar que existan los directorios
    if not os.path.exists(DATA_DIR):
        errores.append(f"Directorio de datos no existe: {DATA_DIR}")
    
    # Verificar que las URLs sean válidas
    for tienda, secciones in [
        ('Carrefour', CARREFOUR_SECCIONES),
        ('Disco', DISCO_SECCIONES)
    ]:
        for nombre, url in secciones.items():
            if not url.startswith('http'):
                errores.append(f"URL inválida para {tienda}/{nombre}: {url}")
    
    if errores:
        print("❌ Errores de configuración:")
        for error in errores:
            print(f"  - {error}")
        return False
    
    print("✅ Configuración válida")
    return True


if __name__ == "__main__":
    # Test de la configuración
    print("🔧 Testeando configuración...\n")
    
    print(f"📁 Directorio de datos: {DATA_DIR}")
    print(f"📁 Base de datos:")
    for tienda, path in DB_CONFIG.items():
        print(f"   - {tienda}: {path}")
    
    print(f"\n🏪 Supermercados configurados:")
    print(f"   - Carrefour: {len(CARREFOUR_SECCIONES)} secciones")
    print(f"   - Disco: {len(DISCO_SECCIONES)} secciones")
    
    print("\n" + "="*50)
    validar_config()
