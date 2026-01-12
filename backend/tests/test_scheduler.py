"""Unit tests for APScheduler and scheduled collection functions."""
import pytest
import logging
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta, date
from uuid import uuid4

from app.scheduler import init_scheduler, shutdown_scheduler, scheduler
from app.api.collection import (
    trigger_daily_collection,
    trigger_daily_collection_retry,
    increment_failure_count,
    reset_failure_count,
    check_failure_alert_threshold
)
from app.models.data_collection import DataCollection


@pytest.fixture
def mock_scheduler():
    """Mock APScheduler for testing."""
    with patch('app.scheduler.scheduler') as mock:
        mock.running = True
        mock.get_jobs.return_value = []
        mock.start = MagicMock()
        mock.add_job = MagicMock()
        mock.shutdown = MagicMock()
        yield mock


def test_scheduler_initialization(mock_scheduler):
    """Test that scheduler initializes with daily job."""
    with patch('app.scheduler.scheduler', mock_scheduler):
        init_scheduler()

        # Verify add_job called with correct parameters
        mock_scheduler.add_job.assert_called_once()
        call_args = mock_scheduler.add_job.call_args

        assert call_args.kwargs['id'] == 'daily_collection'
        assert call_args.kwargs['max_instances'] == 1
        assert call_args.kwargs['replace_existing'] is True
        assert mock_scheduler.start.called


def test_scheduler_shutdown():
    """Test that scheduler shuts down gracefully."""
    mock = MagicMock()
    mock.shutdown = MagicMock()

    with patch('app.scheduler.scheduler', mock):
        shutdown_scheduler()

        mock.shutdown.assert_called_once_with(wait=True)


@pytest.mark.asyncio
async def test_trigger_daily_collection_prevents_duplicates(db_session):
    """Test that scheduled job skips if collection in progress."""
    # Create existing in-progress collection
    existing = DataCollection(
        id=uuid4(),
        status="in_progress",
        started_at=datetime.now(timezone.utc)
    )
    db_session.add(existing)
    await db_session.commit()

    # Mock run_collection to track calls
    with patch('app.api.collection.run_collection', new=AsyncMock()) as mock_run:
        with patch('app.api.collection.get_db', return_value=iter([db_session])):
            await trigger_daily_collection()

            # Should NOT start new collection
            mock_run.assert_not_called()


@pytest.mark.asyncio
async def test_trigger_daily_collection_success(db_session):
    """Test successful scheduled collection."""
    with patch('app.api.collection.run_collection', new=AsyncMock()) as mock_run:
        with patch('app.api.collection.reset_failure_count', new=AsyncMock()) as mock_reset:
            with patch('app.api.collection.get_db', return_value=iter([db_session])):
                await trigger_daily_collection()

                # Should run collection
                assert mock_run.called

                # Should reset failure count
                assert mock_reset.called


@pytest.mark.asyncio
async def test_retry_logic_on_failure(db_session):
    """Test that retry is scheduled on failure."""
    with patch('app.api.collection.run_collection', new=AsyncMock(side_effect=Exception("API error"))):
        with patch('app.api.collection.increment_failure_count', new=AsyncMock()):
            with patch('app.api.collection.check_failure_alert_threshold', new=AsyncMock()):
                with patch('app.scheduler.scheduler') as mock_scheduler:
                    mock_scheduler.add_job = MagicMock()

                    with patch('app.api.collection.get_db', return_value=iter([db_session])):
                        await trigger_daily_collection()

                        # Verify retry job was added
                        assert mock_scheduler.add_job.called
                        call_args = mock_scheduler.add_job.call_args
                        assert call_args.kwargs['id'] == 'daily_collection_retry'
                        assert call_args.kwargs['func'] == trigger_daily_collection_retry


@pytest.mark.asyncio
async def test_failure_count_tracking(db_session):
    """Test failure count increments and resets."""
    # Increment failure count
    await increment_failure_count(db_session)

    # Verify count
    from app.models.api_quota_usage import ApiQuotaUsage
    from sqlalchemy import select

    result = await db_session.execute(
        select(ApiQuotaUsage).where(ApiQuotaUsage.api_name == 'scheduler_failures')
    )
    usage = result.scalar_one()
    assert usage.units_used == 1
    assert usage.date == date.today()

    # Increment again
    await increment_failure_count(db_session)
    await db_session.refresh(usage)
    assert usage.units_used == 2

    # Reset
    await reset_failure_count(db_session)
    result = await db_session.execute(
        select(ApiQuotaUsage).where(ApiQuotaUsage.api_name == 'scheduler_failures')
    )
    usage = result.scalar_one_or_none()
    assert usage is None


@pytest.mark.asyncio
async def test_alert_threshold_2_days(db_session, caplog):
    """Test alert triggered after 2 consecutive days of failures."""
    from app.models.api_quota_usage import ApiQuotaUsage

    # Add failures for today and yesterday
    today = date.today()
    yesterday = today - timedelta(days=1)

    db_session.add(ApiQuotaUsage(api_name='scheduler_failures', date=today, units_used=1))
    db_session.add(ApiQuotaUsage(api_name='scheduler_failures', date=yesterday, units_used=1))
    await db_session.commit()

    # Check alert threshold
    with caplog.at_level(logging.CRITICAL):
        await check_failure_alert_threshold(db_session)

    # Verify critical log message
    assert "ALERT: Scheduled collection failed 2 days in a row" in caplog.text


@pytest.mark.asyncio
async def test_no_alert_with_single_day_failure(db_session, caplog):
    """Test no alert triggered with only today's failure."""
    from app.models.api_quota_usage import ApiQuotaUsage

    # Add failure only for today
    today = date.today()
    db_session.add(ApiQuotaUsage(api_name='scheduler_failures', date=today, units_used=1))
    await db_session.commit()

    # Check alert threshold
    with caplog.at_level(logging.CRITICAL):
        await check_failure_alert_threshold(db_session)

    # Verify NO critical log message
    assert "ALERT: Scheduled collection failed 2 days in a row" not in caplog.text


@pytest.mark.asyncio
async def test_retry_does_not_schedule_another_retry(db_session):
    """Test that retry function doesn't schedule infinite retries."""
    with patch('app.api.collection.run_collection', new=AsyncMock(side_effect=Exception("API error"))):
        with patch('app.api.collection.increment_failure_count', new=AsyncMock()):
            with patch('app.api.collection.check_failure_alert_threshold', new=AsyncMock()):
                with patch('app.scheduler.scheduler') as mock_scheduler:
                    mock_scheduler.add_job = MagicMock()

                    with patch('app.api.collection.get_db', return_value=iter([db_session])):
                        await trigger_daily_collection_retry()

                        # Verify NO retry job was added
                        mock_scheduler.add_job.assert_not_called()


@pytest.mark.asyncio
async def test_retry_skips_if_collection_in_progress(db_session):
    """Test that retry skips if a collection is already running."""
    # Create existing in-progress collection
    existing = DataCollection(
        id=uuid4(),
        status="in_progress",
        started_at=datetime.now(timezone.utc)
    )
    db_session.add(existing)
    await db_session.commit()

    # Mock run_collection to track calls
    with patch('app.api.collection.run_collection', new=AsyncMock()) as mock_run:
        with patch('app.api.collection.get_db', return_value=iter([db_session])):
            await trigger_daily_collection_retry()

            # Should NOT start new collection
            mock_run.assert_not_called()


@pytest.mark.asyncio
async def test_scheduled_collection_creates_record(db_session):
    """Test that scheduled collection creates a DataCollection record."""
    from sqlalchemy import select

    with patch('app.api.collection.run_collection', new=AsyncMock()):
        with patch('app.api.collection.reset_failure_count', new=AsyncMock()):
            with patch('app.api.collection.get_db', return_value=iter([db_session])):
                await trigger_daily_collection()

                # Verify collection record was created
                stmt = select(DataCollection)
                result = await db_session.execute(stmt)
                collections = result.scalars().all()
                assert len(collections) > 0
                assert collections[0].status == "in_progress"
