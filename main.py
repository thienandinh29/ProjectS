import sys

if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--self-test":
        # Explicit diagnostic mode never creates hooks or sends keyboard input.
        import json
        from pathlib import Path
        import tkinter as tk
        from telex_app.ui import App, SAMPLE
        from telex_app.engine import prepare
        from telex_app.oracle import Oracle
        from telex_app.importers import decode_text
        report = {}
        try:
            plan = prepare(SAMPLE)
            assert Oracle().render("".join(s.key for s in plan.strokes)) == SAMPLE
            report["telex_oracle"] = "passed"
            assert decode_text("Tiếng Việt".encode()) == "Tiếng Việt"
            from docx import Document
            Document()
            report["imports"] = "passed"
            root = tk.Tk()
            root.withdraw()
            app = App(root)
            root.update_idletasks()
            assert app.start_button.instate(["disabled"])
            root.destroy()
            report["interface"] = "passed"
            report["keyboard_input_sent"] = False
        except Exception as error:
            report["error"] = str(error)
        Path(sys.argv[2]).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        sys.exit(1 if "error" in report else 0)
    else:
        from telex_app.ui import main
        main()
