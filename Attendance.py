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
with tab2:
    st.title("Attendance Status by Date (Pivoted View)")
    from_date = st.date_input("From Date")
    to_date = st.date_input("To Date")

    if from_date and to_date and from_date <= to_date:
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor(dictionary=True)

            # Get all roll numbers and names
            cursor.execute("SELECT id AS RollNo, StudentName FROM Students_Data")
            students = cursor.fetchall()
            students_df = pd.DataFrame(students)

            # Get attendance within date range
            query = f"""
            SELECT 
                s.id AS RollNo,
                s.StudentName,
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
            ORDER BY s.id, d.Date
            """

            cursor.execute(query)
            attendance = cursor.fetchall()
            attendance_df = pd.DataFrame(attendance)

            # Pivot: Dates as columns
            pivot_df = attendance_df.pivot(index=["RollNo", "StudentName"], columns="Date", values="Status")
            pivot_df = pivot_df.reset_index()

            st.subheader(f"Attendance from {from_date} to {to_date}")
            st.dataframe(pivot_df)

        except mysql.connector.Error as err:
            st.error(f"Database error: {err}")
        finally:
            cursor.close()
            conn.close()
    elif from_date > to_date:
        st.warning("⚠️ 'From Date' must be before or equal to 'To Date'")
