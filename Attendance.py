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

    # Get all students in selected batch
    cursor.execute("SELECT id as RollNo, StudentName FROM Students_Data WHERE Batch = %s", (selected_batch,))
    students = pd.DataFrame(cursor.fetchall())

    # Get full date range
    date_range = pd.date_range(start=from_date, end=to_date)
    date_df = pd.DataFrame({'Date': date_range.strftime('%Y-%m-%d')})

    # Cross join to get full matrix
    full_grid = students.assign(key=1).merge(date_df.assign(key=1), on='key').drop('key', axis=1)

    # Fetch actual attendance
    cursor.execute("""
        SELECT RollNo, Date FROM AttendanceRecord
        WHERE Date BETWEEN %s AND %s AND RollNo IN (
            SELECT id FROM Students_Data WHERE Batch = %s
        )
    """, (from_date, to_date, selected_batch))
    attendance = pd.DataFrame(cursor.fetchall())
    attendance['Status'] = 'Present'

        # Ensure consistent data types
    full_grid['RollNo'] = full_grid['RollNo'].astype(str)
    attendance['RollNo'] = attendance['RollNo'].astype(str)
    
    full_grid['Date'] = pd.to_datetime(full_grid['Date']).dt.strftime('%Y-%m-%d')
    attendance['Date'] = pd.to_datetime(attendance['Date']).dt.strftime('%Y-%m-%d')

    # Merge and fill missing
    merged = full_grid.merge(attendance, on=['RollNo', 'Date'], how='left')
    merged['Status'] = merged['Status'].fillna('Absent')

    # Pivot
    pivot_df = merged.pivot(index=['RollNo', 'StudentName'], columns='Date', values='Status').reset_index()

    # Mark full-absent days as Holiday
    for col in pivot_df.columns[2:]:
        if all(pivot_df[col] == 'Absent'):
            pivot_df[col] = 'Holiday'

    # Reorder columns
    pivot_df = pivot_df[['RollNo', 'StudentName'] + sorted(pivot_df.columns[2:])]

    st.dataframe(pivot_df, use_container_width=True)
