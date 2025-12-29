<h1 align="center">Sistema Automatizado de Monitoreo de Precios: Canasta Familiar</h1>

<p align="center">
  Este proyecto resuelve la ineficiencia en la recolección y análisis de precios de productos de la canasta familiar en plazas de mercado y tiendas externas. Se transformó un proceso manual basado en papel y lápiz en un <b>flujo de datos automatizado (End-to-End)</b>.
</p>

<br>

<h2>🚀 El Desafío (Problemática)</h2>
Originalmente, el cliente recolectaba datos físicamente (papel), lo que generaba:
<ul>
  <li><b>Alta latencia:</b> Horas perdidas pasando datos manualmente a Excel.</li>
  <li><b>Errores humanos:</b> Inconsistencias en la transcripción de datos.</li>
  <li><b>Falta de visibilidad:</b> Imposibilidad de comparar precios entre plazas y tiendas en tiempo real.</li>
</ul>

<br>

<h2>🛠️ Solución Técnica (Stack Tecnológico)</h2>
Diseñé e implementé una arquitectura que cubre todo el ciclo de vida del dato:
<ul>
  <li><b>Captura de Datos (Frontend):</b> Creé una interfaz web personalizada con <b>HTML, CSS y JavaScript</b> para agilizar la entrada de datos. Implementé un buscador dinámico de productos que <b>optimizó el tiempo de carga en un 30%</b> respecto al método anterior.</li>
  <li><b>Almacenamiento:</b> Integración con la API de Google Sheets para persistencia de datos inmediata y accesible.</li>
  <li><b>Procesamiento (ETL):</b> Desarrollé scripts en <b>Python (Pandas)</b> para la extracción, limpieza y transformación:
    <ul>
      <li>Cálculo automático de variaciones de precios entre días (Precios SDDE).</li>
      <li>Consolidación de múltiples fuentes (Plazas de Mercado vs. Tiendas Externas).</li>
    </ul>
  </li>
</ul>

<br>

<h2>📊 Insights y Resultados</h2>
El sistema genera reportes automáticos que permiten:
<ul>
  <li><b>Análisis Comparativo (Resumen PMD):</b> Visualización directa de la brecha de costos entre plazas de mercado locales y tiendas a sus alrededores.</li>
  <li><b>Monitoreo Diario (Precios SDDE):</b> Detección inmediata de fluctuaciones de precios de un día para otro.</li>
  <li><b>Eficiencia Operativa:</b> Eliminación total del uso de papel y reducción drástica del tiempo de carga de datos, <b>reduciendo el proceso de 4 horas a solo 10 minutos.</b></li>
</ul>

<br>

<h2>🧠 Retos Superados</h2>
<ul>
  <li><b>Optimización de UX:</b> Reducción de la latencia en la captura mediante un cuadro de búsqueda inteligente en JS que permite filtrar productos rápidamente.</li>
  <li><b>Integridad de Datos:</b> Ajuste de lógica de procesamiento para estandarizar formatos de fecha regionales que causaban errores en los cálculos temporales.</li>
</ul>

<br>

<h2>📂 Estructura del Repositorio</h2>
<ul>
  <li><code>index.html</code>: Código fuente del formulario web para captura de datos.
    <br>🔗 <a href="https://darlingmartinez.github.io/UBIKO_freelancer/">Visualizar Formulario Web</a>
  </li>
  <li><code>Procesar.py</code>: Script con la lógica de transformación ETL en Python.
    <br>🔗 <a href="https://darlingmartinez.github.io/UBIKO_freelancer/Admin">Acceso al Generador de Excel</a>
  </li>
  <li><code>Reporte_Comparativo.xlsx</code>: Muestra del reporte final generado (datos anonimizados).</li>
</ul>

<br>

<blockquote>
  <b>Nota importante:</b> Los datos utilizados en este repositorio son ficticios para proteger la confidencialidad e integridad de la información real del cliente.
</blockquote>
