import streamlit as st
import pandas as pd
import mysql.connector

# MySQL connection
conn = mysql.connector.connect(
    host="82.180.143.66",
    user="u263681140_AttendanceInt",
    password="SagarAtten@12345",
    database="u263681140_Attendance"
)

cursor = conn.cursor(dictionary=True)

# SQL JOIN for required fields
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

# Convert to DataFrame
df = pd.DataFrame(results)

# Streamlit display
st.title("Attendance Summary")
st.dataframe(df)

# Cleanup
cursor.close()
conn.close()
