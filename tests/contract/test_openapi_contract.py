from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]

OPENAPI_PATH = (
    REPO_ROOT
    / "project-specifications"
    / "specs"
    / "001-event-ledger-api"
    / "contracts"
    / "openapi.yaml"
)

BUNDLED_OPENAPI_PATH = (
    REPO_ROOT / "src" / "event_ledger_api" / "contracts" / "openapi.yaml"
)


def test_bundled_openapi_matches_spec_kit_copy():
    assert BUNDLED_OPENAPI_PATH.is_file()
    assert OPENAPI_PATH.read_text(encoding="utf-8") == BUNDLED_OPENAPI_PATH.read_text(
        encoding="utf-8"
    )


def load_spec() -> dict:
    with OPENAPI_PATH.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def test_required_paths_and_methods_exist():
    spec = load_spec()
    paths = spec["paths"]
    assert "get" in paths["/health"]
    assert "post" in paths["/events"]
    assert "get" in paths["/events"]
    assert "get" in paths["/events/{id}"]
    assert "get" in paths["/accounts/{accountId}/balance"]


def test_required_schemas_exist():
    schemas = load_spec()["components"]["schemas"]
    for name in (
        "EventSubmission",
        "EventResponse",
        "EventListResponse",
        "PaginationMeta",
        "BalanceResponse",
        "CurrencyBalance",
        "ErrorResponse",
    ):
        assert name in schemas


def test_post_events_response_codes():
    responses = load_spec()["paths"]["/events"]["post"]["responses"]
    assert {"201", "200", "409", "422"} <= set(responses.keys())


def test_list_events_pagination_parameters():
    parameters = load_spec()["paths"]["/events"]["get"]["parameters"]
    names = {param["name"] for param in parameters}
    assert {"account", "limit", "offset"} <= names


def test_event_list_response_includes_pagination():
    props = load_spec()["components"]["schemas"]["EventListResponse"]["properties"]
    assert "pagination" in props
    assert props["pagination"]["$ref"].endswith("PaginationMeta")
