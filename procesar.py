import pandas as pd
import os
import sys

# --- CONFIGURACIÓN ---
# ID de tu hoja de cálculo de Google Sheets (DEBE SER PÚBLICO)
SHEET_ID = '1j3l4u61zS44YfBPck5K7YLby1izFHMIxMZrHzhdXEU8' 
SHEET_NAME = 'Hoja1' # Asegúrate que coincida con el nombre de tu pestaña
URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}'

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

        with pd.ExcelWriter(
            output_file,
            engine='xlsxwriter',
            engine_kwargs={'options': {'nan_inf_to_errors': True}}
        ) as writer:

            workbook = writer.book
            num_fmt = workbook.add_format({'num_format': '#,##0'})
            percent_fmt = workbook.add_format({'num_format': '0.00%'})
            
            # Formato para el texto del total (Gris + Negrita)
            total_text_fmt = workbook.add_format({
                'bg_color': '#E7E6E6',
                'bold': True
            })
            
            # Formato para los números del total (Gris + Negrita + Separador de miles)
            total_num_fmt = workbook.add_format({
                'bg_color': '#E7E6E6',
                'bold': True,
                'num_format': '#,##0'
            })

            # =====================================================
            # HOJA 1: RESUMEN PMD 
            # =====================================================
            resumen = df_limpio.pivot_table(
                index='PLAZA',
                columns='TIPO_PUNTO',
                values='VENTA_PRECIO',
                aggfunc='sum',
                fill_value=0
            ).reset_index()

            resumen = resumen.rename(columns={
                'PLAZA': 'PDM',
                'plaza': '$PM',
                'externo': '$Tienda'
            })

            resumen['Diferencia (Tienda - Plaza)'] = resumen['$Tienda'] - resumen['$PM']
            resumen['Represent %'] = resumen.apply(
                lambda r: (r['Diferencia (Tienda - Plaza)'] / r['$PM'])
                if r['$PM'] != 0 else pd.NA,
                axis=1
            )

            resumen = resumen[['PDM', '$PM', '$Tienda', 'Diferencia (Tienda - Plaza)', 'Represent %']]

            suma_pm = resumen['$PM'].sum()

            resumen = pd.concat([
                resumen,
                pd.DataFrame([[None]*5, [None]*5], columns=resumen.columns),
                pd.DataFrame([{
                    'PDM': 'Promedio',
                    '$PM': suma_pm
                }])
            ], ignore_index=True)

            resumen.to_excel(writer, sheet_name='Resumen PMD', index=False)

            ws = writer.sheets['Resumen PMD']
            ws.set_column('B:D', 18, num_fmt)
            ws.set_column('E:E', 15, percent_fmt)

            # =====================================================
            # HOJA 2: PRECIOS SDDE 
            # =====================================================
            precios_sdde = df_limpio.pivot_table(
                index='FECHA_DIA',
                columns='PRODUCTO',
                values='VENTA_PRECIO',
                aggfunc='mean'
            ).round(2)

            precios_sdde.index.name = 'Fecha de aplicación (Fecha, hora y minuto)'
            precios_sdde.to_excel(writer, sheet_name='Precios SDDE')

            ws = writer.sheets['Precios SDDE']
            ws.set_column('A:A', 35)
            ws.set_column('B:XFD', 15, num_fmt)

            # =====================================================
            # HOJAS POR LOCALIDAD 
            # =====================================================
            localidades = df_limpio['LOCALIDAD'].dropna().unique()

            for localidad in localidades:
                df_loc = df_limpio[
                    (df_limpio['LOCALIDAD'] == localidad) &
                    (df_limpio['ES_CANASTA'].str.upper().isin(['SI', 'SÍ']))
                ]

                if df_loc.empty:
                    continue

                reporte = df_loc.pivot_table(
                    index=['GRUPO_ALIMENTARIO', 'PRODUCTO'],
                    columns='TIPO_PUNTO',
                    values='VENTA_PRECIO',
                    aggfunc='mean',
                    fill_value=0
                ).reset_index()

                col_pdm = f'PDM {localidad}'

                reporte = reporte.rename(columns={
                    'GRUPO_ALIMENTARIO': 'Grupo',
                    'PRODUCTO': 'Productos',
                    'plaza': col_pdm,
                    'externo': 'Tiendas'
                })

                reporte['Dif. Precio ($)'] = reporte['Tiendas'] - reporte[col_pdm]
                reporte['Dif. Porc. (%)'] = reporte.apply(
                    lambda r: (r['Dif. Precio ($)'] / r[col_pdm])
                    if r[col_pdm] != 0 else pd.NA,
                    axis=1
                )

                reporte = reporte[['Grupo', 'Productos', col_pdm, 'Tiendas',
                                   'Dif. Precio ($)', 'Dif. Porc. (%)']].round(2)

                total_pdm = reporte[col_pdm].sum()
                total_tiendas = reporte['Tiendas'].sum()

                # Generamos el Excel
                reporte.to_excel(writer, sheet_name=localidad, index=False)

                ws = writer.sheets[localidad]
                ws.set_column('A:B', 25)
                ws.set_column('C:E', 15, num_fmt)
                ws.set_column('F:F', 15, percent_fmt)

                # --- CAMBIO APLICADO AQUÍ ---
                # Calculamos el índice de la fila donde debe ir el total (después de los datos)
                fila_total_idx = len(reporte) + 1 
                
                # Escribimos la fila de totales manualmente para controlar el rango del color
                # Argumentos: write(fila, columna, contenido, formato)
                ws.write(fila_total_idx, 1, 'Suma total', total_text_fmt) # Columna B
                ws.write(fila_total_idx, 2, total_pdm, total_num_fmt)    # Columna C
                ws.write(fila_total_idx, 3, total_tiendas, total_num_fmt)# Columna D
                # -----------------------------

        print("Archivo generado correctamente: Reporte_Comparativo.xlsx")

    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    generar_reportes_completos()
