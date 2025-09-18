import time
from datetime import date
import uiautomator2 as u2


def connect_device():
    """Connect to an Android device using uiautomator2."""
    return u2.connect()


def restart_app(d, app_package="com.asisto.tcomparto", start_wait=10):
    """Stop and start the app to ensure a clean state."""
    d.app_stop(app_package)
    d.app_start(app_package)
    time.sleep(start_wait)


def open_planilla_tab(d):
    """Navigate to the 'Planilla' tab in the app."""
    d(text="Planilla").click()


def navigate_to_month(d, target_year, target_month):
    """Navigate back through calendar months to the target month/year."""
    today = date.today()
    today_formatted = today.strftime("%d/%m/%Y")
    d(text=today_formatted).click()
    time.sleep(1)

    device_month = today.month
    device_year = today.year
    months_back = (device_year - target_year) * 12 + (device_month - target_month)

    if months_back > 0:
        for _ in range(months_back):
            d(resourceId="android:id/prev").click()
            time.sleep(0.5)
    else:
        print("Already at or past the target month.")


def select_day_and_accept(d, day):
    """Click on a day and accept the selection."""
    d(text=str(day)).click()
    d(text="ACEPTAR").click()
    time.sleep(2)


def get_event_data(d):
    """Retrieve times, addresses, and names of events from the UI."""
    times = d(resourceId="com.asisto.tcomparto:id/tv_event_time")
    addresses = d(resourceId="com.asisto.tcomparto:id/tv_event_location")
    names = d(resourceId="com.asisto.tcomparto:id/tv_event_user")
    return times, addresses, names
