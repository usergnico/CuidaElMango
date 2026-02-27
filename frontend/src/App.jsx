import { useState, useEffect } from 'react'
import { supabase } from './config/supabase'
import { Search, Loader2, X, Moon, Sun, Check, AlertTriangle, RefreshCw } from 'lucide-react'
import './App.css'

function App() {
  const [busqueda, setBusqueda] = useState('')
  const [loading, setLoading] = useState(false)
  const [resultadosBusqueda, setResultadosBusqueda] = useState([])
  const [productosSeleccionados, setProductosSeleccionados] = useState([])
  const [comparacion, setComparacion] = useState(null)
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode')
    return saved ? JSON.parse(saved) : false
  })

  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode)
    localStorage.setItem('darkMode', JSON.stringify(darkMode))
  }, [darkMode])

  // Buscar productos
  const buscarProductos = async (e) => {
    e.preventDefault()
    if (!busqueda.trim()) return

    setLoading(true)
    
    try {
      const { data, error } = await supabase
        .from('productos')
        .select('*')
        .ilike('nombre_normalizado', `%${busqueda}%`)
        .limit(50)

      if (error) throw error

      if (!data || data.length === 0) {
        alert(`No se encontraron productos con "${busqueda}"`)
        setResultadosBusqueda([])
        return
      }

      setResultadosBusqueda(data)

    } catch (error) {
      console.error('Error:', error)
      alert('Error al buscar: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  // Seleccionar producto
  const seleccionarProducto = (producto) => {
    const yaSeleccionado = productosSeleccionados.some(p => p.id === producto.id)
    if (yaSeleccionado) {
      alert('Este producto ya está en tu lista')
      return
    }

    setProductosSeleccionados([...productosSeleccionados, producto])
    setBusqueda('')
    setResultadosBusqueda([])
  }

  // Comparar con matching inteligente
  const compararProductos = async () => {
    if (productosSeleccionados.length === 0) return

    setLoading(true)
    
    try {
      // Llamar al endpoint de matching inteligente
      const response = await fetch('http://localhost:8000/comparar-inteligente', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          productos: productosSeleccionados
        })
      })

      if (!response.ok) {
        throw new Error('Error en la comparación')
      }

      const data = await response.json()
      setComparacion(data)

    } catch (error) {
      console.error('Error:', error)
      alert('Error al comparar: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  // Cambiar producto (corrección manual)
  const cambiarProducto = async (productoOrigenId, nuevoProducto) => {
    try {
      // Guardar equivalencia en DB
      await fetch('http://localhost:8000/equivalencias', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          producto_a_id: productoOrigenId,
          producto_b_id: nuevoProducto.id
        })
      })

      // Actualizar comparación localmente
      const tienda = nuevoProducto.tienda
      const nuevaComparacion = { ...comparacion }
      
      const index = nuevaComparacion[tienda].findIndex(
        p => p.producto_origen_id === productoOrigenId
      )
      
      if (index !== -1) {
        nuevaComparacion[tienda][index] = {
          ...nuevoProducto,
          match_score: 100,
          match_nivel: 'MUY_ALTA',
          corregido_manualmente: true,
          producto_origen_id: productoOrigenId
        }
        
        // Recalcular totales
        nuevaComparacion.totales = {
          Carrefour: calcularTotal(nuevaComparacion.Carrefour),
          Disco: calcularTotal(nuevaComparacion.Disco)
        }
        
        setComparacion(nuevaComparacion)
        alert('✅ Producto actualizado y equivalencia guardada')
      }

    } catch (error) {
      console.error('Error:', error)
      alert('Error al guardar equivalencia')
    }
  }

  const calcularTotal = (productos) => {
    return productos
      .filter(p => !p.no_disponible)
      .reduce((sum, p) => sum + parseFloat(p.precio || 0), 0)
  }

  const limpiar = () => {
    setBusqueda('')
    setResultadosBusqueda([])
    setProductosSeleccionados([])
    setComparacion(null)
  }

  const eliminarSeleccionado = (index) => {
    const nuevos = [...productosSeleccionados]
    nuevos.splice(index, 1)
    setProductosSeleccionados(nuevos)
  }

  return (
    <div className="app">
      <nav className="navbar">
        <div className="container">
          <a href="/" className="logo" onClick={(e) => { e.preventDefault(); limpiar(); }}>
            🥭 CuidaElMango
          </a>
          <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center' }}>
            <button onClick={() => setDarkMode(!darkMode)} className="theme-toggle">
              {darkMode ? <Sun size={20} /> : <Moon size={20} />}
            </button>
            <a href="https://github.com/usergnico/CuidaElMango" target="_blank" rel="noopener noreferrer" className="github-link">
              GitHub
            </a>
          </div>
        </div>
      </nav>

      <main className="main">
        <div className="container">
          <div className="hero">
            <h1>🥭 CuidaElMango</h1>
            <p>Con amor para el pueblo argento</p>
          </div>

          {!comparacion && (
            <>
              {/* Lista de Seleccionados */}
              {productosSeleccionados.length > 0 && (
                <div className="selected-products">
                  <h3>Productos para comparar ({productosSeleccionados.length})</h3>
                  <div className="selected-list">
                    {productosSeleccionados.map((producto, index) => (
                      <div key={index} className="selected-item">
                        <div className="selected-info">
                          <span className="selected-tienda">
                            {producto.tienda === 'Carrefour' ? '🛒' : '🛍️'}
                          </span>
                          <span className="selected-nombre">{producto.nombre}</span>
                          <span className="selected-precio">${parseFloat(producto.precio).toFixed(2)}</span>
                        </div>
                        <button className="btn-remove" onClick={() => eliminarSeleccionado(index)}>
                          <X size={16} />
                        </button>
                      </div>
                    ))}
                  </div>
                  <button className="btn btn-primary" onClick={compararProductos} disabled={loading}>
                    {loading ? (
                      <>
                        <Loader2 className="spin" size={20} />
                        Comparando...
                      </>
                    ) : (
                      <>
                        <Check size={20} />
                        Comparar {productosSeleccionados.length} producto{productosSeleccionados.length > 1 ? 's' : ''}
                      </>
                    )}
                  </button>
                </div>
              )}

              {/* Buscador */}
              <div className="search-section">
                <div className="search-card">
                  <h2>Buscar Productos</h2>
                  <p className="subtitle">
                    {productosSeleccionados.length === 0 
                      ? 'Empezá buscando tu primer producto'
                      : 'Seguí agregando productos a tu lista'
                    }
                  </p>

                  <form onSubmit={buscarProductos}>
                    <div className="input-wrapper">
                      <input
                        type="text"
                        value={busqueda}
                        onChange={(e) => setBusqueda(e.target.value)}
                        placeholder="Ej: aceite, atun, arroz"
                        className="search-input"
                        disabled={loading}
                        autoFocus
                      />
                      <p className="hint">
                        💡  
                      </p>
                    </div>

                    <div className="button-group">
                      <button type="submit" className="btn btn-primary" disabled={loading || !busqueda.trim()}>
                        {loading ? (
                          <>
                            <Loader2 className="spin" size={20} />
                            Buscando...
                          </>
                        ) : (
                          <>
                            <Search size={20} />
                            Buscar
                          </>
                        )}
                      </button>

                      {(busqueda || productosSeleccionados.length > 0 || resultadosBusqueda.length > 0) && (
                        <button type="button" className="btn btn-secondary" onClick={limpiar}>
                          <X size={20} />
                          Limpiar
                        </button>
                      )}
                    </div>
                  </form>
                </div>

                {/* Resultados */}
                {resultadosBusqueda.length > 0 && (
                  <div className="search-results">
                    <h3>Resultados ({resultadosBusqueda.length})</h3>
                    <p className="results-hint">Hacé clic en un producto para agregarlo</p>
                    
                    <div className="results-grid">
                      {resultadosBusqueda.map((producto) => (
                        <div key={producto.id} className="result-card" onClick={() => seleccionarProducto(producto)}>
                          {producto.imagen_url && (
                            <div className="result-image">
                              <img src={producto.imagen_url} alt={producto.nombre} onError={(e) => e.target.style.display = 'none'} />
                            </div>
                          )}
                          
                          <div className="result-info">
                            <div className="result-tienda">
                              {producto.tienda === 'Carrefour' ? '🛒 Carrefour' : '🛍️ Disco'}
                            </div>
                            <div className="result-nombre">{producto.nombre}</div>
                            {producto.marca && (
                              <div className="result-marca">Marca: {producto.marca}</div>
                            )}
                            <div className="result-precio">${parseFloat(producto.precio).toFixed(2)}</div>
                          </div>
                          
                          <div className="result-action">
                            <span>+ Agregar</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </>
          )}

          {/* Comparación */}
          {comparacion && (
            <div className="results">
              <div className="results-header">
                <h2>Comparación Inteligente</h2>
                <button className="btn-clear" onClick={limpiar}>
                  <X size={18} />
                  Nueva Comparación
                </button>
              </div>

              {/* Metadata */}
              {comparacion.metadata && (
                <div className="metadata-card">
                  <div className="metadata-item">
                    <span>Matches encontrados:</span>
                    <strong>{comparacion.metadata.matches_encontrados}</strong>
                  </div>
                  <div className="metadata-item">
                    <span>Alta confianza:</span>
                    <strong className="text-green">{comparacion.metadata.matches_alta_confianza}</strong>
                  </div>
                  {comparacion.metadata.productos_sin_match > 0 && (
                    <div className="metadata-item">
                      <span>Sin match:</span>
                      <strong className="text-warning">{comparacion.metadata.productos_sin_match}</strong>
                    </div>
                  )}
                </div>
              )}

              {/* Recomendación */}
              {comparacion.recomendacion && (
                <div className="recommendation">
                  <h3>💡 Te conviene {comparacion.recomendacion.tienda}</h3>
                  <p className="savings">
                    Ahorrás ${comparacion.recomendacion.ahorro} ({comparacion.recomendacion.porcentaje}%)
                  </p>
                </div>
              )}

              {/* Comparación */}
              <div className="comparison">
                {['Carrefour', 'Disco'].map(tienda => (
                  <div key={tienda} className="store-card">
                    <div className="store-header">
                      <span className="store-icon">{tienda === 'Carrefour' ? '🛒' : '🛍️'}</span>
                      <h3>{tienda}</h3>
                    </div>

                    <div className="products">
                      {comparacion[tienda].map((producto, index) => (
                        <ProductoComparado 
                          key={producto.id || index}
                          producto={producto}
                          onCambiar={cambiarProducto}
                        />
                      ))}
                    </div>

                    <div className="store-total">
                      <span>Total:</span>
                      <span>${comparacion.totales[tienda].toFixed(2)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

// Componente para producto comparado con opción de cambiar
function ProductoComparado({ producto, onCambiar }) {
  const [mostrarAlternativas, setMostrarAlternativas] = useState(false)

  if (producto.no_disponible) {
    return (
      <div className="product product-unavailable">
        <div className="product-name">❌ Producto no disponible</div>
        <p className="text-small">No se encontró equivalente en esta tienda</p>
      </div>
    )
  }

  if (producto.es_origen) {
    return (
      <div className="product product-origin">
        <div className="origin-badge">✓ Producto seleccionado</div>
        {producto.imagen_url && (
          <div className="product-image">
            <img src={producto.imagen_url} alt={producto.nombre} onError={(e) => e.target.style.display = 'none'} />
          </div>
        )}
        <div className="product-name">{producto.nombre}</div>
        <div className="product-price">${parseFloat(producto.precio).toFixed(2)}</div>
      </div>
    )
  }

  // Producto matcheado
  const confianzaBaja = producto.match_score < 70
  const confianzaMedia = producto.match_score >= 70 && producto.match_score < 85

  return (
    <div className={`product ${confianzaBaja ? 'product-low-confidence' : ''}`}>
      {/* Badge de confianza */}
      {producto.corregido_manualmente ? (
        <div className="confidence-badge confidence-manual">
          ✓ Corregido manualmente
        </div>
      ) : (
        <div className={`confidence-badge confidence-${producto.match_nivel?.toLowerCase()}`}>
          Score: {producto.match_score}% ({producto.match_nivel})
        </div>
      )}

      {producto.imagen_url && (
        <div className="product-image">
          <img src={producto.imagen_url} alt={producto.nombre} onError={(e) => e.target.style.display = 'none'} />
        </div>
      )}
      
      <div className="product-name">{producto.nombre}</div>
      
      {producto.marca && (
        <div className="product-marca">Marca: {producto.marca}</div>
      )}
      
      <div className="product-price">${parseFloat(producto.precio).toFixed(2)}</div>

      {/* Botón para cambiar si la confianza es baja/media */}
      {(confianzaBaja || confianzaMedia) && producto.alternativas && producto.alternativas.length > 0 && (
        <div className="product-actions">
          <button 
            className="btn-change"
            onClick={() => setMostrarAlternativas(!mostrarAlternativas)}
          >
            <RefreshCw size={16} />
            {mostrarAlternativas ? 'Cerrar' : 'Cambiar producto'}
          </button>
        </div>
      )}

      {/* Modal de alternativas */}
      {mostrarAlternativas && producto.alternativas && (
        <div className="alternativas-modal">
          <h4>Alternativas disponibles:</h4>
          <div className="alternativas-list">
            {producto.alternativas.map((alt, idx) => (
              <div 
                key={idx} 
                className="alternativa-item"
                onClick={() => {
                  onCambiar(producto.producto_origen_id, alt)
                  setMostrarAlternativas(false)
                }}
              >
                <div className="alternativa-info">
                  <div className="alternativa-nombre">{alt.nombre}</div>
                  <div className="alternativa-score">Score: {alt.match_score}%</div>
                </div>
                <div className="alternativa-precio">${parseFloat(alt.precio).toFixed(2)}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default App
