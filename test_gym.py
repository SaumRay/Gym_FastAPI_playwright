import pytest
from playwright.sync_api import Page, APIRequestContext, expect
from datetime import date

BASE  = "http://localhost:8000"
API   = f"{BASE}/api/workouts"
TODAY = date.today().isoformat()

# ── Sample payloads ───────────────────────────────────────
BENCH_PRESS = {
    "name": "Bench Press", "category": "chest",
    "sets": 4, "reps": 10, "weight_kg": 80.0, "workout_date": TODAY
}
SQUAT = {
    "name": "Squat", "category": "legs",
    "sets": 5, "reps": 5, "weight_kg": 100.0, "workout_date": TODAY
}
RUNNING = {
    "name": "Treadmill Run", "category": "cardio",
    "duration_mins": 30, "workout_date": TODAY
}

# ── Reset before every test ───────────────────────────────
@pytest.fixture(autouse=True)
def reset(api: APIRequestContext):
    api.delete(API)
    yield
    api.delete(API)


# ════════════════════════════════════════════════════════
#  PURE API TESTS
# ════════════════════════════════════════════════════════

class TestAPICreate:

    def test_create_strength_workout(self, api: APIRequestContext):
        res  = api.post(API, data=BENCH_PRESS)
        assert res.status == 201
        body = res.json()
        assert body["name"]      == "Bench Press"
        assert body["category"]  == "chest"
        assert body["sets"]      == 4
        assert body["reps"]      == 10
        assert body["weight_kg"] == 80.0
        assert "id" in body
        assert "created_at" in body

    def test_create_cardio_workout(self, api: APIRequestContext):
        res  = api.post(API, data=RUNNING)
        assert res.status == 201
        body = res.json()
        assert body["duration_mins"] == 30
        assert body["sets"]      is None
        assert body["weight_kg"] is None

    def test_create_defaults_date_to_today(self, api: APIRequestContext):
        res = api.post(API, data={"name": "Plank", "category": "core"})
        assert res.status == 201
        assert res.json()["workout_date"] == TODAY

    def test_create_missing_name_returns_422(self, api: APIRequestContext):
        res = api.post(API, data={"category": "chest"})
        assert res.status == 422

    def test_create_missing_category_returns_422(self, api: APIRequestContext):
        res = api.post(API, data={"name": "Deadlift"})
        assert res.status == 422


class TestAPIRead:

    def test_get_all_workouts(self, api: APIRequestContext):
        api.post(API, data=BENCH_PRESS)
        api.post(API, data=SQUAT)
        res = api.get(API)
        assert res.status == 200
        assert len(res.json()) == 2

    def test_get_empty_list(self, api: APIRequestContext):
        res = api.get(API)
        assert res.status == 200
        assert res.json() == []

    def test_get_by_id(self, api: APIRequestContext):
        created = api.post(API, data=BENCH_PRESS).json()
        res     = api.get(f"{API}/{created['id']}")
        assert res.status == 200
        assert res.json()["name"] == "Bench Press"

    def test_get_by_invalid_id_returns_404(self, api: APIRequestContext):
        res = api.get(f"{API}/nonexistent-id")
        assert res.status == 404

    def test_filter_by_date(self, api: APIRequestContext):
        api.post(API, data=BENCH_PRESS)
        api.post(API, data={**SQUAT, "workout_date": "2026-01-01"})
        res  = api.get(f"{API}?date={TODAY}")
        data = res.json()
        assert all(w["workout_date"] == TODAY for w in data)
        assert len(data) == 1

    def test_filter_by_category(self, api: APIRequestContext):
        api.post(API, data=BENCH_PRESS)
        api.post(API, data=SQUAT)
        api.post(API, data=RUNNING)
        res  = api.get(f"{API}?category=legs")
        data = res.json()
        assert len(data) == 1
        assert data[0]["name"] == "Squat"


class TestAPIUpdate:

    def test_update_weight_and_reps(self, api: APIRequestContext):
        created = api.post(API, data=BENCH_PRESS).json()
        res     = api.put(f"{API}/{created['id']}", data={"weight_kg": 85.0, "reps": 8})
        assert res.status == 200
        body = res.json()
        assert body["weight_kg"] == 85.0
        assert body["reps"]      == 8
        assert body["sets"]      == 4   # unchanged

    def test_update_notes(self, api: APIRequestContext):
        created = api.post(API, data=BENCH_PRESS).json()
        res     = api.put(f"{API}/{created['id']}", data={"notes": "New PR!"})
        assert res.json()["notes"] == "New PR!"

    def test_update_nonexistent_returns_404(self, api: APIRequestContext):
        res = api.put(f"{API}/ghost-id", data={"reps": 5})
        assert res.status == 404


class TestAPIDelete:

    def test_delete_workout(self, api: APIRequestContext):
        created = api.post(API, data=BENCH_PRESS).json()
        res     = api.delete(f"{API}/{created['id']}")
        assert res.status == 204

        check = api.get(f"{API}/{created['id']}")
        assert check.status == 404

    def test_delete_nonexistent_returns_404(self, api: APIRequestContext):
        res = api.delete(f"{API}/ghost-id")
        assert res.status == 404


class TestAPISummary:

    def test_summary_totals(self, api: APIRequestContext):
        api.post(API, data=BENCH_PRESS)   # 4×10×80  = 3200kg
        api.post(API, data=SQUAT)         # 5×5×100  = 2500kg
        res  = api.get(f"{BASE}/api/summary?date={TODAY}")
        body = res.json()
        assert body["total_workouts"]  == 2
        assert body["total_volume_kg"] == 5700.0
        assert body["by_category"]["chest"] == 1
        assert body["by_category"]["legs"]  == 1

    def test_summary_empty_day(self, api: APIRequestContext):
        res  = api.get(f"{BASE}/api/summary?date=2000-01-01")
        body = res.json()
        assert body["total_workouts"]  == 0
        assert body["total_volume_kg"] == 0.0


# ════════════════════════════════════════════════════════
#  UI + API E2E TESTS
# ════════════════════════════════════════════════════════

class TestUI:

    def test_homepage_loads(self, page: Page):
        page.goto(BASE)
        expect(page).to_have_title("Gym Workout Tracker")
        expect(page.locator("h1")).to_contain_text("GYM")
        expect(page.locator("#log-btn")).to_be_visible()

    def test_empty_state_shown(self, page: Page):
        page.goto(BASE)
        expect(page.locator("#workout-list")).to_contain_text("No workouts logged")

    def test_log_strength_workout_via_form(self, page: Page):
        page.goto(BASE)
        page.fill("#f-name",   "Bench Press")
        page.select_option("#f-category", "chest")
        page.fill("#f-sets",   "4")
        page.fill("#f-reps",   "10")
        page.fill("#f-weight", "80")
        page.click("#log-btn")
        expect(page.locator("#toast")).to_contain_text("Bench Press")
        expect(page.locator("#workout-list")).to_contain_text("Bench Press")

    def test_log_cardio_workout(self, page: Page):
        page.goto(BASE)
        page.fill("#f-name",     "Treadmill Run")
        page.select_option("#f-category", "cardio")
        page.fill("#f-duration", "30")
        page.click("#log-btn")
        expect(page.locator("#workout-list")).to_contain_text("Treadmill Run")
        expect(page.locator("#workout-list")).to_contain_text("30m")

    def test_stats_update_after_logging(self, page: Page):
        page.goto(BASE)
        page.fill("#f-name",   "Squat")
        page.select_option("#f-category", "legs")
        page.fill("#f-sets",   "5")
        page.fill("#f-reps",   "5")
        page.fill("#f-weight", "100")
        page.click("#log-btn")
        page.wait_for_timeout(400)
        expect(page.locator("#stat-count")).to_contain_text("1")
        expect(page.locator("#stat-sets")).to_contain_text("5")

    def test_error_toast_on_empty_name(self, page: Page):
        page.goto(BASE)
        page.click("#log-btn")
        expect(page.locator("#toast")).to_contain_text("Enter exercise name")

    def test_delete_workout_from_ui(self, page: Page, api: APIRequestContext):
        workout = api.post(API, data=BENCH_PRESS).json()
        page.goto(BASE)
        expect(page.locator("#workout-list")).to_contain_text("Bench Press")
        page.click(f"[data-testid='delete-{workout['id']}']")
        page.wait_for_timeout(400)
        expect(page.locator("#workout-list")).not_to_contain_text("Bench Press")

    def test_category_filter(self, page: Page, api: APIRequestContext):
        api.post(API, data=BENCH_PRESS)
        api.post(API, data=SQUAT)
        page.goto(BASE)
        page.click(".filter-btn[data-cat='chest']")
        expect(page.locator("#workout-list")).to_contain_text("Bench Press")
        expect(page.locator("#workout-list")).not_to_contain_text("Squat")
        page.click(".filter-btn[data-cat='legs']")
        expect(page.locator("#workout-list")).to_contain_text("Squat")
        expect(page.locator("#workout-list")).not_to_contain_text("Bench Press")

    def test_mock_api_response(self, page: Page):
        page.route(
            "**/api/workouts",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body='[{"id":"mock1","name":"Mocked Deadlift","category":"back","sets":3,"reps":5,"weight_kg":120.0,"duration_mins":null,"notes":null,"workout_date":"2026-03-13","created_at":"2026-03-13T10:00:00"}]'
            ) if route.request.method == "GET" else route.continue_()
        )
        page.goto(BASE)
        expect(page.locator("#workout-list")).to_contain_text("Mocked Deadlift")

    def test_enter_key_submits_form(self, page: Page):
        page.goto(BASE)
        page.fill("#f-name", "Pull Ups")
        page.select_option("#f-category", "back")
        page.press("#f-name", "Enter")
        page.wait_for_timeout(400)
        expect(page.locator("#workout-list")).to_contain_text("Pull Ups")