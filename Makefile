include .env

.DEFAULT_GOAL=build

network:
	@docker network inspect ${DOCKER_NETWORK_NAME} >/dev/null 2>&1 || docker network create ${DOCKER_NETWORK_NAME}

volumes:
	@docker volume inspect ${DATA_VOLUME_HOST} >/dev/null 2>&1 || docker volume create --name ${DATA_VOLUME_HOST}
	@docker volume inspect ${SHARED_DATA_VOLUME} >/dev/null 2>&1 || docker volume create --name ${SHARED_DATA_VOLUME}

pull:
	docker pull ${DOCKER_NOTEBOOK_IMAGE}

notebook_image: pull singleuser/Dockerfile
	cp requirements.txt ./singleuser
	docker build -t ${LOCAL_NOTEBOOK_IMAGE} \
	--build-arg JUPYTERHUB_VERSION=${JUPYTERHUB_VERSION} \
	--build-arg DOCKER_NOTEBOOK_IMAGE=${DOCKER_NOTEBOOK_IMAGE} \
        --build-arg DOCKER_NOTEBOOK_SHARED_DIR=${DOCKER_NOTEBOOK_SHARED_DIR} \
	./singleuser
	rm ./singleuser/requirements.txt

build: network volumes
	docker compose build \
	--build-arg CONFIGPROXY_AUTH_TOKEN=$(openssl rand -hex 32) \
	--build-arg JUPYTERHUB_VERSION=${JUPYTERHUB_VERSION} \
	--build-arg JUPYTERHUB_CONFIG_PATH=${JUPYTERHUB_CONFIG_PATH}

.PHONY: network volumes pull notebook_image build
