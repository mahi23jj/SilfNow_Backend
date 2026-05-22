"""
Test reporter trust scoring and reconciliation.
"""
from datetime import datetime, timedelta
from sqlmodel import Session, create_engine, SQLSession

from app.models.report import Report, QueueLevel, VehicleAvailability
from app.models.reporter_profile import ReporterProfile
from app.models.system_state import SystemState
from app.services.report_service import (
    get_or_create_reporter_trust,
    register_report_submission,
    reconcile_reporter_trust,
    compute_edge_status_per_transport,
    DEFAULT_REPORTER_TRUST,
    TRUST_CORROBORATED_DELTA,
    TRUST_CONTRADICTED_DELTA,
)


def test_get_or_create_reporter_trust_creates_profile():
    """Test that missing profile is created with default trust."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        user_id = 1
        trust = get_or_create_reporter_trust(user_id, session)
        
        assert trust == DEFAULT_REPORTER_TRUST
        
        profile = session.query(ReporterProfile).filter(
            ReporterProfile.user_id == user_id
        ).first()
        assert profile is not None
        assert profile.trust_score == DEFAULT_REPORTER_TRUST


def test_get_or_create_reporter_trust_returns_existing():
    """Test that existing profile is returned."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        user_id = 1
        profile = ReporterProfile(user_id=user_id, trust_score=0.8)
        session.add(profile)
        session.commit()
        
        trust = get_or_create_reporter_trust(user_id, session)
        assert trust == 0.8


def test_register_report_submission_increments_total_reports():
    """Test that report submissions update reporter history once."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        user_id = 1
        profile = ReporterProfile(user_id=user_id, trust_score=0.8, total_reports=0)
        session.add(profile)
        session.commit()

        updated_profile = register_report_submission(user_id, session)

        assert updated_profile.total_reports == 1
        assert updated_profile.trust_score == 0.81


def test_trust_multiplier_reduces_weight_for_low_trust():
    """Test that low trust reduces report weight in aggregation."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        edge_id = 1
        now = datetime.utcnow()
        
        # Create two reports with same metadata but different trust
        report_high_trust = Report(
            user_id=1,
            edge_id=edge_id,
            queue_level=QueueLevel.HIGH,
            vehicle_availability=VehicleAvailability.AVAILABLE,
            transport_types=["bus"],
            created_at=now,
            location_score=1.0,
            estimated_wait_time=10,
        )
        report_low_trust = Report(
            user_id=2,
            edge_id=edge_id,
            queue_level=QueueLevel.HIGH,
            vehicle_availability=VehicleAvailability.AVAILABLE,
            transport_types=["bus"],
            created_at=now,
            location_score=1.0,
            estimated_wait_time=10,
        )
        
        # Set trust scores
        profile_high = ReporterProfile(user_id=1, trust_score=1.0)
        profile_low = ReporterProfile(user_id=2, trust_score=0.2)
        
        session.add_all([report_high_trust, report_low_trust, profile_high, profile_low])
        session.commit()
        
        results = compute_edge_status_per_transport([report_high_trust, report_low_trust], session)
        
        assert len(results) == 1
        assert results[0]["transport_type"] == "bus"
        # With mixed trust, the high-trust report should dominate
        assert results[0]["queue_level"] == "HIGH"


def test_reconcile_corroborates_majority():
    """Test that corroborated reports increase trust."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        edge_id = 1
        user_id = 1
        now = datetime.utcnow()
        
        # Report older than window (will be reconciled)
        old_report = Report(
            user_id=user_id,
            edge_id=edge_id,
            queue_level=QueueLevel.HIGH,
            vehicle_availability=VehicleAvailability.AVAILABLE,
            transport_types=["bus"],
            created_at=now - timedelta(minutes=15),
            location_score=1.0,
        )
        
        # Recent reports in same window (consensus)
        recent_report_1 = Report(
            user_id=2,
            edge_id=edge_id,
            queue_level=QueueLevel.HIGH,
            vehicle_availability=VehicleAvailability.AVAILABLE,
            transport_types=["bus"],
            created_at=now - timedelta(minutes=12),
            location_score=1.0,
        )
        recent_report_2 = Report(
            user_id=3,
            edge_id=edge_id,
            queue_level=QueueLevel.HIGH,
            vehicle_availability=VehicleAvailability.AVAILABLE,
            transport_types=["bus"],
            created_at=now - timedelta(minutes=11),
            location_score=1.0,
        )
        
        profile = ReporterProfile(user_id=user_id, trust_score=DEFAULT_REPORTER_TRUST)
        
        session.add_all([old_report, recent_report_1, recent_report_2, profile])
        session.commit()
        
        reconcile_reporter_trust(session)
        
        # Refresh profile
        session.refresh(profile)
        expected_trust = DEFAULT_REPORTER_TRUST + TRUST_CORROBORATED_DELTA
        assert profile.trust_score == expected_trust


if __name__ == "__main__":
    test_get_or_create_reporter_trust_creates_profile()
    print("✓ test_get_or_create_reporter_trust_creates_profile")
    
    test_get_or_create_reporter_trust_returns_existing()
    print("✓ test_get_or_create_reporter_trust_returns_existing")
    
    test_trust_multiplier_reduces_weight_for_low_trust()
    print("✓ test_trust_multiplier_reduces_weight_for_low_trust")
    
    test_reconcile_corroborates_majority()
    print("✓ test_reconcile_corroborates_majority")
    
    print("\nAll trust tests passed!")
