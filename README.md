Resumen del Proyecto: Peluquería App
La "Peluquería App" es una aplicación web diseñada para la gestión integral de un negocio de peluquería o barbería. Su objetivo principal es simplificar y automatizar tareas administrativas diarias, permitiendo al usuario (probablemente el dueño o administrador de la peluquería) gestionar productos, pedidos, clientes y turnos de manera eficiente.

Funcionalidades Clave
El proyecto se estructura en varias secciones principales, cada una dedicada a un aspecto específico de la gestión del negocio:

Gestión de Productos:

Permite añadir, editar y eliminar productos (champús, tintes, etc.) con detalles como marca, descripción, precio mayorista y porcentaje de venta.

Calcula automáticamente el precio de venta final.

Gestión de Pedidos:

Registra los pedidos de productos, incluyendo la fecha y los ítems del pedido (con marca, descripción, precio mayorista al momento del pedido y cantidad).

Calcula el precio total de cada pedido.

Ofrece funcionalidades de búsqueda por rango de fechas y exportación de pedidos a PDF.

Gestión de Clientes:

Permite añadir, editar y eliminar información de clientes (nombre, apellido, dirección, teléfono).

Muestra un detalle completo de cada cliente, incluyendo sus turnos programados y los servicios/trabajos realizados.

Proporciona estadísticas de ingresos por servicios de clientes, con filtros por mes y año.

Calendario de Turnos:

Visualización interactiva de un calendario mensual que muestra todos los turnos programados.

Funcionalidad Reciente: Aviso prominente de los turnos del día actual en la página principal (productos).

Funcionalidad Reciente: Posibilidad de agregar nuevos turnos directamente haciendo clic en un día del calendario, con un formulario modal que incluye un desplegable para seleccionar clientes existentes.

Mejora Reciente: Visualización optimizada de los eventos en las celdas del calendario, mostrando el nombre completo del cliente y la descripción de la cita de forma más clara, especialmente en dispositivos móviles, similar a la estética de Google Calendar.

Los eventos en el calendario son enlaces directos a la página de edición del turno.

Tecnología Utilizada
El proyecto está construido con las siguientes tecnologías:

Backend:

Flask: Microframework de Python para el desarrollo web.

SQLAlchemy: ORM (Object-Relational Mapper) para interactuar con la base de datos (SQLite).

Python datetime y locale: Para el manejo y formato de fechas, asegurando que se muestren en castellano.

Frontend:

Jinja2: Motor de plantillas para renderizar el HTML dinámicamente.

Tailwind CSS: Framework CSS de utilidad para un diseño responsivo y moderno.

JavaScript (Vanilla JS): Para la interactividad del lado del cliente, incluyendo la lógica del calendario, la gestión de la modal de turnos y las llamadas a la API.

jsPDF: Librería JavaScript para la generación de documentos PDF.

Estado Actual y Próximos Pasos
El proyecto ha evolucionado para ofrecer una solución robusta para la gestión de peluquerías. Las últimas actualizaciones se han centrado en mejorar la usabilidad del calendario y la visibilidad de la información clave.
