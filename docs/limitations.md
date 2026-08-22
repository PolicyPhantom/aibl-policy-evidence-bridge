# Limitations

This repository is a deterministic reference prototype for one small policy-to-execution boundary. It is not production-ready and does not establish legal compliance, safety, effectiveness, or empirical validity.

v0.1.2 intentionally excludes:

- graphical UI or REST API;
- database, cloud deployment, Docker, or Kubernetes;
- production authentication, authorization infrastructure, IAM, or OAuth;
- live LLM integration or automatic policy generation, approval, amendment, or migration;
- real CRM, audit repository, robot, or other production connector;
- ROS 2, MCP, plugin, vector-database, or benchmark architecture;
- large-scale datasets, statistical evaluation, or model comparison;
- production telemetry, enterprise observability, high availability, or scalability work;
- automatic suspension detection;
- automated legal or regulatory compliance determination.

Authority, evidence, destinations, operating conditions, execution, and operational-state transitions are all fixture-driven or mock-only. The narrow policy schema supports only the two frozen rule shapes required by the scenarios; it is not a general policy language.

The executable policy has `effective_from` but no `effective_until` field or policy-expiry semantics in this prototype. Decision IDs use a 12-hex-character SHA-256 prefix; they are deterministic prototype identifiers, not audit-grade globally collision-resistant identifiers.

Human and institutional responsibility remains outside the prototype. Before public release, the project owner must also select a license; the absence of a `LICENSE` file grants no implied license.
