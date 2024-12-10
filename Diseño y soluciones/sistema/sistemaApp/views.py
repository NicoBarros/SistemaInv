from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.cache import cache_control
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from .models import Producto,Proveedor,Categoria,Cliente,Venta
from .forms import CategoriaForms, ProveedorForm, ClienteForm, ProductoForm, VentaForm, RegisterForm
from django.http import JsonResponse,HttpResponseForbidden
from django.utils import timezone
from decimal import Decimal
from django.db.models import Q
from datetime import datetime
import os

def login_view(request):
    """
    Vista para manejar el proceso de inicio de sesión.

    Esta vista recibe una solicitud POST con las credenciales del usuario (username y password).
    Intenta autenticar al usuario y, si la autenticación es exitosa, inicia la sesión y redirige al usuario
    a la página principal. Si las credenciales son incorrectas, muestra un mensaje de error.

    Parámetros:
    - request: objeto HttpRequest que contiene los datos de la solicitud.

    Retorna:
    - renderiza el formulario de inicio de sesión en caso de error o solicitud GET.
    - redirige al usuario a la página principal si la autenticación es exitosa.
    """
    
    # Inicializa la variable para el mensaje de error en caso de que las credenciales sean incorrectas.
    error_message = None
    
    # Si la solicitud es un POST (enviar formulario).
    if request.method == 'POST':
        # Obtiene los datos de 'username' y 'password' del formulario enviado.
        username = request.POST['username']
        password = request.POST['password']
        
        # Usa la función 'authenticate' para intentar autenticar al usuario con las credenciales.
        user = authenticate(request, username=username, password=password)
        
        # Si la autenticación es exitosa.
        if user is not None:
            # Si el usuario es autenticado correctamente, se inicia la sesión.
            login(request, user)
            
            # Redirige al usuario a la página principal ('Home').
            return redirect('Home')
        else:
            # Si las credenciales son incorrectas, se muestra un mensaje de error.
            error_message = "Usuario o contraseña incorrectos"
    
    # Si la solicitud no es un POST o si hay un error, se renderiza el formulario de inicio de sesión.
    return render(request, 'venta/login.html', {'error_message': error_message})


def logout_view(request):
    """
    Vista para manejar el proceso de cierre de sesión.

    Esta vista cierra la sesión del usuario actual, redirige al usuario a la página de inicio de sesión 
    y evita que la página de cierre de sesión se guarde en caché.

    Parámetros:
    - request: objeto HttpRequest que contiene los datos de la solicitud.

    Retorna:
    - redirige al usuario a la página de inicio de sesión ('login').
    """
    
    # Cierra la sesión del usuario.
    logout(request)
    
    # Crea una respuesta HTTP que redirige al usuario a la página de inicio de sesión ('login').
    response = HttpResponseRedirect('login')
    
    # Configura las cabeceras HTTP para evitar el almacenamiento en caché.
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'  # Evita que se guarde en caché.
    response['Pragma'] = 'no-cache'  # Para versiones anteriores de HTTP.
    response['Expires'] = '0'  # Establece la fecha de expiración a cero, forzando que se recargue la página.

    # Redirige a la página de login.
    return redirect('login')


@login_required
# Requiere que el usuario esté autenticado para acceder a esta vista.
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
# Controla el caché para evitar que la página sea almacenada.
def home(request):
    """
    Vista que muestra el inicio de la aplicación, con los productos agregados y su total.

    Esta vista recupera los productos agregados desde la sesión del usuario, calcula el total 
    de los precios de venta y renderiza la página de inicio con esa información.

    Parámetros:
    - request: objeto HttpRequest que contiene los datos de la solicitud.

    Retorna:
    - una respuesta con la plantilla 'home.html', que contiene la lista de productos agregados y el total calculado.
    """
    
    # Obtiene la lista de productos agregados desde la sesión del usuario. Si no hay productos, se inicializa como una lista vacía.
    productos_agregados = request.session.get('productos_agregados', [])
    
    # Calcula el total sumando el precio de venta de cada producto agregado.
    total = sum(producto['precio_venta'] for producto in productos_agregados)
    
    # Renderiza la plantilla 'home.html' pasando los productos agregados y el total calculado.
    return render(request, 'venta/home.html', {
        'productos_agregados': productos_agregados,  # Lista de productos añadidos.
        'total': total,  # Suma total del precio de los productos agregados.
    })


def register_view(request):
    """
    Vista para registrar un nuevo usuario.

    Esta vista permite a los administradores registrar nuevos usuarios en el sistema. 
    Verifica si el usuario tiene permisos de superusuario antes de permitir el registro. 
    Si la solicitud es POST, procesa el formulario de registro y crea un nuevo usuario. 
    Si no es POST, simplemente muestra un formulario vacío.

    Parámetros:
    - request: objeto HttpRequest que contiene los datos de la solicitud.

    Retorna:
    - una respuesta HTTP con la plantilla 'register/registrar_user.html', 
      que contiene el formulario de registro, o redirige si el registro es exitoso.
    """
    
    # Verifica si el usuario actual tiene permisos de superusuario (administrador).
    # Si no, se devuelve una respuesta de "Forbidden" (prohibido).
    if not request.user.is_superuser:
        return HttpResponseForbidden("No tienes permiso para registrar usuarios.")
    
    # Si la solicitud es POST (cuando el formulario es enviado):
    if request.method == 'POST':
        # Se crea un objeto de formulario con los datos enviados.
        form = RegisterForm(request.POST)
        
        # Si el formulario es válido:
        if form.is_valid():
            # Se obtienen los datos del formulario.
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            # Se crea un nuevo usuario con el nombre de usuario y la contraseña proporcionados.
            user = User.objects.create_user(username=username, password=password)
            user.save()  # Se guarda el nuevo usuario en la base de datos.
            
            # Redirige a la vista de registro (lo que puede ser una forma de mostrar un mensaje de éxito o un nuevo formulario).
            return redirect('register')
    else:
        # Si la solicitud no es POST (por ejemplo, si se está accediendo a la página por primera vez),
        # se crea una instancia vacía del formulario.
        form = RegisterForm()

    # Se renderiza la plantilla 'registrar_user.html' pasando el formulario como contexto.
    return render(request, 'register/registrar_user.html', {'form': form})


@login_required
def buscar_productos(request):
    """
    Vista para buscar productos basados en un término de búsqueda.

    Esta vista permite a los usuarios autenticados realizar una búsqueda de productos 
    en la base de datos. El término de búsqueda puede ser parte del nombre o código del 
    producto. Los resultados se limitan a los primeros 10 productos que coincidan con 
    el término de búsqueda.

    Parámetros:
    - request: objeto HttpRequest que contiene los datos de la solicitud.

    Retorna:
    - Una respuesta JSON con los productos encontrados que contienen el término de búsqueda 
      en el nombre o código del producto. Si no se encuentra el parámetro 'q', se devuelve 
      una respuesta vacía.
    """
    
    # Verifica si se ha proporcionado un parámetro 'q' en la solicitud GET.
    if 'q' in request.GET:
        query = request.GET['q']  # Obtiene el término de búsqueda de la URL.
        
        # Realiza una consulta para buscar productos cuyo nombre o código contengan el término de búsqueda.
        # Se limita a los primeros 10 resultados.
        productos = Producto.objects.filter(
            Q(nombre_producto__icontains=query) | Q(codigo_producto__icontains=query)
        ).values('codigo_producto', 'nombre_producto')[:10]  

        # Crea una lista de diccionarios con los resultados de búsqueda.
        resultados = []
        for producto in productos:
            resultados.append({
                'codigo': producto['codigo_producto'],
                'nombre': producto['nombre_producto'],
            })
        
        # Devuelve los resultados como una respuesta JSON.
        return JsonResponse({'productos': resultados})
    
    # Si no se encuentra el parámetro 'q', se devuelve una respuesta vacía.
    return JsonResponse({'productos': []})


@login_required
def agregar_varios_productos(request):
    """
    Vista para agregar varios productos al carrito de compras de un usuario.

    Esta vista permite a los usuarios autenticados buscar productos por código o nombre, 
    agregar productos al carrito, y actualizar la cantidad de productos en el carrito si ya 
    están añadidos. Verifica la disponibilidad de stock antes de agregar productos.

    Parámetros:
    - request: objeto HttpRequest que contiene los datos de la solicitud. Debe contener un 
      término de búsqueda y los detalles del producto a agregar (código y cantidad).

    Retorna:
    - Una respuesta renderizada con el carrito actualizado, el mensaje de éxito o error, 
      el total de la compra y los productos encontrados.
    """
    
    # Verifica si ya existe una lista de productos agregados en la sesión
    if 'productos_agregados' not in request.session:
        # Si no existe, crea una lista vacía
        request.session['productos_agregados'] = []

    # Inicializa variables para los mensajes y productos encontrados
    mensaje = None
    productos_encontrados = None
    
    if request.method == 'POST':  # Si la solicitud es un POST
        # Obtiene el término de búsqueda del formulario y elimina los espacios extra
        search_term = request.POST.get('search', '').strip()

        # Si hay un término de búsqueda, busca los productos que coincidan en código o nombre
        if search_term:
            productos_encontrados = Producto.objects.filter(
                Q(codigo_producto__icontains=search_term) | Q(nombre_producto__icontains=search_term)
            )
        
        # Obtiene el código del producto y la cantidad a agregar desde el formulario
        codigo_producto = request.POST.get('codigo_producto')
        cantidad_a_agregar = int(request.POST.get('cantidad', 1))  # Valor por defecto de cantidad es 1
        
        try:
            # Intenta obtener el producto correspondiente al código proporcionado
            producto = Producto.objects.get(codigo_producto=codigo_producto)

            # Verifica si la cantidad a agregar excede el stock disponible
            if cantidad_a_agregar > producto.stock_actual:
                # Si no hay suficiente stock, muestra un mensaje de error
                mensaje = f"Stock insuficiente para '{producto.nombre_producto}'. Solo quedan {producto.stock_actual} unidades."
            else:
                # Obtiene los productos actualmente en el carrito de la sesión
                productos_agregados = request.session['productos_agregados']

                # Verifica si el producto ya está en el carrito
                producto_en_carrito = next((p for p in productos_agregados if p['codigo'] == producto.codigo_producto), None)

                if producto_en_carrito:
                    # Si el producto ya está en el carrito, actualiza la cantidad
                    cantidad_actual = producto_en_carrito['cantidad']
                    if cantidad_actual + cantidad_a_agregar > producto.stock_actual:
                        # Si la nueva cantidad excede el stock, muestra un mensaje de error
                        mensaje = f"Stock insuficiente para '{producto.nombre_producto}'. Solo puedes agregar {producto.stock_actual - cantidad_actual} unidades más."
                    else:
                        # Si hay suficiente stock, actualiza la cantidad en el carrito
                        producto_en_carrito['cantidad'] += cantidad_a_agregar
                        mensaje = f"Producto '{producto.nombre_producto}' actualizado en el carrito."
                else:
                    # Si el producto no está en el carrito, lo agrega con su cantidad
                    producto_data = {
                        'codigo': producto.codigo_producto,
                        'nombre': producto.nombre_producto,
                        'precio_venta': producto.precio_venta,
                        'stock_actual': producto.stock_actual,
                        'cantidad': cantidad_a_agregar
                    }
                    # Agrega el producto al carrito en la sesión
                    request.session['productos_agregados'].append(producto_data)
                    mensaje = f"Producto '{producto.nombre_producto}' añadido con éxito al carrito."

                # Marca la sesión como modificada para guardar los cambios
                request.session.modified = True

        except Producto.DoesNotExist:
            # Si no se encuentra el producto, muestra un mensaje de error
            mensaje = "El producto no existe."

    # Calcula el total del carrito sumando los precios de los productos multiplicados por su cantidad
    total = sum(producto['precio_venta'] * producto['cantidad'] for producto in request.session['productos_agregados'])
    
    # Obtiene los productos agregados del carrito
    productos_agregados = request.session['productos_agregados']
    
    # Renderiza la plantilla 'home.html' pasando el mensaje, los productos en el carrito, el total y los productos encontrados
    return render(request, 'venta/home.html', {
        'mensaje': mensaje,                # Mensaje de éxito o error
        'productos_agregados': productos_agregados,  # Productos en el carrito
        'total': total,                    # Total de la compra
        'productos_encontrados': productos_encontrados  # Resultados de la búsqueda
    })



@login_required  # Se asegura de que solo los usuarios autenticados puedan acceder a esta vista
def gProductos(request):
    """
    Vista para obtener y mostrar todos los productos de la base de datos.

    Esta vista obtiene todos los productos registrados en la base de datos y calcula 
    el total de productos y el precio de costo total utilizando métodos de la clase Producto.
    Luego, renderiza una plantilla con esta información.

    Parámetros:
    - request: objeto HttpRequest que contiene los datos de la solicitud.

    Retorna:
    - Una respuesta renderizada con la lista de productos, el total de productos y el total 
      del precio de costo.
    """
    
    # Obtiene todos los productos de la base de datos
    productos = Producto.objects.all()

    # Llama al método de clase 'contar_productos_totales' para obtener el total de productos
    total_productos = Producto.contar_productos_totales()

    # Llama al método de clase 'sumar_precio_costo_total' para obtener la suma total del precio de costo de los productos
    total_precio_costo = Producto.sumar_precio_costo_total()

    # Renderiza la plantilla 'productos.html' y pasa los productos, total de productos y total de precio de costo
    return render(request, 'producto/productos.html', {
        'productos': productos,                  # Lista de productos para mostrar en la plantilla
        'total_productos': total_productos,      # Total de productos para mostrar en la plantilla
        'total_precio_costo': total_precio_costo # Total de precio de costo de los productos para mostrar en la plantilla
    })



@login_required  # Asegura que solo los usuarios autenticados puedan acceder a esta vista
def crear_producto(request):
    """
    Vista para crear un nuevo producto en la base de datos.

    Esta vista maneja la creación de un nuevo producto a través de un formulario.
    Si el formulario es válido, el producto se guarda en la base de datos y se muestra un mensaje de éxito.
    En caso de error en el formulario, se muestra un mensaje de error.

    Parámetros:
    - request: objeto HttpRequest que contiene los datos de la solicitud.

    Retorna:
    - Una respuesta renderizada con el formulario de creación de producto, o una redirección 
      a la vista 'GestionProductos' si el formulario es válido y el producto es guardado correctamente.
    """
    
    # Si la solicitud es de tipo POST, significa que el formulario fue enviado
    if request.method == 'POST':
        # Se crea una instancia del formulario ProductoForm con los datos del POST
        form = ProductoForm(request.POST)
        
        # Si el formulario es válido (es decir, los datos cumplen con las validaciones)
        if form.is_valid():
            # Guarda el nuevo producto en la base de datos
            form.save()

            # Muestra un mensaje de éxito al usuario
            messages.success(request, 'Producto creado exitosamente.')

            # Redirige a la vista 'GestionProductos' (una vista que lista los productos)
            return redirect('GestionProductos')
        else:
            # Si hubo un error con el formulario, muestra un mensaje de error
            messages.error(request, 'Hubo un error al crear el producto.')
    else:
        # Si la solicitud es GET, simplemente inicializa un formulario vacío
        form = ProductoForm()

    # Renderiza la plantilla 'crear_producto.html' pasando el formulario al contexto
    return render(request, 'producto/crear_producto.html', {'form': form})



@login_required  # Asegura que solo los usuarios autenticados puedan acceder a esta vista
def modificar_producto(request, codigo_producto):
    """
    Vista para modificar un producto existente.

    Esta vista permite modificar un producto, utilizando un formulario prellenado con los datos del producto.
    El código del producto no es editable. Si el formulario es válido, los cambios se guardan en la base de datos.
    En caso de error en el formulario, se muestra un mensaje de error.

    Parámetros:
    - request: objeto HttpRequest que contiene los datos de la solicitud.
    - codigo_producto: código del producto que se va a modificar.

    Retorna:
    - Una respuesta renderizada con el formulario de modificación de producto, o una redirección 
      a la vista 'GestionProductos' si el formulario es válido y el producto es modificado correctamente.
    """
    
    # Obtiene el producto correspondiente al 'codigo_producto' proporcionado en la URL.
    # Si no se encuentra, devuelve un error 404.
    producto = get_object_or_404(Producto, codigo_producto=codigo_producto)

    # Si la solicitud es de tipo POST (cuando el usuario envía el formulario con datos modificados)
    if request.method == 'POST':
        # Se crea una instancia del formulario ProductoForm con los datos del POST y el producto a modificar
        # También se pasa readonly_codigo=True para evitar que el código del producto se pueda modificar.
        form = ProductoForm(request.POST, instance=producto, readonly_codigo=True)

        # Si el formulario es válido (es decir, los datos cumplen con las validaciones)
        if form.is_valid():
            # Guarda los cambios realizados en el producto en la base de datos
            form.save()

            # Muestra un mensaje de éxito al usuario
            messages.success(request, 'Producto modificado exitosamente.')

            # Redirige a la vista 'GestionProductos' (que lista todos los productos)
            return redirect('GestionProductos')
        else:
            # Si hubo un error con el formulario, muestra un mensaje de error
            messages.error(request, 'Hubo un error al modificar el producto.')

    else:
        # Si la solicitud es GET, se inicializa el formulario con los datos del producto actual
        # Y se pasa readonly_codigo=True para que el código del producto no sea editable.
        form = ProductoForm(instance=producto, readonly_codigo=True)

    # Renderiza la plantilla 'modificar_producto.html' pasando el formulario y el producto al contexto
    return render(request, 'producto/modificar_producto.html', {'form': form, 'producto': producto})



@login_required  # Asegura que solo los usuarios autenticados puedan acceder a esta vista
def eliminar_producto(request, codigo_producto):
    """
    Vista para eliminar un producto.

    Esta vista permite eliminar un producto de la base de datos. Si la solicitud es de tipo POST,
    se elimina el producto correspondiente al código proporcionado. Si la solicitud es GET, se muestra
    una página de confirmación antes de proceder con la eliminación.

    Parámetros:
    - request: objeto HttpRequest que contiene los datos de la solicitud.
    - codigo_producto: código del producto que se va a eliminar.

    Retorna:
    - Una redirección a la vista 'GestionProductos' si la eliminación se confirma.
    - Una respuesta renderizada con la página de confirmación si la solicitud es GET.
    """
    
    # Obtiene el producto correspondiente al 'codigo_producto' proporcionado en la URL.
    # Si no se encuentra, devuelve un error 404.
    producto = get_object_or_404(Producto, codigo_producto=codigo_producto)

    # Si la solicitud es de tipo POST (cuando el usuario confirma la eliminación)
    if request.method == 'POST':
        # Elimina el producto de la base de datos
        producto.delete()

        # Redirige a la vista 'GestionProductos' (que lista todos los productos)
        return redirect('GestionProductos')

    # Si la solicitud es GET, renderiza una página de confirmación para eliminar el producto
    return render(request, 'producto/eliminar_producto.html', {'producto': producto})


@login_required  # Asegura que solo los usuarios autenticados puedan acceder a esta vista
def gDepartamentos(request):
    """
    Vista para mostrar las categorías de departamentos.

    Esta vista obtiene todas las categorías de departamentos de la base de datos y las pasa
    a la plantilla 'departamento/departamentos.html' para ser renderizadas.

    Parámetros:
    - request: objeto HttpRequest que contiene los datos de la solicitud.

    Retorna:
    - Una respuesta renderizada con las categorías obtenidas de la base de datos.
    """
    
    # Obtiene todas las categorías de la base de datos
    categoria = Categoria.objects.all()  # 'Categoria' es el modelo que almacena las categorías

    # Renderiza la plantilla 'departamento/departamentos.html' y pasa las categorías al contexto
    return render(request, 'departamento/departamentos.html', {'categoria': categoria})



@login_required  # Asegura que solo los usuarios autenticados puedan acceder a esta vista
def crear_departamentos(request):
    """
    Vista para crear un nuevo departamento.

    Esta vista permite crear un nuevo departamento en la base de datos. Si la solicitud es de tipo
    POST, se procesa el formulario enviado y se guarda la nueva categoría en la base de datos.
    Si la solicitud es de tipo GET, se muestra un formulario vacío para crear un nuevo departamento.

    Parámetros:
    - request: objeto HttpRequest que contiene los datos de la solicitud.

    Retorna:
    - Una respuesta renderizada con el formulario para crear el departamento si la solicitud es GET.
    - Redirige a la vista 'GestionDepartamentos' si el formulario es válido y se guarda el departamento.
    """
    
    # Si el método HTTP es POST, significa que el formulario ha sido enviado
    if request.method == 'POST':
        # Se crea una instancia del formulario 'CategoriaForms' con los datos enviados en el formulario
        form = CategoriaForms(request.POST)
        
        # Si el formulario es válido, se guarda la categoría
        if form.is_valid():
            categoria = form.save(commit=False)  # Se guarda el objeto categoría sin guardarlo aún en la base de datos
            categoria.save()  # Se guarda en la base de datos
            return redirect('GestionDepartamentos')  # Redirige a la vista 'GestionDepartamentos' después de guardar la categoría
    else:
        # Si la solicitud no es POST, simplemente se crea un formulario vacío
        form = CategoriaForms()
    
    # Renderiza la plantilla 'crear_departamentos.html' y pasa el formulario al contexto
    return render(request, 'departamento/crear_departamentos.html', {'form': form})


@login_required  # Asegura que solo los usuarios autenticados puedan acceder a esta vista
def modificar_departamentos(request, categoria_id):
    """
    Vista para modificar el nombre de un departamento existente.

    Esta vista permite modificar el nombre de un departamento ya existente en la base de datos.
    Si la solicitud es de tipo POST, se actualiza el nombre del departamento con los datos enviados.
    Si la solicitud es de tipo GET, se muestra el formulario para modificar la categoría con los datos actuales.

    Parámetros:
    - request: objeto HttpRequest que contiene los datos de la solicitud.
    - categoria_id: el ID del departamento que se desea modificar.

    Retorna:
    - Redirige a la vista 'GestionDepartamentos' después de guardar los cambios en el departamento.
    - Renderiza el formulario para modificar el departamento si la solicitud es GET.
    """
    
    # Se obtiene la categoría con el ID proporcionado en la URL, o se muestra una página de error si no existe
    categoria = get_object_or_404(Categoria, categoria_id=categoria_id)
    
    # Si el método HTTP es POST, significa que se enviaron los datos para modificar la categoría
    if request.method == 'POST':
        # Se obtiene el nuevo nombre del departamento desde el formulario
        nombre = request.POST.get('nombreDepartamentoModificar')
        
        # Se asigna el nuevo nombre a la categoría
        categoria.nombre = nombre
        
        # Se guarda la categoría con el nuevo nombre en la base de datos
        categoria.save()
        
        # Después de guardar los cambios, redirige a la vista 'GestionDepartamentos'
        return redirect('GestionDepartamentos')
    
    # Si no es un método POST, simplemente renderiza el formulario con la categoría actual
    return render(request, 'departamento/modificar_departamentos.html', {'categoria': categoria})



@login_required  # Asegura que solo los usuarios autenticados puedan acceder a esta vista
def eliminar_departamentos(request, categoria_id):
    """
    Vista para eliminar un departamento existente.

    Esta vista permite eliminar un departamento de la base de datos. Si la solicitud es de tipo POST, 
    se elimina el departamento correspondiente al ID proporcionado. Si la solicitud es de tipo GET, 
    se muestra una página de confirmación para la eliminación del departamento.

    Parámetros:
    - request: objeto HttpRequest que contiene los datos de la solicitud.
    - categoria_id: el ID del departamento que se desea eliminar.

    Retorna:
    - Redirige a la vista 'GestionDepartamentos' después de eliminar el departamento.
    - Renderiza una página de confirmación si la solicitud es GET.
    """
    
    # Se obtiene la categoría con el ID proporcionado en la URL, o se muestra una página de error si no existe
    categoria = get_object_or_404(Categoria, categoria_id=categoria_id)
    
    # Si el método HTTP es POST, significa que el usuario ha confirmado la eliminación
    if request.method == 'POST':
        # Se elimina la categoría de la base de datos
        categoria.delete()
        
        # Se muestra un mensaje de éxito para informar al usuario que la categoría fue eliminada correctamente
        messages.success(request, "Categoría eliminada correctamente.")
        
        # Después de eliminar la categoría, redirige a la vista 'GestionDepartamentos'
        return redirect('GestionDepartamentos')
    
    # Si no es un método POST (por ejemplo, si el usuario está viendo la página de confirmación),
    # se renderiza la plantilla 'eliminar_departamentos.html' con la categoría a eliminar.
    return render(request, 'departamento/eliminar_departamentos.html', {'categoria': categoria})


@login_required  # Asegura que solo los usuarios autenticados puedan acceder a esta vista
def productos_asociados(request, categoria_id):
    """
    Vista para mostrar los productos asociados a una categoría específica.

    Esta vista obtiene una categoría por su ID y filtra los productos que están asociados a esa categoría.
    Luego, renderiza una página que muestra la categoría y los productos asociados.

    Parámetros:
    - request: objeto HttpRequest que contiene los datos de la solicitud.
    - categoria_id: el ID de la categoría de la cual se desean obtener los productos asociados.

    Retorna:
    - Renderiza la plantilla 'prod_asociados.html' con los productos asociados a la categoría.
    """
    
    # Se obtiene la categoría con el ID proporcionado en la URL, o se muestra una página de error si no existe
    categoria = get_object_or_404(Categoria, categoria_id=categoria_id)
    
    # Se filtran los productos que pertenecen a esta categoría específica
    productos = Producto.objects.filter(categoria=categoria)
    
    # Se renderiza la plantilla 'prod_asociados.html', pasando la categoría y los productos asociados
    return render(request, 'departamento/prod_asociados.html', {'categoria': categoria, 'productos': productos})


@login_required  # Asegura que solo los usuarios autenticados puedan acceder a esta vista
def gProveedor(request):
    """
    Vista para mostrar la lista de proveedores ordenados por su ID.

    Esta vista obtiene todos los proveedores de la base de datos y los ordena por el campo 'id'.
    Luego, renderiza una página que muestra la lista de proveedores.

    Parámetros:
    - request: objeto HttpRequest que contiene los datos de la solicitud.

    Retorna:
    - Renderiza la plantilla 'proveedores.html' con la lista de proveedores ordenada.
    """
    
    # Se obtienen todos los proveedores y se ordenan por el campo 'id'
    proveedor = Proveedor.objects.order_by('id')
    
    # Se renderiza la plantilla 'proveedores.html', pasando la lista de proveedores al contexto
    return render(request, 'proveedor/proveedores.html', {'proveedor': proveedor})


@login_required  # Asegura que solo los usuarios autenticados puedan acceder a esta vista
def crear_proveedor(request):
    """
    Vista para crear un nuevo proveedor.

    Si la solicitud es de tipo POST, se procesan los datos del formulario para crear un nuevo proveedor.
    Si la solicitud es GET, se muestra un formulario vacío para que el usuario pueda ingresar los datos.

    Parámetros:
    - request: objeto HttpRequest que contiene los datos de la solicitud.

    Retorna:
    - Si la solicitud es POST y el formulario es válido, guarda el proveedor en la base de datos
      y redirige a la vista de gestión de proveedores.
    - Si la solicitud es GET, renderiza un formulario vacío para ingresar los datos del proveedor.
    """
    
    if request.method == 'POST':  # Si la solicitud es de tipo POST (envío del formulario)
        form = ProveedorForm(request.POST)  # Se crea una instancia del formulario con los datos enviados
        if form.is_valid():  # Verifica si los datos del formulario son válidos
            proveedor = form.save(commit=False)  # Guarda el objeto Proveedor, pero no lo guarda en la base de datos aún
            proveedor.save()  # Guarda el proveedor en la base de datos
            return redirect('GestionProveedores')  # Redirige a la página de gestión de proveedores (la lista de proveedores)
    else:
        form = ProveedorForm()  # Si la solicitud es GET, se crea un formulario vacío
    
    # Renderiza la plantilla 'crear_proveedor.html', pasando el formulario al contexto
    return render(request, 'proveedor/crear_proveedor.html', {'form': form})


@login_required  # Asegura que solo los usuarios autenticados puedan acceder a esta vista
def modificar_proveedor(request, id):
    """
    Vista para modificar los datos de un proveedor existente.

    Si la solicitud es de tipo POST, procesa los datos del formulario y guarda los cambios en el proveedor.
    Si la solicitud es GET, muestra el formulario con los datos actuales del proveedor para que el usuario los modifique.

    Parámetros:
    - request: objeto HttpRequest que contiene los datos de la solicitud.
    - id: ID del proveedor a modificar.

    Retorna:
    - Si la solicitud es POST y el formulario es válido, guarda los cambios en el proveedor y redirige
      a la vista de gestión de proveedores.
    - Si la solicitud es GET, renderiza el formulario con los datos actuales del proveedor.
    """
    
    proveedor = get_object_or_404(Proveedor, id=id)  # Obtiene el proveedor con el ID especificado o devuelve un error 404 si no se encuentra
    
    if request.method == 'POST':  # Si la solicitud es de tipo POST (envío del formulario)
        form = ProveedorForm(request.POST, instance=proveedor)  # Crea una instancia del formulario con los datos enviados y el proveedor existente
        if form.is_valid():  # Verifica si los datos del formulario son válidos
            form.save()  # Guarda los cambios realizados en el proveedor
            return redirect('GestionProveedores')  # Redirige a la página de gestión de proveedores (la lista de proveedores)
    else:
        form = ProveedorForm(instance=proveedor)  # Si la solicitud es GET, se crea el formulario con los datos actuales del proveedor
    
    # Renderiza la plantilla 'modificar_proveedor.html', pasando el formulario y los datos del proveedor al contexto
    return render(request, 'proveedor/modificar_proveedor.html', {'form': form, 'proveedor': proveedor})


@login_required  # Asegura que solo los usuarios autenticados puedan acceder a esta vista
def eliminar_proveedor(request, id):
    """
    Vista para eliminar un proveedor.

    Si la solicitud es de tipo POST, elimina el proveedor de la base de datos.
    Si la solicitud es GET, muestra una página de confirmación para que el usuario confirme la eliminación.

    Parámetros:
    - request: objeto HttpRequest que contiene los datos de la solicitud.
    - id: ID del proveedor a eliminar.

    Retorna:
    - Si la solicitud es POST, elimina el proveedor y redirige a la vista de gestión de proveedores.
    - Si la solicitud es GET, renderiza una página de confirmación para la eliminación del proveedor.
    """
    
    proveedor = get_object_or_404(Proveedor, id=id)  # Obtiene el proveedor con el ID especificado o devuelve un error 404 si no se encuentra
    print(f"El proveedor encontrado: {proveedor.id}, {proveedor.nombre},{proveedor.direccion},{proveedor.detalles}.{proveedor.detalles}")
    # Esto imprimirá los detalles del proveedor encontrado en la consola para depuración.

    if request.method == 'POST':  # Si la solicitud es de tipo POST (cuando el usuario confirma la eliminación)
        proveedor.delete()  # Elimina el proveedor de la base de datos
        return redirect('GestionProveedores')  # Redirige a la página de gestión de proveedores después de la eliminación

    # Si la solicitud es GET (cuando el usuario accede para confirmar la eliminación), renderiza la plantilla de confirmación
    return render(request, 'proveedor/eliminar_proveedor.html', {'proveedor': proveedor})


@login_required  # Asegura que solo los usuarios autenticados puedan acceder a esta vista
def gCliente(request):
    """
    Vista para obtener y mostrar todos los clientes.

    Obtiene todos los clientes de la base de datos y los pasa a la plantilla 'clientes.html' para ser mostrados.

    Parámetros:
    - request: objeto HttpRequest que contiene los datos de la solicitud.

    Retorna:
    - Renderiza la plantilla 'clientes.html', pasando todos los clientes obtenidos desde la base de datos como contexto.
    """
    
    clientes = Cliente.objects.all()  # Obtiene todos los clientes de la base de datos
    return render(request, 'cliente/clientes.html', {'clientes': clientes})
    # Renderiza la plantilla 'clientes.html', pasando los clientes obtenidos como contexto


@login_required  # Asegura que solo los usuarios autenticados puedan acceder a esta vista
def crear_cliente(request):
    """
    Vista para crear un nuevo cliente.

    Si la solicitud es de tipo POST, se procesan los datos del formulario para crear un nuevo cliente,
    validarlos y guardarlos en la base de datos. Si hay errores de validación, se muestran al usuario.
    
    Si la solicitud es GET, se muestra un formulario vacío para crear un nuevo cliente.

    Parámetros:
    - request: objeto HttpRequest que contiene los datos de la solicitud.

    Retorna:
    - Si la solicitud es POST y la validación es exitosa, redirige a la vista 'GestionClientes'.
    - Si hay errores de validación, los muestra en la plantilla 'crear_cliente.html'.
    - Si la solicitud es GET, renderiza el formulario vacío de creación de cliente.
    """
    
    if request.method == 'POST':  # Si se recibe una solicitud POST, se procesan los datos del formulario
        # Se crea una nueva instancia de Cliente con los datos enviados desde el formulario
        cliente = Cliente(
            nombre=request.POST.get('nombre'),
            apellido=request.POST.get('apellido'),
            telefono=request.POST.get('telefono'),
            direccion=request.POST.get('direccion'),
            limite_credito=request.POST.get('limite_credito'),
            deuda=request.POST.get('deuda'),
        )

        try:
            cliente.full_clean()  # Valida todos los campos del cliente según las restricciones del modelo
            cliente.save()  # Si la validación es exitosa, guarda el cliente en la base de datos
            return redirect('GestionClientes')  # Redirige a la vista de gestión de clientes
        except ValidationError as e:
            # Si hay errores de validación, se capturan y se devuelven a la vista con los mensajes de error
            return render(request, 'cliente/crear_cliente.html', {'errors': e.message_dict})

    # Si no es una solicitud POST (es una solicitud GET), simplemente renderiza el formulario
    return render(request, 'cliente/crear_cliente.html')


@login_required  # Asegura que solo los usuarios autenticados puedan acceder a esta vista
def modificar_cliente(request, id_cliente):
    """
    Vista para modificar los datos de un cliente existente.

    Si la solicitud es de tipo POST, se procesan los datos del formulario para actualizar
    la información del cliente en la base de datos. Si hay errores de validación, se muestran
    al usuario. Si la solicitud es GET, se muestra el formulario con los datos actuales del cliente.

    Parámetros:
    - request: objeto HttpRequest que contiene los datos de la solicitud.
    - id_cliente: ID del cliente a modificar.

    Retorna:
    - Si la solicitud es POST y los datos son válidos, redirige a la vista 'GestionClientes'.
    - Si hay errores de validación, los muestra en la plantilla 'modificar_cliente.html'.
    - Si la solicitud es GET, renderiza el formulario con los datos actuales del cliente.
    """
    
    # Busca el cliente con el id proporcionado, si no existe, devuelve un error 404
    cliente = get_object_or_404(Cliente, id_cliente=id_cliente)

    if request.method == 'POST':  # Si se recibe una solicitud POST, se procesan los datos del formulario
        # Crea un formulario con los datos enviados en la solicitud POST y la instancia del cliente a modificar
        form = ClienteForm(request.POST, instance=cliente)

        if form.is_valid():  # Si el formulario es válido
            try:
                # Guarda los datos del cliente sin confirmación inmediata (commit=False)
                cliente = form.save(commit=False)
                cliente.full_clean()  # Valida el cliente antes de guardarlo
                cliente.save()  # Guarda el cliente modificado en la base de datos
                return redirect('GestionClientes')  # Redirige a la vista de gestión de clientes
            except ValidationError as e:
                # Si hay un error de validación, se agrega al formulario para mostrarlo al usuario
                form.add_error(None, e)  # Agrega el error general al formulario
    else:
        # Si la solicitud no es POST (es un GET, por ejemplo), se muestra el formulario con los datos del cliente
        form = ClienteForm(instance=cliente)

    # Renderiza la plantilla con el formulario y los datos del cliente
    return render(request, 'cliente/modificar_cliente.html', {'form': form, 'cliente': cliente})


@login_required  # Asegura que solo los usuarios autenticados puedan acceder a esta vista
def eliminar_cliente(request, id_cliente):
    """
    Vista para eliminar un cliente existente.

    Si la solicitud es de tipo POST, se confirma la eliminación del cliente y se elimina de la base de datos.
    Si la solicitud es GET, se muestra una página de confirmación para la eliminación del cliente.

    Parámetros:
    - request: objeto HttpRequest que contiene los datos de la solicitud.
    - id_cliente: ID del cliente a eliminar.

    Retorna:
    - Si la solicitud es POST, el cliente es eliminado y se redirige a la vista 'GestionClientes'.
    - Si la solicitud es GET, se muestra la plantilla de confirmación 'eliminar_cliente.html'.
    """
    
    # Busca el cliente con el id proporcionado, si no existe, devuelve un error 404
    cliente = get_object_or_404(Cliente, id_cliente=id_cliente)

    if request.method == 'POST':  # Si se recibe una solicitud POST (cuando se confirma la eliminación)
        cliente.delete()  # Elimina el cliente de la base de datos
        return redirect('GestionClientes')  # Redirige a la vista de gestión de clientes

    # Si la solicitud es GET (cuando se muestra la confirmación de eliminación), se renderiza la plantilla
    return render(request, 'cliente/eliminar_cliente.html', {'cliente': cliente})


@login_required  # Asegura que solo los usuarios autenticados puedan acceder a esta vista
def abonar_deuda(request, id_cliente):
    """
    Vista para abonar una cantidad a la deuda de un cliente.

    Si la solicitud es de tipo POST, el monto a abonar es procesado, y si es válido, se abona a la deuda del cliente.
    Si la solicitud es GET, se muestra el formulario para ingresar el monto del abono.

    Parámetros:
    - request: objeto HttpRequest que contiene los datos de la solicitud.
    - id_cliente: ID del cliente a quien se le abonará el monto en su deuda.

    Retorna:
    - Si la solicitud es POST y el monto es válido, se abona la deuda y se redirige a la vista 'GestionClientes'.
    - Si la solicitud es POST y el monto no es válido, se muestra un mensaje de error.
    - Si la solicitud es GET, se muestra el formulario para ingresar el monto.
    """
    
    # Busca el cliente con el id proporcionado, si no existe, devuelve un error 404
    cliente = get_object_or_404(Cliente, id_cliente=id_cliente)

    if request.method == 'POST':  # Si se recibe una solicitud POST (cuando el usuario hace el abono)
        try:
            # Intenta obtener el monto a abonar desde el formulario
            monto = int(request.POST.get('monto', 0))  # Convierte el monto a entero

            # Verifica si el monto es válido (mayor a 0)
            if monto <= 0:
                messages.error(request, "El monto debe ser mayor a 0.")  # Mensaje de error si el monto no es válido
            else:
                # Llama al método 'abonar_deuda' del modelo Cliente para reducir la deuda
                cliente.abonar_deuda(monto)
                # Muestra un mensaje de éxito al usuario
                messages.success(request, f"Se abonaron ${monto} a la deuda del cliente.")
                return redirect('GestionClientes')  # Redirige a la vista de gestión de clientes
        except ValueError:
            # Captura el error si el monto no es un número válido
            messages.error(request, "Por favor, ingresa un monto válido.")  # Mensaje de error si hay un problema con la conversión del monto

    # Si la solicitud es GET o si hay un error en la solicitud POST, se renderiza la plantilla
    return render(request, 'cliente/abonar_cliente.html', {'cliente': cliente})


@login_required  # Asegura que solo los usuarios autenticados puedan acceder a esta vista
def aumentar_deuda(request, id_cliente):
    """
    Vista para aumentar la deuda de un cliente.

    Si la solicitud es de tipo POST, el monto a aumentar es procesado y, si es válido, se suma a la deuda del cliente.
    Si la solicitud es GET, se muestra el formulario para ingresar el monto a aumentar.

    Parámetros:
    - request: objeto HttpRequest que contiene los datos de la solicitud.
    - id_cliente: ID del cliente cuya deuda se desea aumentar.

    Retorna:
    - Si la solicitud es POST y el monto es válido, se aumenta la deuda y se redirige a la vista 'GestionClientes'.
    - Si la solicitud es POST y el monto no es válido, se muestra un mensaje de error.
    - Si el aumento de deuda supera el límite de crédito, se muestra un mensaje de error.
    - Si la solicitud es GET, se muestra el formulario para ingresar el monto.
    """
    
    # Busca el cliente con el id proporcionado, si no existe, devuelve un error 404
    cliente = get_object_or_404(Cliente, id_cliente=id_cliente)

    if request.method == 'POST':  # Si se recibe una solicitud POST (cuando el usuario desea aumentar la deuda)
        try:
            # Intenta obtener el monto a aumentar desde el formulario
            monto = int(request.POST.get('monto', 0))  # Convierte el monto a entero

            # Verifica si el monto es válido (mayor a 0)
            if monto <= 0:
                messages.error(request, "El monto debe ser mayor a 0.")  # Mensaje de error si el monto no es válido
            else:
                # Verifica si el cliente tiene un límite de crédito y si el aumento de deuda supera ese límite
                if cliente.limite_credito != -1 and cliente.deuda + monto > cliente.limite_credito:
                    messages.error(request, "El monto a aumentar supera el límite de crédito del cliente.")
                else:
                    # Si el monto es válido y no supera el límite de crédito, se aumenta la deuda
                    cliente.deuda += monto  
                    cliente.save()  # Guarda los cambios en la base de datos
                    messages.success(request, f"Se aumentó ${monto} a la deuda del cliente.")  # Mensaje de éxito
                return redirect('GestionClientes')  # Redirige a la vista de gestión de clientes
        except ValueError:
            # Captura el error si el monto no es un número válido
            messages.error(request, "Por favor, ingresa un monto válido.")  # Mensaje de error si hay un problema con la conversión del monto

    # Si la solicitud es GET o si hay un error en la solicitud POST, se renderiza la plantilla
    return render(request, 'cliente/aumentar_deuda.html', {'cliente': cliente})


@login_required
def agregar_producto(request):
    """
    Vista para agregar productos al carrito de compras (sesión de productos agregados).

    Si la solicitud es de tipo POST, el código o nombre del producto y la cantidad solicitada son procesados.
    Si el producto es encontrado en la base de datos y hay suficiente stock, el producto se agrega a la sesión.
    Si no hay suficiente stock o el producto no existe, se muestra un mensaje de error.

    Parámetros:
    - request: objeto HttpRequest que contiene los datos de la solicitud.

    Retorna:
    - Si la solicitud es POST, redirige a la misma vista con el mensaje de éxito o error y los productos agregados a la sesión.
    - Calcula el total de la venta sumando el precio por cantidad de cada producto agregado.
    """
    
    # Verifica si no existen productos agregados en la sesión y los inicializa como una lista vacía
    if 'productos_agregados' not in request.session:
        request.session['productos_agregados'] = []

    mensaje = None  # Variable para almacenar mensajes de éxito o error
    if request.method == 'POST':  # Verifica si la solicitud es un POST (el usuario ha enviado el formulario)
        producto_input = request.POST.get('producto')  # Obtiene el código o nombre del producto ingresado
        cantidad = int(request.POST.get('cantidad', 1))  # Obtiene la cantidad solicitada (por defecto 1)

        if producto_input:  # Verifica si se ha ingresado un código o nombre de producto
            try:
                # Si el valor ingresado es un número, busca el producto por código
                if producto_input.isdigit():  
                    producto = Producto.objects.get(codigo_producto=producto_input)
                else:
                    # Si no es un número, busca el producto por nombre (con búsqueda parcial)
                    producto = Producto.objects.get(nombre_producto__icontains=producto_input)

                # Verifica si hay suficiente stock para la cantidad solicitada
                if producto.stock_actual >= cantidad:
                    # Si hay stock suficiente, agrega el producto a la sesión
                    producto_data = {
                        'codigo': producto.codigo_producto,
                        'nombre': producto.nombre_producto,
                        'precio_venta': producto.precio_venta,
                        'cantidad': cantidad,
                        'stock_actual': producto.stock_actual
                    }
                    request.session['productos_agregados'].append(producto_data)  # Agrega el producto a la lista de productos en sesión
                    request.session.modified = True  # Marca la sesión como modificada para guardar los cambios

                    # Mensaje de éxito
                    mensaje = f"Producto '{producto.nombre_producto}' agregado con éxito. Cantidad: {cantidad}."
                else:
                    # Mensaje de error si no hay suficiente stock
                    mensaje = f"No hay suficiente stock de '{producto.nombre_producto}' para la cantidad solicitada. Stock disponible: {producto.stock_actual}."

            except Producto.DoesNotExist:
                # Mensaje de error si el producto no existe en la base de datos
                mensaje = "El producto no existe."
        else:
            # Mensaje de error si no se ha ingresado un producto
            mensaje = "Debe ingresar un código o nombre de producto."

    # Calcula el total de la venta sumando el precio * cantidad de cada producto en la lista
    total = sum(producto['precio_venta'] * producto['cantidad'] for producto in request.session['productos_agregados'])
    # Recupera los productos que se han agregado a la sesión
    productos_agregados = request.session['productos_agregados']
    
    # Renderiza la plantilla con los mensajes, los productos agregados y el total de la venta
    return render(request, 'venta/home.html', {'mensaje': mensaje, 'productos_agregados': productos_agregados, 'total': total})

@login_required
def quitar_producto(request, codigo_producto):
    """
    Vista para eliminar un producto del carrito de compras (productos agregados a la sesión).

    Si la lista de productos agregados existe en la sesión, se elimina el producto con el código proporcionado.
    Luego, la sesión se actualiza con la lista de productos sin el producto eliminado.

    Parámetros:
    - request: objeto HttpRequest que contiene los datos de la solicitud.
    - codigo_producto: el código del producto a eliminar de la lista de productos agregados.

    Retorna:
    - Redirige al usuario a la página de inicio (Home) después de eliminar el producto.
    """
    
    # Verifica si existe una lista de productos agregados en la sesión
    if 'productos_agregados' in request.session:
        # Obtiene la lista de productos agregados desde la sesión
        productos = request.session.get('productos_agregados', [])
        
        # Crea una lista con los productos que no coincidan con el código del producto a eliminar
        productos_actualizados = [producto for producto in productos if producto['codigo'] != codigo_producto]
        
        # Actualiza la sesión con la lista de productos actualizada (sin el producto eliminado)
        request.session['productos_agregados'] = productos_actualizados
        request.session.modified = True  # Marca la sesión como modificada para guardar los cambios

    # Redirige al usuario a la página de inicio (Home) después de eliminar el producto
    return redirect('Home')


@login_required
def cancelar_venta(request):
    """
    Vista para cancelar una venta eliminando los productos agregados del carrito de compras.

    Si existen productos agregados en la sesión, se elimina la lista de productos de la sesión y se marca la sesión como modificada para guardar los cambios.

    Parámetros:
    - request: objeto HttpRequest que contiene los datos de la solicitud.

    Retorna:
    - JsonResponse: Un objeto JSON con el estado de la operación (success).
    """
    
    # Verifica si existen productos agregados en la sesión
    if 'productos_agregados' in request.session:
        # Elimina la lista de productos agregados de la sesión
        del request.session['productos_agregados']
        
        # Marca la sesión como modificada para que los cambios se guarden
        request.session.modified = True  

    # Devuelve una respuesta JSON con el estado de la operación
    return JsonResponse({'status': 'success'})


@login_required
def registrar_venta(request):
    """
    Vista para registrar una venta, procesando el formulario y actualizando el stock de los productos.

    Si la solicitud es de tipo POST, procesa los datos del formulario y registra la venta en la base de datos. Además, actualiza el stock de los productos comprados y limpia la lista de productos agregados en la sesión.

    Parámetros:
    - request: objeto HttpRequest que contiene los datos de la solicitud.

    Retorna:
    - Redirect: Redirige a la página de inicio ('Home') si la venta se registra exitosamente.
    - Render: Si la solicitud no es de tipo POST, renderiza la página con un formulario vacío.
    """
    
    # Verifica si la solicitud es de tipo POST (envío de formulario)
    if request.method == 'POST':
        # Se inicializa el formulario con los datos enviados en la solicitud POST
        form = VentaForm(request.POST)
        
        # Si el formulario es válido
        if form.is_valid():
            # Creamos una instancia de la venta, pero sin guardarla todavía
            venta = form.save(commit=False)
            
            # Asignamos la fecha de la venta a la fecha actual
            venta.fecha = timezone.now()
            
            # Calculamos el total de la venta sumando el precio de venta de cada producto multiplicado por la cantidad
            venta.total = sum(
                producto['precio_venta'] * producto['cantidad']
                for producto in request.session.get('productos_agregados', [])
            )
            
            # Asignamos el vendedor como el usuario logueado
            venta.vendedor = request.user
            
            # Guardamos la venta en la base de datos
            venta.save()

            # Actualizamos el stock de los productos que fueron comprados
            for producto_data in request.session['productos_agregados']:
                producto = Producto.objects.get(codigo_producto=producto_data['codigo'])
                
                # Restamos la cantidad de productos comprados del stock actual
                producto.stock_actual -= producto_data['cantidad']
                
                # Guardamos el producto actualizado
                producto.save()

            # Limpiamos la lista de productos agregados en la sesión, ya que la venta ha sido registrada
            request.session['productos_agregados'] = []
            request.session.modified = True

            # Redirigimos al usuario a la página de inicio
            return redirect('Home')

    # Si la solicitud no es de tipo POST, se inicializa un formulario vacío
    else:
        form = VentaForm()

    # Se renderiza la página con el formulario de venta
    return render(request, 'venta/home.html', {'form': form})


@login_required
def historial_ventas(request):
    """
    Vista para mostrar el historial de ventas, incluyendo una lista de ventas, el total de ventas realizadas y la suma de los totales.

    Obtiene todas las ventas ordenadas por fecha (de la más reciente a la más antigua) y calcula el número total de ventas y la suma de los montos de todas las ventas.

    Parámetros:
    - request: objeto HttpRequest que contiene los datos de la solicitud.

    Retorna:
    - Render: Renderiza la plantilla 'historial_ventas.html' con la lista de ventas, el número total de ventas y la suma de los totales de las ventas.
    """
    
    # Obtiene todas las ventas ordenadas por fecha en orden descendente (de la más reciente a la más antigua)
    ventas = Venta.objects.all().order_by('-fecha')
    
    # Llama a un método personalizado para contar el número total de ventas
    contar_ventas = Venta.contar_ventas()
    
    # Llama a un método personalizado para calcular la suma de los totales de todas las ventas
    sumar_totales = Venta.sumar_totales()
    
    # Renderiza la plantilla 'historial_ventas.html' con los datos obtenidos
    return render(request, 'venta/historial_ventas.html', {
        'ventas': ventas,              # Lista de ventas para mostrar en el historial
        'contar_ventas': contar_ventas,  # Número total de ventas realizadas
        'sumar_totales': sumar_totales,  # Suma total de los montos de todas las ventas
    })

def generar_reporte_ventas(request):
    """
    Vista para generar un reporte de ventas en formato .txt basado en una fecha seleccionada.

    La vista permite al usuario seleccionar una fecha a través de un formulario. Filtra las ventas realizadas en esa fecha
    y genera un archivo de texto con el historial detallado de ventas, incluyendo información como ID de venta, cliente, 
    método de pago, vendedor y el total. El archivo se ofrece como descarga al usuario.

    Parámetros:
    - request: objeto HttpRequest que contiene los datos de la solicitud.

    Flujo:
    1. Se obtiene la fecha seleccionada desde el formulario enviado mediante POST.
    2. Se valida el formato de la fecha.
    3. Se filtran las ventas realizadas en la fecha proporcionada.
    4. Se genera el contenido del archivo .txt con los datos de las ventas.
    5. Se retorna el archivo como respuesta para su descarga.
    6. Si no es una solicitud POST, se renderiza una plantilla para seleccionar la fecha.

    Retorna:
    - HttpResponse: Un archivo de texto con las ventas del día seleccionado para su descarga.
    - Render: Renderiza la plantilla 'generar_reporte.html' si no se ha enviado el formulario.
    """
    
    if request.method == 'POST':
        # Obtiene la fecha seleccionada del formulario en formato de cadena
        fecha_str = request.POST.get('fecha')
        
        try:
            # Convierte la fecha proporcionada a un objeto de tipo date
            fecha_seleccionada = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            # Si la fecha no es válida, retorna un mensaje de error
            return HttpResponse("Fecha inválida", status=400)
        
        # Filtra las ventas realizadas en la fecha seleccionada
        ventas_del_dia = Venta.objects.filter(fecha__date=fecha_seleccionada)

        # Genera el contenido del archivo .txt
        contenido = "Historial de Ventas del Día\n"
        contenido += f"Fecha: {fecha_seleccionada}\n"
        contenido += "====================================\n"
        
        for venta in ventas_del_dia:
            contenido += (
                f"ID: {venta.id_venta}, "
                f"Cliente: {venta.id_cliente}, "
                f"Método de Pago: {venta.metodo_pago}, "
                f"Vendedor: {venta.vendedor}, "
                f"Total: ${venta.total}\n"
            )
        
        contenido += "====================================\n"
        contenido += f"Total de Ventas: {ventas_del_dia.count()}\n"
        contenido += f"Suma Total: ${sum(venta.total for venta in ventas_del_dia)}\n"

        # Devuelve el archivo .txt como respuesta para su descarga
        response = HttpResponse(contenido, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename=ventas_{fecha_seleccionada}.txt'
        return response

    # Renderiza la plantilla para seleccionar una fecha si no es una solicitud POST
    return render(request, 'venta/generar_reporte.html')

