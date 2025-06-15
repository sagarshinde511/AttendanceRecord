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

# Create tabs
tab1, tab2 = st.tabs(["📝 Attendance Summary", "📅 Daily Status"])


# TAB 1: JOIN of AttendanceRecord + Students_Data
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
        ORDER BY ar.id DESC
        """
        cursor.execute(query)
        results = cursor.fetchall()
        df1 = pd.DataFrame(results)

        st.title("Attendance Summary")
        st.dataframe(df1)

    except mysql.connector.Error as err:
        st.error(f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()

# TAB 2: Present/Absent by Date
with tab2:
    selected_date = st.date_input("Select Date to Check Attendance")

    if selected_date:
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor(dictionary=True)

            query = f"""
            SELECT 
                s.id AS RollNo,
                s.StudentName,
                CASE 
                    WHEN a.RollNo IS NOT NULL THEN 'Present'
                    ELSE 'Absent'
                END AS Status
            FROM Students_Data s
            LEFT JOIN (
                SELECT DISTINCT RollNo
                FROM AttendanceRecord
                WHERE Date = '{selected_date}'
            ) a ON s.id = a.RollNo
            """
            cursor.execute(query)
            results = cursor.fetchall()
            df2 = pd.DataFrame(results)

            st.title("Daily Attendance Status")
            st.dataframe(df2)

        except mysql.connector.Error as err:
            st.error(f"Database error: {err}")
        finally:
            cursor.close()
            conn.close()
