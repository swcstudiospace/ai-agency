# Control planes

| Service | Port | Role |
|---------|------|------|
| AgentOS | 7777 | Agents, teams, workflows, MCP |
| Drop gateway | 7788 | Hybrid MCP+ACP, Linear, CoT x GoT |
| Hermes bridge | 7790 | Browser/skills/memory/KIP |
| Anda nexus | 8091 | Cognitive Nexus |

```bash
curl -s http://127.0.0.1:7777/health
curl -s http://127.0.0.1:7788/health
curl -s http://127.0.0.1:7790/health
systemctl status drop-gateway hermes-bridge anda-nexus
```
