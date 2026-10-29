from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, UploadFile
from choose_source import load_data

app = FastAPI()

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)


@app.get("/")
def home():
    return {"message": "API projektu działa"}


@app.post("/load-csv")
async def load_csv(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".csv"):
        return {"error": "Wybierz plik CSV."}

    saved_file = DATA_DIR / Path(file.filename).name
    content = await file.read()
    saved_file.write_bytes(content)

    data = load_data("csv", str(saved_file))

    return {
        "saved_file": str(saved_file),
        "filename": file.filename,
        "rows": len(data),
        "columns": list(data.columns),
        "preview": data.head(10).to_dict(orient="records"),
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)




    KOELJENY



from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile

from choose_source import (
    DATAFRAME_PATH,
    UPLOAD_DIR,
    clear_saved_data,
    get_saved_dataframe_preview,
    load_data,
    save_dataframe,
)

app = FastAPI()


@app.get("/")
def home():
    return {"message": "API projektu działa"}


@app.post("/load-csv")
async def load_csv(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Wybierz plik CSV.",
        )

    # Usuwa poprzedni plik wejściowy i poprzedni df.pkl.
    clear_saved_data()

    # Zapisuje nowy przesłany plik CSV.
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    saved_file = UPLOAD_DIR / Path(file.filename).name
    saved_file.write_bytes(await file.read())

    # Wczytuje CSV do DataFrame'u.
    try:
        df = load_data("csv", str(saved_file))
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))

    # Zapisuje DataFrame jako pickle.
    dataframe_path = save_dataframe(df)

    # Odczytuje pickle i wypisuje próbkę w terminalu.
    preview_data = get_saved_dataframe_preview()

    return {
        "uploaded_file": str(saved_file),
        "dataframe_file": str(dataframe_path),
        **preview_data,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)


    I KOLEJNEY 


    from html import escape
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse

from choose_source import (
    UPLOAD_DIR,
    clear_saved_data,
    get_saved_dataframe_preview,
    load_data,
    save_dataframe,
)
from select_columns import get_saved_columns, select_dataframe_columns

app = FastAPI()


@app.get("/")
def home():
    return {"message": "API projektu działa"}


@app.post("/load-csv")
async def load_csv(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Wybierz plik CSV.",
        )

    # Usuwa poprzedni plik wejściowy i poprzedni df.pkl.
    clear_saved_data()

    # Zapisuje nowy przesłany plik CSV.
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    saved_file = UPLOAD_DIR / Path(file.filename).name
    saved_file.write_bytes(await file.read())

    # Wczytuje CSV do DataFrame'u.
    try:
        df = load_data("csv", str(saved_file))
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))

    # Zapisuje DataFrame jako pickle.
    dataframe_path = save_dataframe(df)

    # Odczytuje pickle i wypisuje próbkę w terminalu.
    preview_data = get_saved_dataframe_preview()

    return {
        "uploaded_file": str(saved_file),
        "dataframe_file": str(dataframe_path),
        **preview_data,
    }


@app.get("/select-columns", response_class=HTMLResponse)
def show_column_selection_form():
    try:
        columns = get_saved_columns()
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))

    options = "".join(
        f'<option value="{escape(column, quote=True)}">'
        f"{escape(column)}</option>"
        for column in columns
    )

    feature_checkboxes = "".join(
        f'<label class="feature">'
        f'<input type="checkbox" name="feature_columns" '
        f'value="{escape(column, quote=True)}">'
        f" {escape(column)}</label>"
        for column in columns
    )

    return f"""
    <!DOCTYPE html>
    <html lang="pl">
    <head>
        <meta charset="UTF-8">
        <title>Wybór kolumn</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 32px; }}
            label {{ display: block; margin: 16px 0 6px; }}
            select {{ min-width: 280px; padding: 6px; }}
            .feature {{ margin: 8px 0; }}
            button {{ margin-top: 20px; padding: 8px 16px; }}
        </style>
    </head>
    <body>
        <h1>Wybierz kolumny z DataFrame'u</h1>

        <form method="post" action="/select-columns">
            <label for="date_column">Kolumna daty:</label>
            <select id="date_column" name="date_column" required>
                {options}
            </select>

            <label for="target_column">Kolumna celu, czyli przewidywany popyt:</label>
            <select id="target_column" name="target_column" required>
                {options}
            </select>

            <p>Wybierz kolumny cech:</p>
            {feature_checkboxes}

            <button type="submit">Zapisz wybrane kolumny</button>
        </form>

        <script>
            const dateSelect = document.getElementById("date_column");
            const targetSelect = document.getElementById("target_column");
            const featureCheckboxes =
                document.querySelectorAll('input[name="feature_columns"]');

            function updateFeatureChoices() {{
                const excluded = new Set([
                    dateSelect.value,
                    targetSelect.value
                ]);

                featureCheckboxes.forEach((checkbox) => {{
                    checkbox.disabled = excluded.has(checkbox.value);
                    if (checkbox.disabled) {{
                        checkbox.checked = false;
                    }}
                }});
            }}

            dateSelect.addEventListener("change", updateFeatureChoices);
            targetSelect.addEventListener("change", updateFeatureChoices);
            updateFeatureChoices();
        </script>
    </body>
    </html>
    """


@app.post("/select-columns", response_class=HTMLResponse)
def submit_column_selection(
    date_column: str = Form(...),
    target_column: str = Form(...),
    feature_columns: list[str] = Form(default=[]),
):
    try:
        result = select_dataframe_columns(
            date_column=date_column,
            target_column=target_column,
            feature_columns=feature_columns,
        )
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    return f"""
    <!DOCTYPE html>
    <html lang="pl">
    <head>
        <meta charset="UTF-8">
        <title>Wybrane kolumny</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 32px; }}
            table {{ border-collapse: collapse; margin-top: 16px; }}
            th, td {{ border: 1px solid #999; padding: 6px 10px; }}
        </style>
    </head>
    <body>
        <h1>Wybrane dane zapisane</h1>
        <p>Plik: {escape(result["selected_dataframe_file"])}</p>
        <p>Liczba wierszy: {result["rows"]}</p>
        <p>Wybrane kolumny: {escape(", ".join(result["columns"]))}</p>
        <h2>Próbka DataFrame'u</h2>
        {result["preview_html"]}
        <p><a href="/select-columns">Wróć do wyboru kolumn</a></p>
    </body>
    </html>
    """


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)












kolejny










from html import escape
from pathlib import Path

import pandas as pd
import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse

from choose_source import (
    UPLOAD_DIR,
    clear_saved_data,
    get_saved_dataframe_preview,
    load_data,
    save_dataframe,
)
from select_columns import get_saved_columns, select_dataframe_columns

app = FastAPI()


def page(content: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html lang="pl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Projekt AI</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 1000px;
                   margin: 32px auto; padding: 0 16px; }}
            label {{ display: block; margin: 14px 0 6px; }}
            select, input[type="file"] {{ padding: 8px; }}
            select {{ min-width: 280px; }}
            .feature {{ margin: 8px 0; }}
            button {{ margin: 20px 0; padding: 10px 16px; cursor: pointer; }}
            table {{ border-collapse: collapse; margin-top: 16px; }}
            th, td {{ border: 1px solid #999; padding: 6px 10px; }}
            .message {{ margin: 16px 0; }}
        </style>
    </head>
    <body>
        {content}
    </body>
    </html>
    """


def upload_form(message: str = "") -> HTMLResponse:
    message_html = f'<p class="message">{escape(message)}</p>' if message else ""

    return HTMLResponse(page(f"""
        <h1>Wczytaj dane i wybierz kolumny</h1>
        {message_html}

        <form method="post" action="/" enctype="multipart/form-data">
            <label for="file">Wybierz plik CSV:</label>
            <input id="file" type="file" name="file" accept=".csv" required>
            <br>
            <button type="submit">Wczytaj CSV</button>
        </form>
    """))


def column_form(columns: list[str], preview_html: str = "") -> HTMLResponse:
    options = "".join(
        f'<option value="{escape(column, quote=True)}">'
        f"{escape(column)}</option>"
        for column in columns
    )

    feature_checkboxes = "".join(
        f'<label class="feature">'
        f'<input type="checkbox" name="feature_columns" '
        f'value="{escape(column, quote=True)}"> {escape(column)}</label>'
        for column in columns
    )

    return HTMLResponse(page(f"""
        <h1>Wybierz kolumny</h1>
        <p>Plik został wczytany. Oto próbka danych z DataFrame'u:</p>
        {preview_html}

        <form method="post" action="/">
            <label for="date_column">Kolumna daty:</label>
            <select id="date_column" name="date_column" required>
                {options}
            </select>

            <label for="target_column">Kolumna celu, czyli przewidywana wartość:</label>
            <select id="target_column" name="target_column" required>
                {options}
            </select>

            <p>Wybierz kolumny cech:</p>
            {feature_checkboxes}

            <button type="submit">Zapisz wybrane kolumny</button>
        </form>

        <script>
            const dateSelect = document.getElementById("date_column");
            const targetSelect = document.getElementById("target_column");
            const checkboxes =
                document.querySelectorAll('input[name="feature_columns"]');

            function updateFeatures() {{
                const excluded = new Set([
                    dateSelect.value,
                    targetSelect.value
                ]);

                checkboxes.forEach((checkbox) => {{
                    checkbox.disabled = excluded.has(checkbox.value);
                    if (checkbox.disabled) {{
                        checkbox.checked = false;
                    }}
                }});
            }}

            dateSelect.addEventListener("change", updateFeatures);
            targetSelect.addEventListener("change", updateFeatures);
            updateFeatures();
        </script>
    """))


def selected_result(result: dict) -> HTMLResponse:
    return HTMLResponse(page(f"""
        <h1>Wybrane dane zapisane</h1>
        <p>Plik: {escape(result["selected_dataframe_file"])}</p>
        <p>Liczba wierszy: {result["rows"]}</p>
        <p>Wybrane kolumny: {escape(", ".join(result["columns"]))}</p>
        <h2>Próbka zapisanego DataFrame'u</h2>
        {result["preview_html"]}
        <p><a href="/">Wróć do początku</a></p>
    """))


@app.get("/", response_class=HTMLResponse)
def home():
    return upload_form()


@app.post("/", response_class=HTMLResponse)
async def continue_workflow(
    file: UploadFile | None = File(default=None),
    date_column: str | None = Form(default=None),
    target_column: str | None = Form(default=None),
    feature_columns: list[str] = Form(default=[]),
):
    # Krok 1: użytkownik przesyła CSV.
    if file is not None and file.filename:
        if not file.filename.lower().endswith(".csv"):
            return upload_form("Wybierz plik CSV.")

        clear_saved_data()
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        saved_file = UPLOAD_DIR / Path(file.filename).name
        saved_file.write_bytes(await file.read())

        try:
            df = load_data("csv", str(saved_file))
            save_dataframe(df)

            # Odczytuje zapisany DataFrame z pickle i wypisuje próbkę w logach.
            preview_data = get_saved_dataframe_preview()
            preview_html = pd.DataFrame(
                preview_data["preview"]
            ).to_html(index=False, escape=True)

            # Nazwy kolumn formularza pobiera z zapisanego DataFrame'u.
            columns = get_saved_columns()
            return column_form(columns, preview_html)

        except Exception as error:
            return upload_form(f"Błąd wczytywania pliku: {error}")

    # Krok 2: użytkownik wybiera kolumny. Funkcja zapisuje df_selected.pkl.
    if date_column and target_column:
        try:
            result = select_dataframe_columns(
                date_column=date_column,
                target_column=target_column,
                feature_columns=feature_columns,
            )
            return selected_result(result)
        except (FileNotFoundError, ValueError) as error:
            return upload_form(str(error))

    return upload_form("Najpierw wybierz plik CSV.")


@app.post("/load-csv")
async def load_csv(file: UploadFile = File(...)):
    """Dotychczasowy endpoint API pozostaje dostępny."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Wybierz plik CSV.")

    clear_saved_data()
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    saved_file = UPLOAD_DIR / Path(file.filename).name
    saved_file.write_bytes(await file.read())

    try:
        df = load_data("csv", str(saved_file))
        dataframe_path = save_dataframe(df)
        preview_data = get_saved_dataframe_preview()
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))

    return {
        "uploaded_file": str(saved_file),
        "dataframe_file": str(dataframe_path),
        **preview_data,
    }


@app.get("/select-columns", response_class=HTMLResponse)
def show_column_selection_form():
    """Dotychczasowa strona wyboru kolumn pozostaje dostępna."""
    try:
        columns = get_saved_columns()
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))

    return column_form(columns)


@app.post("/select-columns", response_class=HTMLResponse)
def submit_column_selection(
    date_column: str = Form(...),
    target_column: str = Form(...),
    feature_columns: list[str] = Form(default=[]),
):
    """Dotychczasowy endpoint zapisu wyboru pozostaje dostępny."""
    try:
        result = select_dataframe_columns(
            date_column=date_column,
            target_column=target_column,
            feature_columns=feature_columns,
        )
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    return selected_result(result)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)























    kolejny
    from html import escape
from pathlib import Path
from typing import List, Optional

import pandas as pd
import uvicorn
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse

from choose_source import (
    UPLOAD_DIR,
    clear_saved_data,
    get_saved_dataframe_preview,
    load_data,
    save_dataframe,
)
from select_columns import get_saved_columns, select_dataframe_columns


app = FastAPI()


def make_page(content: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html lang="pl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Wybór danych</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 1100px;
                margin: 32px auto;
                padding: 0 16px;
            }}
            label {{ display: block; margin: 10px 0; }}
            button {{ padding: 10px 16px; margin-top: 16px; }}
            table {{ border-collapse: collapse; margin-top: 16px; }}
            th, td {{ border: 1px solid #999; padding: 6px 10px; }}
            .message {{ margin: 16px 0; }}
        </style>
    </head>
    <body>{content}</body>
    </html>
    """


def upload_page(message: str = "") -> HTMLResponse:
    message_html = f'<p class="message">{escape(message)}</p>' if message else ""

    return HTMLResponse(make_page(f"""
        <h1>Wczytaj plik CSV</h1>
        {message_html}
        <form method="post" action="/" enctype="multipart/form-data">
            <input type="hidden" name="action" value="upload">
            <label for="file">Wybierz plik CSV:</label>
            <input id="file" type="file" name="file" accept=".csv" required>
            <button type="submit">Wczytaj CSV</button>
        </form>
    """))


def selection_page(
    columns: List[str],
    preview_html: str,
    message: str = "",
) -> HTMLResponse:
    checkboxes = "".join(
        f"""
        <label>
            <input type="checkbox" name="selected_columns"
                   value="{escape(column, quote=True)}">
            {escape(column)}
        </label>
        """
        for column in columns
    )

    message_html = f'<p class="message">{escape(message)}</p>' if message else ""

    return HTMLResponse(make_page(f"""
        <h1>Wybierz kolumny</h1>
        <p>Próbka wczytanego DataFrame'u:</p>
        {preview_html}
        {message_html}
        <form method="post" action="/">
            <input type="hidden" name="action" value="select">
            <p>Zaznacz jedną lub więcej kolumn:</p>
            {checkboxes}
            <button type="submit">Zapisz wybrane kolumny</button>
        </form>
    """))


def result_page(result: dict) -> HTMLResponse:
    return HTMLResponse(make_page(f"""
        <h1>Wybrane dane zapisane</h1>
        <p>DataFrame: {escape(result["selected_dataframe_file"])}</p>
        <p>Lista kolumn: {escape(result["selected_columns_file"])}</p>
        <p>Liczba wierszy: {result["rows"]}</p>
        <p>Wybrane kolumny: {escape(", ".join(result["columns"]))}</p>
        <h2>Próbka zapisanego DataFrame'u</h2>
        {result["preview_html"]}
        <p><a href="/">Wczytaj kolejny plik</a></p>
    """))


@app.get("/", response_class=HTMLResponse)
def home():
    return upload_page()


@app.post("/", response_class=HTMLResponse)
async def continue_workflow(
    action: str = Form(...),
    file: Optional[UploadFile] = File(default=None),
    selected_columns: List[str] = Form(default=[]),
):
    if action == "upload":
        if file is None or not file.filename:
            return upload_page("Wybierz plik CSV.")

        if not file.filename.lower().endswith(".csv"):
            return upload_page("Wybierz plik CSV.")

        try:
            clear_saved_data()

            UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            saved_file = UPLOAD_DIR / Path(file.filename).name
            saved_file.write_bytes(await file.read())

            df = load_data("csv", str(saved_file))
            save_dataframe(df)

            preview_data = get_saved_dataframe_preview()
            preview_html = pd.DataFrame(
                preview_data["preview"]
            ).to_html(index=False, escape=True)

            columns = get_saved_columns()

            return selection_page(columns, preview_html)

        except Exception as error:
            return upload_page(f"Błąd wczytywania CSV: {error}")

    if action == "select":
        try:
            result = select_dataframe_columns(selected_columns)
            return result_page(result)

        except (FileNotFoundError, ValueError) as error:
            try:
                columns = get_saved_columns()
                preview_data = get_saved_dataframe_preview()
                preview_html = pd.DataFrame(
                    preview_data["preview"]
                ).to_html(index=False, escape=True)

                return selection_page(
                    columns,
                    preview_html,
                    str(error),
                )
            except Exception as read_error:
                return upload_page(str(read_error))

    return upload_page("Nieznana czynność.")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)






























    kolejny


    from html import escape
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse

from choose_source import (
    UPLOAD_DIR,
    clear_saved_data,
    get_saved_dataframe_preview,
    load_data,
    save_dataframe,
)
from detect_types import detect_types
from select_columns import get_saved_columns, select_dataframe_columns
from set_date import (
    get_date_column_options,
    save_date_settings,
    set_date,
)


app = FastAPI()


def _page(title: str, body: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html lang="pl">
    <head>
        <meta charset="UTF-8">
        <title>{escape(title)}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 1100px;
                margin: 36px auto;
                padding: 0 20px;
                color: #222;
            }}
            h1 {{ margin-bottom: 22px; }}
            label {{ display: block; margin: 10px 0; }}
            button {{
                margin-top: 18px;
                padding: 10px 18px;
                cursor: pointer;
            }}
            table {{
                border-collapse: collapse;
                margin: 16px 0;
                width: 100%;
            }}
            th, td {{
                border: 1px solid #aaa;
                padding: 8px;
                text-align: left;
            }}
            .section {{ margin: 22px 0; }}
            .error {{ color: #a00; }}
        </style>
    </head>
    <body>
        <h1>{escape(title)}</h1>
        {body}
    </body>
    </html>
    """


def _selection_form() -> str:
    preview_data = get_saved_dataframe_preview()
    columns = get_saved_columns()

    checkboxes = "".join(
        f'<label><input type="checkbox" name="selected_columns" '
        f'value="{escape(column, quote=True)}"> '
        f'{escape(column)}</label>'
        for column in columns
    )

    preview_html = _records_to_html(
        preview_data["preview"],
        preview_data["columns"],
    )

    return _page(
        "Wybierz kolumny",
        f"""
        <div class="section">
            <p>Próbka wczytanego DataFrame'u:</p>
            {preview_html}
        </div>
        <form method="post" action="/select-columns">
            <p>Zaznacz jedną lub więcej kolumn:</p>
            {checkboxes}
            <button type="submit">Zapisz wybrane kolumny</button>
        </form>
        """,
    )


def _records_to_html(records: list, columns: list) -> str:
    if not records:
        return "<p>Brak danych do wyświetlenia.</p>"

    headers = "".join(f"<th>{escape(str(column))}</th>" for column in columns)

    rows = []
    for record in records:
        cells = "".join(
            f"<td>{escape(str(record.get(column, '')))}</td>"
            for column in columns
        )
        rows.append(f"<tr>{cells}</tr>")

    return (
        "<table><thead><tr>"
        + headers
        + "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


@app.get("/", response_class=HTMLResponse)
def home():
    return _page(
        "Wczytaj plik CSV",
        """
        <form method="post" action="/load-csv" enctype="multipart/form-data">
            <label for="file">Wybierz plik CSV:</label>
            <input id="file" type="file" name="file" accept=".csv" required>
            <button type="submit">Wczytaj CSV</button>
        </form>
        """,
    )


@app.post("/load-csv", response_class=HTMLResponse)
async def load_csv(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Wybierz plik CSV.")

    clear_saved_data()

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    saved_file = UPLOAD_DIR / Path(file.filename).name
    saved_file.write_bytes(await file.read())

    try:
        df = load_data("csv", str(saved_file))
        save_dataframe(df)
        return _selection_form()
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.get("/select-columns", response_class=HTMLResponse)
def show_column_selection_form():
    try:
        return _selection_form()
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.post("/select-columns", response_class=HTMLResponse)
def submit_column_selection(
    selected_columns: list[str] = Form(default=[]),
):
    try:
        result = select_dataframe_columns(selected_columns)
        detected_types = detect_types()

        type_summary = "".join(
            f"<p><strong>{escape(type_name)}:</strong> "
            f"{escape(', '.join(columns) if columns else 'brak')}</p>"
            for type_name, columns in detected_types.items()
        )

        return _page(
            "Wybrane dane zapisane",
            f"""
            <p>DataFrame: {escape(result["selected_dataframe_file"])}</p>
            <p>Lista kolumn: {escape(result["selected_columns_file"])}</p>
            <p>Liczba wierszy: {result["rows"]}</p>
            <p>Wybrane kolumny: {escape(", ".join(result["columns"]))}</p>

            <h2>Rozpoznane typy kolumn</h2>
            {type_summary}

            <h2>Próbka zapisanego DataFrame'u</h2>
            {result["preview_html"]}

            <p><a href="/set-date">Przejdź do ustawień daty</a></p>
            <p><a href="/">Wczytaj kolejny plik</a></p>
            """,
        )
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.get("/set-date", response_class=HTMLResponse)
def show_date_settings_form():
    try:
        date_columns = get_date_column_options()

        options = "".join(
            f'<option value="{escape(column, quote=True)}">'
            f"{escape(column)}</option>"
            for column in date_columns
        )

        return _page(
            "Ustawienia daty",
            f"""
            <form method="post" action="/set-date">
                <label for="date_column">Kolumna daty:</label>
                <select id="date_column" name="date_column" required>
                    {options}
                </select>

                <label for="duplicate_method">
                    Obsługa duplikatów dla danych liczbowych:
                </label>
                <select id="duplicate_method" name="duplicate_method">
                    <option value="mean">Średnia</option>
                    <option value="sum">Suma</option>
                </select>

                <label for="fill_method">Uzupełnianie braków:</label>
                <select id="fill_method" name="fill_method">
                    <option value="zero">Zera</option>
                    <option value="ffill">Poprzednia wartość</option>
                    <option value="mean">Średnia</option>
                </select>

                <button type="submit">Zapisz ustawienia i przetwórz dane</button>
            </form>
            """,
        )
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.post("/set-date", response_class=HTMLResponse)
def submit_date_settings(
    date_column: str = Form(...),
    duplicate_method: str = Form(...),
    fill_method: str = Form(...),
):
    try:
        settings_path = save_date_settings(
            date_column=date_column,
            duplicate_method=duplicate_method,
            fill_method=fill_method,
        )
        result = set_date()

        return _page(
            "Dane przygotowane według daty",
            f"""
            <p>Ustawienia: {escape(settings_path)}</p>
            <p>DataFrame: {escape(result["dataframe_file"])}</p>
            <p>Liczba wierszy: {result["rows"]}</p>
            <p>Kolumny: {escape(", ".join(result["columns"]))}</p>

            <h2>Próbka zapisanego DataFrame'u</h2>
            {result["preview_html"]}

            <p><a href="/">Wczytaj kolejny plik</a></p>
            """,
        )
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)




































    KOLENE 



    from html import escape
from pathlib import Path

import pandas as pd
import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse

from choose_source import (
    UPLOAD_DIR,
    clear_saved_data,
    get_saved_dataframe_preview,
    load_data,
    save_dataframe,
)
from clean_data import (
    clean_data,
    get_cleaning_options,
    save_cleaning_methods,
)
from date_features import (
    date_features,
    get_date_source_options,
    save_date_source,
)
from detect_types import detect_types
from select_columns import get_saved_columns, select_dataframe_columns
from set_date import (
    get_date_column_options,
    save_date_settings,
    set_date,
)


app = FastAPI()


def _page(title: str, body: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html lang="pl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{escape(title)}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 1100px;
                margin: 36px auto;
                padding: 0 20px;
                color: #222;
            }}
            h1 {{ margin-bottom: 22px; }}
            label {{ display: block; margin: 10px 0; }}
            select, input {{ padding: 6px; }}
            button {{
                margin-top: 18px;
                padding: 10px 18px;
                cursor: pointer;
            }}
            table {{
                border-collapse: collapse;
                margin: 16px 0;
                width: 100%;
            }}
            th, td {{
                border: 1px solid #aaa;
                padding: 8px;
                text-align: left;
            }}
            .section {{ margin: 22px 0; }}
            .error {{ color: #a00; }}
        </style>
    </head>
    <body>
        <h1>{escape(title)}</h1>
        {body}
    </body>
    </html>
    """


def _records_to_html(records: list, columns: list) -> str:
    if not records:
        return "<p>Brak danych do wyświetlenia.</p>"

    headers = "".join(
        f"<th>{escape(str(column))}</th>"
        for column in columns
    )

    rows = []
    for record in records:
        cells = "".join(
            f"<td>{escape(str(record.get(column, '')))}</td>"
            for column in columns
        )
        rows.append(f"<tr>{cells}</tr>")

    return (
        "<table><thead><tr>"
        + headers
        + "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def _selection_form() -> str:
    preview_data = get_saved_dataframe_preview()
    columns = get_saved_columns()

    checkboxes = "".join(
        f'<label><input type="checkbox" name="selected_columns" '
        f'value="{escape(column, quote=True)}"> '
        f'{escape(column)}</label>'
        for column in columns
    )

    preview_html = _records_to_html(
        preview_data["preview"],
        preview_data["columns"],
    )

    return _page(
        "Wybierz kolumny",
        f"""
        <div class="section">
            <p>Próbka wczytanego DataFrame'u:</p>
            {preview_html}
        </div>
        <form method="post" action="/select-columns">
            <p>Zaznacz jedną lub więcej kolumn:</p>
            {checkboxes}
            <button type="submit">Zapisz wybrane kolumny</button>
        </form>
        """,
    )


@app.get("/", response_class=HTMLResponse)
def home():
    return _page(
        "Wczytaj plik CSV",
        """
        <form method="post" action="/load-csv" enctype="multipart/form-data">
            <label for="file">Wybierz plik CSV:</label>
            <input id="file" type="file" name="file" accept=".csv" required>
            <button type="submit">Wczytaj CSV</button>
        </form>
        """,
    )


@app.post("/load-csv", response_class=HTMLResponse)
async def load_csv(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Wybierz plik CSV.")

    try:
        clear_saved_data()

        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        saved_file = UPLOAD_DIR / Path(file.filename).name
        saved_file.write_bytes(await file.read())

        df = load_data("csv", str(saved_file))
        save_dataframe(df)

        return _selection_form()

    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.get("/select-columns", response_class=HTMLResponse)
def show_column_selection_form():
    try:
        return _selection_form()
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.post("/select-columns", response_class=HTMLResponse)
def submit_column_selection(
    selected_columns: list[str] = Form(default=[]),
):
    try:
        result = select_dataframe_columns(selected_columns)
        detected_types = detect_types()

        type_summary = "".join(
            f"<p><strong>{escape(type_name)}:</strong> "
            f"{escape(', '.join(columns) if columns else 'brak')}</p>"
            for type_name, columns in detected_types.items()
        )

        return _page(
            "Wybrane dane zapisane",
            f"""
            <p>DataFrame: {escape(result["selected_dataframe_file"])}</p>
            <p>Lista kolumn: {escape(result["selected_columns_file"])}</p>
            <p>Liczba wierszy: {result["rows"]}</p>
            <p>Wybrane kolumny: {escape(", ".join(result["columns"]))}</p>

            <h2>Rozpoznane typy kolumn</h2>
            {type_summary}

            <h2>Próbka zapisanego DataFrame'u</h2>
            {result["preview_html"]}

            <p><a href="/set-date">Przejdź do ustawień daty</a></p>
            <p><a href="/">Wczytaj kolejny plik</a></p>
            """,
        )

    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.get("/set-date", response_class=HTMLResponse)
def show_date_settings_form():
    try:
        date_columns = get_date_column_options()
        options = "".join(
            f'<option value="{escape(column, quote=True)}">'
            f"{escape(column)}</option>"
            for column in date_columns
        )

        return _page(
            "Ustawienia daty",
            f"""
            <form method="post" action="/set-date">
                <label for="date_column">Kolumna daty:</label>
                <select id="date_column" name="date_column" required>
                    {options}
                </select>

                <label for="duplicate_method">
                    Obsługa duplikatów dla danych liczbowych:
                </label>
                <select id="duplicate_method" name="duplicate_method">
                    <option value="mean">Średnia</option>
                    <option value="sum">Suma</option>
                </select>

                <label for="fill_method">Uzupełnianie braków:</label>
                <select id="fill_method" name="fill_method">
                    <option value="zero">Zera</option>
                    <option value="ffill">Poprzednia wartość</option>
                    <option value="mean">Średnia</option>
                </select>

                <button type="submit">
                    Zapisz ustawienia i przetwórz dane
                </button>
            </form>
            """,
        )

    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.post("/set-date", response_class=HTMLResponse)
def submit_date_settings(
    date_column: str = Form(...),
    duplicate_method: str = Form(...),
    fill_method: str = Form(...),
):
    try:
        settings_path = save_date_settings(
            date_column=date_column,
            duplicate_method=duplicate_method,
            fill_method=fill_method,
        )
        result = set_date()

        return _page(
            "Dane przygotowane według daty",
            f"""
            <p>Ustawienia: {escape(settings_path)}</p>
            <p>DataFrame: {escape(result["dataframe_file"])}</p>
            <p>Liczba wierszy: {result["rows"]}</p>
            <p>Kolumny: {escape(", ".join(result["columns"]))}</p>

            <h2>Próbka zapisanego DataFrame'u</h2>
            {result["preview_html"]}

            <p><a href="/clean-data">Przejdź do czyszczenia danych</a></p>
            <p><a href="/">Wczytaj kolejny plik</a></p>
            """,
        )

    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.get("/clean-data", response_class=HTMLResponse)
def show_cleaning_form():
    try:
        options = get_cleaning_options()

        fields = "".join(
            f"""
            <div class="section">
                <label>
                    <strong>{escape(item["column"])}</strong>
                    — braków: {item["missing"]}
                </label>
                <select name="methods" required>
                    <option value="none">Bez zmian</option>
                    <option value="drop">Usuń wiersze z brakiem</option>
                    <option value="zero">Uzupełnij zerem</option>
                    <option value="ffill">Uzupełnij poprzednią wartością</option>
                    <option value="mean">Średnia (tekst: poprzednia wartość)</option>
                </select>
            </div>
            """
            for item in options
        )

        return _page(
            "Czyszczenie danych",
            f"""
            <p>Dla każdej kolumny wybierz sposób obsługi brakujących wartości.
            Liczba braków pochodzi z <code>df_date.pkl</code>.</p>

            <form method="post" action="/clean-data">
                {fields}
                <button type="submit">Zapisz metody i wyczyść dane</button>
            </form>
            """,
        )

    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.post("/clean-data", response_class=HTMLResponse)
def submit_cleaning_form(methods: list[str] = Form(...)):
    try:
        options = get_cleaning_options()

        if len(methods) != len(options):
            raise ValueError("Wybierz metodę dla każdej kolumny.")

        method_map = {
            item["column"]: method
            for item, method in zip(options, methods)
        }

        settings_path = save_cleaning_methods(method_map)
        result = clean_data()

        return _page(
            "Dane wyczyszczone",
            f"""
            <p>Ustawienia: {escape(settings_path)}</p>
            <p>DataFrame: {escape(result["dataframe_file"])}</p>
            <p>Liczba wierszy: {result["rows"]}</p>
            <p>Kolumny: {escape(", ".join(result["columns"]))}</p>

            <h2>Próbka zapisanego DataFrame'u</h2>
            {result["preview_html"]}

            <p><a href="/date-features">
                Przejdź do tworzenia cech daty
            </a></p>
            """,
        )

    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.get("/date-features", response_class=HTMLResponse)
def show_date_features_form():
    try:
        options = get_date_source_options()

        if not options:
            raise ValueError("Nie znaleziono indeksu ani kolumn do wyboru.")

        choices = "".join(
            f'<option value="{escape(item["source"] + "|" + item["name"], quote=True)}">'
            f'{escape(item["label"])}</option>'
            for item in options
        )

        return _page(
            "Cechy daty",
            f"""
            <p>Wybierz indeks lub kolumnę zawierającą datę z
            <code>df_clean.pkl</code>.</p>

            <form method="post" action="/date-features">
                <label for="date_source">Źródło daty:</label>
                <select id="date_source" name="date_source" required>
                    {choices}
                </select>

                <button type="submit">Utwórz cechy daty</button>
            </form>
            """,
        )

    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.post("/date-features", response_class=HTMLResponse)
def submit_date_features(date_source: str = Form(...)):
    try:
        source, name = date_source.split("|", 1)
        settings_path = save_date_source(source, name)
        result = date_features()

        return _page(
            "Cechy daty zapisane",
            f"""
            <p>Ustawienia: {escape(settings_path)}</p>
            <p>DataFrame: {escape(result["dataframe_file"])}</p>
            <p>Liczba wierszy: {result["rows"]}</p>
            <p>Kolumny: {escape(", ".join(result["columns"]))}</p>

            <h2>Próbka zapisanego DataFrame'u</h2>
            {result["preview_html"]}

            <p><a href="/">Wczytaj kolejny plik</a></p>
            """,
        )

    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)






    NOWE

    import uvicorn
from fastapi import FastAPI

from clean_data_ui import router as clean_data_router
from columns_ui import router as columns_router
from date_features_ui import router as date_features_router
from date_ui import router as date_router
from upload_ui import router as upload_router

app = FastAPI()

app.include_router(upload_router)
app.include_router(columns_router)
app.include_router(date_router)
app.include_router(clean_data_router)
app.include_router(date_features_router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)

    




    KOLEJNEY



    import uvicorn
from fastapi import FastAPI

from upload_ui import router as upload_router
from columns_ui import router as columns_router
from date_ui import router as date_router
from clean_data_ui import router as clean_data_router
from date_features_ui import router as date_features_router
from create_lags_ui import router as create_lags_router
from rolling_stats_ui import router as rolling_stats_router


app = FastAPI()

app.include_router(upload_router)
app.include_router(columns_router)
app.include_router(date_router)
app.include_router(clean_data_router)
app.include_router(date_features_router)
app.include_router(create_lags_router)
app.include_router(rolling_stats_router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)






KOLEJNEY
import uvicorn
from fastapi import FastAPI

from upload_ui import router as upload_router
from columns_ui import router as columns_router
from date_ui import router as date_router
from clean_data_ui import router as clean_data_router
from date_features_ui import router as date_features_router
from create_lags_ui import router as create_lags_router
from rolling_stats_ui import router as rolling_stats_router
from set_target_ui import router as set_target_router
from transform_data_ui import router as transform_data_router


app = FastAPI()

app.include_router(upload_router)
app.include_router(columns_router)
app.include_router(date_router)
app.include_router(clean_data_router)
app.include_router(date_features_router)
app.include_router(create_lags_router)
app.include_router(rolling_stats_router)
app.include_router(set_target_router)
app.include_router(transform_data_router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)import uvicorn
from fastapi import FastAPI

from upload_ui import router as upload_router
from columns_ui import router as columns_router
from date_ui import router as date_router
from clean_data_ui import router as clean_data_router
from date_features_ui import router as date_features_router
from create_lags_ui import router as create_lags_router
from rolling_stats_ui import router as rolling_stats_router
from set_target_ui import router as set_target_router
from transform_data_ui import router as transform_data_router


app = FastAPI()

app.include_router(upload_router)
app.include_router(columns_router)
app.include_router(date_router)
app.include_router(clean_data_router)
app.include_router(date_features_router)
app.include_router(create_lags_router)
app.include_router(rolling_stats_router)
app.include_router(set_target_router)
app.include_router(transform_data_router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)









    


    