from flask import Flask, render_template, request, redirect, session, flash, get_flashed_messages
from flask_session import Session
from datetime import datetime
from s3_service import uploadToS3, get_object_url
from Models import *
from db_connection import create_connection
from utils import *
from db_service import *

app = Flask(__name__, template_folder='template/dist',
            static_folder="template/dist/assets")
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
Session(app)

output = {}
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


@app.route("/")
def home():
    return render_template('login.html')


@app.route("/<page_name>")
def render_page(page_name):
    return render_template('%s.html' % page_name)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/studentRegister")
def studentRegister():
    retrieveSupervisor_sql = "SELECT * FROM " + universitySupervisorTable
    connection = create_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(retrieveSupervisor_sql)
        uniSupervisorResults = cursor.fetchall()
        uniSupervisorList = []
        for supervisor in uniSupervisorResults:
            uniSupervisorList.append(UniversitySupervisor(
                supervisor[0], supervisor[1], supervisor[2], supervisor[3], supervisor[4]))

    except Exception as e:
        connection.rollback()  # Rollback the transaction if an exception occurs
    finally:
        cursor.close()
        connection.close()

    error = get_flashed_messages(category_filter=['student-error'])
    if error:
        error = error[0]
    return render_template('studentRegister.html', uniSupervisorList=uniSupervisorList, error=error)


@app.route("/AddStud", methods=['POST'])
def AddStud():
    # Student Table
    studEmail = request.form['studentEmail']
    curEduLevel = request.form['level']
    cohort = request.form['cohort']
    programme = request.form['programme']
    tutGrp = request.form['tutorialGroup']
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

    insertStud_sql = "INSERT INTO " + studentTable + \
        " VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    insertStudPersonal_sql = "INSERT INTO " + studentPersonalTable + \
        " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    retrieveSuperviser_sql = "SELECT * FROM " + \
        universitySupervisorTable + " WHERE Email = %s"
    retrieveStud_sql = "SELECT * FROM " + studentTable + " WHERE StudentEmail = %s"
    connection = create_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(retrieveStud_sql, (studEmail))
        if (cursor.fetchone() is not None):
            print("Student already exists")
            flash("Student already exists", 'student-error')
            # Redirect to the studentRegister route
            return redirect("/studentRegister")

        # Execute the query
        cursor.execute(retrieveSuperviser_sql, (supervisorEmail))
        uniSupervisor = cursor.fetchone()
        supervisorId = uniSupervisor[0]

        # Upload image file in S3
        uploadToS3(profilePic, "students/" + studEmail + "/profile.png")
        profilePath = "students/" + studEmail + "/profile.png"

        insertStud_sql = "INSERT INTO " + studentTable + \
            " VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        insertStudPersonal_sql = "INSERT INTO " + studentPersonalTable + \
            " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

        cursor.execute(insertStud_sql, (studEmail, curEduLevel, cohort,
                       programme, tutGrp, latestCgpa, studId, supervisorId))
        cursor.execute(insertStudPersonal_sql, (studName, nric, gender, ownTransport,
                       healthRemark, personalEmail, termAddr, permAddr, contactNo, profilePath, studEmail))

        connection.commit()
    except Exception as e:
        connection.rollback()  # Rollback the transaction if an exception occurs
    finally:
        cursor.close()
        connection.close()

    return render_template("studentLogin.html", success="You may login now")


@app.route("/StudLogin", methods=['POST'])
def StudLogin():
    studEmail = request.form['studentEmail']
    nric = request.form['nric']

    retrieveStudentPersonal_sql = "SELECT * FROM " + \
        studentPersonalTable + " WHERE StudentEmail = %s AND NRIC = %s"
    connection = create_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(retrieveStudentPersonal_sql, (studEmail, nric))
        studentPersonal = cursor.fetchone()
    except Exception as e:
        connection.rollback()  # Rollback the transaction if an exception occurs
    finally:
        cursor.close()
        connection.close()

    if studentPersonal is None:
        return render_template('studentLogin.html', error="Invalid Email or NRIC")
    else:
        if studentPersonal[len(studentPersonal) - 1] == studEmail and studentPersonal[1] == nric:
            session["studEmail"] = studEmail
            return redirect("/studentHome")


@app.route("/studentHome")
def studentDashboard():
    studEmail = session["studEmail"]
    retrieveStudent_sql = "SELECT * FROM " + \
        studentTable + " WHERE StudentEmail = %s"
    retrieveStudentPersonal_sql = "SELECT * FROM " + \
        studentPersonalTable + " WHERE StudentEmail = %s"
    connection = create_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(retrieveStudent_sql, (studEmail))
        student = cursor.fetchone()
        cursor.execute(retrieveStudentPersonal_sql, (studEmail))
        studentPersonal = cursor.fetchone()
        student = {"name": studentPersonal[0], "studId": student[6],
                   "profilePic": get_object_url(studentPersonal[9])}
    except Exception as e:
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

    return render_template("studentHome.html", student=student)


@app.route("/studentProfile")
def studentProfile():
    studEmail = session["studEmail"]
    retrieveStudent_sql = "SELECT * FROM " + \
        studentTable + " WHERE StudentEmail = %s"
    retrieveStudentPersonal_sql = "SELECT * FROM " + \
        studentPersonalTable + " WHERE StudentEmail = %s"
    retrieveSupervisor_sql = "SELECT * FROM " + \
        universitySupervisorTable + " WHERE StaffId = %s"
    connection = create_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(retrieveStudent_sql, (studEmail))
        student = cursor.fetchone()
        cursor.execute(retrieveStudentPersonal_sql, (studEmail))
        studentPersonal = cursor.fetchone()
        studentObj = Student(student[0], student[1], student[2], student[3], student[4], student[5], student[6], student[7],
                             studentPersonal[0], studentPersonal[1], studentPersonal[2], studentPersonal[3], studentPersonal[4], studentPersonal[5], studentPersonal[6], studentPersonal[7], studentPersonal[8], studentPersonal[9])
        studentObj.profilePic = get_object_url(studentObj.profilePic)
        cursor.execute(retrieveSupervisor_sql, (studentObj.supervisorId))
        result = cursor.fetchone()
        supervisor = UniversitySupervisor(
            result[0], result[1], result[2], result[3], result[4])
        studentSupervisor = {
            "name": supervisor.name, "email": supervisor.email}
    except Exception as e:
        connection.rollback()
    finally:
        cursor.close()
        connection.close()
    student_dict = vars(studentObj)
    for key, value in student_dict.items():
        print(f"{key}: {value}")

    success = get_flashed_messages(category_filter=['update-success'])
    if success:
        success = success[0]

    return render_template("studentProfile.html", student=studentObj, supervisor=studentSupervisor, success=success)


@app.route("/UpdateStudProfile", methods=['POST'])
def updateStudProfile():
    studEmail = session["studEmail"]
    # profile, cgpa, own transport, health remarks, personal email, mobile, term address

    cgpa = request.form['cgpa']
    ownTransport = request.form['transport']
    healthRemark = request.form.get('healthRemark', '')
    personalEmail = request.form['personalEmail']
    mobile = request.form['mobile']
    termAddr = request.form.get('termAddr', '')

    connection = create_connection()
    cursor = connection.cursor()

    try:
        updateStud_sql = "UPDATE " + studentTable + \
            " SET LatestCgpa = %s WHERE StudentEmail = %s"
        updateStudProfile_sql = "UPDATE " + studentPersonalTable + \
            " SET ProfilePic = %s WHERE StudentEmail = %s"
        updateStudPersonal_sql = "UPDATE " + studentPersonalTable + \
            " SET OwnTransport = %s, HealthRemark = %s, PersonalEmail = %s, ContactNo = %s, TermAddress = %s WHERE StudentEmail = %s"
        if 'profile' in request.files:
            profilePic = request.files['profile']
            if profilePic.filename != '':
                # Upload image file in S3
                uploadToS3(profilePic, "students/" +
                           studEmail + "/profile.png")
                profilePath = "students/" + studEmail + "/profile.png"
                # Update profile pic path in Student Table
                cursor.execute(updateStudProfile_sql, (profilePath, studEmail))

        cursor.execute(updateStud_sql, (cgpa, studEmail))
        cursor.execute(updateStudPersonal_sql, (ownTransport,
                       healthRemark, personalEmail, mobile, termAddr, studEmail))
        connection.commit()
        flash("Your profile has been updated!", 'update-success')
        print("success")
    except Exception as e:
        print(e)
        connection.rollback()  # Rollback the transaction if an exception occurs
        print("got problem")
    finally:
        cursor.close()
        connection.close()

    return redirect("/studentProfile")


@app.route("/AddCompany", methods=['POST'])
def AddComp():

    # Company Table
    compName = request.form['companyName']
    username = request.form['cUsername']
    password = request.form['cPassword']
    otClaim = request.form['otClaim']
    compAddr = request.form['address']
    ssmCert = request.files['ssmCert']
    industry = request.form.getlist('industries')
    totalStaff = request.form['totalStaff']
    companyStatus = "Pending"
    website = request.form.get('website', '')
    # FK PersonInChargeId <-- CompanyPersonnel Table
    # CompanyPersonnel Table
    name = request.form['personName']
    designation = request.form['designation']
    contactNo = request.form['contact']
    email = request.form['pEmail']

    insertComp_sql = "INSERT INTO " + companyTable + \
        " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    insertPic_sql = "INSERT INTO " + \
        companyPersonnelTable + " VALUES (%s, %s, %s, %s, %s)"
    connection = create_connection()
    cursor = connection.cursor()
    delimiter = '|'
    try:
        print("hii")
        success = ""
        # Retrieve company id sequence number from table SEQ_MATRIX
        retrieveSeqNo_sql = "SELECT SEQ_NO FROM " + \
            sequenceTable + " WHERE TBL_NAME = '" + companyTable + "'"
        cursor.execute(retrieveSeqNo_sql)
        seqNo = cursor.fetchone()[0]
        compId = "CP" + fillLeftZero(6, seqNo)
        # Retrieve person in charge id sequence number from table SEQ_MATRIX
        retrieveSeqNo_sql = "SELECT SEQ_NO FROM " + sequenceTable + \
            " WHERE TBL_NAME = '" + companyPersonnelTable + "'"
        cursor.execute(retrieveSeqNo_sql)
        seqNo = cursor.fetchone()[0]
        picId = "PIC" + fillLeftZero(4, seqNo)

        # Update sequence number in SEQ_MATRIX
        updateCmpSeq_sql = "UPDATE " + sequenceTable + \
            " SET SEQ_NO = SEQ_NO + 1 WHERE TBL_NAME = '" + companyTable + "'"
        updatePicSeq_sql = "UPDATE " + sequenceTable + \
            " SET SEQ_NO = SEQ_NO + 1 WHERE TBL_NAME = '" + companyPersonnelTable + "'"
        cursor.execute(updateCmpSeq_sql)
        cursor.execute(updatePicSeq_sql)

        compLogoPath = ""
        if 'logo' in request.files:
            logo = request.files['logo']
            if logo.filename != '':
                print("logo not empty")
                # Upload image file in S3
                uploadToS3(logo, "companies/" + compId + "/logo.png")
                compLogoPath = "companies/" + compId + "/logo.png"
        # Upload ssm cert pdf file in S3
        uploadToS3(ssmCert, "companies/" + compId + "/ssmCert.pdf")
        ssmCertPath = "companies/" + compId + "/ssmCert.pdf"

        cursor.execute(insertPic_sql, (picId, name,
                       designation, contactNo, email))
        cursor.execute(insertComp_sql, (compId, compName, username, password, otClaim, compAddr,
                       ssmCertPath, delimiter.join(industry), compLogoPath, totalStaff, companyStatus, website, picId))

        connection.commit()
        success = "Company registration successful. Please wait for admin approval. You will be notified via email once your company status is updated."
    except Exception as e:
        print(e)
        connection.rollback()  # Rollback the transaction if an exception occurs
    finally:
        cursor.close()
        connection.close()

    return render_template("companyLogin.html", success=success)


@app.route("/CompLogin")
def CompLogin():
    username = request.args.get('username')
    password = request.args.get('password')

    retrieveCompany_sql = "SELECT * FROM " + companyTable + \
        " WHERE Username = %s AND Password = %s"
    connection = create_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(retrieveCompany_sql, (username, password))
        company = cursor.fetchone()
    except Exception as e:
        connection.rollback()  # Rollback the transaction if an exception occurs
    finally:
        cursor.close()
        connection.close()

    if company is None:
        return render_template('companyLogin.html', error="Invalid Username or Password")
    else:
        if company[2] == username and company[3] == password:
            session["companyId"] = company[0]
            return redirect("/companyHome")


@app.route("/companyHome")
def companyDashboard():
    compId = session["companyId"]
    retrieveCompany_sql = "SELECT * FROM " + companyTable + " WHERE CompanyId = %s"
    connection = create_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(retrieveCompany_sql, (compId))
        company = cursor.fetchone()
        # cursor.execute(retrievePIC_sql, (company[12]))
        # personInCharge = cursor.fetchone()
        print(company)
        company = {"companyName": company[1], "username": company[2], "logo": get_object_url(
            company[8]), "companyStatus": company[10]}
    except Exception as e:
        print(e)
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

    return render_template("companyHome.html", company=company)


@app.route("/companyProfile")
def companyProfile():
    compId = session['companyId']
    retrieveCompany_sql = "SELECT * FROM " + companyTable + " WHERE CompanyId = %s"
    retrievePIC_sql = "SELECT * FROM " + \
        companyPersonnelTable + " WHERE PersonInChargeId = %s"
    connection = create_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(retrieveCompany_sql, (compId))
        companyResult = cursor.fetchone()
        cursor.execute(retrievePIC_sql, (companyResult[12]))
        companyPersonnel = cursor.fetchone()
        company = Company(companyResult[0], companyResult[1], companyResult[2], companyResult[3], companyResult[4], companyResult[5],
                          companyResult[6], companyResult[7], companyResult[8], companyResult[9], companyResult[10], companyResult[11], companyResult[12])
        pic = CompanyPersonnel(companyPersonnel[0], companyPersonnel[1],
                               companyPersonnel[2], companyPersonnel[3], companyPersonnel[4])
        company.logo = get_object_url(company.logo)

    except Exception as e:
        print(e)
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

    success = get_flashed_messages(category_filter=['update-success'])
    if success:
        success = success[0]

    return render_template("companyProfile.html", company=company, personInCharge=pic, success=success)


@app.route("/UpdateCompProfile", methods=['POST'])
def updateCompProfile():
    # Company Table
    compId = session['companyId']
    compName = request.form['companyName']
    otClaim = request.form['otClaim']
    compAddr = request.form['address']
    industry = request.form.getlist('industries')
    totalStaff = request.form['totalStaff']
    website = request.form.get('website', '')
    # FK PersonInChargeId <-- CompanyPersonnel Table
    # CompanyPersonnel Table
    picId = request.form['personInChargeId']
    name = request.form['personName']
    designation = request.form['designation']
    contactNo = request.form['contact']
    email = request.form['pEmail']

    updateCompany_sql = "UPDATE " + companyTable + \
        " SET CompanyName = %s, OTClaim = %s, Address = %s, Industry = %s, TotalStaff = %s, Website = %s WHERE CompanyId = %s"
    updateCompanyPersonnel_sql = "UPDATE " + companyPersonnelTable + \
        " SET Name = %s, Designation = %s, ContactNo = %s, Email = %s WHERE PersonInChargeId = %s"
    connection = create_connection()
    cursor = connection.cursor()
    delimiter = '|'
    try:
        print("hii")
        compLogoPath = ""
        if 'logo' in request.files:
            logo = request.files['logo']
            if logo.filename != '':
                print("logo not empty")
                # Upload image file in S3
                compLogoPath = "companies/" + compId + "/logo.png"
                uploadToS3(logo, compLogoPath)
                updateCompLogo_sql = "UPDATE " + companyTable + \
                    " SET Logo = %s WHERE CompanyId = %s"
                cursor.execute(updateCompLogo_sql, (compLogoPath, compId))
        cursor.execute(updateCompany_sql, (compName, otClaim, compAddr,
                       delimiter.join(industry), totalStaff, website, compId))
        cursor.execute(updateCompanyPersonnel_sql,
                       (name, designation, contactNo, email, picId))

        flash("Your profile has been updated!", 'update-success')
        connection.commit()
    except Exception as e:
        print(e)
        connection.rollback()  # Rollback the transaction if an exception occurs
    finally:
        cursor.close()
        connection.close()

    return redirect("/companyProfile")


@app.route("/jobPosting")
def jobPosting():
    compId = session["companyId"]

    companyResult = retrieveCompById(compId)
    jobsResult = retrieveCompJobById(compId)

    company = {"companyName": companyResult[1], "username": companyResult[2], "logo": get_object_url(
        companyResult[8]), "companyStatus": companyResult[10]}
    companyJobs = []
    for job in jobsResult:
        job = InternshipJob(job[0], job[1], job[2], job[3], job[4],
                            job[5], job[6], job[7], job[8], job[9], job[10])
        companyJobs.append(job)

    success = get_flashed_messages(category_filter=['job-added'])
    if success:
        success = success[0]

    return render_template("jobPosting.html", company=company, companyJobs=companyJobs, success=success)


@app.route("/jobPostingDetailViewEdit")
def jobPostingDetails():
    jobId = request.args.get('jobId')
    compId = session["companyId"]

    companyResult = retrieveCompById(compId)
    company = {"companyName": companyResult[1], "username": companyResult[2], "logo": get_object_url(
        companyResult[8]), "companyStatus": companyResult[10]}
    jobResult = retrieveJobById(jobId)
    job = InternshipJob(jobResult[0], jobResult[1], jobResult[2], jobResult[3], jobResult[4],
                        jobResult[5], jobResult[6], jobResult[7], jobResult[8], jobResult[9], jobResult[10])

    success = get_flashed_messages(category_filter=['update-success'])
    if success:
        success = success[0]

    return render_template("jobPostingDetailViewEdit.html", company=company, job=job, success=success)


@app.route("/UpdateJobDetail", methods=['POST'])
def updateJobDetail():
    jobId = request.form['jobId']
    jobTitle = request.form['jobTitle']
    jobDesc = request.form['jobDesc']
    allowance = request.form['allowance']
    workingDay = request.form['workingDay']
    workingHour = request.form['workingHour']
    openFor = request.form['openFor']
    accessory = request.form['accessory']
    accommodation = request.form['accommodation']

    # by default, set these 2 to "N"
    diploma = "N"
    degree = "N"

    if openFor == "diploma":
        diploma = "Y"
    elif openFor == "degree":
        degree = "Y"
    elif openFor == "diplomaAndDegree":
        diploma = "Y"
        degree = "Y"

    updateJobDetail_sql = "UPDATE " + internshipJobTable + \
        " SET JobTitle = %s, JobDescription = %s, Allowance = %s, WorkingDay = %s, WorkingHour = %s, Diploma = %s, Degree = %s, AccessoryProvide = %s, Accommodation = %s WHERE JobId = %s"
    try:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute(updateJobDetail_sql, (jobTitle, jobDesc, allowance, workingDay,
                       workingHour, diploma, degree, accessory, accommodation, jobId))
        connection.commit()
        flash("Job Post has been updated successfully", 'update-success')
    except Exception as e:
        print(e)
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

    return redirect("/jobPostingDetailViewEdit?jobId=" + jobId)


@app.route("/jobAdding")
def jobPostingDetail():
    compId = session["companyId"]

    companyResult = retrieveCompById(compId)
    company = {"companyName": companyResult[1], "username": companyResult[2], "logo": get_object_url(
        companyResult[8]), "companyStatus": companyResult[10]}

    return render_template("jobAdding.html", company=company)


@app.route("/AddJob", methods=['POST'])
def AddJob():
    # InternshipJob Table
    # jobId = request.form['jobId']
    jobTitle = request.form['jobTitle']
    jobDesc = request.form['jobDesc']
    allowance = request.form['allowance']
    workingDay = request.form['workingDay']
    workingHour = request.form['workingHour']
    openFor = request.form['openFor']
    accessory = request.form['accessory']
    accommodation = request.form['accommodation']
    # by default, set these 2 to "N"
    diploma = "N"
    degree = "N"

    if openFor == "diploma":
        diploma = "Y"
    elif openFor == "degree":
        degree = "Y"
    elif openFor == "diplomaAndDegree":
        diploma = "Y"
        degree = "Y"
    # FK companyId <-- Company Table
    compId = session["companyId"]
    try:
        insertJob_sql = "INSERT INTO " + internshipJobTable + \
            " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

        seqNo = retrieveSeqNoByTblName(internshipJobTable)
        print(seqNo)
        jobId = "J" + fillLeftZero(5, seqNo)
        print(jobId)
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute(insertJob_sql, (jobId, jobTitle, jobDesc, allowance, workingDay,
                       workingHour, diploma, degree, accessory, accommodation, compId))
        
        # Update sequence number in SEQ_MATRIX
        updateJobSeq_sql = "UPDATE " + sequenceTable + \
            " SET SEQ_NO = SEQ_NO + 1 WHERE TBL_NAME = '" + internshipJobTable + "'"
        cursor.execute(updateJobSeq_sql)
        connection.commit()
        flash("Job has been added successfully", 'job-added')
    except Exception as e:
        print(e)
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

    return redirect("/jobPosting")


def AddTask():
    # Task Table
    # taskId = request.form['taskId']
    taskName = request.form['taskName']
    dueDate = request.form['dueDate']

    insertTask_sql = "INSERT INTO " + taskTable + " VALUES (%s, %s, %s)"
    connection = create_connection()
    cursor = connection.cursor()


def AddCompRequest():
    # CompanyRequest Table
    # requestId = request.form['requestId']
    companyName = request.form['companyName']
    companyAddr = request.form['companyAddr']
    requestStatus = "Pending"
    # FK studEmail
    # FK adminId

    insertCompRequest_sql = "INSERT INTO " + \
        companyRequestTable + " VALUES (%s, %s, %s, %s)"
    connection = create_connection()
    cursor = connection.cursor()


def submitReport():
    # Submission Table
    # submissionId = request.form['submissionId']
    dateSubmitted = datetime.now()
    report = request.files['report']
    # taskId
    # studEmail

    insertSubmission_sql = "INSERT INTO " + submissionTable + \
        " (SubmissionId, DateSubmitted, Report, TaskId, StudentEmail) VALUES (%s, %s, %s, %s, %s)"
    connection = create_connection()
    cursor = connection.cursor()


def applyJob():
    # InternshipApplication Table
    # applicationId = request.form['applicationId']
    applicationStatus = "Pending"
    applyDate = datetime.now()
    # FK jobId
    # FK studEmail

    insertApplication_sql = "INSERT INTO " + internshipApplicationTable + \
        "(ApplicationId, ApplicationStatus, ApplyDate, JobId, StudentEmail) VALUES (%s, %s, %s, %s, %s)"
    connection = create_connection()
    cursor = connection.cursor()


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

    insertInternship_sql = "INSERT INTO " + \
        internshipTable + " VALUES (%s, %s, %s, %s, %s, %s)"
    connection = create_connection()
    cursor = connection.cursor()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
