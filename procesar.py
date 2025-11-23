import pandas as pd
import os
import sys

# --- CONFIGURACIÓN ---
# ID de tu hoja de cálculo
SHEET_ID = 'AKfycbyK3CAcbmQ3sKZ2UxLcQjort9PITPlMhV7xKXW5pT5Iv-zwGZyPb55gmoQZl4YG_HGWig' 
SHEET_NAME = 'Hoja 1' # Asegúrate que coincida con el nombre de tu pestaña
URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}'

def generar_reportes():
    try:
        print("Descargando datos de Google Sheets...")
        df = pd.read_csv(URL)
        
        # Limpieza básica
        df = df.fillna('')
        if 'VENTA_PRECIO' in df.columns:
            df['VENTA_PRECIO'] = pd.to_numeric(df['VENTA_PRECIO'], errors='coerce')

        # --- REPORTE 1: COMPARATIVO ---
        print("Generando comparativo...")
        comparativo = pd.pivot_table(
            df,
            index='PRODUCTO',
            columns='TIPO_PUNTO',
            values='VENTA_PRECIO',
            aggfunc='mean'
        ).reset_index()
        
        # Calcular diferencia si existen ambas columnas
        if 'plaza' in comparativo.columns and 'externo' in comparativo.columns:
            comparativo['DIFERENCIA'] = comparativo['plaza'] - comparativo['externo']

        # Guardar Excel Comparativo
        with pd.ExcelWriter('Reporte_Comparativo.xlsx') as writer:
            comparativo.to_excel(writer, sheet_name='Resumen', index=False)
            df.to_excel(writer, sheet_name='Data Fuente', index=False)
            
        print("¡Archivos generados con éxito!")

    except Exception as e:
        print(f"Error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    generar_reportes()
