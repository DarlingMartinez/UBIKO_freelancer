import pandas as pd
import os
import sys
import time

# --- CONFIGURACIÓN ---
# ID de tu hoja de cálculo de Google Sheets (DEBE SER PÚBLICO)
SHEET_ID = '1j3l4u61zS44YfBPck5K7YLby1izFHMIxMZrHzhdXEU8' 
SHEET_NAME = 'Hoja1' # Asegúrate que coincida con el nombre de tu pestaña
URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}&cache_buster={int(time.time())}'

def generar_reportes_completos():
    try:
        print("Descargando datos...")
        df = pd.read_csv(URL)

        # --- LIMPIEZA GENERAL ---
        df = df.fillna(0)
        df['VENTA_PRECIO'] = pd.to_numeric(df['VENTA_PRECIO'], errors='coerce').fillna(0)

        if 'TIPO_PUNTO' in df.columns:
            df['TIPO_PUNTO'] = df['TIPO_PUNTO'].apply(
                lambda x: 'plaza' if 'plaza' in str(x).lower() or 'pmd' in str(x).lower() else 'externo'
            )

        if 'FECHA' in df.columns:
            df['FECHA'] = pd.to_datetime(df['FECHA'], errors='coerce')
            df['FECHA_DIA'] = df['FECHA'].dt.date
            df = df.dropna(subset=['FECHA'])

        df_limpio = df[df['VENTA_PRECIO'] > 0].copy()

        output_file = 'Reporte_Comparativo.xlsx'

        with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
            workbook = writer.book
            num_fmt = workbook.add_format({'num_format': '#,##0'})
            percent_fmt = workbook.add_format({'num_format': '0.00%'})
            total_text_fmt = workbook.add_format({'bg_color': '#E7E6E6', 'bold': True})
            total_num_fmt = workbook.add_format({'bg_color': '#E7E6E6', 'bold': True, 'num_format': '#,##0'})

            # HOJA 1: RESUMEN PMD
            resumen = df_limpio.pivot_table(index='PLAZA', columns='TIPO_PUNTO', values='VENTA_PRECIO', aggfunc='sum', fill_value=0).reset_index()
            resumen = resumen.rename(columns={'PLAZA': 'PDM', 'plaza': '$PM', 'externo': '$Tienda'})
            if '$PM' in resumen.columns and '$Tienda' in resumen.columns:
                resumen['Diferencia (Tienda - Plaza)'] = resumen['$Tienda'] - resumen['$PM']
                resumen['Represent %'] = resumen.apply(lambda r: (r['Diferencia (Tienda - Plaza)'] / r['$PM']) if r['$PM'] != 0 else 0, axis=1)
            
            suma_pm = resumen['$PM'].sum() if '$PM' in resumen.columns else 0
            fila_promedio = pd.DataFrame([{'PDM': 'Promedio', '$PM': suma_pm}])
            resumen = pd.concat([resumen, fila_promedio], ignore_index=True)
            resumen.to_excel(writer, sheet_name='Resumen PMD', index=False)
            ws_res = writer.sheets['Resumen PMD']
            ws_res.set_column('B:D', 18, num_fmt)
            ws_res.set_column('E:E', 15, percent_fmt)

            # HOJA 2: PRECIOS SDDE (AJUSTADA)
            precios_sdde = df_limpio.pivot_table(index='FECHA_DIA', columns='PRODUCTO', values='VENTA_PRECIO', aggfunc='mean').round(0)
            precios_sdde.index.name = 'Fecha de aplicación'
            precios_sdde.to_excel(writer, sheet_name='Precios SDDE')
            ws_sdde = writer.sheets['Precios SDDE']
            ws_sdde.set_column('A:A', 20)
            ws_sdde.set_column('B:XFD', 12, num_fmt)
            ws_sdde.freeze_panes(1, 1)

            # HOJAS POR PLAZA
            plazas = df_limpio['PLAZA'].dropna().unique()
            for plaza in plazas:
                df_pla = df_limpio[(df_limpio['PLAZA'] == plaza) & (df_limpio['ES_CANASTA'].str.upper().isin(['SI', 'SÍ']))]
                if df_pla.empty: continue
                reporte = df_pla.pivot_table(index=['GRUPO_ALIMENTARIO', 'PRODUCTO'], columns='TIPO_PUNTO', values='VENTA_PRECIO', aggfunc='mean', fill_value=0).reset_index()
                
                nombre_pdm = str(plaza)
                col_pdm_label = f"PDM {nombre_pdm}" if "PDM" not in nombre_pdm.upper() else nombre_pdm
                reporte = reporte.rename(columns={'GRUPO_ALIMENTARIO': 'Grupo', 'PRODUCTO': 'Productos', 'plaza': col_pdm_label, 'externo': 'Tiendas'})
                
                if col_pdm_label in reporte.columns and 'Tiendas' in reporte.columns:
                    reporte['Dif. Precio ($)'] = reporte['Tiendas'] - reporte[col_pdm_label]
                    reporte['Dif. Porc. (%)'] = reporte.apply(lambda r: (r['Dif. Precio ($)'] / r[col_pdm_label]) if r[col_pdm_label] != 0 else 0, axis=1)

                total_pdm = reporte[col_pdm_label].sum() if col_pdm_label in reporte.columns else 0
                total_tiendas = reporte['Tiendas'].sum() if 'Tiendas' in reporte.columns else 0
                sheet_name = str(plaza)[:31].replace(':', '').replace('/', '')
                reporte.to_excel(writer, sheet_name=sheet_name, index=False)
                ws = writer.sheets[sheet_name]
                ws.set_column('A:B', 25)
                ws.set_column('C:E', 15, num_fmt)
                ws.set_column('F:F', 15, percent_fmt)
                fila_total_idx = len(reporte) + 1 
                ws.write(fila_total_idx, 1, 'Suma total', total_text_fmt)
                ws.write(fila_total_idx, 2, total_pdm, total_num_fmt)
                ws.write(fila_total_idx, 3, total_tiendas, total_num_fmt)

        print("Archivo generado correctamente: Reporte_Comparativo.xlsx")
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    generar_reportes_completos()
