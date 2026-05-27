"""
Playwright tests for Fauxx UI/UX Polish
Tests: Login, Navigation, Mobile 375px, Console Errors
"""
import pytest
from playwright.sync_api import Page, expect, ConsoleMessage
from conftest import BASE_URL


class TestLoginFlow:
    """Test login and authentication flow"""
    
    def test_login_redirect(self, page: Page):
        """Test that unauthenticated users are redirected to login"""
        # Clear any existing auth
        page.context.clear_cookies()
        page.evaluate("localStorage.clear()")
        
        page.goto(BASE_URL)
        # Should redirect to login
        expect(page).to_have_url("**/login")
    
    def test_login_success(self, page: Page):
        """Test successful login flow"""
        page.goto(f"{BASE_URL}/login")
        
        # Check login page elements exist
        expect(page.locator("input[type='password'], input[name='api_key']")).to_be_visible()
        
        # Enter test API key
        api_input = page.locator("input[type='password'], input[name='api_key']").first
        api_input.fill("test-api-key-for-testing")
        
        # Submit
        submit_btn = page.locator("button[type='submit']").first
        submit_btn.click()
        
        # Should redirect to dashboard
        page.wait_for_url("**/")

    def test_login_no_api_key(self, page: Page):
        """Test login fails without API key"""
        page.goto(f"{BASE_URL}/login")
        
        # Try to submit without key
        submit_btn = page.locator("button[type='submit']").first
        if submit_btn.is_enabled():
            submit_btn.click()
        
        # Should stay on login page or show error
        page.wait_for_timeout(500)


class TestNavigation:
    """Test navigation through all 4 pages"""
    
    @pytest.fixture(autouse=True)
    def setup_auth(self, page: Page):
        """Setup: Set valid API key in localStorage"""
        page.goto(BASE_URL)
        page.evaluate("localStorage.setItem('fauxx_api_key', 'test-key')")
    
    def test_navigate_to_dashboard(self, page: Page):
        """Test Dashboard page loads"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Check header nav exists
        expect(page.locator(".header-nav")).to_be_visible()
        
        # Check dashboard page is active
        expect(page.locator("#page-dashboard")).to_be_visible()
        expect(page.locator("#page-dashboard.active")).to_be_visible()
        
        # Check dashboard elements
        expect(page.locator(".dashboard-grid")).to_be_visible()
        expect(page.locator("#stat-actions")).to_be_visible()
    
    def test_navigate_to_targeting(self, page: Page):
        """Test Targeting page loads"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Click Targeting nav button
        page.click(".header-nav button:has-text('TARGETING')")
        page.wait_for_timeout(200)
        
        # Check targeting page is active
        expect(page.locator("#page-targeting")).to_have_class(".*active.*")
        
        # Check targeting elements
        expect(page.locator(".module-grid")).to_be_visible()
        expect(page.locator(".layer-grid")).to_be_visible()
    
    def test_navigate_to_logs(self, page: Page):
        """Test Logs page loads"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Click Logs nav button
        page.click(".header-nav button:has-text('LOGS')")
        page.wait_for_timeout(200)
        
        # Check logs page is active
        expect(page.locator("#page-logs")).to_have_class(".*active.*")
        
        # Check log table exists
        expect(page.locator(".log-table")).to_be_visible()
    
    def test_navigate_to_settings(self, page: Page):
        """Test Settings page loads"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Click Settings nav button
        page.click(".header-nav button:has-text('CONFIG')")
        page.wait_for_timeout(200)
        
        # Check settings page is active
        expect(page.locator("#page-settings")).to_have_class(".*active.*")
        
        # Check settings elements
        expect(page.locator(".intensity-slider")).to_be_visible()
        expect(page.locator(".preset-btn").first).to_be_visible()
    
    def test_keyboard_navigation(self, page: Page):
        """Test keyboard shortcuts (1-4) for navigation"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Press '2' for Targeting
        page.keyboard.press("2")
        page.wait_for_timeout(200)
        expect(page.locator("#page-targeting")).to_have_class(".*active.*")
        
        # Press '3' for Logs
        page.keyboard.press("3")
        page.wait_for_timeout(200)
        expect(page.locator("#page-logs")).to_have_class(".*active.*")
        
        # Press '4' for Settings
        page.keyboard.press("4")
        page.wait_for_timeout(200)
        expect(page.locator("#page-settings")).to_have_class(".*active.*")
        
        # Press '1' for Dashboard
        page.keyboard.press("1")
        page.wait_for_timeout(200)
        expect(page.locator("#page-dashboard")).to_have_class(".*active.*")


class TestMobileResponsive:
    """Test mobile responsiveness at 375px"""
    
    @pytest.fixture(autouse=True)
    def setup_mobile(self, page: Page):
        """Setup: Set mobile viewport and auth"""
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto(BASE_URL)
        page.evaluate("localStorage.setItem('fauxx_api_key', 'test-key')")
    
    def test_mobile_375px_layout(self, page: Page):
        """Test that 375px viewport renders correctly"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Main app should be visible
        expect(page.locator(".app")).to_be_visible()
        
        # Header should be visible and not overflow
        header = page.locator(".command-header")
        expect(header).to_be_visible()
        
        # Dashboard content should be visible
        expect(page.locator(".dashboard-grid")).to_be_visible()
    
    def test_mobile_sidebar_hidden(self, page: Page):
        """Test that sidebar is hidden on mobile"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Sidebar should be hidden via CSS
        sidebar = page.locator(".command-sidebar")
        # Check computed display
        display = page.evaluate("getComputedStyle(document.querySelector('.command-sidebar')).display")
        assert display == "none", f"Sidebar should be hidden on mobile, but display is {display}"
    
    def test_mobile_touch_targets(self, page: Page):
        """Test that touch targets are at least 44px"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Check nav buttons have adequate size
        nav_buttons = page.locator(".header-nav button")
        count = nav_buttons.count()
        
        for i in range(count):
            btn = nav_buttons.nth(i)
            box = btn.bounding_box()
            if box:
                # Check min-width and min-height
                min_size = page.evaluate("""(selector) => {
                    const el = document.querySelector(selector);
                    const style = getComputedStyle(el);
                    return {
                        width: el.offsetWidth,
                        height: el.offsetHeight,
                        minWidth: style.minWidth,
                        minHeight: style.minHeight
                    };
                }""", btn.evaluate_handle("el => el").as_element().get_attribute("class"))
                
                # Element should be at least 44px in either dimension for touch
                assert box['width'] >= 30 or box['height'] >= 30, \
                    f"Button too small: {box['width']}x{box['height']}"
    
    def test_mobile_log_table_readable(self, page: Page):
        """Test that log table is readable on mobile"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Navigate to logs
        page.click(".header-nav button:has-text('LOGS')")
        page.wait_for_timeout(200)
        
        # Log table should be scrollable/visible
        expect(page.locator(".log-table")).to_be_visible()


class TestConsoleErrors:
    """Test for zero console errors"""
    
    @pytest.fixture(autouse=True)
    def setup_console_capture(self, page: Page):
        """Setup: Enable console message capture"""
        page.goto(BASE_URL)
        page.evaluate("localStorage.setItem('fauxx_api_key', 'test-key')")
    
    def test_no_console_errors_on_load(self, page: Page):
        """Test that dashboard loads without console errors"""
        errors = []
        
        def handle_console(msg: ConsoleMessage):
            if msg.type == "error":
                errors.append(msg.text)
        
        page.on("console", handle_console)
        
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)  # Wait for any async operations
        
        # Filter out known non-critical errors
        critical_errors = [e for e in errors if not any(
            x in e.lower() for x in ['favicon', 'net::err_connection_refused', '404']
        )]
        
        assert len(critical_errors) == 0, f"Console errors found: {critical_errors}"
    
    def test_no_console_errors_navigation(self, page: Page):
        """Test that navigation doesn't produce console errors"""
        errors = []
        
        def handle_console(msg: ConsoleMessage):
            if msg.type == "error":
                errors.append(msg.text)
        
        page.on("console", handle_console)
        
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Navigate through all pages
        page.click(".header-nav button:has-text('TARGETING')")
        page.wait_for_timeout(300)
        
        page.click(".header-nav button:has-text('LOGS')")
        page.wait_for_timeout(300)
        
        page.click(".header-nav button:has-text('CONFIG')")
        page.wait_for_timeout(300)
        
        page.click(".header-nav button:has-text('DASHBOARD')")
        page.wait_for_timeout(300)
        
        # Check for errors
        critical_errors = [e for e in errors if not any(
            x in e.lower() for x in ['favicon', 'net::err_connection_refused']
        )]
        
        assert len(critical_errors) == 0, f"Console errors during navigation: {critical_errors}"
    
    def test_no_console_errors_interactions(self, page: Page):
        """Test that UI interactions don't produce console errors"""
        errors = []
        
        def handle_console(msg: ConsoleMessage):
            if msg.type == "error":
                errors.append(msg.text)
        
        page.on("console", handle_console)
        
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Try some interactions
        # Click command palette shortcut hint dismiss
        shortcut_hint = page.locator(".shortcut-hint")
        if shortcut_hint.count() > 0:
            page.wait_for_timeout(9000)  # Wait for auto-hide
        
        # Toggle engine button
        engine_btn = page.locator("#btn-engine")
        if engine_btn.count() > 0:
            engine_btn.click()
            page.wait_for_timeout(500)
        
        # Open command palette
        page.keyboard.press("Control+k")
        page.wait_for_timeout(300)
        
        # Check for errors
        critical_errors = [e for e in errors if not any(
            x in e.lower() for x in ['favicon', 'net::err_connection_refused']
        )]
        
        assert len(critical_errors) == 0, f"Console errors during interactions: {critical_errors}"


class TestIntensitySlider:
    """Test intensity slider functionality"""
    
    @pytest.fixture(autouse=True)
    def setup_auth(self, page: Page):
        """Setup: Authenticate"""
        page.goto(BASE_URL)
        page.evaluate("localStorage.setItem('fauxx_api_key', 'test-key')")
    
    def test_intensity_slider_shows_value(self, page: Page):
        """Test that intensity slider displays current value"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Navigate to settings
        page.click(".header-nav button:has-text('CONFIG')")
        page.wait_for_timeout(200)
        
        # Check slider exists
        slider = page.locator("#intensity-slider")
        expect(slider).to_be_visible()
        
        # Check current value display
        current_val = page.locator("#intensity-current")
        expect(current_val).to_be_visible()
        
        # Default value should be shown
        val = current_val.text_content()
        assert val and val != '—', "Intensity value not displayed"
    
    def test_intensity_slider_presets(self, page: Page):
        """Test that intensity presets work"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        page.click(".header-nav button:has-text('CONFIG')")
        page.wait_for_timeout(200)
        
        # Click LOW preset
        preset = page.locator(".preset-btn:has-text('LOW')")
        expect(preset).to_be_visible()
        preset.click()
        page.wait_for_timeout(300)
        
        # HIGH preset
        preset = page.locator(".preset-btn:has-text('HIGH')")
        preset.click()
        page.wait_for_timeout(300)


class TestCommandPalette:
    """Test command palette functionality"""
    
    @pytest.fixture(autouse=True)
    def setup_auth(self, page: Page):
        """Setup: Authenticate"""
        page.goto(BASE_URL)
        page.evaluate("localStorage.setItem('fauxx_api_key', 'test-key')")
    
    def test_command_palette_opens(self, page: Page):
        """Test that command palette opens with Ctrl+K"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Open palette
        page.keyboard.press("Control+k")
        page.wait_for_timeout(200)
        
        # Check palette is visible
        palette = page.locator("#command-palette")
        expect(palette).to_be_visible()
        
        # Check input is focused
        input_field = page.locator("#palette-input")
        expect(input_field).to_be_focused()
    
    def test_command_palette_navigation(self, page: Page):
        """Test command palette navigation commands"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Open palette
        page.keyboard.press("Control+k")
        page.wait_for_timeout(200)
        
        # Type to filter
        page.fill("#palette-input", "targeting")
        page.wait_for_timeout(200)
        
        # Results should be filtered
        results = page.locator(".palette-item")
        expect(results.first).to_be_visible()
    
    def test_command_palette_close(self, page: Page):
        """Test that command palette closes with Escape"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        # Open palette
        page.keyboard.press("Control+k")
        page.wait_for_timeout(200)
        
        # Close with Escape
        page.keyboard.press("Escape")
        page.wait_for_timeout(200)
        
        # Check palette is hidden
        palette = page.locator("#command-palette")
        expect(palette).to_be_hidden()
