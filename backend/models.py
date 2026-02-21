from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class Producto(BaseModel):
    nombre: str
    tienda: str
    categoria: Optional[str] = None
    precio: float
    promo: Optional[str] = None
    imagen_url: Optional[str] = None
    url: Optional[str] = None

class Gasto(BaseModel):
    usuario_id: str
    fecha: datetime
    total: float
    productos: dict  # JSON con detalles