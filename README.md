# Application stack

A simple stack for an application serving port-to-port shipping rates. The
stack consists of a Flask application serving an API, backed by a PostgreSQL
database.

## Prerequisites

The following tools must be installed:

* [Docker](https://docs.docker.com/install/)
* [Docker Compose](https://docs.docker.com/compose/install/#install-compose)

Docker (meaning the container engine) is everywhere and has a vast and easy
to use ecosystem. The only viable competitor is rkt by CoreOS, which has much
less traction but can certainly be worth a closer look.

Docker Compose is a good tool for running a stack of containers locally, and
its configuration can be easily deployed to a Docker swarm. While not
necessarily the first choice for production deployments, it's a great choice
for local development.

See below for further thoughts and examples of container deployments.

## Deploying locally

To run the stack:

``` sh
docker-compose up
```

To build and run the database on its own:

``` sh
docker build -f Dockerfile-db -t ratesdb:dev .
docker run --network host ratesdb:dev
```

To build and run the application on its own:

``` sh
docker build -f Dockerfile-api -t ratesapi:dev .
docker run --network host ratesapi:dev
```

## Deploying to non-local targets

Once a container image is built, any kind of Docker-compatible orchestration
approach can be used to deploy the image. The image first has to be published
to a repository that can be accessed by the orchestration tool. In this case,
it is natural to use something like `docker-compose push` to push the images
to a central repo.

### Single vs multiple images

It's arguably a bad idea to use a locally built image as the "golden" image
that's pushed upstream with the goal of reaching production; it should rather
be built in a CI/CD pipeline to avoid any dependency found only on the
developer's system. Once the image is built in the pipeline, it should be
deployable, without any change, to any environment, be it a sandbox, staging
or production – its runtime environment decides how it behaves (see below).

While desirable, it might be tricky to supply a full environment to run
images locally. If needed, multiple Dockerfiles or [Docker Compose
files](https://docs.docker.com/compose/extends/#example-use-case) provides a
way to build an image for local-only testing, and another in the CI/CD
pipeline for actual deployment to test/staging/prod environments.

### Decoupling from environment, configuration and state

There should be some level of decoupling of the container image build process
and its environment. For example, a database password should not be kept in
the application's code repository. The same goes for less sensitive data like
usernames and hostnames of other services. Using the orchestration tool's
environment variable handling should be preferred whenever possible.

The same goes for configuration. For example, deployment details like CPU,
memory and replication counts can be decoupled from the application repo, so
that things like scaling, re-deploys and rollbacks can be done independently
of the application's code.

Containers should aim to be stateless and thus easily replaceable. For
example, the rates database is a good candidate for being separated out to
its own resource. While you can always have containers with persistent data
volumes, this complicates deployments and concurrency.

### Example targets

Good deployment targets for the rates application can be a Docker swarm or
Kubernetes, including any cloud provider with support for those interfaces.
AWS ECS is also a viable option, with its [Docker Compose-like
interface](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/cmd-ecs-cli-compose.html)

With Docker Compose and Swarm, the `docker-compose.yml` file can be augmented
with [service
details](https://docs.docker.com/get-started/part5/#add-a-new-service-and-redeploy)
around replica counts, resource limits and restart policies before being
[deployed to
Swarm](https://docs.docker.com/engine/swarm/stack-deploy/#deploy-the-stack-to-the-swarm)
with a command like `docker stack deploy -c docker-compose.yml ratesapp`.

With Kubernetes, a simple pod can be launched with `kubectl create -f pod-rates.yaml`, with a manifest similar to the Docker Compose file:

``` text
apiVersion: v1
kind: Pod
metadata:
  name: rates
spec:
  containers:
  - name: api
    image: ratesapi:dev
    ports:
    - containerPort: 3000
  - name: db
    image: ratesdb:dev
    ports:
    - containerPort: 5432
```

Going further, a [deployment
manifest](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#creating-a-deployment)
can be used to control deployed resources like replica counts, CPU/memory
limits, etc.