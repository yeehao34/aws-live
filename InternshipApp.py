from flask import Flask, render_template, request, redirect, session
from flask_session import Session
from pymysql import connections
import os
import boto3
from config import *
from datetime import datetime
from s3_service import uploadToS3, get_object_url
from Models import Student, Company, UniversitySupervisor, Admin, InternshipJob, CompanyPersonnel

app = Flask(__name__, template_folder='template/dist', static_folder="template/dist/assets")
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
Session(app)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,  
    user=customuser,
    password=custompass,
    db=customdb
)

output = {}
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

@app.route("/")
def home():
    return render_template('login.html')

@app.route("/<page_name>")
def render_page(page_name):
    return render_template('%s.html' % page_name)

@app.route("/studentRegister")
def studentRegister():
    retrieveSupervisor_sql = "SELECT * FROM " + universitySupervisorTable
    cursor = db_conn.cursor()
    try:
        cursor.execute(retrieveSupervisor_sql)
        uniSupervisorResults = cursor.fetchall()
        uniSupervisorList = []
        for supervisor in uniSupervisorResults:
            print(supervisor)
            uniSupervisorList.append(UniversitySupervisor(supervisor[0], supervisor[1], supervisor[2], supervisor[3], supervisor[4])) 
            
    except Exception as e:
        db_conn.rollback()  # Rollback the transaction if an exception occurs   
    finally:
        cursor.close()
        
    return render_template('studentRegister.html', uniSupervisorList = uniSupervisorList)

@app.route("/AddStud", methods=['POST'])
def AddStud():
    # Student Table
    studEmail = request.form['studentEmail']
    curEduLevel = request.form['level']
    cohort = request.form['cohort']
    programme = request.form['programme']
    tutGrp  = request.form['tutorialGroup']
    latestCgpa = request.form['cgpa']
    studId = request.form['studentId']
    supervisorEmail = request.form['supervisorEmail']
    # StudentPersonal Table
    studName = request.form['studentName']
    nric = request.form['nric']
    gender = request.form['gender']
    ownTransport = request.form['transport']
    healthRemark = request.form['healthRemark']
    personalEmail = request.form['personalEmail']
    termAddr = request.form['termAddress']
    permAddr = request.form['permAddress']
    contactNo = request.form['mobile']
    profilePic = request.files['profile']
    # FK StudentEmail <-- Student Table
    
    insertStud_sql = "INSERT INTO " + studentTable + " VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    insertStudPersonal_sql = "INSERT INTO " + studentPersonalTable + " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    retrieveSuperviser_sql = "SELECT * FROM " + universitySupervisorTable + " WHERE Email = %s"
    cursor = db_conn.cursor()
    
    if profilePic.filename == "":
        return "Please choose a profile picture file"
    
    try:
        
        # Execute the query 
        cursor.execute(retrieveSuperviser_sql, (supervisorEmail))
        uniSupervisor = cursor.fetchone()
        supervisorId = uniSupervisor[0]
                
        # Upload image file in S3
        uploadToS3(profilePic, "students/" + studEmail + "/profile.png")
        profilePath = "students/" + studEmail + "/profile.png"
        
        insertStud_sql = "INSERT INTO " + studentTable + " VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        insertStudPersonal_sql = "INSERT INTO " + studentPersonalTable + " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        
        cursor.execute(insertStud_sql, (studEmail, curEduLevel, cohort, programme, tutGrp, latestCgpa, studId, supervisorId))
        cursor.execute(insertStudPersonal_sql, (studName, nric, gender, ownTransport, healthRemark, personalEmail, termAddr, permAddr, contactNo, profilePath, studEmail))
        
        db_conn.commit()
    except Exception as e:
        db_conn.rollback()  # Rollback the transaction if an exception occurs
    finally:
        cursor.close()
    
    # Set Flask Session
    session["studEmail"] = studEmail
        
    return redirect("/")
    

@app.route("/StudLogin", methods=['POST'])
def StudLogin():
    studEmail = request.form['studentEmail']
    nric = request.form['nric']
    
    retrieveStudentPersonal_sql = "SELECT * FROM " + studentPersonalTable + " WHERE StudentEmail = %s AND NRIC = %s"
    cursor = db_conn.cursor()
    try:
        cursor.execute(retrieveStudentPersonal_sql, (studEmail, nric))
        studentPersonal = cursor.fetchone()
        if studentPersonal is not None:
            retrieveStudent_sql = "SELECT * FROM " + studentTable + " WHERE StudentEmail = %s"
            cursor.execute(retrieveStudent_sql, (studEmail))
            student = cursor.fetchone()
    except Exception as e:
        db_conn.rollback()  # Rollback the transaction if an exception occurs
    finally:
        cursor.close()
        
    if studentPersonal is None:
        return render_template('studentLogin.html', error="Invalid Email or NRIC")
    else:     
        if studentPersonal[len(studentPersonal) -1] == studEmail and studentPersonal[1] == nric:
            session["studEmail"] = studEmail
            studentObj = Student(student[0], student[1], student[2], student[3], student[4], student[5], student[6], student[7], \
                studentPersonal[0], studentPersonal[1], studentPersonal[2], studentPersonal[3], studentPersonal[4], studentPersonal[5], studentPersonal[6], studentPersonal[7], studentPersonal[8], studentPersonal[9])
            studentProfile = get_object_url(studentObj.profilePic)
            return render_template("studentHome.html", student = studentObj, studentProfile = studentProfile)



def AddComp():
    # Company Table
    # compId = request.form['compId']
    compName = request.form['compName']
    username = request.form['username']
    password = request.form['password']
    otClaim = request.form['otClaim']
    compAddr = request.form['compAddr']
    ssmCert = request.files['ssmCert']
    industry = request.form['industry']
    compLogo = request.files['compLogo']
    totalStaff = request.form['totalStaff']
    companyStatus = "Pending"
    website = request.form['website']
    # FK PersonInChargeId <-- CompanyPersonnel Table
    # CompanyPersonnel Table
    # picId = request.form['picId']
    name = request.form['name']
    designation = request.form['designation']
    contactNo = request.form['contactNo']
    email = request.form['email']
    
    insertPersonnel_sql = "INSERT INTO " + companyPersonnelTable + " VALUES (%s, %s, %s, %s, %s)"
    insertComp_sql = "INSERT INTO " + companyTable + " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()
    
    if ssmCert.filename == "":
        return "Please upload SSM Certificate"
    

def AddJob():
    # InternshipJob Table
    # jobId = request.form['jobId']
    jobTitle = request.form['jobTitle']
    jobDesc = request.form['jobDesc']
    allowance = request.form['allowance']
    workingDay = request.form['workingDay']
    workingHour = request.form['workingHour']
    diploma = request.form['diploma']
    degree = request.form['degree']
    accessoryProvide = request.form['accessoryProvide']
    accommodation = request.form['accommodation']
    # FK companyId <-- Company Table 
    
    insertJob_sql = "INSERT INTO " + internshipJobTable + " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

def AddTask():
    # Task Table
    # taskId = request.form['taskId']
    taskName = request.form['taskName']
    dueDate = request.form['dueDate']
    
    insertTask_sql = "INSERT INTO " + taskTable + " VALUES (%s, %s, %s)"
    cursor = db_conn.cursor()
    

def AddCompRequest():
    # CompanyRequest Table
    # requestId = request.form['requestId']
    companyName = request.form['companyName']
    companyAddr = request.form['companyAddr']
    requestStatus = "Pending"
    # FK studEmail
    # FK adminId
    
    insertCompRequest_sql = "INSERT INTO " + companyRequestTable + " VALUES (%s, %s, %s, %s)"
    cursor = db_conn.cursor()
    
def submitReport():
    # Submission Table
    # submissionId = request.form['submissionId']
    dateSubmitted = datetime.now()
    report = request.files['report']
    # taskId
    # studEmail
    
    insertSubmission_sql = "INSERT INTO " + submissionTable + " (SubmissionId, DateSubmitted, Report, TaskId, StudentEmail) VALUES (%s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()
    
def applyJob():
    # InternshipApplication Table
    # applicationId = request.form['applicationId']
    applicationStatus = "Pending"
    applyDate = datetime.now()
    # FK jobId
    # FK studEmail
    
    insertApplication_sql = "INSERT INTO " + internshipApplicationTable + "(ApplicationId, ApplicationStatus, ApplyDate, JobId, StudentEmail) VALUES (%s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()
    
def AddInternship():
    # Internship Table
    # studEmail
    companyName = request.form['companyName']
    companyAddr = request.form['companyAddr']
    allowance = request.form['allowance']
    compSupervisorName = request.form['compSupervisorName']
    compSupervisorEmail = request.form['compSupervisorEmail']
    compAcceptanceForm = request.files['compAcceptanceForm']
    parentAckForm = request.files['parentAckForm']
    indemnityLetter = request.files['indemnityLetter']
    
    insertInternship_sql = "INSERT INTO " + internshipTable + " VALUES (%s, %s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()
    
    if compAcceptanceForm.filename == "":
        return "Please upload Company Acceptance Form"
    
    if parentAckForm.filename == "":
        return "Please upload Parent Acknowledgement Form"
    
    if indemnityLetter.filename == "":
        return "Please upload Indemnity Letter"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
