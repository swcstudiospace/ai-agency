# Shared memory (Anda / KIP)

- Brain DB: Anda Cognitive Nexus (:8091) with dual-write local SQLite
- Ops metrics: separate analytics store
- Capsules: `kip_memory/data/` with KIP_ICP_MODE=local by default
- Daily timer: agency-brain-daily.timer

Linear is the ops work log; KIP is the knowledge graph.
