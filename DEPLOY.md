# S.A.R.A.L. production deploy checklist

Primary product = **Next.js on Vercel**. Secondary demo = **Streamlit on HF Spaces**.
Both talk to one **hosted FastAPI**.

```
Vercel (web/)  ──BFF──►  FastAPI host  ◄──HTTP──  HF Streamlit
                              │
                     Pinecone + Groq (+ optional Redis)
```

## 1. Host FastAPI (Render)

1. Push this repo (or connect GitHub) to [Render](https://render.com).
2. Use Blueprint [`render.yaml`](render.yaml) **or** create a Web Service:
   - Dockerfile: `Dockerfile.api`
   - Health check: `/`
3. Set env vars:
   - `GROQ_API_KEY` (required)
   - `PINECONE_API_KEY` (required)
   - `PINECONE_INDEX_NAME` = `bharat-schemes`
   - `SARAL_CORS_ORIGINS` = `https://<your-vercel-app>.vercel.app,https://manavv007-s-a-r-a-l.hf.space`
   - `SARAL_API_KEY` (optional but recommended)
   - `REDIS_URL` (optional)
4. Confirm `GET https://<api-host>/` → `{"status":"online"}`.

Local Docker smoke test:

```bash
docker build -f Dockerfile.api -t saral-api .
docker run --rm -p 8000:8000 --env-file .env -e PORT=8000 saral-api
```

## 2. Deploy Next.js (`web/`) to Vercel

1. Import the GitHub repo in Vercel.
2. **Root Directory** = `web`
3. Env:
   - `BACKEND_URL` = `https://<api-host>/api/v1`
   - `SARAL_API_KEY` = same as API (if auth enabled)
4. Deploy → open the HTTPS URL on your phone.
5. Officer mic: open chat → officer → **Allow microphone** (requires HTTPS; LAN `http://IP` will not prompt).

## 3. Hugging Face Streamlit Space

1. Space secrets / variables:
   - `SARAL_API_BASE_URL` or `BACKEND_URL` = `https://<api-host>/api/v1`
   - `SARAL_API_KEY` = same as API (if auth enabled)
2. Re-enable GitHub Action **Sync to Hugging Face** (was paused while developing).
3. Sync workflow now excludes `web/`, skill packs, scraper, PDFs and installs slim [`requirements-spaces.txt`](requirements-spaces.txt) as Space `requirements.txt`.
4. Manual sync: Actions → Sync to Hugging Face → **Run workflow**.

## 4. Phone mic verify

| URL | Expected |
|-----|----------|
| `https://<vercel>/` | Allow microphone dialog works |
| `http://192.168.x.x:3000` | HTTPS warning; no prompt |

Typing always remains as fallback.
