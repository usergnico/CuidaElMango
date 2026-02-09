"""
Script para verificar qué selectores CSS funcionan en cada sección.
Útil para agregar nuevas secciones sin romper el scraper.
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time

SECCIONES_TEST = {
    'Carrefour': {
        'almacen': 'https://www.carrefour.com.ar/almacen',
        'bebidas': 'https://www.carrefour.com.ar/bebidas',
        'lacteos': 'https://www.carrefour.com.ar/lacteos-productos-frescos-y-huevos',
    },
    'Disco': {
        'almacen': 'https://www.disco.com.ar/almacen',
        'bebidas': 'https://www.disco.com.ar/bebidas',
        'lacteos': 'https://www.disco.com.ar/lacteos-productos-frescos-y-huevos',
    }
}

# Selectores posibles para cada campo
SELECTORES_POSIBLES = {
    'nombre': [
        'span.vtex-product-summary-2-x-productBrand',
        'h2.vtex-product-summary-2-x-productBrand',
        'div.vtex-product-summary-2-x-productBrand',
        'span.product-name',
        'h3.product-title',
    ],
    'precio': [
        'span.valtech-carrefourar-product-price-0-x-currencyContainer',
        'div.discoargentina-store-theme-1dCOMij_MzTzZOCohX1K7w',
        'span.vtex-product-price-1-x-sellingPrice',
        'div.price-tag',
        'span.selling-price',
    ],
    'promo': [
        'span[class*="promo"]',
        'div[class*="discount"]',
        'span[class*="badge"]',
        'div.promotional-flag',
    ]
}


def verificar_url(page, tienda: str, seccion: str, url: str):
    """Verifica qué selectores funcionan en una URL específica"""
    
    print(f"\n{'='*70}")
    print(f"🔍 Analizando: {tienda} - {seccion}")
    print(f"📍 URL: {url}")
    print(f"{'='*70}\n")
    
    try:
        # Navegar
        print("⏳ Cargando página...")
        page.goto(url, wait_until='networkidle', timeout=30000)
        
        # Scroll para activar lazy load
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)
        
        html = page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        # Primero verificamos el container de productos
        print("📦 Buscando containers de productos...")
        containers = soup.find_all('article')
        if not containers:
            containers = soup.find_all('div', class_='product-item')
        if not containers:
            containers = soup.find_all('div', class_='vtex-product-summary')
        
        print(f"   Encontrados: {len(containers)} productos\n")
        
        if not containers:
            print("   ❌ No se encontraron productos. Puede ser que:")
            print("      - La página requiere JS más complejo")
            print("      - Los selectores cambiaron")
            print("      - Hay un captcha o bloqueo")
            return
        
        # Analizar el primer producto
        primer_producto = containers[0]
        print("🧪 Probando selectores en el primer producto:\n")
        
        resultados = {}
        
        for campo, selectores in SELECTORES_POSIBLES.items():
            print(f"  {campo.upper()}:")
            encontrado = False
            
            for selector in selectores:
                try:
                    # Probar con find
                    elemento = primer_producto.select_one(selector)
                    
                    if elemento:
                        texto = elemento.get_text(strip=True)
                        if texto:  # Solo mostrar si tiene contenido
                            print(f"    ✅ {selector}")
                            print(f"       → '{texto[:50]}...' " if len(texto) > 50 else f"       → '{texto}'")
                            
                            if not encontrado:  # Guardar el primero que funcione
                                resultados[campo] = selector
                                encontrado = True
                except Exception:
                    pass
            
            if not encontrado:
                print(f"    ❌ Ningún selector funcionó")
        
        # Mostrar resumen
        print(f"\n{'─'*70}")
        print("📋 RESUMEN - Selectores que funcionan:")
        print(f"{'─'*70}\n")
        
        if resultados:
            print("```python")
            print(f"# {tienda.upper()} - {seccion}")
            print("SELECTORES = {")
            for campo, selector in resultados.items():
                print(f"    '{campo}': '{selector}',")
            print("}")
            print("```\n")
        else:
            print("❌ No se encontraron selectores funcionales\n")
        
        # Bonus: mostrar estructura HTML del primer producto
        print("🔧 Estructura HTML del producto (para debugging):")
        print("─" * 70)
        html_producto = primer_producto.prettify()[:1000]
        print(html_producto)
        print("...\n")
        
    except Exception as e:
        print(f"❌ Error: {e}\n")


def run_verificacion():
    """Ejecuta la verificación en todas las secciones"""
    
    print("\n" + "="*70)
    print("🎯 VERIFICADOR DE SELECTORES CSS")
    print("="*70)
    print("\nEste script analiza las secciones y muestra qué selectores funcionan.")
    print("Útil para agregar nuevas secciones sin romper el scraper.\n")
    
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)  # headless=True para más rápido
        page = browser.new_page()
        
        for tienda, secciones in SECCIONES_TEST.items():
            for seccion, url in secciones.items():
                verificar_url(page, tienda, seccion, url)
                
                # Pausa entre requests para no saturar
                print("⏸️  Esperando 3 segundos antes de la siguiente...\n")
                time.sleep(3)
        
        browser.close()
    
    print("\n" + "="*70)
    print("✅ Verificación completa")
    print("="*70)
    print("\nPróximos pasos:")
    print("1. Copia los selectores que funcionaron")
    print("2. Actualiza tu scraper con esos selectores")
    print("3. Si una sección no funcionó, investiga manualmente")


if __name__ == "__main__":
    # Puedes testear una sola URL así:
    # with sync_playwright() as p:
    #     browser = p.firefox.launch(headless=False)
    #     page = browser.new_page()
    #     verificar_url(page, "Carrefour", "bebidas", "https://www.carrefour.com.ar/bebidas")
    #     browser.close()
    
    # O ejecutar el test completo:
    run_verificacion()
