from db_connection import create_connection

sequenceTable = "SEQ_MATRIX"
studentTable = 'Student'
companyTable = 'Company'
universitySupervisorTable = 'UniversitySupervisor'
adminTable = 'Admin'
taskTable = 'Task'
companyRequestTable = 'CompanyRequest'
studentPersonalTable = 'StudentPersonal'
submissionTable = 'Submission'
internshipTable = 'Internship'
internshipApplicationTable = 'InternshipApplication'
internshipJobTable = 'InternshipJob'
companyPersonnelTable = 'CompanyPersonnel'

def retrieveAllStud():
    conn = create_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM " + studentTable)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def retrieveAllComp():
    conn = create_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM " + companyTable)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def retrieveAllUniSup():
    conn = create_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM " + universitySupervisorTable)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def retrieveAllJob():
    conn = create_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM " + internshipJobTable)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def retrieveCompById(compId):
    row = None
    try:
        conn = create_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM " + companyTable + " WHERE companyId = %s", (compId,))
        row = cur.fetchone()
    except Exception as e:
        print(e)
    finally:
        cur.close()
        conn.close()
    return row

def retrieveCompJobById(compId):
    conn = create_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM " + internshipJobTable + " WHERE companyId = %s", (compId,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def retrieveJobById(jobId):
    row = None
    try:
        conn = create_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM " + internshipJobTable + " WHERE jobId = %s", (jobId,))
        row = cur.fetchone()
    except Exception as e:
        print(e)
    finally:
        cur.close()
        conn.close()
    return row

def retrieveStudByEmail(studEmail):
    conn = create_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM " + studentTable + " WHERE email = %s", (studEmail,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def retrieveSeqNoByTblName(tblName):
    conn = create_connection()
    cur = conn.cursor()
    cur.execute("SELECT SEQ_NO FROM " + sequenceTable + " WHERE TBL_NAME = '" + tblName + "'")
    seqNo = cur.fetchone()[0]
    cur.close()
    conn.close()
    return seqNo