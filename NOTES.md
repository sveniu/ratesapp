# Notes on the solution

The application description in `README.md` makes a few assumptions and
glosses over some details:

## Infrastructure as code

With "infrastructure as code", I understand infrastructure to include
everything from networking to compute instances, storage, policies and
databases. In this task, deployment details like scaling and resource limits
are relevant infrastructure components, and should thus be codified.

However, I have stopped after pushing the container image, opting to not have
any deployment details in the code repo. At that point, automatic triggers
should pick up the image and continue with deployment. My first choice here
would be Spinnaker, a deployment tool that gives both developers and
ops a flexible and robust interface for making and monitoring deployments.

For base infrastructure, I would use a tool like Terraform and keep at least
the staging and production environments fully codified – dev/sandbox
environments can be a bit more loosely defined. Fully defined base
infrastructure makes sense in many ways, not least when it comes to disaster
recovery.
  
## Deploying containers

I don't have direct experience with neither Docker swarm nor Kubernetes, but
understand the concepts. So the deployment descriptions in `README.md` are
quite vague, also because I think deployments should be handled separately
from the application code by specialized tools. I tried to highlight some of
the general aspects around container deployments instead of including
howto-style commands needed to set up a cluster.

Setup and maintenance of a container cluster is an exercise in itself, and
while it is entirely doable, my vote goes to using cloud providers that makes
the base cluster controllers available for you to use.

## Extended service

### System design

![Diagram](https://github.com/sveniu/ratesapp/raw/master/diagram.png)

A setup with a read/write database master and one or more read replicas
across availability zones and regions, can provide a good starting point for
a system that can scale out read capacity while being resilient to failure;
each database instance (writer, read replicas) can be set up with multi-AZ
failover. These are AWS terms, but the concept is the same across any kind of
infrastructure.

It is assumed that the database is shared between the ingest and data serving
processes, so that heavy ingests don't directly affect the serving
application. They may affect the database, and thus indirectly the
application; see below.

In the spirit of micro services, each service should "own" its state, so you
could say that the "rates" service should have a single interface towards
other services and the world, and handle its state (database) internally. The
ingest system would then send updates to the rates service instead of
directly to the database. This may or may not be a good idea here, but can at
least be taken into consideration.

### Identifying bottlenecks

Monitoring should start with getting as many useful metrics exported as
possible, from all components of the system. Assuming PostgreSQL databases,
these are easily instrumented and provide details on CPU, memory, disk and
network usage, connection counts, replication lag, queries, vacuums, etc.

From the ingest system and serving application, they would typically have
default instrumentation around CPU, memory, disk and network utilization.
They should preferably also have custom metrics that are either graphed
directly, or made part of a deeper insight with application performance
monitoring tools.

As the load grows, baseline thresholds will be hit and alarms triggered. With
suitable graphing tools, it is easy to correlate events between metrics and
systems, to identify what's causing the bottlenecks.

### Addressing bottlenecks

Depending on the bottleneck, it can normally be addressed by two main
approaches: Vertical scaling, for example by adding more CPU, memory and
disk; or horizontal scaling, by increasing the number of components in the
system, such as application containers.

Horizontal scaling should be preferred, but it's not always easy to do. A
common example is monolithic SQL databases that keep growing and more
CPU/memory/disk is thrown at the problem. Read replicas take you only so far
if the bottleneck is on the write side. Introducing sharding can be an
option, or even looking at entirely different data stores.

## Additional questions

### Large batches

The batch updates, like any other part of the system, should be designed to
scale horizontally. In practice, this means that the batches must be allowed
to be split into smaller pieces. Smaller batches means you can scale the
ingest system horizontally as well. The ingest system needs to track batch
progress, so that failed ones can be retried.

It sounds odd that batch updates have a requirement for processing time,
unless they are taking unreasonable amounts of time to complete – that is,
the updates can't keep up with the external ingest rate. Even billions of
updates shouldn't take much time to ingest into a reasonably scaled
PostgreSQL instance. Index updates might be a tricky challenge here, though,
and needs careful consideration.

### Code updates

As described earlier, deployment tooling can make code deploys work well
without any adverse effect on production traffic. Both the ingest and data
serving application can use the same mechanism.

Common deployment strategies include blue/green, where the new cluster takes
over 100% of the traffic (of course with connection draining for the old
cluster in the load balancer), leaving the old cluster available for quick
rollback. Other strategies can gradually introduce nodes from the new
cluster, with various levels of checking to see that it performs as it
should, before continuing towards 100% replacement of the old cluster nodes.

All of this can be automated to get to the level of full continuous
deployment.

Developers should be empowered to trigger and track their own deployments.

### Scaling

As earlier, a good deployment tool takes care of this. The application code
and build remain the same. Deploying into an environment can be done by
either configuring the scaling per environment, per application; or simply
copying the scaling that's used for the soon-to-be-upgraded cluster.

Automatic scaling must be used in production, but can also be useful in
staging and development.

The production database would be kept at the same scale continuously, but it
can be deployed as a less powerful (and cheaper) setup in the other
environments.