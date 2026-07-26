from clinical_calculators import load_registry


def test_search_diagnostics_are_isolated_between_responses():
    registry = load_registry()

    first = registry.search_detailed("chads vasc")
    first_results = first.results
    first_match = first.match_for("CALC-0049")

    second = registry.search_detailed("脓毒症")

    assert second.results != first_results
    assert first.results == first_results
    assert first.match_for("CALC-0049") == first_match
    assert first_match is not None
    assert first_match.coverage == 1.0
