import pytest
from playwright.sync_api import Page, expect, sync_playwright
import time

BASE_URL = "http://localhost:8000"


@pytest.fixture
def page():
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True)
    context = browser.new_context()
    p = context.new_page()
    yield p
    p.close()
    context.close()
    browser.close()
    pw.stop()


class TestDashboard:
    def test_page_loads(self, page: Page):
        """Test that the dashboard loads without errors"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        expect(page.locator(".app")).to_be_visible()

    # === STAT WIDGETS ===
    def test_stat_widgets_exist(self, page: Page):
        """Test all stat widgets are visible"""
        page.goto(BASE_URL)
        expect(page.locator("#stat-actions")).to_be_visible()
        expect(page.locator("#stat-categories")).to_be_visible()
        expect(page.locator("#stat-modules")).to_be_visible()
        expect(page.locator("#stat-uptime")).to_be_visible()
        expect(page.locator("#stat-data")).to_be_visible()

    # === ENGINE CONTROLS ===
    def test_engine_start(self, page: Page):
        """Test engine start button"""
        page.goto(BASE_URL)
        page.click("#start-btn")
        time.sleep(1)

    def test_engine_stop(self, page: Page):
        """Test engine stop button"""
        page.goto(BASE_URL)
        page.click("#btn-engine")
        time.sleep(1)

    def test_trigger_now(self, page: Page):
        """Test manual trigger button"""
        page.goto(BASE_URL)
        page.click("#trigger-action")
        time.sleep(2)

    # === RECENT ACTIONS ===
    def test_recent_actions_visible(self, page: Page):
        """Test recent actions section"""
        page.goto(BASE_URL)
        expect(page.locator(".card-header:has-text('Recent Actions')")).to_be_visible()

    # === TARGETING - POISON MODULES ===
    def test_poison_modules(self, page: Page):
        """Test all poison modules can be toggled"""
        page.goto(BASE_URL)
        page.click("text=Targeting")
        time.sleep(0.5)

        modules = [
            "#toggle-search_poison",
            "#toggle-ad_pollution",
            "#toggle-dns_noise",
            "#toggle-cookie_saturation",
            "#toggle-fingerprint",
            "#toggle-location_spoof",
            "#toggle-app_signal"
        ]

        for module in modules:
            toggle = page.locator(module)
            if toggle.count() > 0:
                toggle.click()
                time.sleep(0.2)
                toggle.click()

    # === TARGETING LAYERS ===
    def test_targeting_layers(self, page: Page):
        """Test all targeting layers can be toggled"""
        page.goto(BASE_URL)
        page.click("text=Targeting")
        time.sleep(0.5)

        layers = ["#toggle-layer0", "#toggle-layer1", "#toggle-layer2", "#toggle-layer3"]
        for layer in layers:
            toggle = page.locator(layer)
            if toggle.count() > 0:
                toggle.click()
                time.sleep(0.2)

    # === PERSONA ROTATION ===
    def test_persona_rotation(self, page: Page):
        """Test persona rotation button"""
        page.goto(BASE_URL)
        page.click("text=Persona")
        time.sleep(0.5)

        rotate_btn = page.locator(".rotate-btn, button:has-text('Rotate')")
        if rotate_btn.count() > 0:
            rotate_btn.click()
            time.sleep(1)

    # === CATEGORY WEIGHTS ===
    def test_category_weights_adjustment(self, page: Page):
        """Test that adjusting weights changes behavior"""
        page.goto(BASE_URL)
        page.click("text=Targeting")
        time.sleep(0.5)

        weights = page.locator(".weight-slider, input[type='range']")
        if weights.count() > 0:
            weights.first.fill("50")
            time.sleep(0.5)

    # === ACTION LOG ===
    def test_action_log_expand_collapse(self, page: Page):
        """Test expand all / collapse all"""
        page.goto(BASE_URL)
        page.click("text=Action Log")
        time.sleep(0.5)

        expand_btn = page.locator("button:has-text('Expand All')")
        if expand_btn.count() > 0:
            expand_btn.click()
            time.sleep(0.5)

        collapse_btn = page.locator("button:has-text('Collapse All')")
        if collapse_btn.count() > 0:
            collapse_btn.click()
            time.sleep(0.5)

    def test_action_log_limit_filter(self, page: Page):
        """Test log limit filters (10, 25, 50, 100, 250, 500)"""
        page.goto(BASE_URL)
        page.click("text=Action Log")
        time.sleep(0.5)

        limits = ["10", "25", "50", "100", "250", "500"]
        for limit in limits:
            limit_select = page.locator(".limit-select, select")
            if limit_select.count() > 0:
                limit_select.select_option(limit)
                time.sleep(0.3)

    def test_action_log_type_filter(self, page: Page):
        """Test type and status filters"""
        page.goto(BASE_URL)
        page.click("text=Action Log")
        time.sleep(0.5)

        type_select = page.locator(".type-filter, select").first
        if type_select.count() > 0:
            options = type_select.locator("option")
            if options.count() > 1:
                options.nth(1).click()
                time.sleep(0.3)

    # === SETTINGS ===
    def test_intensity_presets(self, page: Page):
        """Test intensity presets: Minimal, Balanced, Maximum, Custom"""
        page.goto(BASE_URL)
        page.click("text=Settings")
        time.sleep(0.5)

        presets = ["MINIMAL", "BALANCED", "MAXIMUM"]
        for preset in presets:
            btn = page.locator(f".preset-btn:has-text('{preset}')")
            if btn.count() > 0:
                btn.click()
                time.sleep(0.5)

    def test_custom_intensity(self, page: Page):
        """Test custom intensity input"""
        page.goto(BASE_URL)
        page.click("text=Settings")
        time.sleep(0.5)

        custom_input = page.locator("#custom-intensity")
        if custom_input.count() > 0:
            custom_input.fill("150")
            custom_input.press("Enter")
            time.sleep(0.5)

    # === THEME ===
    def test_theme_presets(self, page: Page):
        """Test theme color presets"""
        page.goto(BASE_URL)
        page.click("text=Settings")
        time.sleep(0.5)

        theme_btn = page.locator(".theme-btn").first
        if theme_btn.count() > 0:
            theme_btn.click()
            time.sleep(0.5)

    def test_theme_custom_color(self, page: Page):
        """Test custom color picker"""
        page.goto(BASE_URL)
        page.click("text=Settings")
        time.sleep(0.5)

        custom_color = page.locator(".theme-custom, input[type='color']")
        if custom_color.count() > 0:
            custom_color.fill("#ff0080")
            time.sleep(0.5)

    # === SIDEBAR TOGGLE ===
    def test_sidebar_toggle(self, page: Page):
        """Test sidebar collapse/expand button"""
        page.goto(BASE_URL)

        page.set_viewport_size({"width": 375, "height": 667})
        time.sleep(0.5)

        sidebar_toggle = page.locator(".sidebar-toggle, .hamburger-btn")
        if sidebar_toggle.count() > 0:
            sidebar_toggle.click()
            time.sleep(0.5)

        page.set_viewport_size({"width": 1280, "height": 800})
        time.sleep(0.5)
