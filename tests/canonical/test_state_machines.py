import pytest

from seion_core.canonical.state_machines import TransitionError, transition, validate_state


def test_claim_requires_proof_path_before_proved():
    validate_state("claim", "PROOF_IN_PROGRESS")
    assert transition("claim", "PROOF_IN_PROGRESS", "PROVED", "independent proof").next == "PROVED"
    with pytest.raises(TransitionError):
        transition("claim", "OPEN", "PROVED", "numerical residual")


def test_experiment_terminal_path_is_explicit():
    result = transition("experiment", "RUNNING", "FAILED_NUMERICAL_GATE", "bound exceeded")
    assert result.next == "FAILED_NUMERICAL_GATE"
    with pytest.raises(TransitionError):
        transition("experiment", "PAPER_ELIGIBLE", "COMPLETE", "backward")
