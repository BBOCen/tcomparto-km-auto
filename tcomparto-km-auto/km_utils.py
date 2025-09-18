import re
import fitz  # PyMuPDF

def extract_address_parts(address):
    if "(" in address:
        address = re.sub(r"\s*\(.*?\)\s*", "", address)

    print("Full address is: "+address)
    street = address.split(",")[0]
    if "CP: " in address:
        postcode = address.split("CP: ")[1].strip()
    else:
        postcode = ""

    if postcode == "29730":
        town = "Rincón"
    elif postcode == "29738":
        town = "Benagalbón"
    elif postcode == "29720":
        town = "La Cala"
    else:
        town = ""

    print(f"New address is: {street}, {town}, {postcode}")
    if "Carretera Cortijo El Acebuchal" in address:
        return "Carretera Cortijo El Acebuchal, Rincón, 29730"
    elif "Calle Cortijo Los Morenos Altos" in address:
        return "Cortijo los Morenos Altos, 12, Rincón, 29738"

    return f"{street}, {town}, {postcode}"

def write_distance_data(input_path, output_base_path, pdf_data, pdf_event_data):
    max_rows = 14
    distance_between_rows = 21
    output_index = 1
    event_count = 0

    def new_doc():
        return fitz.open(input_path)

    doc = new_doc()
    page = doc[0]

    # Write non-event data once per new file
    def write_static_data():
        for key in pdf_data:
            page.insert_text(
                (pdf_data[key]['x1'], pdf_data[key]['y2']),
                text=str(pdf_data[key]['value']),
                fontsize=12
            )

    write_static_data()

    # Combine event data into rows
    events = list(zip(
        pdf_event_data['event_dates'],
        pdf_event_data['event_addresses'],
        pdf_event_data['event_distances']
    ))

    total_km = 0

    for i, (date, address, distance) in enumerate(events):
        row_y = 301.84 + distance_between_rows * (event_count % max_rows)

        split_addresses = address.split("->")
        cleaned_addresses = []
        for a in split_addresses:
            cleaned_addresses.append(extract_address_parts(a))

        address = " -> ".join(cleaned_addresses)
        # Write event row
        page.insert_text((31.33, row_y), text=date, fontsize=10)
        page.insert_text((87.33, row_y), text=address, fontsize=8)
        page.insert_text((487.33, row_y), text=distance.strip(), fontsize=12)

        try:
            dist_float = float(re.findall(r'[\d.,]+', distance.replace(',', '.'))[0])
        except (IndexError, ValueError):
            dist_float = 0.0
        total_km += round(dist_float, 2)

        event_count += 1

        # When 14 rows are written, save and start a new file
        if event_count % max_rows == 0:
            output_path = f"{output_base_path}_page_{output_index}.pdf"
            page.insert_text((490.67, 598.71), text=f"{total_km:.2f}", fontsize=12)
            doc.save(output_path)
            doc.close()
            output_index += 1
            doc = new_doc()
            page = doc[0]
            write_static_data()

    # Save remaining data if not saved yet
    if event_count % max_rows != 0:
        output_path = f"{output_base_path}_page_{output_index}.pdf"
        page.insert_text((490.67, 598.71), text=f"{total_km:.2f}", fontsize=12)
        doc.save(output_path)
        doc.close()

def write_page_number(file_path, page_number):
    doc = fitz.open(file_path)
    page = doc[0]
    page.insert_text((460.67, 142.04), text=str(page_number), fontsize=12)
    doc.saveIncr()  # Save changes incrementally
    doc.close()
