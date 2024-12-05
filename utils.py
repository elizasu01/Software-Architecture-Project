# utils.py
from datetime import datetime
from db_utils import get_db_connection

def save_appointment(patient_full_name, appointment_date, physician_name, specialty, 
                     facility_name, patient_telephone_number, patient_email, zip_code, telephone_number):
    connection = get_db_connection()
    cursor = connection.cursor()

    now = datetime.now()
    query = """
    INSERT INTO appointments (patient_full_name, appointment_date, status, doctor_full_name, specialty, 
    facility_name, patient_phone_number, patient_email, zip_code, telephone_number, created_at, updated_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (patient_full_name, appointment_date, 'scheduled', physician_name, specialty, 
                           facility_name, patient_telephone_number, patient_email, zip_code, telephone_number, now, now))
    connection.commit()
    connection.close()
