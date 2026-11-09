# Métricas de calidad y rendimiento

Este documento reúne las métricas cuantitativas del **Sistema de Gestión Inmobiliaria OP**. Sirven como evidencia del requerimiento no funcional **RNF03** («registrar inmuebles, fotografías y documentos sin degradar significativamente el tiempo de respuesta de las consultas»).

Hay dos grupos:

1. **Métricas locales** (secciones 1 a 4): medidas el 04/11/2026 en un entorno de desarrollo Linux con el script [`metricas/medir_rendimiento.py`](metricas/medir_rendimiento.py). Cualquiera puede repetirlas en su propio equipo.

> **Importante:** los tiempos en milisegundos dependen de la máquina donde se mide. En el equipo Windows de la estudiante o en PythonAnywhere los valores serán distintos. Lo que no cambia es la cantidad de consultas SQL por pantalla ni el tamaño de las respuestas. Por eso son la referencia principal para comparar.
2. **Métricas en el sitio publicado** con Lighthouse (sección 5): se toman en `https://opagenteinmobiliario.pythonanywhere.com` después de la publicación.

## 1. Entorno y datos de prueba

| Elemento | Valor |
|---|---|
| Fecha | 04/11/2026 |
| Software | Python 3.13, Django 6.1.3, SQLite, `DEBUG = False` |
| Equipo | Entorno de desarrollo en la nube con Linux y 2 núcleos, usado durante la construcción del sistema. **No es el equipo Windows de la estudiante** ni el servidor de publicación. |
| Datos cargados | 100 inmuebles, 25 propietarios, 195 ofertas comerciales, 300 fotografías (3 por inmueble, 1.920 × 1.280 px, ~312 KB cada una) y 34 pólizas |
| Repeticiones | 30 por vista (10 para la ficha PDF), después de 3 peticiones de calentamiento |
| Forma de medir | Cliente de pruebas de Django: mide el tiempo que tarda el servidor en procesar la petición (consultas, lógica y plantilla). No incluye la red ni la descarga de Bootstrap, que se miden con Lighthouse. |

## 2. Tiempos de respuesta del servidor

| Vista | Mediana | Percentil 95 | Consultas SQL | Tamaño HTML |
|---|---:|---:|---:|---:|
| Ingreso (formulario de login) | 0,8 ms | 0,9 ms | 0 | 1,9 KB |
| Listado de inmuebles (página 1 de 7) | 11,9 ms | 19,6 ms | 6 | 16,7 KB |
| Listado con 6 filtros combinados | 12,4 ms | 18,9 ms | 6 | 10,1 KB |
| Detalle de inmueble | 6,3 ms | 7,0 ms | 9 | 16,5 KB |
| Formulario de nuevo inmueble | 22,0 ms | 27,6 ms | 3 | 32,5 KB |
| Registrar inmueble con una oferta (envío) | 7,3 ms | 11,0 ms | 8 | — |
| Listado de propietarios | 4,2 ms | 4,7 ms | 4 | 11,9 KB |
| Alertas de pólizas | 5,1 ms | 5,7 ms | 4 | 8,1 KB |
| **Ficha PDF con 3 fotografías** | **350,8 ms** | **361,6 ms** | 5 | **240,2 KB** |

*La mediana es el tiempo típico. El percentil 95 indica que 95 de cada 100 peticiones tardaron eso o menos.*

**Lectura de los resultados**

- Todas las pantallas responden en menos de 30 ms en el servidor. El límite habitual para que una acción se perciba como inmediata es 100 ms.
- El listado tarda lo mismo con y sin filtros (6 consultas en ambos casos). La búsqueda por modalidad y precio en las ofertas se resuelve en una sola consulta con una subconsulta `EXISTS`.
- La ficha PDF es la operación más pesada (unos 0,35 s), porque arma el documento, incrusta las fotos y aplica la marca de agua. Sigue por debajo de 1 segundo, y el archivo de 240 KB se comparte sin problema por WhatsApp o correo.

## 3. Consultas SQL constantes (problema N+1)

La medición encontró un problema en el listado de propietarios. La columna «Inmuebles» hacía una consulta extra por cada propietario de la página: 24 consultas para 20 filas. Se corrigió calculando el número de inmuebles en la misma consulta del listado (`annotate(num_inmuebles=Count("inmuebles"))`).

| Listado de propietarios | Consultas SQL | Mediana |
|---|---:|---:|
| Antes de la corrección | 24 | 12,6 ms |
| Después de la corrección | **4** | **4,2 ms** |

Se agregaron dos pruebas automáticas (`RendimientoListadosTests`). Comprueban que el número de consultas de los listados de inmuebles y de propietarios no aumenta cuando hay más registros. Si alguien vuelve a introducir el problema, la prueba falla.

## 4. Pruebas automáticas y cobertura de código

| Métrica | Valor |
|---|---|
| Pruebas automáticas | **137**, todas aprobadas (135 funcionales y 2 de rendimiento) |
| Cobertura de código de la aplicación | **95 %** (1.096 líneas, 59 sin ejecutar) |
| `views.py` | 98 % |
| `ficha.py`, `forms.py`, `models.py`, `formato.py` | 97 % |
| `admin.py` | 88 % |

La cobertura se midió con `coverage.py` sin contar las migraciones ni el propio archivo de pruebas. Las líneas sin cubrir son sobre todo la configuración de producción (`settings.py`), que solo se activa en el servidor, y los archivos de arranque `wsgi.py`/`asgi.py`.

```bash
pip install coverage
coverage run --source=inmuebles,gestion_inmobiliaria manage.py test inmuebles
coverage report --omit="*/migrations/*,*/tests.py"
```

## 5. Lighthouse en el sitio publicado

Lighthouse mide lo que vive el usuario en el navegador: carga de la página, accesibilidad y buenas prácticas. Se ejecuta sobre el sitio publicado, no en el entorno local.

**Cómo medir** (Google Chrome en computador):

1. Abrir `https://opagenteinmobiliario.pythonanywhere.com` e iniciar sesión.
2. Ir a la pantalla que se va a medir y abrir las herramientas de desarrollador (F12) → pestaña **Lighthouse**.
3. Modo **Navegación**, dispositivo **Escritorio** y categorías Rendimiento, Accesibilidad, Prácticas recomendadas y SEO.
4. En el engranaje de configuración, **desmarcar «Borrar almacenamiento»** (*Clear storage*). Si queda marcado, Lighthouse cierra la sesión y mide la pantalla de ingreso.
5. Pulsar **Analizar la carga de la página** y anotar los resultados. Si se repite la medición, dejar la mediana.

**Resultados** (Chrome, modo Escritorio, sitio publicado; una sola ejecución por pantalla):

| Pantalla | Fecha | Contenido | Rendimiento | Accesibilidad | Prácticas recomendadas | SEO |
|---|---|---|---:|---:|---:|---:|
| Ingreso | 05/11/2026 | Antes de la descripción meta | 100 | 100 | 100 | 91 |
| Ingreso | 05/11/2026 | Después de la descripción meta | 98 | 100 | 100 | 100 |
| Listado de inmuebles | 05/11/2026 | Vacío | 100 | 94 | 100 | 91 |
| Listado de inmuebles | 08/11/2026 | 3 inmuebles | 100 | 94 | 100 | 100 |
| Listado con filtros avanzados abiertos | 08/11/2026 | 3 inmuebles | 100 | 94 | 100 | 100 |
| Listado de propietarios | 08/11/2026 | 4 propietarios | 100 | 100 | 100 | 100 |
| Todas las pólizas | 08/11/2026 | 1 póliza de prueba (próxima a vencer) | 100 | 93 | 100 | 100 |
| Formulario de nuevo inmueble | 08/11/2026 | Formulario vacío | 100 | 95 | 100 | 100 |
| Detalle de inmueble | 08/11/2026 | Inmueble con póliza | 100 | 95 | 100 | 100 |
| Panel de administración | 08/11/2026 | Panel de Django | 100 | 96 | 100 | 54 |

El SEO del ingreso y del listado pasó de 91 a 100 tras agregar la descripción meta (commit del 05/11/2026). El rendimiento del ingreso marcó 98 en la segunda medición: es una variación normal entre ejecuciones (depende de la red y del servidor en ese momento) y sigue en el rango verde (90 a 100). El SEO de 54 del panel de administración es intencional: Django incluye en el panel la etiqueta `<meta name="robots" content="NONE,NOARCHIVE">` para que los buscadores no lo indexen, y Lighthouse lo penaliza. Un panel interno no debe aparecer en Google. No se registraron FCP, LCP, TBT ni CLS; las observaciones de accesibilidad quedan pendientes de revisar.

*FCP: primer contenido visible. LCP: carga del elemento principal. TBT: tiempo en que la página no responde. CLS: estabilidad visual (que nada «salte» mientras carga).*

## 6. Cómo repetir la medición local

Desde la carpeta del proyecto, con el entorno virtual activo:

```bash
python docs/metricas/medir_rendimiento.py
```

El script crea una base de datos y una carpeta de archivos temporales (no modifica `db.sqlite3` ni `media/`). Carga los datos de prueba, mide cada vista y guarda los resultados en `docs/metricas/metricas_locales.json`. Los tiempos cambian según el equipo (Windows, Linux, servidor de publicación), pero la cantidad de consultas SQL debe ser la misma.
