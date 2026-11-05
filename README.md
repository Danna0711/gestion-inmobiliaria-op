# Sistema de Gestión Inmobiliaria — OP Agente Inmobiliario

Sistema web para centralizar la información de los inmuebles de **OP Agente Inmobiliario**: características, propietarios, ofertas comerciales, fotografías, documentos legales y pólizas, con búsqueda avanzada y generación de fichas en PDF para compartir con los clientes.

Proyecto de práctica profesional de **Danna Valentina Betancourt Pico**, Ingeniería de Software, Facultad de Ingeniería, Corporación Universitaria Iberoamericana (Bogotá, 2026).

![Listado de inmuebles](docs/capturas/listado_inmuebles.png)

## Contenido

- [Problema que resuelve](#problema-que-resuelve)
- [Funcionalidades](#funcionalidades)
- [Tecnologías](#tecnologías)
- [Priorización de requerimientos (MoSCoW)](#priorización-de-requerimientos-moscow)
- [Arquitectura y modelo de datos](#arquitectura-y-modelo-de-datos)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Instalación y ejecución](#instalación-y-ejecución)
- [Pruebas](#pruebas)
- [Métricas de rendimiento](#métricas-de-rendimiento)
- [Publicación en producción](#publicación-en-producción)
- [Capturas](#capturas)
- [Estado del proyecto](#estado-del-proyecto)

## Problema que resuelve

La empresa administraba la información de sus inmuebles en hojas de cálculo, carpetas físicas y conversaciones de WhatsApp, sin un sistema que la integrara. Esto generaba demoras para ubicar un inmueble, riesgo de enviar fotos o datos desactualizados a los clientes y falta de claridad sobre el propietario y el estado de cada propiedad. El sistema reúne todo en un solo lugar y genera una ficha profesional de cada inmueble.

## Funcionalidades

| Módulo | Descripción |
|---|---|
| Inmuebles | Ficha única para todos los tipos (casa, apartamento, bodega, local, lote, otro), organizada por secciones. Las secciones de zonas comunes y de datos de bodega solo aparecen para los tipos que aplican. |
| Ofertas comerciales | Cada inmueble tiene una o varias ofertas (venta o arriendo), con área, precio o canon, IVA del 19 % calculado y administración. |
| Propietarios | Registro con identificación única; un propietario puede tener varios inmuebles. |
| Fotografías | Carga múltiple con etiqueta por área. Las fotos se reducen automáticamente (máximo 1.920 px) para ahorrar espacio. |
| Documentos legales | Escritura, certificado de tradición, impuesto predial, planos, contrato de consignación y otros, en PDF, Word, Excel o imagen. |
| Pólizas | Registro con documento adjunto y alertas: vigente, por vencer (30 días o menos) o vencida. |
| Búsqueda y filtros | Texto, tipo, estado, modalidad, ciudad, barrio, rango de precio, habitaciones mínimas y ordenamiento, combinables entre sí. |
| Ficha en PDF | Ficha para el cliente con logo, marca de agua, fotografías, características, ofertas y contacto de la empresa. Excluye los datos internos (propietario, matrículas, margen, impuesto predial). |
| Compartir | Botón que abre el menú de compartir del dispositivo (WhatsApp, correo, etc.) con la ficha adjunta. |
| Seguridad | Acceso solo con usuario y contraseña. Fotografías y documentos se entregan únicamente con sesión iniciada. |
| Administración | Panel de Django personalizado con la imagen de la empresa para gestionar usuarios y registros. |

## Tecnologías

| Componente | Versión | Uso |
|---|---|---|
| Python | 3.13 | Lenguaje |
| Django | 6.1 | Framework web: modelos, vistas, plantillas, autenticación, administración y pruebas |
| SQLite | incluida | Base de datos |
| Pillow | 12 o superior | Validación y reducción de imágenes |
| xhtml2pdf | 0.2.27 | Generación de la ficha en PDF (incluye pypdf y reportlab, usados para la marca de agua) |
| Bootstrap | 5.3.3 (CDN) | Diseño de la interfaz web |

## Priorización de requerimientos (MoSCoW)

Los 17 requerimientos funcionales, los 4 no funcionales y los ajustes acordados con la empresa se priorizaron con el método MoSCoW. La matriz completa, con la justificación de cada uno, está en [docs/moscow.md](docs/moscow.md).

| Prioridad | Qué incluye | Estado |
|---|---|---|
| **Must have** (14) | Registro de inmuebles (RF01, RF02, RF04, RF07, RF16), ofertas comerciales, propietarios (RF08, RF09), fotografías (RF10), documentos legales (RF11), búsqueda (RF14), ficha PDF (RF15), acceso web (RNF01) y seguridad (RNF04) | Implementado |
| **Should have** (9) | Zonas comunes (RF03), matrículas (RF05), datos de bodega y local (RF06), pólizas y alertas (RF12, RF13), información adicional (RF17), facilidad de uso (RNF02), rendimiento (RNF03) y compartir la ficha | Implementado |
| **Could have** (5) | Panel de administración con la marca, logo y marca de agua en el PDF, reducción automática de fotos, ordenamiento del listado y colores de la marca | Implementado |
| **Won't have** (5) | Roles por asesor, registro de clientes, publicación en portales, envíos automáticos y dominio propio | Fuera del alcance de esta versión |

## Arquitectura y modelo de datos

Arquitectura en capas con el patrón **Modelo-Vista-Plantilla (MVT)** de Django. El usuario entra desde el navegador; cada petición pasa por el enrutamiento y la capa de seguridad (sesión obligatoria) antes de llegar a las vistas, que usan el ORM para leer y guardar en SQLite. Las fotografías y documentos se guardan en `media/` y solo se entregan con sesión iniciada.

![Diagrama de arquitectura](docs/diagramas/arquitectura.png)

**Modelo de datos.** Seis entidades. El inmueble es el centro: pertenece a un propietario y tiene sus ofertas comerciales, fotografías, documentos y pólizas (todas relaciones 1 a N).

![Diagrama entidad-relación](docs/diagramas/der.png)

| Entidad | Campos (con id) | Descripción |
|---|:---:|---|
| Propietario | 5 | Dueño del inmueble. Número de identificación único. |
| Inmueble | 48 | Ficha única para todos los tipos: captación, ubicación, áreas, zonas comunes, valores, matrículas y datos de bodega. |
| OfertaComercial | 10 | Venta o arriendo, con área, valor, IVA y administración. Todo inmueble tiene al menos una. |
| Fotografia | 4 | Imagen con etiqueta por área (fachada, sala, cocina…). |
| Documento | 4 | Escritura, certificado de tradición, predial, planos, contrato u otro. |
| Poliza | 7 | Nombre, valor, vencimiento, número de contrato y documento adjunto. |

Los diagramas también están en SVG (`docs/diagramas/*.svg`) para ampliarlos sin perder calidad.

## Estructura del proyecto

```
gestion-inmobiliaria-op/
├── manage.py
├── requirements.txt
├── gestion_inmobiliaria/        # Configuración (settings.py, urls.py)
├── templates/admin/             # Personalización del panel de administración
├── docs/                        # Capturas, diagramas, matriz MoSCoW, métricas y ficha de ejemplo
└── inmuebles/                   # Aplicación principal
    ├── models.py                # Entidades
    ├── views.py                 # Lógica de cada pantalla
    ├── forms.py                 # Formularios y validaciones
    ├── ficha.py                 # Generación de la ficha en PDF
    ├── formato.py               # Formato en pesos, fechas y etiquetas en español
    ├── admin.py                 # Panel de administración
    ├── tests.py                 # Pruebas automáticas
    ├── migrations/              # Cambios de la base de datos
    ├── locale/                  # Traducciones faltantes de Django
    ├── static/inmuebles/        # Logo, marca de agua y colores de la marca
    └── templates/               # Pantallas del sistema
```

## Instalación y ejecución

Requisitos: Python 3.13 y Git.

```bash
# 1. Descargar el proyecto
git clone https://github.com/Danna0711/gestion-inmobiliaria-op.git
cd gestion-inmobiliaria-op

# 2. Crear y activar el entorno virtual
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux o macOS

# 3. Instalar las librerías
pip install -r requirements.txt

# 4. Crear la base de datos
python manage.py migrate

# 5. Crear el usuario administrador
python manage.py createsuperuser

# 6. Iniciar el servidor
python manage.py runserver
```

Luego abrir **http://127.0.0.1:8000** para el sistema y **http://127.0.0.1:8000/admin/** para el panel de administración. Los usuarios de los asesores se crean desde el panel, en «Usuarios».

> En Windows, si PowerShell no permite activar el entorno virtual, ejecutar una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

## Pruebas

El sistema cuenta con **137 pruebas automáticas**: 135 funcionales, que cubren los 17 requerimientos funcionales, la seguridad de acceso y los 5 casos de uso, y 2 de rendimiento, que controlan el número de consultas de los listados. La cobertura de código es del **95 %**. Usan una base de datos y una carpeta de archivos temporales, por lo que no modifican los datos reales.

```bash
python manage.py test inmuebles          # resumen
python manage.py test inmuebles -v 2     # detalle de cada prueba
```

## Métricas de rendimiento

Medición del 04/11/2026 en un entorno de desarrollo Linux (no en el equipo Windows de la estudiante), con 100 inmuebles, 300 fotografías y `DEBUG` desactivado. Los tiempos cambian según el equipo; la cantidad de consultas SQL no. Detalle, método y cómo repetirla en [docs/metricas.md](docs/metricas.md):

| Vista | Tiempo de respuesta (mediana) | Percentil 95 | Consultas SQL |
|---|---:|---:|---:|
| Listado de inmuebles | 11,9 ms | 19,6 ms | 6 |
| Listado con 6 filtros combinados | 12,4 ms | 18,9 ms | 6 |
| Detalle de inmueble | 6,3 ms | 7,0 ms | 9 |
| Registrar inmueble con una oferta | 7,3 ms | 11,0 ms | 8 |
| Alertas de pólizas | 5,1 ms | 5,7 ms | 4 |
| Ficha PDF con 3 fotografías (240 KB) | 350,8 ms | 361,6 ms | 5 |

Todas las pantallas responden en menos de 30 ms en el servidor y la ficha PDF en menos de medio segundo. La medición detectó consultas repetidas en el listado de propietarios: se corrigió y bajó de 24 a 4 consultas. Las métricas de Lighthouse se toman sobre el sitio publicado (ver [docs/metricas.md](docs/metricas.md#5-lighthouse-en-el-sitio-publicado)).

## Publicación en producción

En desarrollo no se necesita configuración adicional. En el servidor se activa el modo de producción con estas variables de entorno (nunca se suben al repositorio):

| Variable | Valor |
|---|---|
| `DJANGO_PRODUCCION` | `1` |
| `DJANGO_SECRET_KEY` | Clave secreta larga y aleatoria |
| `DJANGO_ALLOWED_HOSTS` | Dominio del sitio, por ejemplo `opagente.pythonanywhere.com` |

Con el modo de producción activo: `DEBUG` desactivado, solo HTTPS, cookies seguras y sesión de 12 horas. Después de instalar se ejecutan `python manage.py migrate` y `python manage.py collectstatic`, y la carpeta `staticfiles/` se publica como `/static/`. El alojamiento previsto es PythonAnywhere.

## Capturas

| Ingreso | Detalle del inmueble |
|---|---|
| ![Ingreso](docs/capturas/ingreso.png) | ![Detalle](docs/capturas/detalle_inmueble.png) |

Ficha en PDF ([ver ejemplo](docs/ficha_ejemplo.pdf)):

![Ficha PDF](docs/capturas/ficha_pdf.png)

Panel de administración:

![Panel de administración](docs/capturas/panel_administracion.png)

*Las capturas usan datos de prueba.*

## Estado del proyecto

| Fase | Actividades | Estado |
|---|---|---|
| Levantamiento y diseño | ACT1–ACT6: acta, requerimientos, especificación, modelo de datos, normalización y arquitectura | Completa |
| Desarrollo de módulos | ACT7–ACT13: entorno, inmuebles, fotografías, documentos y pólizas, propietarios, búsqueda | Completa |
| Fichas y entrega | ACT14–ACT15: ficha en PDF y compartir | Completa |
| | ACT16–ACT19: pruebas funcionales con la empresa, correcciones, manual de usuario, capacitación y entrega | En curso |

---

Desarrollado para **OP Agente Inmobiliario** en el marco de la práctica profesional. Docente asesor: Rogelio Vásquez.
