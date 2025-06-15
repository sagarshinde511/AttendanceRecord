import streamlit as st
import pandas as pd
import mysql.connector

# Database config
DB_CONFIG = {
    'host': '82.180.143.66',
    'user': 'u263681140_AttendanceInt',
    'password': 'SagarAtten@12345',
    'database': 'u263681140_Attendance'
}

# Streamlit App with Tabs
tab1, tab2 = st.tabs(["📝 Attendance Summary", "📅 Attendance Status by Date Range"])

with tab1:
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT 
            ar.RollNo,
            ar.Date,
            ar.Time,
            sd.id,
            sd.StudentName
        FROM 
            AttendanceRecord ar
        JOIN 
            Students_Data sd
        ON 
            ar.RollNo = sd.id
        ORDER BY STR_TO_DATE(ar.Date, '%Y-%m-%d') DESC, STR_TO_DATE(ar.Time, '%H:%i:%s') DESC
        """
        cursor.execute(query)
        results = cursor.fetchall()
        df1 = pd.DataFrame(results)

        st.title("Attendance Summary (Latest First)")
        st.dataframe(df1)

    except mysql.connector.Error as err:
        st.error(f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()
# TAB 2: Daily Status with From–To Date
# TAB 2: Pivoted Attendance Status
# TAB 2: Pivoted Attendance with Batch Filter + Highlight + Excel
with tab2:
    st.title("Attendance Status by Date (Pivoted View)")
    from_date = st.date_input("From Date")
    to_date = st.date_input("To Date")

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        # Fetch all batch options
        cursor.execute("SELECT DISTINCT Batch FROM Students_Data")
        batch_list = [row['Batch'] for row in cursor.fetchall()]
        selected_batch = st.selectbox("Select Batch", batch_list)

        if from_date and to_date and from_date <= to_date and selected_batch:
            # Get attendance for selected batch
            query = f"""
            SELECT 
                s.id AS RollNo,
                s.StudentName,
                s.Batch,
                d.Date,
                CASE 
                    WHEN a.RollNo IS NOT NULL THEN 'Present'
                    ELSE 'Absent'
                END AS Status
            FROM Students_Data s
            CROSS JOIN (
                SELECT DISTINCT Date
                FROM AttendanceRecord
                WHERE Date BETWEEN '{from_date}' AND '{to_date}'
            ) d
            LEFT JOIN AttendanceRecord a 
                ON s.id = a.RollNo AND a.Date = d.Date
            WHERE s.Batch = %s
            ORDER BY s.id, d.Date
            """
            cursor.execute(query, (selected_batch,))
            records = cursor.fetchall()
            df = pd.DataFrame(records)

            # Pivot
            #pivot_df = df.pivot(index=["RollNo", "StudentName"], columns="Date", values="Status").reset_index()
            pivot_df = df.pivot_table(
                index=["RollNo", "StudentName"],
                columns="Date",
                values="Status",
                aggfunc="first"  # Or you can use 'max' or 'min' based on logic
            ).reset_index()
            # Highlight 'Absent'
            def highlight_absents(val):
                return 'background-color: #ffcccc' if val == 'Absent' else ''

            styled_df = pivot_df.style.applymap(highlight_absents, subset=pivot_df.columns[2:])

            st.subheader(f"{selected_batch} Attendance from {from_date} to {to_date}")
            st.dataframe(styled_df, use_container_width=True)

            # Excel Download
            output = pd.ExcelWriter("/tmp/attendance_report.xlsx", engine='xlsxwriter')
            pivot_df.to_excel(output, index=False, sheet_name='Attendance')
            output.close()

            with open("/tmp/attendance_report.xlsx", "rb") as file:
                st.download_button("📥 Download Excel", data=file.read(),
                                   file_name=f"Attendance_{selected_batch}.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        elif from_date > to_date:
            st.warning("⚠️ 'From Date' must be before or equal to 'To Date'")

    except mysql.connector.Error as err:
        st.error(f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()
