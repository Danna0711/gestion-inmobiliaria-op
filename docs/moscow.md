# Matriz de priorización MoSCoW

Priorización de los requerimientos del **Sistema de Gestión Inmobiliaria OP**, construida a partir del documento de requerimientos (ACT2: RF01–RF17 y RNF01–RNF04), de la especificación de casos de uso (ACT3: CU01–CU05) y de los ajustes acordados con OP Agente Inmobiliario durante el desarrollo. Las funciones que no figuraban en la ACT2 y se incorporaron sobre la marcha recibieron identificadores nuevos a continuación de los de la Entrega 1: RF18–RF26 y RNF05–RNF07 (ver [Incorporados durante el desarrollo](#incorporados-durante-el-desarrollo)).

| Categoría | Significado en este proyecto |
|---|---|
| **M — Must have** (debe tener) | Sin esto el sistema no resuelve el problema: centralizar el inmueble, su propietario, sus fotos y sus documentos, encontrarlo rápido y generar la ficha. |
| **S — Should have** (debería tener) | Importante para la operación diaria de la empresa, pero el sistema podría salir sin ello por un tiempo corto. |
| **C — Could have** (podría tener) | Mejora la experiencia o la presentación; se incluye si el tiempo lo permite. |
| **W — Won't have** (no tendrá en esta versión) | Fuera del alcance acordado para la práctica. Queda como trabajo futuro. |

## Matriz

| ID | Requerimiento | Prioridad | Justificación | Caso de uso | Estado |
|---|---|:---:|---|---|---|
| RF01 | Registrar inmueble con datos de captación (ID, fecha, agente, ciudad, tipo) | **M** | Es el registro base de todo el sistema. | CU01 | Implementado |
| RF02 | Ubicación y áreas (departamento, barrio, dirección, conjunto, estrato, piso, áreas) | **M** | Sin ubicación ni áreas no se puede ofrecer el inmueble. | CU01 | Implementado |
| RF04 | Valores de la transacción (precio o canon, administración, margen, predial) | **M** | El precio es el dato que más consultan los clientes. Se amplió a ofertas comerciales. | CU01 | Implementado |
| RF18 | Ofertas comerciales: una o varias por inmueble, venta o arriendo, IVA calculado | **M** | Acordado con la empresa el 23/10/2026: todo inmueble debe tener al menos una oferta. | CU01 | Implementado |
| RF07 | Estado del inmueble (disponible, reservado, vendido, arrendado) | **M** | Evita ofrecer inmuebles que ya no están disponibles. | CU01 | Implementado |
| RF08 | Registro de propietarios | **M** | La empresa necesita saber de quién es cada inmueble. | CU01 | Implementado |
| RF09 | Un propietario con varios inmuebles | **M** | Caso frecuente en la empresa (relación 1 a N). | CU01 | Implementado |
| RF10 | Carga múltiple de fotografías clasificadas por área | **M** | Las fotos son la base de la ficha y de la oferta al cliente. | CU02 | Implementado |
| RF11 | Documentos legales del inmueble | **M** | Hoy están en carpetas físicas: centralizarlos es parte del problema. | CU02 | Implementado |
| RF14 | Búsqueda y filtros combinados | **M** | Ubicar un inmueble rápido es la principal queja actual. | CU04 | Implementado |
| RF15 | Ficha individual en PDF | **M** | Es lo que la empresa entrega al cliente. | CU05 | Implementado |
| RF16 | Plantilla estándar de captación | **M** | Unifica la información con el formato que ya usa la empresa. | CU01 | Implementado |
| RNF01 | Acceso por navegador web, sin instalación | **M** | Sistema web: los asesores entran desde cualquier PC. | Todos | Implementado |
| RNF04 | Acceso restringido a usuarios autorizados | **M** | Hay datos personales de propietarios y documentos legales. | Todos | Implementado |
| RF03 | Zonas comunes (cuando el inmueble está en conjunto o edificio) | **S** | Solo aplica a algunos tipos de inmueble. | CU01 | Implementado |
| RF05 | Hasta dos matrículas inmobiliarias | **S** | Dato interno necesario para la gestión legal, no para ofrecer. | CU01 | Implementado |
| RF06 | Campos de bodegas y locales (KVA, altura, uso de suelo, muelles, etc.) | **S** | Solo aplica a bodegas y locales, pero son clave para ese cliente. | CU01 | Implementado |
| RF12 | Pólizas con documento adjunto | **S** | Necesario para inmuebles en arriendo. | CU03 | Implementado |
| RF13 | Alertas de pólizas por vencer (30 días o menos) | **S** | Evita que una póliza venza sin aviso. | CU03 | Implementado |
| RF17 | Información adicional de texto libre | **S** | Recoge lo que no tiene un campo propio. | CU01 | Implementado |
| RNF02 | Interfaz sencilla para usuarios sin conocimientos técnicos | **S** | Condición para que los asesores adopten el sistema. | Todos | Implementado |
| RNF03 | Rendimiento: registrar datos sin degradar las consultas | **S** | Se verifica con las [métricas de rendimiento](metricas.md). | Todos | Implementado y medido |
| RF19 | Compartir la ficha desde el sistema (WhatsApp, correo, etc.) | **S** | Ahorra descargar y adjuntar a mano. | CU05 | Implementado |
| RF20 | Panel de administración con la imagen de la empresa | **C** | Presentación profesional para la administradora. | — | Implementado |
| RF21 | Logo y marca de agua en la ficha PDF | **C** | Imagen de marca en lo que recibe el cliente. | CU05 | Implementado |
| RNF05 | Reducción automática de fotos (máx. 1.920 px) | **C** | Ahorra espacio en el servidor y hace la ficha más liviana. | CU02 | Implementado |
| RF22 | Ordenamiento del listado (precio, habitaciones) | **C** | Facilita comparar inmuebles. | CU04 | Implementado |
| RNF06 | Colores de la marca en todo el sistema | **C** | Coherencia visual con la empresa. | — | Implementado |
| RF23 | Roles y permisos diferenciados por asesor | **W** | Hoy todos los usuarios de la empresa ven la misma información. | — | Trabajo futuro |
| RF24 | Registro de clientes interesados (CRM) | **W** | No hace parte del problema planteado. | — | Trabajo futuro |
| RF25 | Publicación automática en portales inmobiliarios o enlace público | **W** | Expondría información fuera de la empresa. | — | Trabajo futuro |
| RF26 | Envío automático de correos o avisos por WhatsApp | **W** | Requiere servicios externos de pago. | — | Trabajo futuro |
| RNF07 | Dominio propio y plan de alojamiento pago | **W** | Se usa el plan gratuito de PythonAnywhere. | — | Trabajo futuro |

## Incorporados durante el desarrollo

Doce de las 33 filas de la matriz no figuraban en el documento de requerimientos de la Entrega 1 (ACT2). Se incorporaron sobre la marcha, por decisiones de la empresa o por mejoras que surgieron al construir y probar el sistema. Se les asignó un identificador nuevo para que la matriz sea trazable completa: nueve funcionales (RF18 a RF26) y tres no funcionales (RNF05 a RNF07).

| ID | Qué es | Origen | Fecha | Estado |
|---|---|---|---|---|
| RF18 | Ofertas comerciales | Decisión de la empresa (amplía RF04: todo inmueble tiene al menos una oferta) | 23/10/2026 | Implementado |
| RF21 | Logo y marca de agua en la ficha PDF | Decisión de la empresa (la ficha muestra solo el contacto general, sin datos internos) | 23/10/2026 | Implementado |
| RF19 | Compartir la ficha desde el sistema | Mejora de operación | 24/10/2026 | Implementado |
| RF20 | Panel de administración con la imagen de la empresa | Mejora de operación | 03/11/2026 | Implementado |
| RNF06 | Colores de la marca en todo el sistema | Mejora de operación | 03/11/2026 | Implementado |
| RNF05 | Reducción automática de fotos (máx. 1.920 px) | Mejora de operación | Sin fecha registrada | Implementado |
| RF22 | Ordenamiento del listado (precio, habitaciones) | Complemento de la búsqueda (CU04) | Sin fecha registrada | Implementado |
| RF23 a RF26, RNF07 | Roles por asesor, registro de clientes, publicación automática, envíos automáticos, dominio propio y alojamiento pago | Delimitación del alcance (Won't have) | — | Trabajo futuro |

## Resumen

| Prioridad | Cantidad | Implementados |
|---|:---:|:---:|
| Must have | 14 | 14 |
| Should have | 9 | 9 |
| Could have | 5 | 5 |
| Won't have | 5 | — |

Todos los requerimientos M, S y C están implementados y tienen pruebas automáticas. La clasificación se construyó a partir del alcance acordado con OP Agente Inmobiliario (ACT1 a ACT3) y de los ajustes pedidos por la empresa durante el desarrollo.
