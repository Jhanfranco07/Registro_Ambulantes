import pandas as pd

def load_data(path: str) -> pd.DataFrame:
    """
    Lee un CSV delimitado por ';', salta líneas mal formadas,
    normaliza nombres a snake_case y elimina columnas 'unnamed'.
    """
    df = pd.read_csv(
        path,
        sep=';',
        engine='python',
        dtype=str,
        encoding='utf-8',
        on_bad_lines='skip'
    )
    # Normaliza encabezados
    df.columns = (
        df.columns
          .str.strip()
          .str.lower()
          .str.replace(' ', '_')
          .str.replace('ñ', 'n')
          .str.replace('/', '_')
    )
    # Elimina columnas que comiencen con 'unnamed'
    df = df.loc[:, ~df.columns.str.startswith('unnamed')]
    return df

def filter_data(df: pd.DataFrame, query: str) -> pd.DataFrame:
    """
    Filtra el DataFrame buscando `query` en cualquier columna (case-insensitive).
    """
    if not query:
        return df
    mask = df.apply(
        lambda row: query.lower() in ' '.join(row.fillna('').astype(str)).lower(),
        axis=1
    )
    return df[mask]

def save_data(df: pd.DataFrame, path: str):
    """
    Guarda el DataFrame en CSV delimitado por ';', eliminando 'unnamed'.
    """
    df = df.loc[:, ~df.columns.str.startswith('unnamed')]
    df.to_csv(path, sep=';', index=False, encoding='utf-8')
