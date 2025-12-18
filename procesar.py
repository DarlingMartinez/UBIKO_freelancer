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
        print("1. Descargando y preparando datos")
        df = pd.read_csv(URL)
        
        # --- PREPARACIÓN GLOBAL DE DATOS ---
        df = df.fillna(0)
        df['VENTA_PRECIO'] = pd.to_numeric(df['VENTA_PRECIO'], errors='coerce').fillna(0)
        
        # Estandarizar TIPO_PUNTO: 'plaza' o 'externo'
        if 'TIPO_PUNTO' in df.columns:
            df['TIPO_PUNTO'] = df['TIPO_PUNTO'].apply(
                lambda x: 'plaza' if 'plaza' in str(x).lower() or 'pmd' in str(x).lower() else 'externo'
            )
        
        
        if 'FECHA' in df.columns:
           
            df['FECHA_DIA'] = pd.to_datetime(df['FECHA'], errors='coerce').dt.normalize() 

            df = df.dropna(subset=['FECHA_DIA'])
        
        # Obtener la lista de plazas únicas
        plazas_unicas = df['PLAZA'].dropna().unique().tolist()
        plazas_unicas = [p for p in plazas_unicas if p != 0 and p != '0']
        
        # --- INICIO DEL GUARDADO DE EXCEL ---
        print(f"2. Iniciando la generación del archivo Excel con {len(plazas_unicas) + 3} hojas...")
        reportes = {}

        # =========================================================================
        # PARTE 1: REPORTE 'Resumen PMD' (Costo Total Canasta) - AJUSTADO
        # =========================================================================
        
        print("3. Generando reporte 'Resumen PMD' (Costo Total Canasta)...")
        nombre_columna_plaza = 'PLAZA' 

        comparativo = pd.pivot_table(
            df, index=nombre_columna_plaza, columns='TIPO_PUNTO', values='VENTA_PRECIO', aggfunc='sum'
        ).reset_index()
        
        if 'plaza' not in comparativo.columns: comparativo['plaza'] = 0
        if 'externo' not in comparativo.columns: comparativo['externo'] = 0
            
        # AJUSTES DE NOMBRE DE COLUMNA
        comparativo = comparativo.rename(columns={
            'PLAZA': 'PDM',
            'plaza': '$ PM', 
            'externo': '$ Tiendas'
        })
        
        comparativo['Diferencia (tienda - plaza)'] = comparativo['$ Tiendas'] - comparativo['$ PM']
        comparativo['Represent. %'] = comparativo.apply(
            lambda row: (row['Diferencia (tienda - plaza)'] / row['$ PM']) * 100 
            if row['$ PM'] != 0 else 0, axis=1
        )
        
        # Definir las columnas finales para la concatenación
        columnas_finales_pmd = ['PDM', '$ PM', '$ Tiendas', 'Diferencia (tienda - plaza)', 'Represent. %']
        
        # Asegurar que 'comparativo' solo tenga las columnas necesarias antes de agregar el resumen
        comparativo = comparativo.reindex(columns=columnas_finales_pmd)

        # Crear filas vacías con None/NaN
        filas_vacias = pd.DataFrame(None, index=range(2), columns=columnas_finales_pmd)
        
        # Agregar fila 'Promedio' (Suma total)
        suma_total_pm = comparativo['$ PM'].sum()
        
        # *** AJUSTE SOLICITADO AQUÍ ***: Usamos None para las últimas 3 columnas.
        fila_resumen = pd.DataFrame({
            'PDM': ['Promedio'], 
            '$ PM': [suma_total_pm], 
            '$ Tiendas': [None], 
            'Diferencia (tienda - plaza)': [None], 
            'Represent. %': [None]
        })
        
        # Asegurar que la fila resumen tenga las columnas exactas
        fila_resumen = fila_resumen.reindex(columns=columnas_finales_pmd)

        # Concatenar: Reporte Original + 2 Filas Vacías + Fila de Promedio
        comparativo = pd.concat([comparativo, filas_vacias, fila_resumen], ignore_index=True)
        
        # El fillna('') en la parte de escritura se encargará de que todos los None/NaN sean celdas vacías
        reporte_pmd = comparativo.round(2) 
        reportes['Resumen PMD'] = reporte_pmd
        
        # =========================================================================
        # PARTE 2: REPORTE 'Precios SDDE' (Precios Promedio Diarios)
        # =========================================================================
        
        print("4. Generando reporte 'Precios SDDE' (Precios Promedio Diarios)...")
        if 'FECHA_DIA' in df.columns and 'PRODUCTO' in df.columns:
            reporte_sdde = pd.pivot_table(
                df[df['FECHA_DIA'].notna()], index='FECHA_DIA', columns='PRODUCTO', 
                values='VENTA_PRECIO', aggfunc='mean'
            ).round(2).reset_index()
            
            reporte_sdde = reporte_sdde.rename(columns={'FECHA_DIA': 'Fecha de aplicación (Fecha, hora y minuto)'})
            reporte_sdde['Fecha de aplicación (Fecha, hora y minuto)'] = reporte_sdde['Fecha de aplicación (Fecha, hora y minuto)'].astype(str)
            reportes['Precios SDDE'] = reporte_sdde
        else:
            print("   Advertencia: Faltan columnas 'FECHA' o 'PRODUCTO' para 'Precios SDDE'. Saltando hoja.")

        # =========================================================================
        # PARTE 3: REPORTE 'Variacion Canasta (IPC)' (IPC Sustituto)
        # =========================================================================

        print("5. Generando reporte 'Variacion Canasta (IPC)' (Variación Diaria)...")
        if 'FECHA_DIA' in df.columns:
            # 1. Calcular el Costo Total de la Canasta por día (suma de todos los precios reportados en esa fecha)
            df_ipc = df.groupby('FECHA_DIA')['VENTA_PRECIO'].sum().reset_index()
            df_ipc = df_ipc.rename(columns={'VENTA_PRECIO': 'Costo Total Canasta Promedio'})
            
            # 2. Ordenar por fecha para calcular la variación
            df_ipc['FECHA_DIA'] = pd.to_datetime(df_ipc['FECHA_DIA'])
            df_ipc = df_ipc.sort_values('FECHA_DIA')
            
            # 3. Calcular la variación diaria (Proxy de IPC)
            df_ipc['Variación Diaria (%)'] = df_ipc['Costo Total Canasta Promedio'].pct_change() * 100
            
            # 4. Formato final
            df_ipc['FECHA_DIA'] = df_ipc['FECHA_DIA'].dt.strftime('%Y-%m-%d')
            reporte_ipc = df_ipc.fillna(0).round(2)
            reportes['Variacion Canasta (IPC)'] = reporte_ipc
        else:
            print("   Advertencia: Faltan columnas 'FECHA' o 'FECHA_DIA' para 'Variacion Canasta (IPC)'. Saltando hoja.")

# =========================================================================
        # PARTE 4: REPORTE POR CADA 'Localidad' (Comparativo Producto por Producto) - AJUSTE DOBLE PDM
        # =========================================================================

        print("6. Generando reportes de Localidad (Producto por Producto)...")
        for plaza in plazas_unicas:
            # 1. Filtrar por PLAZA
            df_plaza = df[df['PLAZA'] == plaza].copy() 
            
            if df_plaza.empty:
                continue
            
            # 2. APLICAR FILTRO CLAVE: Solo productos donde ES_CANASTA sea 'SI'
            if 'ES_CANASTA' in df_plaza.columns:
                df_plaza_filtrada = df_plaza[df_plaza['ES_CANASTA'].astype(str).str.upper().isin(['SI', 'SÍ'])].copy()
            else:
                print(f"   Advertencia: Columna 'ES_CANASTA' no encontrada en los datos. Se incluyen todos los productos para la plaza {plaza}.")
                df_plaza_filtrada = df_plaza.copy()


            if df_plaza_filtrada.empty:
                print(f"   ADVERTENCIA CRÍTICA: La plaza {plaza} no tiene productos marcados como Canasta Básica ('SI'). Saltando hoja.")
                continue

            # Usamos el DataFrame filtrado para la tabla dinámica
            reporte_localidad = pd.pivot_table(
                df_plaza_filtrada,
                index=['GRUPO_ALIMENTARIO', 'PRODUCTO', 'VENTA_UNIDAD_MEDIDA'],
                columns='TIPO_PUNTO',
                values='VENTA_PRECIO',
                aggfunc='mean'
            ).reset_index().rename(columns={'GRUPO_ALIMENTARIO': 'Grupo'}) 

            # *** AJUSTE CLAVE 1: Limpiar el nombre de la plaza para evitar doble PDM ***
            nombre_limpio = plaza.replace('PDM ', '').strip() 
            
            reporte_localidad = reporte_localidad.rename(columns={
                'plaza': f'PDM {nombre_limpio}',
                'externo': 'Tiendas'
            })
            
            nombre_col_pm = f'PDM {nombre_limpio}'
            if nombre_col_pm not in reporte_localidad.columns: reporte_localidad[nombre_col_pm] = 0.0
            if 'Tiendas' not in reporte_localidad.columns: reporte_localidad['Tiendas'] = 0.0

            # Cálculos finales
            reporte_localidad['Dif. Precio ($)'] = reporte_localidad['Tiendas'] - reporte_localidad[nombre_col_pm] 
            
            reporte_localidad['Dif. Porc. (%)'] = reporte_localidad.apply(
                lambda row: (row['Dif. Precio ($)'] / row[nombre_col_pm]) * 100 
                if row[nombre_col_pm] != 0 else 0, axis=1
            )
            
            columnas_finales_localidad = ['Grupo', 'PRODUCTO', 'VENTA_UNIDAD_MEDIDA', nombre_col_pm, 'Tiendas', 'Dif. Precio ($)', 'Dif. Porc. (%)']
            reporte_final_localidad = reporte_localidad.reindex(columns=columnas_finales_localidad).round(2).fillna(0)
            
            # Limitar el nombre de la hoja a 31 caracteres, que es el límite de Excel
            nombre_hoja = plaza[:31] 
            reportes[nombre_hoja] = reporte_final_localidad
        # =========================================================================
        # PARTE 5: ESCRIBIR TODOS LOS REPORTES AL EXCEL FINAL
        # =========================================================================

        print("7. Escribiendo todos los reportes en 'Reporte_Comparativo_FINAL_IPC.xlsx'...")
        with pd.ExcelWriter('Reporte_Comparativo.xlsx', engine='xlsxwriter') as writer:
            workbook = writer.book
            
            general_num_fmt = workbook.add_format({'num_format': '0.00'})
            percent_fmt = workbook.add_format({'num_format': '0.00%'})
            
            for nombre_hoja, df_reporte in reportes.items():
                
                # Para la hoja Resumen PMD, reemplazamos explícitamente los NaN con '' 
                # para que las celdas de separación y las de la fila 'Promedio' queden vacías.
                if nombre_hoja == 'Resumen PMD':
                    df_reporte_escritura = df_reporte.fillna('')
                else:
                    df_reporte_escritura = df_reporte
                    
                df_reporte_escritura.to_excel(writer, sheet_name=nombre_hoja, index=False)
                worksheet = writer.sheets[nombre_hoja]
                
                if nombre_hoja == 'Resumen PMD':
                    # Las columnas B, C y D ahora son: '$ PM', '$ Tiendas', 'Diferencia (tienda - plaza)'
                    worksheet.set_column('B:D', 20, general_num_fmt) 
                    # La columna E ahora es 'Represent. %'
                    worksheet.set_column('E:E', 15, percent_fmt) 
                
                elif nombre_hoja == 'Precios SDDE':
                    worksheet.set_column('A:A', 35)
                    worksheet.set_column('B:XFD', 15, general_num_fmt)
                
                elif nombre_hoja == 'Variacion Canasta (IPC)':
                    # Columna B (Costo Canasta)
                    worksheet.set_column('B:B', 25, general_num_fmt)
                    # Columna C (Variación Diaria)
                    worksheet.set_column('C:C', 20, percent_fmt)
                
                else: # Hojas de Localidad
                    # La columna C:E ahora es: PDM {Plaza}, Tiendas, Dif. Precio ($)
                    worksheet.set_column('C:E', 15, general_num_fmt) 
                    # La columna F ahora es 'Dif. Porc. (%)'
                    worksheet.set_column('F:F', 15, percent_fmt) 
                    worksheet.set_column('A:B', 25)

            # --- Hoja de Data Fuente (sin cambios) ---
            df.to_excel(writer, sheet_name='Data Fuente', index=False)
            
        print("¡Archivo final generado con éxito! El archivo 'Reporte_Comparativo.xlsx' contiene todas las hojas, incluyendo la variación de precios.")

    except Exception as e:
        print(f"Error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    generar_reportes_completos()