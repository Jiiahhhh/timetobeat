from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, status
import os
import asyncio

router = APIRouter()

CRON_SECRET = os.getenv("CRON_SECRET")

def run_sync_task():
    try:
        print("[CRON] Starting games and trailers sync task...")
        
        # 1. Run Game Seeder
        from seed.seed_games import seed
        print("[CRON] Phase 1: Running Game Seeder...")
        # Since seed is async, run it in a new event loop for this background thread
        asyncio.run(seed(test_mode=False))
        print("[CRON] Phase 1 Complete: Game Seeding finished.")
        
        # 2. Run Trailer Fetcher
        from seed.fetch_trailers import run as run_trailers
        print("[CRON] Phase 2: Running Trailer Fetcher...")
        run_trailers(test_mode=False)
        print("[CRON] Phase 2 Complete: Trailer Fetching finished.")
        
        print("[CRON] Background sync task completed successfully.")
    except Exception as e:
        print(f"[CRON ERROR] Sync task failed: {e}")

@router.post("/cron/sync")
def trigger_sync(background_tasks: BackgroundTasks, authorization: str = Header(None)):
    if not CRON_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CRON_SECRET is not configured in backend environment"
        )
        
    expected_header = f"Bearer {CRON_SECRET}"
    if authorization != expected_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing cron secret"
        )
        
    # Since run_sync_task is a sync 'def' function, FastAPI automatically runs it in a threadpool,
    # preventing it from blocking the main FastAPI asyncio event loop.
    background_tasks.add_task(run_sync_task)
    return {"status": "sync_initiated"}
