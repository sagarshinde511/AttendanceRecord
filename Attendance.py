import streamlit as st
import pandas as pd
import mysql.connector

# MySQL database connection
conn = mysql.connector.connect(
    host="82.180.143.66",
    user="u263681140_AttendanceInt",
    password="SagarAtten@12345",
    database="u263681140_Attendance"
)

cursor = conn.cursor(dictionary=True)

# SQL JOIN query
query = """
SELECT 
    ar.id AS AttendanceID,
    ar.Date,
    ar.Time,
    ar.RollNo,
    sd.StudentName,
    sd.StudentCollege,
    sd.Batch,
    sd.Mobile,
    sd.Email,
    sd.Address
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

# Convert to DataFrame
df = pd.DataFrame(results)

# Display in Streamlit
st.title("Student Attendance with Details")
st.dataframe(df)

# Cleanup
cursor.close()
conn.close()
