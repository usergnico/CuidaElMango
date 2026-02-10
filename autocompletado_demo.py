#!/usr/bin/env python3
"""
Sistema de autocompletado para el comparador.
Sugiere productos mientras el usuario escribe.
"""

import sqlite3
import os
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter, FuzzyCompleter
from prompt_toolkit.shortcuts import CompleteStyle
import unicodedata

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
CARREFOUR_DB = os.path.join(DATA_DIR, 'carrefour.db')
DISCO_DB = os.path.join(DATA_DIR, 'disco.db')


def obtener_todos_productos():
    """Obtiene lista de todos los productos únicos de ambas tiendas"""
    productos = set()
    
    # Carrefour
    if os.path.exists(CARREFOUR_DB):
        try:
            conn = sqlite3.connect(CARREFOUR_DB)
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT DISTINCT nombre FROM productos LIMIT 10000")
            except:
                cursor.execute("SELECT DISTINCT nombre FROM productos LIMIT 10000")
            
            for row in cursor.fetchall():
                productos.add(row[0])
            conn.close()
        except:
            pass
    
    # Disco
    if os.path.exists(DISCO_DB):
        try:
            conn = sqlite3.connect(DISCO_DB)
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT DISTINCT nombre FROM productos LIMIT 10000")
            except:
                cursor.execute("SELECT DISTINCT nombre FROM productos LIMIT 10000")
            
            for row in cursor.fetchall():
                productos.add(row[0])
            conn.close()
        except:
            pass
    
    return sorted(list(productos))


def crear_autocompletador():
    """Crea el sistema de autocompletado"""
    print("🔄 Cargando productos para autocompletado...")
    productos = obtener_todos_productos()
    print(f"✅ {len(productos)} productos cargados\n")
    
    # Crear completer fuzzy (busca coincidencias aproximadas)
    completer = FuzzyCompleter(
        WordCompleter(
            productos,
            ignore_case=True,
            sentence=True,
            match_middle=True
        )
    )
    
    return completer


def prompt_con_autocompletado(mensaje, completer):
    """Prompt con autocompletado activado"""
    return prompt(
        mensaje,
        completer=completer,
        complete_style=CompleteStyle.MULTI_COLUMN,
        complete_while_typing=True
    )


if __name__ == "__main__":
    # Demo
    completer = crear_autocompletador()
    
    print("="*60)
    print("🔍 DEMO DE AUTOCOMPLETADO")
    print("="*60)
    print("\nEscribí el nombre de un producto y presioná TAB")
    print("o simplemente empezá a escribir para ver sugerencias\n")
    print("Ejemplo: Escribí 'arr' y presioná TAB\n")
    
    while True:
        try:
            producto = prompt_con_autocompletado(
                "Producto (Ctrl+C para salir): ",
                completer
            )
            
            if producto:
                print(f"✅ Seleccionaste: {producto}\n")
        
        except KeyboardInterrupt:
            print("\n\n👋 ¡Chau!\n")
            break
