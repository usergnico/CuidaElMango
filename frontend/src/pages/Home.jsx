import { useState } from 'react'
import { supabase } from '../config/supabase'
import { Search, Loader2, AlertCircle, TrendingDown, X } from 'lucide-react'

export default function Home() {
  const [busqueda, setBusqueda] = useState('')
  const [loading, setLoading] = useState(false)
  const [resultados, setResultados] = useState(null)
  const [alertas, setAlertas] = useState([])

  const buscarProductosInteligente = async (e) => {
    e.preventDefault()
    
    if (!busqueda.trim()) return

    setLoading(true)
    setAlertas([])
    
    try {
      // Separar productos por comas
      const productosBuscados = busqueda
        .split(',')
        .map(p => p.trim())
        .filter(p => p.length > 0)

      const carritosArmados = {
        Carrefour: [],
        Disco: []
      }

      const nuevasAlertas = []

      // Buscar cada producto en ambas tiendas
      for (const productoBuscado of productosBuscados) {
        console.log(`🔍 Buscando: ${productoBuscado}`)

        // Buscar en Carrefour
        const { data: carrefourResults } = await supabase
          .from('productos')
          .select('*')
          .eq('tienda', 'Carrefour')
          .ilike('nombre', `%${productoBuscado}%`)
          .order('precio', { ascending: true })
          .limit(1)

        // Buscar en Disco
        const { data: discoResults } = await supabase
          .from('productos')
          .select('*')
          .eq('tienda', 'Disco')
          .ilike('nombre', `%${productoBuscado}%`)
          .order('precio', { ascending: true })
          .limit(1)

        // Agregar a carritos
        if (carrefourResults && carrefourResults.length > 0) {
          carritosArmados.Carrefour.push(carrefourResults[0])
        } else {
          nuevasAlertas.push(`⚠️ "${productoBuscado}" no encontrado en Carrefour`)
        }

        if (discoResults && discoResults.length > 0) {
          carritosArmados.Disco.push(discoResults[0])
        } else {
          nuevasAlertas.push(`⚠️ "${productoBuscado}" no encontrado en Disco`)
        }
      }

      setResultados(carritosArmados)
      setAlertas(nuevasAlertas)

    } catch (error) {
      console.error('Error:', error)
      setAlertas(['❌ Error al buscar productos. Intentá de nuevo.'])
    } finally {
      setLoading(false)
    }
  }

  const limpiar = () => {
    setBusqueda('')
    setResultados(null)
    setAlertas([])
  }

  const calcularTotal = (productos) => {
    return productos.reduce((sum, p) => sum + parseFloat(p.precio), 0)
  }

  const totalCarrefour = resultados ? calcularTotal(resultados.Carrefour) : 0
  const totalDisco = resultados ? calcularTotal(resultados.Disco) : 0
  
  const mejorOpcion = totalCarrefour > 0 && totalDisco > 0
    ? totalCarrefour < totalDisco ? 'Carrefour' : 'Disco'
    : null
  
  const ahorro = mejorOpcion ? Math.abs(totalCarrefour - totalDisco) : 0
  const porcentajeAhorro = mejorOpcion 
    ? ((ahorro / Math.max(totalCarrefour, totalDisco)) * 100).toFixed(1)
    : 0

  return (
    <div className="home-page">
      {/* Hero */}
      <div className="hero">
        <h1>🥭 CuidaElMango</h1>
        <p>Ingresá los productos que necesitás y comparamos precios automáticamente</p>
      </div>

      {/* Buscador Inteligente */}
      <div className="buscador-container">
        <div className="buscador-card">
          <h2 className="buscador-title">Comparar Precios</h2>
          <p className="buscador-subtitle">
            Escribí los productos separados por comas
          </p>

          <form onSubmit={buscarProductosInteligente} className="search-form">
            <div className="search-input-group">
              <input
                type="text"
                value={busqueda}
                onChange={(e) => setBusqueda(e.target.value)}
                placeholder="Ej: arroz, aceite 1.5L, atún, fideos matarazzo"
                className="search-input"
                disabled={loading}
              />
              <p className="search-hint">
                💡 Tip: Sé específico para mejores resultados (ej: "aceite natura 1.5L" en vez de solo "aceite")
              </p>
            </div>

            <div className="search-actions">
              <button 
                type="submit" 
                className="btn btn-primary" 
                disabled={loading || !busqueda.trim()}
              >
                {loading ? (
                  <>
                    <Loader2 className="spinner" size={20} />
                    Buscando...
                  </>
                ) : (
                  <>
                    <Search size={20} />
                    Comparar Precios
                  </>
                )}
              </button>

              {(busqueda || resultados) && (
                <button 
                  type="button" 
                  className="btn btn-secondary"
                  onClick={limpiar}
                >
                  <X size={20} />
                  Limpiar
                </button>
              )}
            </div>
          </form>
        </div>

        {/* Alertas */}
        {alertas.length > 0 && (
          <div>
            {alertas.map((alerta, idx) => (
              <div key={idx} className="alert alert-warning">
                <AlertCircle size={20} />
                <span>{alerta}</span>
              </div>
            ))}
          </div>
        )}

        {/* Resultados */}
        {resultados && (
          <div className="resultados-container">
            <div className="resultados-header">
              <h2 className="resultados-title">Comparación</h2>
            </div>

            {/* Recomendación */}
            {mejorOpcion && ahorro > 0 && (
              <div className="recomendacion-card">
                <h3>💡 Te conviene comprar en {mejorOpcion}</h3>
                <p className="ahorro-amount">
                  Ahorrás ${ahorro.toFixed(2)} ({porcentajeAhorro}%)
                </p>
              </div>
            )}

            {/* Comparación lado a lado */}
            <div className="comparacion-grid">
              {/* Carrefour */}
              <div className="tienda-section">
                <div className="tienda-header">
                  <span style={{ fontSize: '2rem' }}>🛒</span>
                  <h3>Carrefour</h3>
                </div>

                {resultados.Carrefour.length > 0 ? (
                  <>
                    <div className="productos-list">
                      {resultados.Carrefour.map((producto) => (
                        <div key={producto.id} className="producto-item">
                          <div className="producto-nombre">{producto.nombre}</div>
                          <div className="producto-precio">
                            ${parseFloat(producto.precio).toFixed(2)}
                          </div>
                          {producto.promo && producto.promo !== 'Precio Regular' && (
                            <div className="producto-promo">
                              🏷️ {producto.promo}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>

                    <div className="tienda-total">
                      <span>Total:</span>
                      <span>${totalCarrefour.toFixed(2)}</span>
                    </div>
                  </>
                ) : (
                  <div className="empty-state">
                    <p>No se encontraron productos en Carrefour</p>
                  </div>
                )}
              </div>

              {/* Disco */}
              <div className="tienda-section">
                <div className="tienda-header">
                  <span style={{ fontSize: '2rem' }}>🛍️</span>
                  <h3>Disco</h3>
                </div>

                {resultados.Disco.length > 0 ? (
                  <>
                    <div className="productos-list">
                      {resultados.Disco.map((producto) => (
                        <div key={producto.id} className="producto-item">
                          <div className="producto-nombre">{producto.nombre}</div>
                          <div className="producto-precio">
                            ${parseFloat(producto.precio).toFixed(2)}
                          </div>
                          {producto.promo && producto.promo !== 'Precio Regular' && (
                            <div className="producto-promo">
                              🏷️ {producto.promo}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>

                    <div className="tienda-total">
                      <span>Total:</span>
                      <span>${totalDisco.toFixed(2)}</span>
                    </div>
                  </>
                ) : (
                  <div className="empty-state">
                    <p>No se encontraron productos en Disco</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
