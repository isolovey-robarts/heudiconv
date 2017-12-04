ORG=akhanf
NAME=heudiconv
VERSION = 0.4.1

DOCKER_NAME=$(ORG)/$(NAME):$(VERSION)
DOCKER_LATEST=$(ORG)/$(NAME):latest
SINGULARITY_NAME=$(ORG)_$(NAME)_$(VERSION)

BUILD_DIR=~/singularity
REMOTE_BUILD_DIR=~/graham/singularity

build:
	rm -f $(BUILD_DIR)/$(SINGULARITY_NAME).img
	sudo singularity build $(BUILD_DIR)/$(SINGULARITY_NAME).img Singularity | tee build_$(SINGULARITY_NAME).log
	cp -vf $(BUILD_DIR)/$(SINGULARITY_NAME).img $(REMOTE_BUILD_DIR)/$(SINGULARITY_NAME).img


sandbox:
	sudo singularity build --sandbox sandbox_$(SINGULARITY_NAME) Singularity | tee -a sandbox_$(SINGULARITY_NAME).log
	
docker_build: 
	echo "Dockerfile not up to date"
#	docker build -t $(DOCKER_NAME) --rm .


docker_tag_latest:
	echo "Dockerfile not up to date"
#	docker tag $(DOCKER_NAME) $(DOCKER_LATEST)

docker_push:
	echo "Dockerfile not up to date"
#	docker push $(DOCKER_NAME)

docker_push_latest:
	echo "Dockerfile not up to date"
#	docker push $(DOCKER_LATEST)

docker_run:
	echo "Dockerfile not up to date"
#	docker run --rm -it $(DOCKER_NAME) /bin/bash	

docker_last_built_date:
	echo "Dockerfile not up to date"
#	docker inspect -f '{{ .Created }}' $(DOCKER_NAME)

