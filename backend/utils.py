"""
Utilidades para extracción de atributos de productos
"""

import re

# Lista de marcas conocidas (ir agregando más)
MARCAS_CONOCIDAS = [
    # Bebidas
    'coca cola', 'coca-cola', 'pepsi', 'sprite', 'fanta', 'schweppes', 
    'seven up', '7up', 'quilmes', 'andes', 'brahma', 'stella artois', 
    'heineken', 'corona', 'budweiser',
    
    # Galletitas/Snacks
    'oreo', 'milka', 'tofi', 'terrabusi', 'bagley', 'arcor', 'georgalos',
    'shot', 'rumba', 'express', 'bagley', 'club social', 'criollitas',
    
    # Aceites/Condimentos
    'natura', 'cocinero', 'lira', 'morixe', 'patito', 'mazola',
    'hellmanns', "hell'mann's", 'hellmans', 'danica', 'cañuelas',
    
    # Lácteos
    'sancor', 'la serenisima', 'serenisima', 'ilolay', 'tregar', 
    'la paulina', 'paulina', 'milkaut', 'casanto',
    
    # Almacén
    'gallo', 'molinos', 'marolio', 'muy bien', 'día', 'argenova',
    'lucchetti', 'matarazzo', 'don vicente', 'favorita',
    
    # Carnes/Fiambres
    'campagnola', 'la campagnola', 'swift', 'paladini', 'carrefour',
    'granja del sol',
    
    # Atún/Conservas
    'gomes', 'la campagnola', 'cuisine', 'lomitos', 'abc',
    
    # Limpieza
    'cif', 'magistral', 'ala', 'skip', 'vivere', 'procenex',
    'ayudin', 'lysoform', 'mr musculo', 'blem',
    
    # Higiene personal
    'dove', 'sedal', 'pantene', 'head shoulders', 'loreal', "l'oreal",
    'nivea', 'rexona', 'axe', 'plusbelle', 'suave'
]

# Palabras a ignorar al limpiar nombre
PALABRAS_IGNORAR = [
    'de', 'la', 'el', 'en', 'con', 'sin', 'al', 'del', 'los', 'las',
    'pack', 'unidades', 'unidad', 'bolsa', 'caja', 'paquete', 'lata',
    'botella', 'envase', 'x'
]

# Variantes comunes
VARIANTES = [
    'clasica', 'original', 'mini', 'family', 'maxi', 'grande', 'chico',
    'light', 'diet', 'zero', 'sin azucar', 'integral', 'premium',
    'suave', 'extra', 'plus', 'max', 'ultra'
]


def extraer_atributos_producto(nombre):
    """
    Extrae atributos estructurados de un nombre de producto
    
    Args:
        nombre (str): Nombre original del producto
        
    Returns:
        dict: Diccionario con atributos extraídos
    """
    
    atributos = {
        'nombre_original': nombre,
        'nombre_limpio': None,
        'marca': None,
        'peso': None,
        'peso_unidad': None,
        'cantidad_unidades': None,
        'variante': None
    }
    
    if not nombre:
        return atributos
    
    nombre_lower = nombre.lower().strip()
    
    # 1. EXTRAER PESO/VOLUMEN
    # Patrones: 170g, 1.5L, 500ml, 1kg, 2,5 kg, etc
    peso_patterns = [
        r'(\d+(?:[.,]\d+)?)\s*(kg|g|l|lt|ml|cc|gr|grs|lts)\b',
        r'(\d+(?:[.,]\d+)?)\s*x\s*(\d+(?:[.,]\d+)?)\s*(kg|g|l|lt|ml|cc|gr)\b'  # Pack: 6 x 1.5L
    ]
    
    for pattern in peso_patterns:
        peso_match = re.search(pattern, nombre_lower)
        if peso_match:
            if len(peso_match.groups()) == 2:
                # Peso simple
                peso_str = peso_match.group(1).replace(',', '.')
                atributos['peso'] = float(peso_str)
                atributos['peso_unidad'] = peso_match.group(2).lower()
            elif len(peso_match.groups()) == 3:
                # Pack (ej: 6 x 1.5L)
                cantidad = int(peso_match.group(1))
                peso_str = peso_match.group(2).replace(',', '.')
                atributos['cantidad_unidades'] = cantidad
                atributos['peso'] = float(peso_str)
                atributos['peso_unidad'] = peso_match.group(3).lower()
            break
    
    # 2. EXTRAER CANTIDAD DE UNIDADES
    # Patrones: pack x 6, 12 unidades, pack 24, x6
    if not atributos['cantidad_unidades']:
        cantidad_patterns = [
            r'pack\s*x?\s*(\d+)',
            r'x\s*(\d+)\s*u',
            r'(\d+)\s*unidades',
            r'x\s*(\d+)(?!\d)',
        ]
        
        for pattern in cantidad_patterns:
            cantidad_match = re.search(pattern, nombre_lower)
            if cantidad_match:
                atributos['cantidad_unidades'] = int(cantidad_match.group(1))
                break
    
    # 3. DETECTAR MARCA
    for marca in MARCAS_CONOCIDAS:
        if marca in nombre_lower:
            atributos['marca'] = marca
            break
    
    # 4. DETECTAR VARIANTE
    for variante in VARIANTES:
        if variante in nombre_lower:
            atributos['variante'] = variante
            break
    
    # 5. GENERAR NOMBRE LIMPIO
    nombre_limpio = nombre_lower
    
    # Quitar peso
    if peso_match:
        nombre_limpio = nombre_limpio.replace(peso_match.group(0), ' ')
    
    # Quitar marca
    if atributos['marca']:
        nombre_limpio = nombre_limpio.replace(atributos['marca'], ' ')
    
    # Quitar palabras ignoradas
    palabras = nombre_limpio.split()
    palabras_filtradas = [
        p for p in palabras 
        if p not in PALABRAS_IGNORAR and len(p) > 2
    ]
    
    atributos['nombre_limpio'] = ' '.join(palabras_filtradas).strip()
    
    return atributos


def normalizar_peso_a_base(peso, unidad):
    """
    Normaliza peso a unidad base (gramos para peso, ml para volumen)
    
    Args:
        peso (float): Cantidad
        unidad (str): Unidad (kg, g, l, ml, etc)
        
    Returns:
        float: Peso normalizado en unidad base
    """
    if not peso or not unidad:
        return 0
    
    unidad = unidad.lower()
    
    # Peso → gramos
    if unidad in ['kg']:
        return peso * 1000
    elif unidad in ['g', 'gr', 'grs']:
        return peso
    
    # Volumen → ml
    elif unidad in ['l', 'lt', 'lts']:
        return peso * 1000
    elif unidad in ['ml', 'cc']:
        return peso
    
    return peso


# Función de test
if __name__ == "__main__":
    # Tests
    tests = [
        "Atún al natural La Campagnola 170 g",
        "Aceite de oliva Natura 1.5 L",
        "Coca Cola Zero 2.25 lt",
        "Oreo Clásica 117g",
        "Fideos Matarazzo tirabuzones 500 gr",
        "Pack x 6 Quilmes Clásica 1 L",
        "Mayonesa Hellmanns 475g",
        "Leche Serenísima entera 1L"
    ]
    
    print("=" * 80)
    print("TESTS DE EXTRACCIÓN DE ATRIBUTOS")
    print("=" * 80)
    
    for test in tests:
        print(f"\nNombre: {test}")
        atributos = extraer_atributos_producto(test)
        print(f"  Marca: {atributos['marca']}")
        print(f"  Peso: {atributos['peso']} {atributos['peso_unidad']}")
        print(f"  Unidades: {atributos['cantidad_unidades']}")
        print(f"  Variante: {atributos['variante']}")
        print(f"  Nombre limpio: {atributos['nombre_limpio']}")
