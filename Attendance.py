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

# TAB 1: Attendance Summary Sorted by RollNo
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
        ORDER BY ar.RollNo ASC, ar.Date DESC
        """
        cursor.execute(query)
        results = cursor.fetchall()
        df1 = pd.DataFrame(results)

        st.title("Attendance Summary (Sorted by Roll No)")
        st.dataframe(df1)

    except mysql.connector.Error as err:
        st.error(f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()

# TAB 2: Daily Status with From–To Date
with tab2:
    st.title("Attendance Status by Date Range")
    from_date = st.date_input("From Date")
    to_date = st.date_input("To Date")

    if from_date and to_date and from_date <= to_date:
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor(dictionary=True)

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
            ORDER BY d.Date, s.id
            """

            cursor.execute(query)
            results = cursor.fetchall()
            df2 = pd.DataFrame(results)

            st.subheader(f"Attendance from {from_date} to {to_date}")
            st.dataframe(df2)

        except mysql.connector.Error as err:
            st.error(f"Database error: {err}")
        finally:
            cursor.close()
            conn.close()
    elif from_date > to_date:
        st.warning("⚠️ 'From Date' must be before or equal to 'To Date'")
