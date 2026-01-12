"""APScheduler configuration and job definitions for automated data collection."""
import logging
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

# Initialize scheduler with Pacific timezone
scheduler = BackgroundScheduler(timezone='America/Los_Angeles')


def init_scheduler():
    """Initialize and start the scheduler with daily collection job.

    This function is called during FastAPI app startup to configure
    the APScheduler BackgroundScheduler with a daily cron job that
    triggers data collection at 7:30 AM Pacific time.

    The scheduler runs in a separate thread and does not block the
    main FastAPI event loop.

    Raises:
        Exception: If scheduler fails to initialize
    """
    try:
        # Import here to avoid circular imports
        from app.api.collection import trigger_daily_collection

        # Add daily collection job (7:30 AM Pacific)
        scheduler.add_job(
            func=trigger_daily_collection,
            trigger=CronTrigger(hour=7, minute=30),
            id='daily_collection',
            name='Daily trend data collection at 7:30 AM Pacific',
            replace_existing=True,
            max_instances=1,  # Prevent overlapping runs
            misfire_grace_time=900  # Allow 15 min late starts
        )

        scheduler.start()

        logger.info(
            "APScheduler initialized successfully",
            extra={
                "event": "scheduler_init",
                "scheduled_jobs": [
                    {
                        "id": job.id,
                        "name": job.name,
                        "next_run": job.next_run_time.isoformat() if job.next_run_time else None
                    }
                    for job in scheduler.get_jobs()
                ]
            }
        )
    except Exception as e:
        logger.exception(
            "Failed to initialize APScheduler",
            extra={
                "event": "scheduler_init_error",
                "error": str(e)
            }
        )
        raise


def shutdown_scheduler():
    """Gracefully shut down the scheduler.

    This function is called during FastAPI app shutdown to ensure
    all running jobs complete before the application exits.
    """
    try:
        scheduler.shutdown(wait=True)
        logger.info("APScheduler shut down gracefully")
    except Exception as e:
        logger.error(f"Error shutting down scheduler: {e}")


# Register shutdown handler for process exit
atexit.register(lambda: scheduler.shutdown(wait=False) if scheduler.running else None)
