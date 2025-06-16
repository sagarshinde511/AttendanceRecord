import streamlit as st
import pandas as pd
import mysql.connector
from datetime import datetime, timedelta
import io
import os

# MySQL connection
conn = mysql.connector.connect(
    host="82.180.143.66",
    user="u263681140_AttendanceInt",
    password="SagarAtten@12345",
    database="u263681140_Attendance"
)
cursor = conn.cursor(dictionary=True)

# Streamlit layout
st.set_page_config(layout="wide")
tabs = st.tabs(["📋 Raw Attendance", "📊 Summary Report"])

# ---------------- TAB 1 ----------------
with tabs[0]:
    query = """
    SELECT ar.RollNo, ar.Date, ar.Time, sd.id, sd.StudentName, sd.Batch
    FROM AttendanceRecord ar
    JOIN Students_Data sd ON ar.RollNo = sd.id
    ORDER BY ar.Date DESC, ar.Time DESC
    """
    cursor.execute(query)
    results = cursor.fetchall()
    df = pd.DataFrame(results)
    st.title("📋 Raw Attendance Log")
    st.dataframe(df)

# ---------------- TAB 2 ----------------
with tabs[1]:
    st.title("📊 Attendance Summary Report")

    # Filters
    cursor.execute("SELECT DISTINCT Batch FROM Students_Data")
    batches = [row['Batch'] for row in cursor.fetchall()]
    selected_batch = st.selectbox("Select Batch", batches)

    from_date = st.date_input("From Date", datetime.today() - timedelta(days=7))
    to_date = st.date_input("To Date", datetime.today())

    # Fetch filtered data
    summary_query = """
    SELECT ar.RollNo, ar.Date, sd.StudentName, sd.Batch,
           CASE WHEN ar.RollNo IS NOT NULL THEN 'Present' ELSE 'Absent' END AS Status
    FROM Students_Data sd
    LEFT JOIN AttendanceRecord ar ON sd.id = ar.RollNo AND ar.Date BETWEEN %s AND %s
    WHERE sd.Batch = %s
    """
    cursor.execute(summary_query, (from_date, to_date, selected_batch))
    summary_data = cursor.fetchall()
    df = pd.DataFrame(summary_data)

    if df.empty:
        st.warning("No attendance data available.")
    else:
        df['Date'] = df['Date'].astype(str)  # Ensure consistent format

        # Pivot the table
        pivot_df = df.pivot_table(index=["RollNo", "StudentName"],
                                  columns="Date",
                                  values="Status",
                                  aggfunc="first").reset_index()

        # Fill NaNs with 'Absent'
        pivot_df.fillna("Absent", inplace=True)

        # Add missing dates as 'Holiday'
        all_dates = pd.date_range(start=from_date, end=to_date).strftime('%Y-%m-%d')
        existing_date_cols = pivot_df.columns[2:]
        missing_dates = sorted(set(all_dates) - set(existing_date_cols))

        for date in missing_dates:
            pivot_df[date] = "Holiday"

        # Mark fully absent columns as Holiday
        for col in pivot_df.columns[2:]:
            if all(pivot_df[col] == 'Absent'):
                pivot_df[col] = 'Holiday'

        # Reorder columns by date
        pivot_df = pivot_df[["RollNo", "StudentName"] + sorted(pivot_df.columns[2:])]

        st.dataframe(pivot_df, use_container_width=True)

        # ---- Excel export ----
        excel_path = "/tmp/attendance_report.xlsx"
        with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
            pivot_df.to_excel(writer, index=False, sheet_name='Attendance')
            workbook = writer.book
            worksheet = writer.sheets['Attendance']

            red_format = workbook.add_format({'bg_color': '#FFC7CE'})  # Red for absent
            yellow_format = workbook.add_format({'bg_color': '#FFFACD'})  # Yellow for holiday

            num_rows, num_cols = pivot_df.shape

            for col in range(2, num_cols):
                col_letter = chr(65 + col) if col < 26 else chr(64 + col // 26) + chr(65 + col % 26)
                cell_range = f"{col_letter}2:{col_letter}{num_rows+1}"

                # Red for Absent
                worksheet.conditional_format(cell_range, {
                    'type': 'text', 'criteria': 'containing', 'value': 'Absent', 'format': red_format
                })

                # Yellow for Holiday
                worksheet.conditional_format(cell_range, {
                    'type': 'text', 'criteria': 'containing', 'value': 'Holiday', 'format': yellow_format
                })

        with open(excel_path, "rb") as file:
            st.download_button(
                label="📥 Download Excel",
                data=file.read(),
                file_name=f"Attendance_{selected_batch}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"download_excel_{selected_batch}"
            )

cursor.close()
conn.close()
