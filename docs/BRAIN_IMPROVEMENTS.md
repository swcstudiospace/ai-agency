# Brain improvements (implemented)

1. **Dual-write** local SQLite + remote Anda DB (`kip_memory/dual_write.py`)
   - formation, remember, skill proposals, sleep consolidations
   - Auto-registers concept + proposition types on nexus
2. **Dual recall** merges remote `SEARCH CONCEPT` + local graph
3. **Daily maintenance** `scripts/daily_brain_maintenance.py`
   - systemd timer `agency-brain-daily.timer` @ 06:15 UTC
   - sleep + `kip_export_icp` capsule + analytics heartbeat
4. **Analytics store** `tools/analytics_store.py` (SQLite; optional Postgres DSN)
   - toolbelt `analytics` on all agents via factory
5. **Cloud** `KIP_ICP_MODE=local|ic_oss|s3|canister`

## Verify
```bash
systemctl is-active anda-nexus agency-brain-daily.timer
PYTHONPATH=. ANDA_NEXUS_URL=http://127.0.0.1:8091 python -m scripts.daily_brain_maintenance
```
