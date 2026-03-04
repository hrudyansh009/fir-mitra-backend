# app/main.py
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.any_rag import AnyIndex
from app.pipelines.krupaya_tapasa import krupaya_tapasa_pipeline


# IMPORTANT:
# Replace this backend with your real vector store backend.
# It must return docs containing meta.text_mr / meta.text_en (recommended).
class DummyBackend:
    def search(self, query: str, k: int = 7, filters=None):
        return [
            (
                0.92,
                {
                    "id": "scst_section_10",
                    "text": "",  # keep empty if you use meta fields
                    "meta": {
                        "section_key": "scst_section_10",
                        "type": "scst",
                        "title_mr": "अनुसूचित जाती/जमातीबाबत सार्वजनिक अपमान (उदाहरण शीर्षक)",
                        "text_mr": "उदा: सार्वजनिक ठिकाणी जातिवाचक शिवीगाळ/अपमान केल्यास संबंधित कलम लागू होऊ शकते.",
                        "title_en": "Public insult related to SC/ST (example title)",
                        "text_en": "Example: Public caste-based insult/abuse may attract this section.",
                    },
                },
            ),
            (
                0.71,
                {
                    "id": "11",
                    "text": "",
                    "meta": {
                        "section_key": "scst_section_11",
                        "type": "scst",
                        "title_mr": "धमकी/दहशत निर्माण (उदाहरण शीर्षक)",
                        "text_mr": "उदा: पीडिताला धमकी देणे/दबाव टाकणे यासंबंधित संकेत आढळल्यास हे कलम सूचित होऊ शकते.",
                        "title_en": "Threat / intimidation (example title)",
                        "text_en": "Example: Threatening or intimidating the victim may attract this section.",
                    },
                },
            ),
        ]


backend = DummyBackend()
any_index = AnyIndex(backend=backend)

app = FastAPI(title="FIR_AI", version="5.1.0")

# CORS: allow local dev + your deployed Vercel frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Local dev
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        # Deployed frontend
        "https://fir-mitra-alpha.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TapasaRequest(BaseModel):
    text: str = Field(..., min_length=1)
    k: int = Field(7, ge=1, le=50)
    lang: str = Field("mr")  # "mr" or "en"


@app.get("/health")
def health():
    return {"status": "ok", "version": app.version}


@app.post("/krupaya_tapasa")
def krupaya_tapasa(req: TapasaRequest):
    lang = req.lang.lower().strip()
    if lang not in {"mr", "en"}:
        lang = "mr"
    return krupaya_tapasa_pipeline(text=req.text, any_index=any_index, k=req.k, lang=lang)