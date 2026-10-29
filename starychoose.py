from pathlib import Path

import pandas as pd
import requests


def load_data(source_type: str, location: str) -> pd.DataFrame:
    if source_type == "csv":
        path = Path(location)

        if not path.exists():
            raise FileNotFoundError(f"Nie znaleziono pliku: {path}")

        return pd.read_csv(path)

    if source_type == "json":
        path = Path(location)

        if not path.exists():
            raise FileNotFoundError(f"Nie znaleziono pliku: {path}")

        return pd.read_json(path)

    if source_type == "api":
        response = requests.get(location, timeout=30)
        response.raise_for_status()
        return pd.json_normalize(response.json())

    raise ValueError("Nieznany typ źródła.")


def choose_source() -> pd.DataFrame:
    while True:
        print("\nWYBIERZ ŹRÓDŁO DANYCH")
        print("1. CSV")
        print("2. JSON")
        print("3. API")

        choice = input("Wpisz 1, 2 albo 3: ").strip()

        try:
            if choice == "1":
                path = input("Podaj ścieżkę do pliku CSV: ").strip()
                data = load_data("csv", path)

            elif choice == "2":
                path = input("Podaj ścieżkę do pliku JSON: ").strip()
                data = load_data("json", path)

            elif choice == "3":
                url = input("Wklej adres API: ").strip()
                data = load_data("api", url)

            else:
                print("Wybierz 1, 2 albo 3.")
                continue

            print("\nDANE WCZYTANE POPRAWNIE")
            print(data.head(10))
            return data

        except Exception as error:
            print(f"\nBŁĄD: {error}")


if __name__ == "__main__":
    selected_data = choose_source()



    KOLEJNY NOWY 17PAZD




from pathlib import Path

import pandas as pd
import requests

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
PROCESSED_DIR = DATA_DIR / "processed"
DATAFRAME_PATH = PROCESSED_DIR / "df.pkl"


def clear_saved_data() -> None:
    """Usuwa poprzedni przesłany plik i poprzedni DataFrame."""
    for folder in (UPLOAD_DIR, PROCESSED_DIR):
        folder.mkdir(parents=True, exist_ok=True)

        for file_path in folder.iterdir():
            if file_path.is_file():
                file_path.unlink()


def save_dataframe(df: pd.DataFrame) -> Path:
    """Zapisuje DataFrame jako plik pickle."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_pickle(DATAFRAME_PATH)
    return DATAFRAME_PATH


def get_saved_dataframe_preview() -> dict:
    """Odczytuje DataFrame z pickle, wypisuje próbkę i przygotowuje ją do API."""
    df = pd.read_pickle(DATAFRAME_PATH)

    print("\nPRÓBKA DATAFRAME ODCZYTANA Z PICKLE:")
    print(df.head(10).to_string(index=False))

    return {
        "rows": len(df),
        "columns": list(df.columns),
        "preview": df.head(10).to_dict(orient="records"),
    }


def load_data(source_type: str, location: str) -> pd.DataFrame:
    if source_type == "csv":
        path = Path(location)
        if not path.exists():
            raise FileNotFoundError(f"Nie znaleziono pliku: {path}")
        return pd.read_csv(path)

    if source_type == "json":
        path = Path(location)
        if not path.exists():
            raise FileNotFoundError(f"Nie znaleziono pliku: {path}")
        return pd.read_json(path)

    if source_type == "api":
        response = requests.get(location, timeout=30)
        response.raise_for_status()
        return pd.json_normalize(response.json())

    raise ValueError("Nieznany typ źródła.")


def choose_source() -> pd.DataFrame:
    while True:
        print("\nWYBIERZ ŹRÓDŁO DANYCH")
        print("1. CSV")
        print("2. JSON")
        print("3. API")

        choice = input("Wpisz 1, 2 albo 3: ").strip()

        if choice == "1":
            source_type = "csv"
            location = input("Podaj ścieżkę do pliku CSV: ").strip()
        elif choice == "2":
            source_type = "json"
            location = input("Podaj ścieżkę do pliku JSON: ").strip()
        elif choice == "3":
            source_type = "api"
            location = input("Wklej adres API: ").strip()
        else:
            print("Wybierz 1, 2 albo 3.")
            continue

        try:
            clear_saved_data()
            df = load_data(source_type, location)
            saved_path = save_dataframe(df)

            print("\nDANE WCZYTANE POPRAWNIE")
            print(df.head(10))
            print(f"\nDataFrame zapisany w: {saved_path}")

            return df

        except Exception as error:
            print(f"\nBŁĄD: {error}")


if __name__ == "__main__":
    selected_data = choose_source()

    KOLEJNEY

    import os
from pathlib import Path

import pandas as pd
import requests
from google.cloud import storage

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
PROCESSED_DIR = DATA_DIR / "processed"
DATAFRAME_PATH = PROCESSED_DIR / "df.pkl"

GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
GCS_UPLOAD_PREFIX = "data/uploads"
GCS_PROCESSED_PREFIX = "data/processed"
GCS_DATAFRAME_BLOB = f"{GCS_PROCESSED_PREFIX}/df.pkl"


def get_gcs_bucket():
    """Zwraca bucket Cloud Storage ustawiony dla usługi."""
    if not GCS_BUCKET_NAME:
        raise RuntimeError(
            "Ustaw zmienną GCS_BUCKET_NAME w konfiguracji usługi Cloud Run."
        )

    return storage.Client().bucket(GCS_BUCKET_NAME)


def clear_saved_data() -> None:
    """Usuwa poprzednie pliki lokalne i kopie z Cloud Storage."""
    bucket = get_gcs_bucket()

    for prefix in (f"{GCS_UPLOAD_PREFIX}/", f"{GCS_PROCESSED_PREFIX}/"):
        for blob in bucket.list_blobs(prefix=prefix):
            blob.delete()

    for folder in (UPLOAD_DIR, PROCESSED_DIR):
        folder.mkdir(parents=True, exist_ok=True)

        for file_path in folder.iterdir():
            if file_path.is_file():
                file_path.unlink()


def save_dataframe(df: pd.DataFrame) -> str:
    """Zapisuje DataFrame jako df.pkl lokalnie i w Cloud Storage."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Zachowuje dotychczasowy zapis lokalny.
    df.to_pickle(DATAFRAME_PATH)

    bucket = get_gcs_bucket()

    # Kopiuje przesłany CSV do Cloud Storage.
    for file_path in UPLOAD_DIR.iterdir():
        if file_path.is_file():
            blob_name = f"{GCS_UPLOAD_PREFIX}/{file_path.name}"
            bucket.blob(blob_name).upload_from_filename(str(file_path))

    # Kopiuje df.pkl do Cloud Storage.
    bucket.blob(GCS_DATAFRAME_BLOB).upload_from_filename(
        str(DATAFRAME_PATH)
    )

    gcs_path = f"gs://{GCS_BUCKET_NAME}/{GCS_DATAFRAME_BLOB}"
    print(f"DataFrame zapisany w: {gcs_path}", flush=True)

    return gcs_path


def get_saved_dataframe_preview() -> dict:
    """Odczytuje df.pkl z Cloud Storage, wypisuje próbkę i zwraca ją do API."""
    bucket = get_gcs_bucket()
    blob = bucket.blob(GCS_DATAFRAME_BLOB)

    if not blob.exists():
        raise FileNotFoundError(
            f"Nie znaleziono pliku gs://{GCS_BUCKET_NAME}/{GCS_DATAFRAME_BLOB}"
        )

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    blob.download_to_filename(str(DATAFRAME_PATH))

    df = pd.read_pickle(DATAFRAME_PATH)

    print("\nPRÓBKA DATAFRAME ODCZYTANA Z PICKLE:", flush=True)
    print(df.head(10).to_string(index=False), flush=True)

    return {
        "rows": len(df),
        "columns": list(df.columns),
        "preview": df.head(10).to_dict(orient="records"),
    }


def load_data(source_type: str, location: str) -> pd.DataFrame:
    if source_type == "csv":
        path = Path(location)
        if not path.exists():
            raise FileNotFoundError(f"Nie znaleziono pliku: {path}")
        return pd.read_csv(path, sep=";")

    if source_type == "json":
        path = Path(location)
        if not path.exists():
            raise FileNotFoundError(f"Nie znaleziono pliku: {path}")
        return pd.read_json(path)

    if source_type == "api":
        response = requests.get(location, timeout=30)
        response.raise_for_status()
        return pd.json_normalize(response.json())

    raise ValueError("Nieznany typ źródła.")


def choose_source() -> pd.DataFrame:
    while True:
        print("\nWYBIERZ ŹRÓDŁO DANYCH")
        print("1. CSV")
        print("2. JSON")
        print("3. API")

        choice = input("Wpisz 1, 2 albo 3: ").strip()

        if choice == "1":
            source_type = "csv"
            location = input("Podaj ścieżkę do pliku CSV: ").strip()
        elif choice == "2":
            source_type = "json"
            location = input("Podaj ścieżkę do pliku JSON: ").strip()
        elif choice == "3":
            source_type = "api"
            location = input("Wklej adres API: ").strip()
        else:
            print("Wybierz 1, 2 albo 3.")
            continue

        try:
            clear_saved_data()
            df = load_data(source_type, location)
            saved_path = save_dataframe(df)

            print("\nDANE WCZYTANE POPRAWNIE")
            print(df.head(10))
            print(f"\nDataFrame zapisany w: {saved_path}")

            return df

        except Exception as error:
            print(f"\nBŁĄD: {error}")


if __name__ == "__main__":
    selected_data = choose_source()