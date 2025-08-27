import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
import tkinter as tk
from tkinter import filedialog, ttk

# Mapping für Usage-Werte
usage_mapping = {
    "Preferred": {"forbidden": "false", "caseSensitive": "false", "preferred": "true"},
    "Deprecated": {"forbidden": "true", "caseSensitive": "false", "preferred": "false"},
    "Admitted": {"forbidden": "false", "caseSensitive": "true", "preferred": "false"}
}

# ---------------- XML Verarbeitung ----------------
def pretty_write(tree, filename):
    xml_str = ET.tostring(tree.getroot(), encoding='utf-8')
    parsed = minidom.parseString(xml_str)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(parsed.toprettyxml(indent="    "))

def process_file(input_file, output_file, progress_var, gui_root, status_label):
    tree = ET.parse(input_file)
    root_xml = tree.getroot()
    XML_NS = "http://www.w3.org/XML/1998/namespace"

    term_entries = root_xml.findall("text/body/termEntry")
    total = len(term_entries)

    for i, term_entry in enumerate(term_entries, start=1):
        de_def_node = term_entry.find(".//langSet[@xml:lang='de-DE']/descrip[@type='Definition']", {'xml': XML_NS})
        en_def_node = term_entry.find(".//langSet[@xml:lang='en-GB']/descrip[@type='Definition']", {'xml': XML_NS})
        de_text = de_def_node.text if de_def_node is not None else ""
        en_text = en_def_node.text if en_def_node is not None else ""

        ET.SubElement(term_entry, "descrip", {"type": "conceptDomain"}).text = "Kärcher"
        ET.SubElement(term_entry, "descrip", {"type": "conceptSubdomain"}).text = "General"

        for lang_set in term_entry.findall("langSet"):
            lang = lang_set.attrib.get("{http://www.w3.org/XML/1998/namespace}lang")
            for descrip in list(lang_set.findall("descrip")):
                lang_set.remove(descrip)
            text = de_text if lang == "de-DE" else en_text
            new_def = ET.Element("descrip", {"type": "conceptDefinition"})
            new_def.text = text
            lang_set.insert(0, new_def)

            for tig in lang_set.findall("tig"):
                usage_value = None
                for tn_type in ["Usage", "Usage TechDok", "Usage Marketing"]:
                    tn = tig.find(f"termNote[@type='{tn_type}']")
                    if tn is not None:
                        usage_value = tn.text
                        break
                for tn_type in ["Usage", "Usage TechDok", "Usage Marketing"]:
                    tn = tig.find(f"termNote[@type='{tn_type}']")
                    if tn is not None:
                        tig.remove(tn)
                if usage_value in usage_mapping:
                    mapping = usage_mapping[usage_value]
                    for k, v in mapping.items():
                        ET.SubElement(tig, "termNote", {"type": k}).text = v

        progress_var.set(int(i / total * 100))
        gui_root.update_idletasks()

    pretty_write(tree, output_file)
    progress_var.set(100)
    status_label.config(text=f"✅ Mapping abgeschlossen: {output_file}", fg="#F9E200")

# ---------------- GUI Funktionen ----------------
def select_file(entry_input, entry_output):
    file_path = filedialog.askopenfilename(filetypes=[("TBX files", "*.tbx")])
    if file_path:
        entry_input.delete(0, tk.END)
        entry_input.insert(0, file_path)
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        entry_output.delete(0, tk.END)
        entry_output.insert(0, base_name + "_mapped")

def start_mapping(entry_input, entry_output, progress_var, gui_root, status_label):
    status_label.config(text="", fg="#F9E200")  # vorher leeren
    input_file = entry_input.get().strip()
    name_only = entry_output.get().strip()  # nur Name
    if not input_file or not os.path.exists(input_file):
        status_label.config(text="❌ Fehler: Bitte eine gültige TBX-Datei auswählen.", fg="red")
        return

    folder = os.path.dirname(input_file)

    if not name_only:
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        name_only = base_name + "_mapped"

    output_file = os.path.join(folder, name_only + ".tbx")
    process_file(input_file, output_file, progress_var, gui_root, status_label)

# ---------------- GUI ----------------
root = tk.Tk()
root.title("TBX Mapper – Kärcher")
root.geometry("1000x450")
root.resizable(True, True)
root.config(bg="#2D2926")  # Anthrazit Hintergrund

main_frame = tk.Frame(root, padx=20, pady=20, bg="#2D2926")
main_frame.pack(fill="both", expand=True)

# Linke Seite: Bedienung
left_frame = tk.Frame(main_frame, bg="#2D2926")
left_frame.pack(side="left", fill="y", padx=(0,20))

# Titel
tk.Label(left_frame, text="TBX Mapper", fg="#F9E200", bg="#2D2926", font=("Arial", 18, "bold")).pack(anchor="w", pady=(0,15))

# Eingabefelder
def create_entry_with_label(parent, label_text):
    tk.Label(parent, text=label_text, fg="#FFFFFF", bg="#2D2926", font=("Arial", 10, "bold")).pack(anchor="w", pady=(5,0))
    entry = tk.Entry(parent, width=50, bg="#FFFFFF", relief="flat", highlightthickness=2, highlightbackground="#F9E200", highlightcolor="#F9E200")
    entry.pack(pady=(0,5))
    return entry

entry_input = create_entry_with_label(left_frame, "TBX-Datei auswählen:")
tk.Button(left_frame, text="Durchsuchen...", command=lambda: select_file(entry_input, entry_output),
          bg="#F9E200", fg="#2D2926", relief="flat", activebackground="#FFD700", width=15).pack(anchor="w", pady=(0,10))

entry_output = create_entry_with_label(left_frame, "Neuer Dateiname:")

# Fortschritt
tk.Label(left_frame, text="Fortschritt:", fg="#FFFFFF", bg="#2D2926", font=("Arial", 10, "bold")).pack(anchor="w", pady=(10,0))
progress_var = tk.IntVar()
progress_bar = ttk.Progressbar(left_frame, maximum=100, variable=progress_var, length=300)
progress_bar.pack(pady=5, anchor="w")

# Status-Label
status_label = tk.Label(left_frame, text="", fg="#F9E200", bg="#2D2926", font=("Arial", 10, "italic"))
status_label.pack(anchor="w", pady=(5,0))

# Mapping Button
tk.Button(left_frame, text="Mapping starten", 
          command=lambda: start_mapping(entry_input, entry_output, progress_var, root, status_label),
          width=25, height=2, bg="#F9E200", fg="#2D2926", font=("Arial", 11, "bold"),
          relief="flat", activebackground="#FFD700").pack(pady=20)

# Rechte Seite: Beschreibung / Infofeld
right_frame = tk.Frame(main_frame, relief="solid", borderwidth=1, padx=15, pady=15, bg="#FFFFFF")
right_frame.pack(side="right", fill="both", expand=True)

description = (
    "🔧 TBX Mapper Tool\n\n"
    "Dieses Tool dient zum Mappen von TBX-Exporten aus CONGREE\n"
    "für den Import in das PHRASE TMS.\n\n"
    "👉 Funktionen:\n"
    " • Definitionen werden angepasst\n"
    " • conceptDomain & Subdomain gesetzt\n"
    " • Usage-Werte (Preferred, Deprecated, Admitted) gemappt\n"
    " • Ausgabe immer als neue TBX-Datei im selben Ordner\n\n"
    "Einfach TBX-Datei auswählen, optional neuen Dateinamen vergeben\n"
    "und 'Mapping starten' klicken."
)

tk.Label(right_frame, text=description, justify="left", bg="#FFFFFF", font=("Arial", 10)).pack(anchor="nw")

root.mainloop()
