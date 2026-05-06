from app.services.path_ranking_service import score_transport_option, choose_best_mode


def make_status(wait=2, confidence=0.8, queue="LOW", availability="AVAILABLE", stability="MODERATE", transport_type="bus"):
    return {
        "estimated_wait_time": wait,
        "confidence": confidence,
        "queue_level": queue,
        "vehicle_availability": availability,
        "stability": stability,
        "transport_type": transport_type,
    }


def test_score_transport_option_prefers_available():
    s1 = make_status(wait=5, confidence=0.9, queue="HIGH", availability="AVAILABLE")
    s2 = make_status(wait=1, confidence=0.2, queue="LOW", availability="UNAVAILABLE")

    assert score_transport_option(s1) > score_transport_option(s2)


def test_choose_best_mode_prefers_higher_score():
    statuses = [make_status(transport_type="bus"), make_status(transport_type="taxi", wait=0, confidence=0.95)]
    mode, status = choose_best_mode(statuses)
    assert mode in ("bus", "taxi")
    assert status["transport_type"] == mode
