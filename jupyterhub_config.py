import os
# Jalar el 'config object'.
c = get_config()

# IP donde JupyterHub escucha.
c.JupyterHub.hub_ip = '0.0.0.0'

# JupyterHub IP (o hostname) de JupyterHub vista desde la red de docker.
# Aca le ponemos 'jupyterhub', justo como en el ./docker-compose.yml.
c.JupyterHub.hub_connect_ip = 'jupyterhub'

## The public facing URL of the whole JupyterHub application.
#  
#          This is the address on which the proxy will bind.
#          Sets protocol, ip, base_url
#c.JupyterHub.bind_url = 'http://jupyterhub:8000'

## The URL on which the Hub will listen. This is a private URL for internal
#  communication. Typically set in combination with hub_connect_url. If a unix
#  socket, hub_connect_url **must** also be set.
#  
#  For example:
#  
#      "http://127.0.0.1:8081"
#      "unix+http://%2Fsrv%2Fjupyterhub%2Fjupyterhub.sock"
#  
#  .. versionadded:: 0.9
#  Default: ''
#c.JupyterHub.hub_bind_url = 'http://jupyterhub:8081'

# Grant admin users permission to access single-user servers.
c.JupyterHub.admin_access = True

# The class to use for spawning single-user servers.
# c.JupyterHub.spawner_class = 'dockerspawner.DockerSpawner'
c.JupyterHub.spawner_class = 'docker'
#from jupyterhub.spawner import SimpleLocalProcessSpawner ###PARA PRUEBAS###
#c.JupyterHub.spawner_class = SimpleLocalProcessSpawner

# Optionally set a global password that all users must use
# c.DummyAuthenticator.password = "your_password"

c.DockerSpawner.image = os.environ['LOCAL_NOTEBOOK_IMAGE']
# JupyterHub requires a single-user instance of the Notebook server, so we
# default to using the `start-singleuser.sh` script included in the
# jupyter/docker-stacks *-notebook images as the Docker run command when
# spawning containers.  Optionally, you can override the Docker run command
# using the DOCKER_SPAWN_CMD environment variable.
spawn_cmd = os.environ.get('DOCKER_SPAWN_CMD', "start-singleuser.sh")
c.DockerSpawner.extra_create_kwargs.update({ 'command': spawn_cmd })

# Connect containers to this Docker network
network_name = os.environ['DOCKER_NETWORK_NAME']
#c.DockerSpawner.use_internal_ip = True
c.DockerSpawner.use_internal_hostname = True
#c.DockerSpawner.hub_ip_connect='jupyterhub'
c.DockerSpawner.network_name = network_name
# Pass the network name as argument to spawned containers
c.DockerSpawner.extra_host_config = { 
    'network_mode': network_name,
    "volume_driver": "local" 
}
# Additional args to pass for container create
# c.DockerSpawner.extra_create_kwargs = {}

# Crear servidores
c.JupyterHub.allow_named_servers = True
c.DockerSpawner.name_template = '{imagename}-{username}-{servername}'

# NO LE MUEVAS ACA #
# Explicitly set notebook directory because we'll be mounting a host volume to
# it.  Most jupyter/docker-stacks *-notebook images run the Notebook server as
# user `jovyan`, and set the notebook directory to `/home/jovyan/work`.
# We follow the same convention.
notebook_home = os.environ.get('DOCKER_NOTEBOOK_DIR') # Normalmente '/home/jovyan/work'
shared_dir = os.environ.get('DOCKER_NOTEBOOK_SHARED_DIR') #Normalmente '/shared-data'
shared_data_vol = os.environ.get('SHARED_DATA_VOLUME') #, jupyterhub-shared-data
c.DockerSpawner.notebook_dir = '/' #notebook dir

# Mount the real user's Docker volume on the host to the notebook user's
# notebook directory in the container
c.DockerSpawner.volumes = {
        'jupyterhub-user-{username}': {
		'bind':notebook_home,
		'mode':'rw'
	},
        shared_data_vol : {
		'bind':shared_dir,
		'mode':'rw'
	}
}

#c.DockerSpawner.extra_create_kwargs.update({ 'volume_driver': 'local' })

# Remove containers once they are stopped
c.DockerSpawner.remove = True
# For debugging arguments passed to spawned containers
c.DockerSpawner.debug = True

## Timeout (in seconds) to wait for spawners to initialize
#  Checking if spawners are healthy can take a long time if many spawners are
#  active at hub start time.
#  
#  If it takes longer than this timeout to check, init_spawner will be left to
#  complete in the background and the http server is allowed to start.
#  
#  A timeout of -1 means wait forever, which can mean a slow startup of the Hub
#  but ensures that the Hub is fully consistent by the time it starts responding
#  to requests. This matches the behavior of jupyterhub 1.0.
#  
#  .. versionadded: 1.1.0
#  Default: 10
c.JupyterHub.init_spawners_timeout = -1

# Tornado settings - allow all origins
origin = '*'
c.JupyterHub.tornado_settings = {
    'headers': {
    'Access-Control-Allow-Origin': origin,
   }
}
c.Spawner.args = [f'--NotebookApp.allow_origin={origin}']
c.NotebookApp.allow_origin = '*'

## File in which to store the cookie secret.
#  Default: 'jupyterhub_cookie_secret'
cookie_secret_path = os.environ.get('JUPYTERHUB_COOKIE_PATH')
c.JupyterHub.cookie_secret_file = os.path.join(cookie_secret_path,
    'jupyterhub_cookie_secret')

### Authenticator

##Dummy Authenticator (para pruebas)##
#from jupyterhub.auth import DummyAuthenticator
#c.JupyterHub.authenticator_class = DummyAuthenticator

## Native Authenticator
import nativeauthenticator

c.JupyterHub.authenticator_class = 'nativeauthenticator.NativeAuthenticator'
c.JupyterHub.template_paths = ["{}/templates/".format(os.path.dirname(nativeauthenticator.__file__))]
c.Authenticator.check_common_password = True
c.Authenticator.minimum_password_length = 10
c.Authenticator.allowed_failed_logins = 3
c.Authenticator.ask_email_on_signup = True
#c.Authenticator.allow_2fa = False
c.Authenticator.open_signup = True

## Set of users that will have admin rights on this JupyterHub.
c.Authenticator.admin_users = set(os.environ.get('ADMIN_USERS').split(',')) #ponerlos entre comillas, separados por comas
c.Authenticator.allowed_users = set(os.environ.get('ALLOWED_USERS').split(',')) #ponerlos entre comillas, separados por comas

## Native Authenticator path for database
jh_data_dir=os.environ.get('DATA_VOLUME_CONTAINER')
c.Authenticator.firstuse_db_path = os.path.join(jh_data_dir,
    'passwords.dbm')
