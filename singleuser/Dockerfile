ARG DOCKER_NOTEBOOK_IMAGE
FROM $DOCKER_NOTEBOOK_IMAGE

# Ambientación a nivel SO
USER root
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && apt-get -yq dist-upgrade \
    && apt-get install -yq --no-install-recommends \
## Soporte para Octave
    octave \
## Soporte para Sagemath
    sagemath sagemath-jupyter \
## Soporte para JAVA (Py(Spark))
    default-jdk \
## Misceláneo
    gnuplot ghostscript \
## Para control de accesos de directorios (grupos, usuarios)
    acl \
## Limpieza
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

#Ambientación de SageMath
# RUN bash /usr/share/sagemath/bin/sage-env

# Soporte para rust
#RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \
#    | sh -s -- -y \
#    && source "${HOME}"/.cargo/env \
#    && rustup component add rust-src \
#    && cargo install evcxr_jupyter \
#    && evcxr_jupyter --install 

USER $NB_UID
#RUN source "${HOME}"/.cargo/env

# Instalaciones adicionales con pip
ARG JUPYTERHUB_VERSION

WORKDIR $HOME
COPY ./requirements.txt ./
RUN pip install --no-cache -r requirements.txt

ENV JUPYTERHUB_HOST='jupyterhub'

# Instalar jupyterlab mas extensiones
RUN jupyter serverextension enable --py jupyterlab --sys-prefix

# Instalar SageMath como un nuevo kernel
# ENV SAGE_ROOT='/usr/bin/sage'
# RUN find / -name share/kernels -type d
# RUN sage -sh -c 'ls -d ${SAGE_ROOT}/share/jupyter/kernels/sagemath'
# RUN jupyter kernelspec install --user $(sage -sh -c 'ls -d ${SAGE_ROOT}/share/jupyter/kernels/sagemath')

# Crear symlynk para documentacion de sagemath (y ahorrar 2GB)
# RUN ln -s $(sage -sh -c 'ls -d ${SAGE_ROOT}/share/jupyter/kernels/sagemath') ${HOME}/.local/share/jupyter
# RUN jupyter nbextension install --py jupyter-resource-usage --sys-prefix
# RUN jupyter nbextension enable --py jupyter-resource-usage --sys-prefix

# Creación de directorios faltantes
USER root
ARG DOCKER_NOTEBOOK_SHARED_DIR
ENV DOCKER_NOTEBOOK_SHARED_DIR=$DOCKER_NOTEBOOK_SHARED_DIR
RUN mkdir "${DOCKER_NOTEBOOK_SHARED_DIR}"
RUN chown -R :"${NB_UID}" "${DOCKER_NOTEBOOK_SHARED_DIR}"

# Cambiar permisos de grupo
RUN chmod -R a+rws "${DOCKER_NOTEBOOK_SHARED_DIR}"

# Permisos por defecto para nuevos archivos: group-writable
# RUN setfacl -dR a::rwx "${DOCKER_NOTEBOOK_SHARED_DIR}"

# Limpieza e instalaciones adicionales
RUN mamba install --quiet --yes \
    'octave_kernel' \
    'tensorflow' \
    'psycopg2' \
    && mamba clean --all -f -y \
    && fix-permissions "${CONDA_DIR}" \
    && fix-permissions "/home/${NB_USER}"

USER $NB_UID
