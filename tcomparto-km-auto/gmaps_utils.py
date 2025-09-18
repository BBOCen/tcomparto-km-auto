import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from km_utils import extract_address_parts


def start_headless_browser(headless=True):
    options = FirefoxOptions()
    options.headless = headless
    options.set_preference(
        "general.useragent.override",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    driver = webdriver.Firefox(options=options)
    driver.set_window_size(1920, 1080)
    return driver


def close_browser(driver):
    driver.quit()
    print("Browser closed.")


def accept_cookies_if_present(driver, wait_time=12):
    wait = WebDriverWait(driver, wait_time)
    try:
        button = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[.//text()[contains(.,'Accept all') or contains(.,'Aceptar todo')]]"
            ))
        )
        button.click()
        print("Cookies accepted (main page).")
        return
    except Exception:
        pass

    try:
        wait.until(EC.frame_to_be_available_and_switch_to_it((
            By.CSS_SELECTOR, "iframe[src*='consent']"
        )))
        try:
            button = wait.until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//button[.//text()[contains(.,'Accept all') or contains(.,'Aceptar todo')]]"
                ))
            )
            button.click()
            print("Cookies accepted (iframe).")
        except Exception:
            print("No cookie button found in iframe.")
        finally:
            driver.switch_to.default_content()
    except Exception:
        print("No consent iframe shown.")


def extract_all_distances_js(driver) -> list | str:
    js = r"""
    return (function() {
      const re = /\b\d+(?:[.,]\d+)?\s*(?:km|m)\b/;
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      let node, results = [];

      const isVisible = (el) => {
        if (!el) return false;
        const style = window.getComputedStyle(el);
        if (!style || style.visibility === 'hidden' || style.display === 'none') return false;
        const rect = el.getBoundingClientRect();
        return (rect.width > 0 && rect.height > 0);
      };

      // Look for "not found" style messages anywhere in DOM
      const errorTexts = document.body.innerText.toLowerCase();
      if (
        errorTexts.includes("google maps can't find") ||
        errorTexts.includes("no results found") ||
        errorTexts.includes("google maps no encuentra") ||
        errorTexts.includes("no se han encontrado resultados") ||
        errorTexts.includes("could not calculate directions") ||
        errorTexts.includes("we could not calculate directions")
      ) {
        return "not_found";
      }

      // Otherwise collect visible distances like before
      while ((node = walker.nextNode())) {
        const text = (node.textContent || '').trim();
        if (!text) continue;
        if (text.length > 80) continue;

        const m = text.match(re);
        if (m) {
          const el = node.parentElement;
          if (isVisible(el)) results.push(m[0]);
        }
      }

      return results;
    })();
    """
    return driver.execute_script(js)


def to_meters(dist_str):
    num = float(re.search(r'[\d.,]+', dist_str).group().replace(',', '.'))
    return num * 1000 if 'km' in dist_str else num


def get_longest_distance_gmaps(origin: str, destination: str, driver, wait_extra: int = 5) -> str:
    if "Carretera Cortijo El Acebuchal" in origin:
        origin = "Carretera Cortijo El Acebuchal, Carretera de Benagalbón, 29730"
    elif "Carretera Cortijo El Acebuchal" in destination:
        destination = "Carretera Cortijo El Acebuchal, Carretera de Benagalbón, 29730"
    elif "Calle Cortijo Los Morenos Altos" in origin:
        origin = "Cortijo los Morenos Altos, 12, Rincón, 29738"
    elif "Calle Cortijo Los Morenos Altos" in destination:
        destination = "Cortijo los Morenos Altos, 12, Rincón, 29738"

    if "(" in origin.lower() and "málaga" not in origin.lower():
        origin = re.sub(r"\s*\((?!.*málaga).*?\)\s*", "", origin, flags=re.IGNORECASE)

    if "(" in destination.lower() and "málaga" not in destination.lower():
        destination = re.sub(r"\s*\((?!.*málaga).*?\)\s*", "", destination, flags=re.IGNORECASE)

    # Extract formatted address
    origin = extract_address_parts(origin)
    destination = extract_address_parts(destination)

    url = (
        "https://www.google.com/maps/dir/"
        f"?api=1&origin={origin}&destination={destination}"
        "&travelmode=driving&units=metric&hl=en"
    )
    print(f"Loading URL: {url}")
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 25)
        accept_cookies_if_present(driver, wait_time=12)

        # wait for main directions panel
        try:
            wait.until(EC.presence_of_element_located((
                By.XPATH, "//*[contains(@class,'section-directions') or contains(@id,'pane') or contains(@class,'widget-directions')]"
            )))
        except Exception:
            pass

        time.sleep(wait_extra)  # give Google time to load alternative routes

        distances = extract_all_distances_js(driver)
        if not distances:
            return "0 km"

        if distances == "not_found":
            print(f"Address not found: {origin} -> {destination}")
            return "9999 km"

        # pick the largest
        max_distance = max(distances, key=to_meters)
        print(f"Longest distance detected: {max_distance}")
        if "km" not in max_distance:
            max_distance = "0 km"
        return max_distance

    except Exception as e:
        print(f"Error getting distance {origin} -> {destination}: {e}")
        return "0 km"
