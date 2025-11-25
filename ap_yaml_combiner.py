import yaml
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

# Drag-and-drop library
from tkinterdnd2 import DND_FILES, TkinterDnD


class RandomYamlGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Archipelago – Random YAML Generator")
        self.root.geometry("650x600")

        self.yaml_files = []
        self.weights = {}

        # Player/seed name
        tk.Label(root, text="Generated YAML Name:", font=("Arial", 12)).pack(pady=5)
        self.name_entry = tk.Entry(root, font=("Arial", 12))
        self.name_entry.insert(0, "MyRandomSeed")
        self.name_entry.pack(fill="x", padx=15)

        # File list
        tk.Label(root, text="YAMLs to Randomize Between:", font=("Arial", 12)).pack(pady=5)

        self.file_list = tk.Listbox(root, height=12, selectmode=tk.MULTIPLE)
        self.file_list.pack(fill="both", expand=True, padx=15)

        # Enable drag & drop onto the listbox
        self.file_list.drop_target_register(DND_FILES)
        self.file_list.dnd_bind("<<Drop>>", self.drop_yaml_files)

        # Buttons
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Add YAMLs", command=self.add_yaml_files).grid(row=0, column=0, padx=10)
        ttk.Button(btn_frame, text="Remove Selected", command=self.remove_selected).grid(row=0, column=1, padx=10)
        ttk.Button(btn_frame, text="Set Weights", command=self.set_weights).grid(row=1, column=0, padx=10, pady=5)
        ttk.Button(btn_frame, text="Generate Random YAML", command=self.generate_yaml).grid(row=1, column=1, padx=10)

    # ----------------------------------------------------------------------
    # Drag & Drop Handler
    # ----------------------------------------------------------------------

    def drop_yaml_files(self, event):
        paths = self.root.splitlist(event.data)
        for p in paths:
            p = p.strip()
            if p.lower().endswith((".yaml", ".yml")):
                if p not in self.yaml_files:
                    self.yaml_files.append(p)
                    self.file_list.insert(tk.END, p)
            else:
                messagebox.showwarning("Invalid File", f"Not a YAML file:\n{p}")

    # ----------------------------------------------------------------------

    def add_yaml_files(self):
        files = filedialog.askopenfilenames(filetypes=[("YAML Files", "*.yaml *.yml")])
        for f in files:
            if f not in self.yaml_files:
                self.yaml_files.append(f)
                self.file_list.insert(tk.END, f)

    def remove_selected(self):
        selected = list(self.file_list.curselection())
        selected.reverse()
        for index in selected:
            file = self.yaml_files[index]
            if file in self.weights:
                del self.weights[file]
            del self.yaml_files[index]
            self.file_list.delete(index)

    # ----------------------------------------------------------------------

    def set_weights(self):
        if not self.yaml_files:
            messagebox.showerror("Error", "No YAML files added.")
            return

        weight_window = tk.Toplevel(self.root)
        weight_window.title("Set Game Weights")

        entries = {}

        for i, file in enumerate(self.yaml_files):
            game_name = Path(file).stem
            tk.Label(weight_window, text=game_name).grid(row=i, column=0, padx=10, pady=5)
            entry = tk.Entry(weight_window)
            entry.insert(0, str(self.weights.get(file, 1)))
            entry.grid(row=i, column=1, padx=10, pady=5)
            entries[file] = entry

        def save_weights():
            for file, entry in entries.items():
                try:
                    w = int(entry.get())
                    if w < 0:
                        raise ValueError
                    self.weights[file] = w
                except:
                    messagebox.showerror("Error", f"Invalid weight for {file}")
                    return
            weight_window.destroy()

        ttk.Button(weight_window, text="Save", command=save_weights).grid(
            row=len(self.yaml_files), column=0, columnspan=2, pady=10
        )

    # ----------------------------------------------------------------------

    def generate_yaml(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Error", "YAML name cannot be empty.")
            return

        if not self.yaml_files:
            messagebox.showerror("Error", "No YAMLs selected.")
            return

        combined = {"name": name, "game": {}, "triggers": []}
        auto_triggers = []
        merged_triggers = []

        # ---------------------------------------------------------

        for yaml_path in self.yaml_files:
            try:
                with open(yaml_path, "r", encoding="utf-8") as f:
                    docs = list(yaml.safe_load_all(f))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load {yaml_path}\n{e}")
                return

            for slot in docs:

                yaml_name = slot.get("name", name)

                # MULTI-SLOT YAML
                if isinstance(slot.get("game"), dict):
                    for game in slot["game"].keys():
                        w = self.weights.get(yaml_path, 1)
                        combined["game"][game] = w
                        combined[game] = slot[game]

                        auto_triggers.append({
                            "option_name": "game",
                            "option_result": game,
                            "options": {None: {"name": yaml_name}}
                        })

                # SINGLE-SLOT YAML
                else:
                    game = slot["game"]
                    w = self.weights.get(yaml_path, 1)
                    combined["game"][game] = w
                    combined[game] = slot[game]

                    auto_triggers.append({
                        "option_name": "game",
                        "option_result": game,
                        "options": {None: {"name": yaml_name}}
                    })

                # Existing triggers
                if slot.get("triggers"):
                    merged_triggers.extend(slot["triggers"])

        combined["triggers"] = merged_triggers + auto_triggers

        # Save YAML
        save_path = filedialog.asksaveasfilename(
            defaultextension=".yaml",
            filetypes=[("YAML Files", "*.yaml")],
            initialfile=f"{name}.yaml"
        )

        if not save_path:
            return

        try:
            with open(save_path, "w", encoding="utf-8") as f:
                yaml.dump(combined, f, sort_keys=False)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save YAML\n{e}")
            return

        messagebox.showinfo("Success", "Random YAML created successfully!")


# ----------------------------------------------------------------------

if __name__ == "__main__":
    root = TkinterDnD.Tk()   # IMPORTANT: enable drag-and-drop
    RandomYamlGUI(root)
    root.mainloop()
