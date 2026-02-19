"""
RAG Customer Support Backend - Flask Application Entry Point
"""
import logging
import os
from flask import Flask
from flask_cors import CORS

from api.documents import documents_bp
from api.search import search_bp
from api.rag import rag_bp
from services.faiss_service import FAISSService
from config import get_config


def create_app(config_name: str = None) -> Flask:
    """Application factory - creates and configures the Flask app."""
    app = Flask(__name__)

    # Load config
    cfg = get_config(config_name or os.getenv("FLASK_ENV", "production"))
    app.config.from_object(cfg)

    # ── Logging ──────────────────────────────────────────────────────────────
    logging.basicConfig(
        level=getattr(logging, app.config["LOG_LEVEL"]),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting RAG Customer Support API (env=%s)", config_name)

    # ── CORS ─────────────────────────────────────────────────────────────────
    CORS(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=True,
    )

    # ── Security headers (production) ─────────────────────────────────────
    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        return response

    # ── Warm-up FAISS on startup to avoid cold-start latency ─────────────
    with app.app_context():
        try:
            faiss_svc = FAISSService()
            faiss_svc.load_or_create_index()
            app.extensions["faiss_service"] = faiss_svc
            logger.info("FAISS index ready (size=%d)", faiss_svc.index.ntotal)
        except Exception as exc:
            logger.warning("FAISS warm-up skipped: %s", exc)

    # ── Register blueprints ───────────────────────────────────────────────
    app.register_blueprint(documents_bp, url_prefix="/api/documents")
    app.register_blueprint(search_bp,    url_prefix="/api/search")
    app.register_blueprint(rag_bp,       url_prefix="/api/rag")

    # ── Health endpoint ───────────────────────────────────────────────────
    @app.get("/health")
    def health():
        return {"status": "ok", "service": "rag-support-api"}

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=os.getenv("FLASK_ENV") == "development",
    )
