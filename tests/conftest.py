"""Configuracion comun de las pruebas de MuscleSense Lab.

MCX-CL (pmcxcl) necesita un runtime OpenCL:
  * Windows: lo aporta el controlador grafico (AMD, Intel o NVIDIA). No hay que hacer nada.
  * Linux sin GPU (VM local de Claude, contenedor en la nube): se usa PoCL, un OpenCL de CPU
    instalado por pip (pocl-binary-distribution). El cargador ICD no lo encuentra solo, asi
    que aqui se le indica con OCL_ICD_VENDORS *antes* de importar pmcxcl.
"""
import glob
import os
import sys
import sysconfig
import tempfile


def configurar_opencl_cpu():
    """Apunta el cargador OpenCL a PoCL si no hay otro runtime. Devuelve la carpeta ICD o None."""
    if not sys.platform.startswith("linux"):
        return None
    if os.environ.get("OCL_ICD_VENDORS"):
        return os.environ["OCL_ICD_VENDORS"]
    if glob.glob("/etc/OpenCL/vendors/*.icd"):
        return None  # ya hay un runtime del sistema (p. ej. una GPU real); no lo tapamos
    candidatos = []
    for clave in ("platlib", "purelib"):
        base = sysconfig.get_paths()[clave]
        candidatos += glob.glob(os.path.join(base, "pyopencl", ".libs", "libpocl*.so*"))
    if not candidatos:
        return None
    carpeta = tempfile.mkdtemp(prefix="musclesense_ocl_")
    with open(os.path.join(carpeta, "pocl.icd"), "w", encoding="ascii") as f:
        f.write(candidatos[0] + "\n")
    os.environ["OCL_ICD_VENDORS"] = carpeta
    return carpeta


configurar_opencl_cpu()
