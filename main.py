# main.py
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from supabase import create_client, Client
import os

app = FastAPI(title="Pulse Gaming API")

# Configurações do CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurações Supabase
SUPABASE_URL = "https://wyogajwawndmwpoltxez.supabase.co".strip()
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind5b2dhandhd25kbXdwb2x0eGV6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODk1ODUyOTUsImV4cCI6MjEwNTE2MTI5NX0.FCDMZEleH2G6VBEqXNfvI2GcpVI5_FRGxjRk8HXrv70".strip()
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- MODELOS DE DADOS ---

class Player(BaseModel):
    nickname: str
    real_name: str
    role: str
    team_tier: str
    photo_url: str

class Recruitment(BaseModel):
    name: str
    nickname: str
    discord: str
    rank: str
    line: str
    experience: str

class Feedback(BaseModel):
    user_name: Optional[str] = "Anônimo"
    rating: int
    category: str
    message: str

class LoginRequest(BaseModel):
    username: str
    password: str

# --- AVALIAÇÃO DA PENEIRA ---
class ApproveCandidate(BaseModel):
    photo_url: str
    role: str

# --- SEGURANÇA ---
ADMIN_TOKEN = "pulse-secure-token-1232134123"

def verify_token(authorization: str = Header(None)):
    if authorization != f"Bearer {ADMIN_TOKEN}":
        raise HTTPException(status_code=401, detail="Não autorizado")
    return True

# --- ROTAS PÚBLICAS ---

@app.get("/players")
async def get_players():
    response = supabase.table("players").select("*").execute()
    return response.data

@app.post("/recruitment")
async def post_recruitment(data: Recruitment):
    response = supabase.table("recruitment").insert(data.dict()).execute()
    return {"status": "success", "data": response.data}

@app.post("/feedback")
async def post_feedback(data: Feedback):
    response = supabase.table("feedbacks").insert(data.dict()).execute()
    return {"status": "success", "data": response.data}

# --- ROTAS ADMIN ---

@app.post("/admin/login")
async def admin_login(data: LoginRequest):
    if data.username == "binho" and data.password == "1232134123":
        return {"token": ADMIN_TOKEN}
    raise HTTPException(status_code=401, detail="Credenciais inválidas")

@app.get("/admin/recruits")
async def get_recruits(authenticated: bool = Depends(verify_token)):
    response = supabase.table("recruitment").select("*").execute()
    return response.data

@app.post("/admin/players")
async def add_player(data: Player, authenticated: bool = Depends(verify_token)):
    response = supabase.table("players").insert(data.dict()).execute()
    return response.data

@app.delete("/admin/players/{player_id}")
async def delete_player(player_id: int, authenticated: bool = Depends(verify_token)):
    supabase.table("players").delete().eq("id", player_id).execute()
    return {"status": "deleted"}

@app.delete("/admin/recruits/{candidate_id}")
async def reject_candidate(candidate_id: int, authenticated: bool = Depends(verify_token)):
    supabase.table("recruitment").delete().eq("id", candidate_id).execute()
    return {"status": "deleted"}

@app.post("/admin/recruits/{candidate_id}/approve")
async def approve_candidate(candidate_id: int, data: ApproveCandidate, authenticated: bool = Depends(verify_token)):
    # 1. Busca os dados da candidatura
    res = supabase.table("recruitment").select("*").eq("id", candidate_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Candidato não encontrado")
    
    cand = res.data[0]
    
    # 2. Insere na tabela de atletas oficiais (players)
    player_data = {
        "nickname": cand["nickname"],
        "real_name": cand["name"],
        "role": data.role,
        "team_tier": cand["line"],
        "photo_url": data.photo_url
    }
    supabase.table("players").insert(player_data).execute()
    
    # 3. Remove da peneira
    supabase.table("recruitment").delete().eq("id", candidate_id).execute()
    return {"status": "approved"}

# --- ROTAS DE FEEDBACK (ADMIN) ---

@app.get("/admin/feedbacks")
async def get_admin_feedbacks(authenticated: bool = Depends(verify_token)):
    response = supabase.table("feedbacks").select("*").order("created_at", desc=True).execute()
    return response.data

@app.delete("/admin/feedbacks/{feedback_id}")
async def delete_admin_feedback(feedback_id: int, authenticated: bool = Depends(verify_token)):
    supabase.table("feedbacks").delete().eq("id", feedback_id).execute()
    return {"status": "deleted"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)