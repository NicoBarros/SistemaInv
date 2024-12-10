"""
URL configuration for sistema project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from sistemaApp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login_view, name = 'login'),
    path('register/', views.register_view, name = 'register'),
    path('home/', views.home, name = 'Home'),
    path('logout/',views.logout_view, name='logout'),
    path('gproductos/',views.gProductos, name='GestionProductos'),
    path('crearproducto/',views.crear_producto, name='CrearProducto'),
    path('modificarproducto/<int:codigo_producto>/',views.modificar_producto, name='ModificarProducto'),
    path('eliminarproducto/<int:codigo_producto>/',views.eliminar_producto, name='EliminarProducto'),
    path('gdepartamentos/',views.gDepartamentos, name='GestionDepartamentos'),
    path('creardepartamento/',views.crear_departamentos, name='CrearDepartamento'),
    path('modificardepartamento/<int:categoria_id>/',views.modificar_departamentos, name='ModificarDepartamento'),
    path('eliminardepartamento/<int:categoria_id>/',views.eliminar_departamentos, name='EliminarDepartamento'),
    path('productosasociados/<int:categoria_id>/', views.productos_asociados, name='ProductosAsociados'),
    path('gproveedor/',views.gProveedor, name='GestionProveedores'),
    path('crearproveedor/',views.crear_proveedor, name='CrearProveedor'),
    path('modificarproveedor/<int:id>/',views.modificar_proveedor, name='ModificarProveedor'),
    path('eliminarproveedor/<int:id>/',views.eliminar_proveedor, name='EliminarProveedor'),
    path('gcliente/',views.gCliente, name='GestionClientes'),
    path('crearcliente/',views.crear_cliente, name='CrearCliente'),
    path('modificarcliente/<int:id_cliente>/', views.modificar_cliente, name='ModificarCliente'),
    path('eliminarcliente/<int:id_cliente>/', views.eliminar_cliente, name='EliminarCliente'),
    path('clientes/abonar/<int:id_cliente>/', views.abonar_deuda, name='AbonarDeuda'),
    path('aumentar_deuda/<int:id_cliente>/', views.aumentar_deuda, name='AumentarDeuda'),
    path('agregar_producto/', views.agregar_producto, name='AgregarProducto'),
    path('quitar/<str:codigo_producto>/', views.quitar_producto, name='QuitarProducto'),
    path('cancelar_venta/', views.cancelar_venta, name='CancelarVenta'),
    path('registrar_venta/', views.registrar_venta, name='RegistrarVenta'),
    path('historial_venta/', views.historial_ventas, name='HistorialVentas'),
    path('generar_reporte_ventas/', views.generar_reporte_ventas, name='generar_reporte_ventas'),
    path('agregar_varios_productos/', views.agregar_varios_productos, name='agregar_varios_productos'),
    path('buscar_productos/', views.buscar_productos, name='buscar_productos'),

]
