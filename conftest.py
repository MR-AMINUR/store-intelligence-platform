"""Pytest configuration and shared fixtures for Store Intelligence Platform tests.

This file is automatically loaded by pytest and provides:
- Hypothesis settings for property-based testing
- Common test fixtures
- Test configuration
"""

from hypothesis import settings, Verbosity

# Configure Hypothesis for property-based testing
# Default profile: 100 iterations minimum as per requirements
settings.register_profile(
    "default",
    max_examples=100,
    deadline=None,  # Disable deadline for slow tests
    print_blob=True,  # Print failing examples for debugging
    verbosity=Verbosity.normal,
    stateful_step_count=10,
)

# CI profile: More iterations for thorough testing in CI/CD
settings.register_profile(
    "ci",
    max_examples=200,
    deadline=None,
    print_blob=True,
    verbosity=Verbosity.normal,
)

# Debug profile: Fewer iterations for quick feedback during development
settings.register_profile(
    "debug",
    max_examples=10,
    deadline=None,
    print_blob=True,
    verbosity=Verbosity.verbose,
)

# Load the default profile
settings.load_profile("default")


# Common test fixtures can be added here
# Example:
# @pytest.fixture
# def sample_config():
#     """Provide sample configuration for tests."""
#     return {...}
