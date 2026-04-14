# Ejecutable de Material Testing Analyzer

El ejecutable autónomo se encuentra en:

```
dist/MaterialTestingAnalyzer/MaterialTestingAnalyzer
```

## Cómo ejecutar

### En Linux/Mac:
```bash
./dist/MaterialTestingAnalyzer/MaterialTestingAnalyzer
```

### En Windows:
```bash
dist\MaterialTestingAnalyzer\MaterialTestingAnalyzer.exe
```

## Nota

Este ejecutable es **completamente autónomo** y no requiere:
- Python instalado
- Entorno virtual
- Instalación de dependencias
- Ningún otro software adicional

Solo necesita ejecutarse directamente.

## Contenido de la carpeta dist/MaterialTestingAnalyzer

La carpeta contiene todos los archivos necesarios para ejecutar la aplicación, incluyendo:
- El ejecutable principal
- Todas las dependencias (PyQt6, matplotlib, numpy, pandas, openpyxl, etc.)
- Archivos de configuración y recursos

**No elimine ni mueva archivos de esta carpeta**, ya que el ejecutable depende de la estructura completa.

## Cambios implementados

### Nuevas características:
1. **Selector de especímenes en todas las secciones**:
   - **Tracción** (ya existía): Selecciona especímenes individuales para visualizar
   - **Impacto** (NUEVO): Selector de especímenes con checkbox "Todos"
   - **Flexión** (NUEVO): Selector de especímenes con checkbox "Todos"

2. **Comportamiento del selector**:
   - Los especímenes seleccionados se muestran en el gráfico
   - La tabla de propiedades se actualiza según los especímenes seleccionados
   - El checkbox "Todos" permite seleccionar/deseleccionar todos a la vez
   - Las estadísticas (en impacto) se calculan solo con especímenes seleccionados

## Requisitos del sistema

- **Sistema Operativo**: Linux, Windows o macOS
- **Arquitectura**: x86_64 (64-bit)
- **Espacio en disco**: ~150 MB para la carpeta completa
- **RAM**: Mínimo 512 MB
- **Pantalla**: Resolución mínima 1024x768

## Soporte

Si encuentra problemas:
1. Asegúrese de ejecutar el archivo correcto en su sistema operativo
2. Verifique que todos los archivos en `dist/MaterialTestingAnalyzer/` estén presentes
3. Intente desde una terminal para ver mensajes de error
