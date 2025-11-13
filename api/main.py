"""
FastAPI Application for Trading Monitor Dashboard
Provides REST API endpoints for analysis decisions, trades, orders, and positions
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from api.routers import analysis, trades, orders, positions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Trading Monitor API",
    description="REST API for Trading Monitor Dashboard",
    version="1.0.0"
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(trades.router, prefix="/api/trades", tags=["trades"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
app.include_router(positions.router, prefix="/api/positions", tags=["positions"])


@app.get("/")
async def root():
    """Root endpoint - API status"""
    return {
        "name": "Trading Monitor API",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8085)
