# process_events.py
import traceback
from datetime import datetime, timedelta
import calendar
import os
import time
from file_utils import create_folder, delete_all_files
from gmaps_utils import start_headless_browser, get_longest_distance_gmaps, close_browser
from km_utils import write_distance_data, write_page_number
from android_ui_utils import (
    connect_device, restart_app, open_planilla_tab,
    navigate_to_month, select_day_and_accept, get_event_data
)

def obtain_month(month_str, status_callback=None):
    """
    Validate the month string provided by the GUI.
    month_str: String from GUI dropdown (e.g., '01', '06', '12')
    status_callback: Function to update GUI status (optional)
    Returns: Formatted month string (e.g., '06') or raises an error
    """
    try:
        if not month_str.isdigit():
            error_msg = "The month must be a number between 1 and 12."
            if status_callback:
                status_callback(error_msg, "error")
            raise ValueError(error_msg)

        month_int = int(month_str)
        if not (1 <= month_int <= 12):
            error_msg = "The month must be a number between 1 and 12."
            if status_callback:
                status_callback(error_msg, "error")
            raise ValueError(error_msg)

        month_str_formatted = f"{month_int:02}"
        return month_str_formatted

    except Exception as e:
        if status_callback:
            status_callback(f"Error: {e}", "error")
        raise

def get_origin_destination_addresses(origin, destination):
    origin_street = origin.split(",")[0].strip()
    origin_post_code = origin.split("CP: ")[1].strip()
    destination_street = destination.split(",")[0].strip()
    destination_post_code = destination.split("CP: ")[1].strip()

    return {
        'origin': f"{origin_street} {origin_post_code}",
        'destination': f"{destination_street} {destination_post_code}"
    }

def process_day(d, day, total_duration, total_km, driver, target_month, target_year, km_file_path, checked_addresses):
    try:
        select_day_and_accept(d, day)
        times, addresses, names = get_event_data(d)
        event_count = min(len(times), len(addresses), len(names))

        if event_count == 0:
            print(f"No events found on day {day}")
        else:
            for i in range(event_count):
                user_time = times[i].get_text()
                user_address = addresses[i].get_text()
                user_name = names[i].get_text()

                try:
                    start_str, end_str = [t.strip() for t in user_time.split('-')]
                    fmt = "%H:%M"
                    start_time = datetime.strptime(start_str, fmt)
                    end_time = datetime.strptime(end_str, fmt)

                    if end_time < start_time:
                        end_time += timedelta(days=1)

                    total_duration += (end_time - start_time)

                    if i > 0 and len(addresses) > 1:
                        prev_time = times[i - 1].get_text()
                        prev_start_str, prev_end_str = [t.strip() for t in prev_time.split('-')]
                        prev_end_time = datetime.strptime(prev_end_str, fmt)

                        gap = start_time - prev_end_time

                        if 0 < gap.total_seconds() <= 3600:
                            origin = addresses[i - 1].get_text()
                            destination = addresses[i].get_text()

                            clean_addresses = get_origin_destination_addresses(origin, destination)

                            formatted_date = datetime.strptime(f"{day}/{target_month}/{target_year}", "%d/%m/%Y")
                            str_date = formatted_date.strftime("%d/%m/%Y")

                            origin_destination_str = f"{clean_addresses['origin']} -> {clean_addresses['destination']}".lower()

                            if origin_destination_str not in checked_addresses:
                                distance = get_longest_distance_gmaps(
                                    clean_addresses['origin'],
                                    clean_addresses['destination'],
                                    driver
                                )
                                checked_addresses[origin_destination_str] = distance
                                print("Distance calculated")
                            else:
                                distance = checked_addresses[origin_destination_str]
                                print("Distance retrieved")

                            print(f"Distance for {origin_destination_str} is {distance}")

                            float_distance = distance.split(" ")[0].strip().replace(",", ".")
                            float_distance = float(float_distance)

                            if float_distance >= 1:
                                destination_clean = ' '.join(destination.splitlines())
                                origin_clean = ' '.join(origin.splitlines())

                                total_km += float_distance
                                write_distance(distance, km_file_path, destination_clean, origin_clean, str_date)

                    print(f"Day {day} Event {i + 1}: Time: {user_time}, Address: {user_address}, Name: {user_name}")

                except Exception as e:
                    print(f"Could not parse time range '{user_time}': {e}")
                    print(f"Raw time string (repr): {repr(user_time)}")
                    print("Full traceback:")
                    traceback.print_exc()

        time.sleep(1)

    except Exception as e:
        print(f"Error on day {day}: {e}")

    finally:
        try:
            formatted_date = datetime.strptime(f"{day}/{target_month}/{target_year}", "%d/%m/%Y")
            str_date = formatted_date.strftime("%d/%m/%Y")
            d(text=str_date).click()
            time.sleep(1)
        except Exception as e:
            print(f"Error re-selecting date {day}/{target_month}/{target_year}: {e}")

    return total_duration, total_km, checked_addresses  # Return updated values

def write_page_numbers(output_dir, output_pdf_name):
    page = 1
    for file_name in os.listdir(output_dir):
        if output_pdf_name in file_name:
            write_page_number(
                os.path.join(output_dir, file_name),
                page
            )
            page += 1

def prepare_data_folders(pdf_path, txt_path):
    delete_all_files(txt_path)
    create_folder(txt_path)
    create_folder(pdf_path)

def write_distance(distance, file_name, destination, origin, date_str):
    with open(file_name, "a", encoding="UTF-8") as file:
        file.write(f"{date_str};{origin};{destination};{distance}\n")

def start_program(month_str, status_callback=None):
    """
    Start the program with the given month.
    month_str: Month from GUI (e.g., '06')
    status_callback: Function to update GUI status
    """
    try:
        month_str = obtain_month(month_str, status_callback)
        process_month(month_str, status_callback)
    except Exception as e:
        if status_callback:
            status_callback(f"Program failed: {e}", "error")

def process_month(month_str: str, status_callback=None, target_year: int = 2025):
    if status_callback:
        status_callback("Connecting to device...", "info")
    d = connect_device()
    restart_app(d)
    open_planilla_tab(d)

    target_month = int(month_str)
    current_days_month = calendar.monthrange(target_year, target_month)[1]

    km_txt_folder = "./files/output/kilometre_reports_txt"
    km_pdf_folder = "./files/output/kilometre_reports_pdf"

    prepare_data_folders(km_pdf_folder, km_txt_folder)

    km_file_name = f"km_{target_month:02}_{target_year}.txt"
    km_file_path = os.path.join(km_txt_folder, km_file_name)

    navigate_to_month(d, target_year, target_month)

    if status_callback:
        status_callback("Starting headless browser...", "info")
    driver = start_headless_browser()
    total_km = 0
    total_duration = timedelta()
    checked_addresses = {}

    for day in range(1, current_days_month + 1):
        if status_callback:
            status_callback(f"Processing day {day}...", "info")
        # Update total_duration and total_km with returned values
        total_duration, total_km, checked_addresses = process_day(d, day, total_duration, total_km, driver, target_month, target_year, km_file_path, checked_addresses)

    total_seconds = int(total_duration.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60

    d.app_stop("com.asisto.tcomparto")
    if status_callback:
        status_callback("Closing browser...", "info")
    close_browser(driver)

    pdf_data = {
        'obra': {'x1': 92.67, 'y2': 142.64, 'value': ""},
        'date_today': {'x1': 454.67, 'y2': 97.98, 'value': datetime.today().strftime("%#d/%#m/%Y")},
        'month': {'x1': 302.67, 'y2': 176.71, 'value': month_str},
        'year': {'x1': 469.33, 'y2': 176.11, 'value': str(target_year)},
        'vehicle': {'x1': 91.33, 'y2': 196.91, 'value': "Seat Ibiza"},
        'plate': {'x1': 418.00, 'y2': 197.04, 'value': "3274 HMP"},
        'owner': {'x1': 114.00, 'y2': 216.91, 'value': "Geomar Ortiz Bueno"}
    }

    event_dates = []
    event_addresses = []
    event_distances = []

    with open(km_file_path, "r", encoding='UTF-8') as km_file:
        for line in km_file:
            line_contents = line.strip().split(";")
            event_dates.append(line_contents[0])
            event_addresses.append(f"{line_contents[1]} -> {line_contents[2]}")
            event_distances.append(line_contents[3])

    pdf_event_data = {
        'event_addresses': event_addresses,
        'event_distances': event_distances,
        'event_dates': event_dates
    }

    output_pdf_name = f"{month_str}_{target_year}"
    output_pdf_base_path = os.path.join("./files/output/kilometre_reports_pdf", output_pdf_name)

    if status_callback:
        status_callback("Writing PDF data...", "info")
    write_distance_data(
        "./files/input/km_document_model.pdf",
        output_pdf_base_path,
        pdf_data,
        pdf_event_data
    )

    output_dir = "./files/output/kilometre_reports_pdf"

    write_page_numbers(output_dir, output_pdf_name)

    print(f"PDF reports saved to: {km_pdf_folder}")
    print(f"TXT reports saved to: {km_txt_folder}")

    print(f"\nTotal time spent on events in {month_str}/{target_year}: {hours}h:{minutes}min")
    print(f"Total kilometres for the month: {total_km:.2f}")
    if status_callback:
        status_callback("Program completed successfully!", "success")