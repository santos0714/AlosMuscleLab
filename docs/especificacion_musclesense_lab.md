# INSTRUCCIÓN PRINCIPAL: PREPARACIÓN DEL ENTORNO Y DESARROLLO DE MUSCLESENSE LAB

Quiero que desarrolles MuscleSense Lab, una plataforma científica de simulación óptica aplicada al estudio de la recuperación muscular.

Sin embargo, NO debes comenzar a desarrollar la aplicación inmediatamente.

Debes trabajar en dos fases obligatorias y consecutivas.

# FASE 1. PREPARACIÓN DEL ENTORNO

Antes de escribir el código del proyecto:

1. Audita el entorno de desarrollo disponible.
2. Identifica las herramientas, extensiones y dependencias instaladas.
3. Comprueba la disponibilidad de Python, Node.js, Git y VS Code.
4. Instala y configura las extensiones y herramientas necesarias para desarrollar el proyecto.

Prioriza las siguientes integraciones:

- GitHub MCP Server.
- Playwright MCP.
- Context7.
- Zotero MCP, si es compatible y aporta valor.
- JupyterLab.
- Claude Code y sus herramientas de desarrollo disponibles.

Instala las bibliotecas científicas necesarias:

- NumPy.
- SciPy.
- Pandas.
- Matplotlib.
- Plotly.
- Scikit-learn.
- Pytest.

Investiga e incorpora Monte Carlo eXtreme (MCX) para simulaciones avanzadas de propagación de fotones en tejidos biológicos.

IMPORTANTE:

- Utiliza documentación oficial.
- Verifica compatibilidad antes de instalar.
- No inventes instalaciones exitosas.
- No expongas credenciales, tokens ni claves API.
- No sobrescribas configuraciones existentes sin respaldo.
- No instales herramientas innecesarias.
- Si una integración requiere autorización manual, solicítala.
- Si una herramienta no está disponible, explica la limitación y ofrece una alternativa.

Al finalizar, entrega un informe con:
- Herramientas instaladas.
- Versiones.
- Extensiones conectadas.
- Pruebas de funcionamiento.
- Dependencias pendientes.
- Problemas encontrados.

No comiences la segunda fase hasta verificar que el entorno está preparado. Si existe alguna limitación, identifica qué partes pueden desarrollarse sin ella.

# FASE 2. DESARROLLO DE MUSCLESENSE LAB

Una vez preparado el entorno, comienza el desarrollo.

## Objetivo científico

Investigar si los cambios en las señales ópticas y los parámetros hemodinámicos musculares permiten estimar el estado de recuperación después del ejercicio.

La región anatómica inicial será el bíceps braquial.

## Fundamento físico

Desarrolla un modelo multicapa que contemple:

1. Piel.
2. Tejido adiposo.
3. Tejido muscular.

Incluye:

- Absorción óptica.
- Dispersión múltiple.
- Propagación de fotones.
- Hemoglobina oxigenada y desoxigenada.
- Contribución de la mioglobina y sus limitaciones de identificación.
- Dependencia de la longitud de onda.
- Grosor y propiedades ópticas de cada tejido.

Implementa la ley de Beer-Lambert modificada cuando corresponda y simulaciones Monte Carlo para estudiar la propagación de fotones.

## Instrumentación virtual

Desarrolla un dispositivo portátil NIRS que incluya:

- LED de 760 nm.
- LED de 810 nm.
- LED de 850 nm.
- Fotodetector.
- Amplificador transimpedancia.
- Procesamiento mediante microcontrolador virtual.
- Distancia emisor-detector configurable.

Los componentes deberán corresponder a alternativas comerciales reales.

## Simulación experimental

Implementa un protocolo de ejercicio y recuperación del bíceps braquial:

- Medición basal.
- Ejercicio.
- Recuperación inmediata.
- Recuperación a los 5 minutos.
- Recuperación a los 15 minutos.
- Recuperación a los 30 minutos.

Permite modificar intensidad, duración y características fisiológicas.

Analiza la relación entre oxigenación muscular, hemodinámica, fatiga y recuperación del rendimiento.

No asumas que la reoxigenación equivale directamente a recuperación muscular.

## Arquitectura tecnológica

Frontend:
- React.
- TypeScript.
- Plotly.

Backend:
- Python.
- FastAPI.
- NumPy.
- SciPy.
- Pandas.

Almacenamiento:
- SQLite.

Pruebas:
- Pytest.
- Playwright.

## Módulos

Desarrolla seis módulos integrados:

1. Optical Physics.
2. Tissue Simulator.
3. Sensor Designer.
4. Exercise Protocol.
5. Signal Processing.
6. Recovery Analysis.

Los cambios de parámetros deben propagarse correctamente entre los módulos.

## Metodología de trabajo

Trabaja progresivamente:

1. Investigación científica.
2. Arquitectura del sistema.
3. Desarrollo del motor físico.
4. Validación matemática.
5. Simulación Monte Carlo.
6. Desarrollo de instrumentación virtual.
7. Construcción de la interfaz.
8. Integración.
9. Pruebas automatizadas.
10. Documentación científica.

No sacrifiques rigor científico por velocidad de desarrollo.

## Agentes especializados

Cuando las capacidades disponibles lo permitan, organiza agentes independientes:

- Physics Agent.
- Biomedical Agent.
- Simulation Agent.
- Hardware Agent.
- Data Science Agent.
- Software Agent.
- Validation Agent.

El Validation Agent deberá revisar críticamente los resultados de los demás.

## RESULTADOS FINALES

Quiero obtener:

1. Una aplicación científica funcional.
2. Un motor de simulación reproducible.
3. Documentación de los modelos matemáticos.
4. Un informe de validación.
5. Referencias científicas verificables.
6. Diseño instrumental del sensor.
7. Lista de materiales y estimación de costos para un prototipo físico.

Comienza exclusivamente con la FASE 1.

Cuando termines, presenta el informe de preparación del entorno y continúa con la FASE 2 solamente cuando hayas verificado las dependencias y resuelto las autorizaciones necesarias.