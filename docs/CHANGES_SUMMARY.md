# Port Configuration Changes

## ✅ Changes Applied

The RiskLens platform has been reconfigured to run on **port 5155** instead of the default 5173.

### Files Modified

1. **docker-compose.yml**
   - Frontend port mapping: `5155:5173`
   - Backend CORS environment: `http://localhost:5155`

2. **backend/app/core/config.py**
   - Default CORS origins: `["http://localhost:5155", "http://localhost:3000"]`

3. **.env.example**
   - CORS_ORIGINS: `http://localhost:5155,http://localhost:3000`

### New Documentation

4. **PORT_CONFIGURATION.md** - Detailed port setup guide
5. **QUICK_REFERENCE.txt** - Quick reference card with all URLs and commands

## 🌐 New Access URLs

- **Frontend:** http://localhost:5155 ← **CHANGED**
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

## 🚀 How to Run

```bash
# 1. Configure
cp .env.example .env

# 2. Start everything
docker-compose up --build

# 3. Seed data (in new terminal)
docker-compose exec backend python -m app.db.seed

# 4. Access at http://localhost:5155
# Login: demo@RiskLens.ai / RiskLens2024
```

## ✅ What Still Works

Everything works exactly the same, just on a different port:

- ✅ 3D Galaxy Map
- ✅ Live Risk Feed
- ✅ Natural Language Query
- ✅ Dashboard & Charts
- ✅ Timeline Explorer
- ✅ PDF Reports
- ✅ Authentication
- ✅ WebSocket live updates
- ✅ All API endpoints

## 📝 Important Notes

1. **CORS is configured** - Backend accepts requests from port 5155
2. **Docker mapping** - Container still runs on 5173 internally, mapped to 5155 externally
3. **No code changes needed** - All internal references remain the same
4. **Documentation updated** - All guides now reference port 5155

## 🔍 Verification

After starting with `docker-compose up --build`:

1. ✅ Frontend loads: http://localhost:5155
2. ✅ Backend health: http://localhost:8000/health
3. ✅ API docs: http://localhost:8000/docs
4. ✅ Can login and use all features

## 📚 Updated Documentation

All documentation files have been updated where necessary:
- START_HERE.md
- QUICKSTART.md
- README.md
- SETUP.md
- RUN_INSTRUCTIONS.txt
- New: PORT_CONFIGURATION.md
- New: QUICK_REFERENCE.txt

## 🎯 Ready to Go!

The platform is ready to run on port 5155. Just follow the commands above and you'll be up and running in 5 minutes.

**Quick Reference:** See QUICK_REFERENCE.txt for all URLs and commands.

