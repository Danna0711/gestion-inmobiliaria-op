# Matriz de priorización MoSCoW

Priorización de los requerimientos del **Sistema de Gestión Inmobiliaria OP**, construida a partir del documento de requerimientos (ACT2: RF01–RF17 y RNF01–RNF04), de la especificación de casos de uso (ACT3: CU01–CU05) y de los ajustes acordados con OP Agente Inmobiliario durante el desarrollo.

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
| — | Ofertas comerciales: una o varias por inmueble, venta o arriendo, IVA calculado | **M** | Acordado con la empresa el 03/11/2026: todo inmueble debe tener al menos una oferta. | CU01 | Implementado |
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
| — | Compartir la ficha desde el sistema (WhatsApp, correo, etc.) | **S** | Ahorra descargar y adjuntar a mano. | CU05 | Implementado |
| — | Panel de administración con la imagen de la empresa | **C** | Presentación profesional para la administradora. | — | Implementado |
| — | Logo y marca de agua en la ficha PDF | **C** | Imagen de marca en lo que recibe el cliente. | CU05 | Implementado |
| — | Reducción automática de fotos (máx. 1.920 px) | **C** | Ahorra espacio en el servidor y hace la ficha más liviana. | CU02 | Implementado |
| — | Ordenamiento del listado (precio, habitaciones) | **C** | Facilita comparar inmuebles. | CU04 | Implementado |
| — | Colores de la marca en todo el sistema | **C** | Coherencia visual con la empresa. | — | Implementado |
| — | Aplicación móvil nativa | **W** | El alcance acordado es un sistema web. | — | Fuera de alcance |
| — | Roles y permisos diferenciados por asesor | **W** | Hoy todos los usuarios de la empresa ven la misma información. | — | Trabajo futuro |
| — | Registro de clientes interesados (CRM) | **W** | No hace parte del problema planteado. | — | Trabajo futuro |
| — | Publicación automática en portales inmobiliarios o enlace público | **W** | Expondría información fuera de la empresa. | — | Trabajo futuro |
| — | Envío automático de correos o avisos por WhatsApp | **W** | Requiere servicios externos de pago. | — | Trabajo futuro |
| — | Dominio propio y plan de alojamiento pago | **W** | Se usa el plan gratuito de PythonAnywhere. | — | Trabajo futuro |

## Resumen

| Prioridad | Cantidad | Implementados |
|---|:---:|:---:|
| Must have | 14 | 14 |
| Should have | 9 | 9 |
| Could have | 5 | 5 |
| Won't have | 6 | — |

Todos los requerimientos M, S y C están implementados y tienen pruebas automáticas. La clasificación se construyó a partir del alcance acordado con OP Agente Inmobiliario (ACT1 a ACT3) y de los ajustes pedidos por la empresa durante el desarrollo.
