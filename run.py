#!/usr/bin/env python3
"""
Script maestro para ejecutar el comparador de precios.
Menú interactivo simple para no-programadores.
"""

import os
import sys

def limpiar_pantalla():
    """Limpia la pantalla de la terminal"""
    os.system('cls' if os.name == 'nt' else 'clear')


def mostrar_menu():
    """Muestra el menú principal"""
    limpiar_pantalla()
    print("=" * 60)
    print("🛒 COMPARADOR DE PRECIOS - ARGENTINA")
    print("=" * 60)
    print()
    print("¿Qué querés hacer?")
    print()
    print("  1) 📥 Scrapear Carrefour (actualizar precios)")
    print("  2) 📥 Scrapear Disco (actualizar precios)")
    print("  3) 📥 Scrapear TODOS (Carrefour + Disco)")
    print()
    print("  4) 💰 Comparar mi carrito")
    print()
    print("  5) 🔧 Ver información del sistema")
    print("  6) ❌ Salir")
    print()
    print("=" * 60)


def scrapear_carrefour():
    """Ejecuta el scraper de Carrefour"""
    print("\n🛒 Scrapeando Carrefour...")
    print("⚠️  Esto puede tardar varios minutos\n")
    
    # Verificar que existe el archivo
    if not os.path.exists('carrefour-scraper.py'):
        print("❌ Error: No se encuentra carrefour-scraper.py")
        input("\nPresioná Enter para volver...")
        return
    
    # Ejecutar el scraper
    os.system('python carrefour-scraper.py')
    
    input("\n✅ Presioná Enter para volver al menú...")


def scrapear_disco():
    """Ejecuta el scraper de Disco"""
    print("\n🛍️ Scrapeando Disco...")
    print("⚠️  Esto puede tardar varios minutos\n")
    
    # Verificar que existe el archivo
    if not os.path.exists('disco-scraper.py'):
        print("❌ Error: No se encuentra disco-scraper.py")
        input("\nPresioná Enter para volver...")
        return
    
    # Ejecutar el scraper
    os.system('python disco-scraper.py')
    
    input("\n✅ Presioná Enter para volver al menú...")


def scrapear_todos():
    """Ejecuta todos los scrapers"""
    print("\n🛒 Scrapeando TODOS los supermercados...")
    print("⚠️  Esto puede tardar 10-30 minutos\n")
    
    confirmar = input("¿Estás seguro? (s/n): ").lower()
    if confirmar != 's':
        print("Cancelado.")
        input("\nPresioná Enter para volver...")
        return
    
    print("\n" + "=" * 60)
    print("1/2: Scrapeando Carrefour...")
    print("=" * 60 + "\n")
    os.system('python carrefour-scraper.py')
    
    print("\n" + "=" * 60)
    print("2/2: Scrapeando Disco...")
    print("=" * 60 + "\n")
    os.system('python disco-scraper.py')
    
    print("\n✅ ¡Todos los scrapers finalizados!")
    input("\nPresioná Enter para volver al menú...")


def comparar_carrito():
    """Ejecuta el comparador de carritos"""
    limpiar_pantalla()
    print("=" * 60)
    print("💰 COMPARADOR DE CARRITOS")
    print("=" * 60)
    print()
    
    # Verificar que existen las bases de datos
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    
    if not os.path.exists(os.path.join(data_dir, 'carrefour.db')):
        print("⚠️  No se encontró la base de datos de Carrefour.")
        print("   Ejecutá primero la opción 1 para scrapear Carrefour.\n")
    
    if not os.path.exists(os.path.join(data_dir, 'disco.db')):
        print("⚠️  No se encontró la base de datos de Disco.")
        print("   Ejecutá primero la opción 2 para scrapear Disco.\n")
    
    if not os.path.exists(os.path.join(data_dir, 'carrefour.db')) and not os.path.exists(os.path.join(data_dir, 'disco.db')):
        print("❌ No hay datos para comparar.")
        input("\nPresioná Enter para volver...")
        return
    
    # Verificar que existe el comparador
    if not os.path.exists('compare_cart.py'):
        print("❌ Error: No se encuentra compare_cart.py")
        input("\nPresioná Enter para volver...")
        return
    
    print("Iniciando comparador...\n")
    os.system('python compare_cart.py')
    
    input("\n✅ Presioná Enter para volver al menú...")


def ver_info():
    """Muestra información del sistema"""
    limpiar_pantalla()
    print("=" * 60)
    print("🔧 INFORMACIÓN DEL SISTEMA")
    print("=" * 60)
    print()
    
    # Python version
    print(f"🐍 Python: {sys.version.split()[0]}")
    
    # Verificar archivos
    print("\n📁 Archivos del proyecto:")
    archivos_necesarios = [
        'carrefour-scraper.py',
        'disco-scraper.py',
        'compare_cart.py',
        'config.py',
        'requirements.txt',
        'run.py'
    ]
    
    for archivo in archivos_necesarios:
        if os.path.exists(archivo):
            print(f"  ✅ {archivo}")
        else:
            print(f"  ❌ {archivo} (falta)")
    
    # Verificar carpetas
    print("\n📂 Carpetas:")
    carpetas = ['data', 'docs']
    for carpeta in carpetas:
        if os.path.exists(carpeta):
            print(f"  ✅ {carpeta}/")
        else:
            print(f"  ❌ {carpeta}/ (falta)")
    
    # Verificar bases de datos
    print("\n💾 Bases de datos:")
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    dbs = ['carrefour.db', 'disco.db']
    
    for db in dbs:
        db_path = os.path.join(data_dir, db)
        if os.path.exists(db_path):
            size = os.path.getsize(db_path) / 1024  # KB
            print(f"  ✅ {db} ({size:.1f} KB)")
        else:
            print(f"  ❌ {db} (no existe)")
    
    # Verificar módulos instalados
    print("\n📦 Dependencias:")
    try:
        import playwright
        print("  ✅ playwright")
    except ImportError:
        print("  ❌ playwright (falta instalar)")
    
    try:
        import bs4
        print("  ✅ beautifulsoup4")
    except ImportError:
        print("  ❌ beautifulsoup4 (falta instalar)")
    
    print("\n" + "=" * 60)
    input("\nPresioná Enter para volver...")


def main():
    """Función principal"""
    while True:
        mostrar_menu()
        
        opcion = input("Ingresá el número de opción: ").strip()
        
        if opcion == '1':
            scrapear_carrefour()
        elif opcion == '2':
            scrapear_disco()
        elif opcion == '3':
            scrapear_todos()
        elif opcion == '4':
            comparar_carrito()
        elif opcion == '5':
            ver_info()
        elif opcion == '6':
            print("\n👋 ¡Chau!\n")
            sys.exit(0)
        else:
            print("\n❌ Opción inválida. Probá de nuevo.")
            input("\nPresioná Enter para continuar...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 ¡Chau!\n")
        sys.exit(0)
