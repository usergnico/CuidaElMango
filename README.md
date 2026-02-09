# 🛒 Comparador de Precios Argentina

> Herramienta open-source para comparar precios entre supermercados argentinos y ahorrar en tus compras.

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/status-alpha-orange.svg)]()

## 🎯 ¿Qué hace?

Este proyecto scrapea automáticamente los precios de supermercados argentinos para que puedas:

- ✅ **Comparar tu carrito** entre Carrefour, Disco y otros supermercados
- 📊 **Ver histórico de precios** y detectar tendencias
- 🏷️ **Identificar promociones** y mejores ofertas
- 💰 **Ahorrar dinero** comprando en el super más barato

## 🚧 Estado del Proyecto

⚠️ **En desarrollo activo** - El proyecto está en fase alpha pero es funcional.

### Supermercados soportados:
- ✅ **Carrefour** (13 secciones)
- ✅ **Disco** (12 secciones)
- 🔜 Día, Coto, Jumbo (planeados)

## 💻 Instalación

```bash
git clone https://github.com/tu-usuario/comparador-precios-ar.git
cd comparador-precios-ar
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install firefox
```

## 🚀 Uso

```bash
python run.py  # Menú interactivo
```

## 📁 Estructura

```
comparador-precios-ar/
├── carrefour-scraper.py
├── disco-scraper.py
├── compare_cart.py
├── run.py
├── config.py
├── data/          # Bases de datos
└── docs/          # Documentación
```

## 🤝 Contribuir

¡Contribuciones bienvenidas! Ver [Issues](https://github.com/tu-usuario/comparador-precios-ar/issues).

## ⚖️ Disclaimer

Solo para uso educativo. Los precios son aproximados. Verificá siempre en el sitio oficial.

---

⭐ Si te sirvió, dejá una estrella!
