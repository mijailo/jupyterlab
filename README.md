# Nginx + Jupyterhub + Dockerspawner

> **Referencias**
> - [Repo de `sglyon`](https://github.com/sglyon/jupyterhub-docker-compose).
> - [Este tutorial](https://hands-on.cloud/docker-how-to-setup-jupyter-behind-nginx-proxy/) de Andrei Maksimov.
> - [Esta ambientación](https://medium.com/quaintitative/jupyter-notebook-on-aws-with-nginx-4326e2122096) de **Jupyterhub+Nginx** en AWS.
> - [Esta](https://jupyter-docker-stacks.readthedocs.io/en/latest/using/selecting.html#jupyter-datascience-notebook) documentación sobre los `single-user-notebooks`.
> - [Esta](https://www.domysee.com/blogposts/reverse-proxy-nginx-docker-compose) entrada sobre un proxy inverso con **Docker Compose+Nginx**.
> - [Tutorial](https://nedjalkov-ivan-j.medium.com/jupyter-lab-behind-a-nginx-reverse-proxy-the-docker-way-8f8d825a2336) sobre **Jupyterlab+Nginx+Docker**.
> - [Tutorial](https://kinow.github.io/jupyterhub/installation-guide-hard.html) sobre **JupyterHub+JupyterLab** utilizando ambientes virtuales de **Python**.
> - [Instalación de docker-compose en `CentOS`](https://serverspace.io/support/help/how-to-install-docker-on-centos-8/).
> - [Docker for developers](https://www.packtpub.com/product/docker-for-developers/9781789536058)

La instalación elegida consta del [jupyter/datascience-notebook](https://github.com/jupyter/docker-stacks/tree/master/datascience-notebook) lanzado por [**JupyterHub**](https://jupyterhub.readthedocs.io/en/latest/)+[**Dockerspawner**](https://jupyterhub-dockerspawner.readthedocs.io/en/latest/api/index.html), detrás de un proxy inverso [**nginx**](https://jupyterhub.readthedocs.io/en/stable/reference/config-proxy.html). Todo se organiza/aisla a través de [**Docker-compose**](https://docs.docker.com/compose/)

De acuerdo con [esta documentación](https://jupyterhub.readthedocs.io/en/latest/), **JupyterHub** está compuesto por:

1. Un _Hub_ (_tornado process_), el _corazón_ de JupyterHub;
2. Un _proxy http_ configurable (_node-http-proxy_), que recibe las peticiones del navegador del cliente.
  * Este funciona detrás de [nginx](https://omarghader.github.io/docker-compose-nginx-tutorial).
3. Varios servidores mono-usuario de Jupyter notebook (Python/Ipython/tornado) monitoreados por _Spawners_.
  * Aquí se utiliza [`docker-spawner`](https://jupyterhub-dockerspawner.readthedocs.io/en/latest/install.html).
4. Una clase de autenticación que administra la forma en que los usuarios acceden al sistema.
  * Acá se utiliza [`native-authenticator`](https://native-authenticator.readthedocs.io/en/latest/quickstart.html).

## Estructura del repositorio

```sh
./
├── certs ## Debe existir, pero no lo incluí por razones de seguridad.
│   ├── dhparam.pem
│   ├── nginx-selfsigned.crt
│   └── nginx-selfsigned.key
├── docker-compose.yml ## Interacción entre Nginx, Jupyterhub y las redes/volúmenes de Docker.
├── Dockerfile.jupyterhub ## Adaptación de una imagen Docker de Jupyterhub.
├── .env ## Variables de ambientación.
├── .gitignore
├── jupyterhub_config.py ## Parámetros de configuración para Jupyterhub.
├── Makefile ## Archivo para ambientar.
├── nginx.conf ## Configuración del proxy inverso Nginx.
├── README.md
├── requirements.txt
├── singleuser
│   └── Dockerfile ## Adaptación de una imagen Docker para los "single-user notebooks".
└── tests ## Carpeta con archivos de referencia y de prueba.
    └── nginx_test.conf
```

Las adaptaciones principales dentro de los cuadernillos (_notebooks_) de **Jupyter** son:

1. Disponibilidad de `psycopg2`, [`koalas`+`pyspark`](https://koalas.readthedocs.io/en/latest) y [`bokeh`](https://docs.bokeh.org/en/latest/index.html).
2. Inclusión de las siguientes [extensiones](https://jupyterlab.readthedocs.io/en/stable/user/extensions.html) de [**Jupyterlab**](https://github.com/jupyterlab/jupyterlab):
   * [@jupyter-server/resource-usage](https://github.com/jupyter-server/jupyter-resource-usage)
   * [ipympl](https://github.com/matplotlib/ipympl)
   * [Language Server Protocol integration for Jupyter(Lab)](https://github.com/jupyter-lsp/jupyterlab-lsp)
   * [Jupyter Bokeh](https://www.npmjs.com/package/@bokeh/jupyter_bokeh)
   * [jupyterlab-drawio](https://github.com/QuantStack/jupyterlab-drawio)
   * [jupyterlab_execute_time](https://github.com/deshaw/jupyterlab-execute-time)
   * [plotly](https://plotly.com/python/)
> **Notas**: 
> 1. Ver los archivos `./Dockerfile.jupyterhub` y `./singleuser/Dockerfile`.
> 2. En **JupyterLab** >= 3 s necesario y suficiente utilizar `pip install <extensión>`.
> 3. Para la extensión **jupyterlab_execute_time**, debe activarse la opción `cell timing` en el _notebook_ vía `Settings->Advanced Settings Editor->Notebook: {"recordTiming": true}`. Esto es una configuración de metadatos, y no una del plugin (que solamente muestra este dato).

## Ambientación, preparación y alta de las aplicaciones

### Creación del directorio con llaves de encriptación, certificado y parámetros de Diffie-Helman - SSL

> **Nota**: Ver [esta](https://jupyterhub.readthedocs.io/en/stable/reference/config-proxy.html) referencia.

1. Crear carpetita:
```sh
mkdir certs
```
2. Generar parámetros [Diffie-Helman](https://en.wikipedia.org/wiki/Diffie%E2%80%93Hellman_key_exchange).
```sh
openssl dhparam -out ./certs/dhparam.pem 4096
```
3. Generar [par llave+certificado autofirmado](https://www.digitalocean.com/community/tutorials/how-to-create-a-self-signed-ssl-certificate-for-nginx-on-centos-7):
```sh
sudo openssl req -x509 -nodes -days 2000 -newkey rsa:2048 -keyout ./certs/nginx-selfsigned.key -out ./certs/nginx-selfsigned.crt
```

### Creación y verificación de contenedores

1. Correr el archivo `Makefile`, que crea/valida contenedores (i.e. jalar imágenes (luego construirlas + adaptarlas), verificar existencia de volúmenes y redes):

```sh
sudo make notebook_image
sudo make build
```

2. Dar de alta los servicios de forma persistente:

```sh
sudo docker-compose up -d
```
> **Nota**: Este comando puede correrse sin el _flag_ `-d` aprovechando una terminal virtual de `tmux`.

### Registro de Kernels

- [SageMath](https://doc.sagemath.org/html/en/installation/launching.html)
- [Octave](https://github.com/rubenv/jupyter-octave)

## Conexión al Hub

Para conectarse al **JupyterHub** desde un equipo local, es necesario:
1. Conectarse a la VPN de la ubicación del servidor remoto.
2. Poner en la barra de direcciones de un navegador de Internet la dirección: `https://<IP_servidorRemoto>:9090/` (ver archivos `nginx.conf` y `docker-compose.yml`).
> **Nota**: En el equipo local (Linux), puede modificarse el archivo `/etc/hosts` para añadir la entrada:
> ```config
> <IP> <alias_1> ... <alias_n>
> #Por ejemplo:
> #231.567.32.1 compu_remota.unam.mx compu_chingona
> ```
3. Aceptar el riesgo advertido por el navegador.
4. Ser feliz.

## Otras notas

- Para depurar la computadora de imágenes, volúmenes etc. puede usarse el siguiente comando:
```sh
sudo docker system prune -a
```
- Para hacer referencia al _host_ desde la red de **Docker**, se puede añadir la llave `extra_hosts` a `docker-compose.yml` con el resultado de:
```sh
ifconfig enp2s0f0 | grep inet | grep -v inet6 | awk '{print $2}'
#El resultado de este comando es <IP_servidorRemoto>
```
- Para cambiar la ruta de trabajo, configuración y almacenamiento de **Docker**, pueden seguirse los tutoriales [de aquí](https://evodify.com/change-docker-storage-location/) y [de acá](https://linuxconfig.org/how-to-move-docker-s-default-var-lib-docker-to-another-directory-on-ubuntu-debian-linux). En mi caso, los arreglos consistieron en:
   - Parar los procesos asociados a **Docker**:
```sh
   sudo systemctl stop docker.socket
   sudo systemctl stop docker.service
```
   - Editar la línea 14 de `/lib/systemd/system/docker.service`, para mover los archivos a `/ubicacion/chingona/docker`.
   - Editar el archivo `/etc/docker/daemon.json`
   - Copiar el contenido de `/var/lib/docker` a `/ubicacion/chingona/docker`:
```sh
   sudo rsync -aqxP /var/lib/docker/ /ubicacion/chingona/docker
```
   - Recargar la configuración para `systemd` de **Docker**:
```sh
   sudo systemctl daemon-reload
   sudo systemctl start docker
```
   - Ver que todo jale en el nuevo directorio:
```sh
   ps aux | grep -i docker | grep -v grep
```
   - En `CentOS 8`, es necesario [configurar el firewall](https://www.reddit.com/r/CentOS/comments/dze8kj/docker_w_centos_8_and_a_firewall/). Para ello:
      * Ejecutar:
```sh
       firewall-cmd --get-active-zones
```
      * Poner la interfaz `docker0` en la zona _confiable_:
```sh
      sudo firewall-cmd --zone=trusted --change-interface=docker0
      sudo firewall-cmd --zone=trusted --add-masquerade --permanent
      sudo firewall-cmd --reload
```
   - En `CentOS 7`, [la configuración](https://unix.stackexchange.com/questions/199966/how-to-configure-centos-7-firewalld-to-allow-docker-containers-free-access-to-th#225845) es análoga:
```sh
   sudo firewall-cmd --permanent --zone=trusted --change-interface=docker0
   sudo firewall-cmd --reload
```
- Cuando se haga un cambio a las `iptables` (ver por ejemplo `/etc/resolv.conf`) del servidor, debe reiniciarse el `docker engine` con:
```sh
sudo service docker restart
```
o bien:
```sh
sudo systemctl restart docker
``` 
Ver [esta](https://stackoverflow.com/questions/52815784/python-pip-raising-newconnectionerror-while-installing-libraries#52819120) referencia.
Además, es importante editar la [_DNS resolution_](https://stackoverflow.com/questions/62968807/dns-resolution-in-docker-containers#62988037) en `/etc/docker/daemon.json`:
```json
{
  "data-root":"/ubicacion/chingona/",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "5"
  },
  "dns": [
    "8.8.8.8"
  ]
}
```
(Ver [esta](https://medium.com/@faithfulanere/solved-docker-build-could-not-resolve-archive-ubuntu-com-apt-get-fails-to-install-anything-9ea4dfdcdcf2) referencia.)
También en el archivo mencionado se puede definir cuál es la ubicación de los datos y metadatos de los contenedores.

## Otros tweaks

- [`jupyterhub-idle-culler`](https://pypi.org/project/jupyterhub-idle-culler/). Puede servir [este](https://github.com/jupyterhub/jupyterhub-idle-culler) repositorio.
