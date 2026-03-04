# Production Deployment

The app runs on a VPS via **Portainer** with **Cloudflare Tunnel** for HTTPS on `bingo.kalinets.com`.

## 1. Create Cloudflare Tunnel

1. Go to [Cloudflare Zero Trust](https://one.dash.cloudflare.com/) → Networks → Tunnels
2. Create a tunnel named `bingo`
3. Copy the tunnel token
4. Add a public hostname:
   - **Domain:** `bingo.kalinets.com`
   - **Service:** `http://app:5001`

## 2. Deploy via Portainer

1. Stacks → Add Stack → Git Repository
2. Set repository URL and compose path: `docker-compose.prod.yml`
3. Under **Environment variables**, add:
   - `TUNNEL_TOKEN` = `<paste token from step 1>`
   - `RP_ID` = `bingo.kalinets.com` (must match the domain users access)
   - `RP_ORIGIN` = `https://bingo.kalinets.com` (full origin with protocol)

> **Note:** Passkeys are bound to the RP ID (domain). Credentials registered on `localhost` won't work on `bingo.kalinets.com` and vice versa.
4. Deploy the stack

## 3. Verify

```bash
curl https://bingo.kalinets.com
```
