# Deploy AIOps Platform (Docker)

Everything is already configured. You only need Docker Desktop.

## Start (easiest)

1. Open **Docker Desktop** and wait until it says "Running".
2. Double-click **`start.bat`** in this folder.

   Or in PowerShell:

   ```powershell
   cd D:\Projects\aiops-platform\deployment
   .\start.ps1
   ```

3. Open **http://localhost** in your browser.
4. **Register** a new account (or sign in if you already have one).

## Stop

Press `Ctrl+C` in the terminal, or:

```powershell
docker compose down
```

## URLs

| Service | URL |
|---------|-----|
| Web UI | http://localhost |
| API docs | http://localhost:8000/docs |
| Health | http://localhost:8000/health |

## Config file

`deployment/.env` is already set up for local use. You do **not** need to edit it unless you want email or OpenAI later.
