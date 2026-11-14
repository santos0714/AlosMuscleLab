"""Configuracion comun de las pruebas de MuscleSense Lab.

MCX-CL (pmcxcl) necesita un runtime OpenCL:
  * Windows: lo aporta el controlador grafico (AMD, Intel o NVIDIA). No hay que hacer nada.
  * Linux sin GPU (VM local de Claude, contenedor en la nube): se usa PoCL, un OpenCL de CPU
    instalado por pip (pocl-binary-distribution). El cargador ICD no lo encuentra solo, asi
    que aqui se le indica con OCL_ICD_VENDORS *antes* de importar pmcxcl.
"""
from musclesense.optical_physics.opencl import configure_cpu_opencl as configurar_opencl_cpu  # noqa: E402

configurar_opencl_cpu()
