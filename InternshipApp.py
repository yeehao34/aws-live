from flask import Flask, render_template, request, redirect, session, flash, get_flashed_messages
from flask_session import Session
from datetime import datetime
from s3_service import uploadToS3, get_object_url
from Models import *
from db_connection import create_connection
from utils import *
from db_service import *
import os

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
attachmentTable = 'Attachment'


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

# --------------------- Student ---------------------------


@app.route("/studentRegister")
def studentRegister():

    connection = create_connection()
    cursor = connection.cursor()
    try:

        uniSupervisorResults = retrieveAllUniSup()
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

    connection = create_connection()
    cursor = connection.cursor()

    try:

        if (retrieveStudByEmail(studEmail) is not None):
            print("Student already exists")
            flash("Student already exists", 'student-error')
            # Redirect to the studentRegister route
            return redirect("/studentRegister")

        # Execute the query
        uniSupervisor = retrieveUniSupervisorByEmail(supervisorEmail)
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

    allStudentDetails = retrieveAllStudDetail()

    for stud in allStudentDetails:
        if stud[-1] == studEmail and stud[1] == nric:
            session["studEmail"] = studEmail
            return redirect("/studentHome")

    return render_template('studentLogin.html', error="Invalid Email or NRIC")


@app.route("/studentHome")
def studentDashboard():
    studEmail = session["studEmail"]

    student = retrieveStudByEmail(studEmail)
    studentPersonal = retrieveStudDetailByEmail(studEmail)
    student = {"name": studentPersonal[0], "studId": student[6],
               "profilePic": get_object_url(studentPersonal[9])}

    internship = retrieveInternshipByEmail(studEmail)
    if internship != None:
        internship = Internship(internship[0], internship[1], internship[2], internship[3],
                                internship[4], internship[5], internship[6], internship[7], internship[8])

    return render_template("studentHome.html", student=student, internship=internship)


@app.route("/studentTask")
def studentTask():
    studEmail = session["studEmail"]

    student = retrieveStudByEmail(studEmail)
    studentPersonal = retrieveStudDetailByEmail(studEmail)
    student = {"name": studentPersonal[0], "studId": student[6],
               "profilePic": get_object_url(studentPersonal[9])}

    studentTasks = retrieveStudentSubmissionByEmail(studEmail)

    pendingTask = []
    completedTask = []
    for studentTask in studentTasks:
        studentTask = Submission(studentTask[0], studentTask[1], studentTask[2],
                                 studentTask[3], studentTask[4], studentTask[5], studentTask[6])
        print(studentTask)
        task = retrieveTaskById(studentTask.taskId)
        print(task)
        task = Task(task[0], task[1], task[2], task[3], task[4], task[5])
        studentTask.taskName = task.taskName
        studentTask.taskDesc = task.taskDesc
        studentTask.dueDate = task.dueDate.strftime("%d, %b %H:%M %p")
        studentTask.attachmentName = task.attachmentName
        studentTask.attachmentURL = get_object_url(task.attachmentURL)
        if studentTask.dateSubmitted == None:
            studentTask.submissionStatus = "Pending"
            pendingTask.append(studentTask)
        else:
            studentTask.submissionStatus = "Submitted"
            completedTask.append(studentTask)

    return render_template("studentTask.html", student=student, pdngTask=pendingTask, cptdTask=completedTask)


@app.route("/viewTask")
def viewTask():
    studEmail = session["studEmail"]
    submissionId = request.args.get('submissionId')
    submissionStatus = request.args.get('submissionStatus')
    student = retrieveStudByEmail(studEmail)
    studentPersonal = retrieveStudDetailByEmail(studEmail)
    student = {"name": studentPersonal[0], "studId": student[6],
               "profilePic": get_object_url(studentPersonal[9])}

    print(submissionId)
    submission = retrieveStudentSubmissionById(submissionId)
    print(submission)
    submission = Submission(submission[0], submission[1], submission[2],
                            submission[3], submission[4], submission[5], submission[6])
    task = retrieveTaskById(submission.taskId)
    task = Task(task[0], task[1], task[2], task[3], task[4], task[5])
    task.attachmentURL = get_object_url(task.attachmentURL)
    if submissionStatus == "pending":
        if (datetime.now() > task.dueDate):
            submitStatus = "Missing"
        else:
            submitStatus = "Pending"
    elif submissionStatus == "submitted":
        if (submission.dateSubmitted > task.dueDate):
            submitStatus = "Turned in Late"
        else:
            submitStatus = "Submitted"
    task.dueDate = task.dueDate.strftime("%d, %b %H:%M %p")
    if submission.dateSubmitted != None:
        submission.dateSubmitted = submission.dateSubmitted.strftime(
            "%d, %b %H:%M %p")

    success = get_flashed_messages(category_filter=['submit-success'])
    if success:
        success = success[0]

    return render_template("/viewTask.html", student=student, submission=submission, taskViewing=task, submitStatus=submitStatus, success=success)


@app.route("/SubmitTask", methods=['GET', 'POST'])
def SubmitTask():
    submissionId = request.form['submissionId']
    report = request.files['report']
    taskName = request.form['taskName']
    dateSubmitted = datetime.now()

    try:
        connection = create_connection()
        cursor = connection.cursor()
        updateSubmission_sql = "UPDATE " + submissionTable + \
            " SET Report = %s, DateSubmitted = %s WHERE SubmissionId = %s"
        path = "students/" + session["studEmail"] + \
            "/" + taskName + "/" + report.filename
        uploadToS3(report, path)
        cursor.execute(updateSubmission_sql, (path, dateSubmitted, submissionId))
        connection.commit()
        
        flash("Your report has been submitted successfully", 'submit-success')        
    except Exception as e:
        print(e)
        connection.rollback()
    finally:
        cursor.close()
        connection.close()
        
    return redirect("/viewTask?submissionId=" + submissionId + "&submissionStatus=submitted")


@app.route("/studentProfile")
def studentProfile():
    studEmail = session["studEmail"]

    student = retrieveStudByEmail(studEmail)
    studentPersonal = retrieveStudDetailByEmail(studEmail)
    studentObj = Student(student[0], student[1], student[2], student[3], student[4], student[5], student[6], student[7],
                         studentPersonal[0], studentPersonal[1], studentPersonal[2], studentPersonal[3], studentPersonal[4], studentPersonal[5], studentPersonal[6], studentPersonal[7], studentPersonal[8], studentPersonal[9])

    studentObj.profilePic = get_object_url(studentObj.profilePic)
    supervisor = retrieveUniSupervisorById(studentObj.supervisorId)
    supervisor = UniversitySupervisor(
        supervisor[0], supervisor[1], supervisor[2], supervisor[3], supervisor[4])
    student_dict = vars(studentObj)
    for key, value in student_dict.items():
        print(f"{key}: {value}")

    success = get_flashed_messages(category_filter=['update-success'])
    if success:
        success = success[0]

    return render_template("studentProfile.html", student=studentObj, supervisor=supervisor, success=success)


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

# --------------------- Student ---------------------------


# --------------------- Company ---------------------------
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


@app.route("/CompLogin", methods=['POST'])
def CompLogin():
    username = request.form['username']
    password = request.form['password']

    allCompanies = retrieveAllComp()

    for company in allCompanies:
        if company[2] == username and company[3] == password:
            session["companyId"] = company[0]
            return redirect("/companyHome")

    return render_template('companyLogin.html', error="Invalid Username or Password")


@app.route("/companyHome")
def companyDashboard():
    compId = session["companyId"]
    companyResult = retrieveCompById(compId)

    company = {"companyName": companyResult[1], "username": companyResult[2], "logo": get_object_url(
        companyResult[8]), "companyStatus": companyResult[10]}

    return render_template("companyHome.html", company=company)


@app.route("/companyProfile")
def companyProfile():
    compId = session['companyId']
    companyResult = retrieveCompById(compId)
    picResult = retrievePICById(companyResult[12])

    company = Company(companyResult[0], companyResult[1], companyResult[2], companyResult[3], companyResult[4], companyResult[5],
                      companyResult[6], companyResult[7], companyResult[8], companyResult[9], companyResult[10], companyResult[11], companyResult[12])
    pic = CompanyPersonnel(picResult[0], picResult[1],
                           picResult[2], picResult[3], picResult[4])
    company.logo = get_object_url(company.logo)

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

# --------------------- Company ---------------------------


# --------------------- Supervisor ---------------------------
@app.route("/SupervisorLogin", methods=['POST'])
def SupervisorLogin():
    email = request.form['email']
    password = request.form['password']

    allSupervisor = retrieveAllUniSup()
    for sup in allSupervisor:
        if sup[1] == email and sup[2] == password:
            session["supervisorId"] = sup[0]
            return redirect("/supervisorHome")

    return render_template('supervisorLogin.html', error="Invalid Email or Password")


@app.route("/supervisorHome")
def supervisorDashboard():
    supervisorId = session['supervisorId']
    supervisor = retrieveUniSupervisorById(supervisorId)
    supervisor = UniversitySupervisor(
        supervisor[0], supervisor[1], supervisor[2], supervisor[3], supervisor[4])

    return render_template("supervisorHome.html", supervisor=supervisor)


@app.route("/supervisorProfile")
def supervisorProfile():
    supervisorId = session['supervisorId']
    supervisor = retrieveUniSupervisorById(supervisorId)

    supervisor = UniversitySupervisor(
        supervisor[0], supervisor[1], supervisor[2], supervisor[3], supervisor[4])

    success = get_flashed_messages(category_filter=['update-success'])
    if success:
        success = success[0]
    return render_template("supervisorProfile.html", supervisor=supervisor, success=success)


@app.route("/UpdateSupervisorProfile", methods=['POST'])
def UpdateSupervisorProfile():
    supervisorId = session['supervisorId']
    password = request.form['newPassword']
    name = request.form['name']
    contact = request.form['contact']

    if password == "":
        password = request.form['oldPassword']

    try:
        updateSupervisor_sql = "UPDATE " + universitySupervisorTable + \
            " SET Password = %s, Name = %s, ContactNo = %s WHERE StaffId = %s"
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute(updateSupervisor_sql,
                       (password, name, contact, supervisorId))
        connection.commit()
    except Exception as e:
        print(e)
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

    flash("Your profile has been updated!", 'update-success')

    return redirect("/supervisorProfile")

# --------------------- Supervisor ---------------------------


# --------------------- Admin ---------------------------
@app.route("/AdminLogin", methods=['POST'])
def AdminLogin():
    username = request.form['username']
    password = request.form['password']

    allAdmin = retrieveAllAdmin()

    for admin in allAdmin:
        if admin[1] == username and admin[2] == password:
            session["adminId"] = admin[0]
            return redirect("/adminHome")

    return render_template('adminLogin.html', error="Invalid Username or Password")


@app.route("/adminHome")
def adminDashboard():
    adminId = session['adminId']
    allAdmin = retrieveAllAdmin()
    for admin in allAdmin:
        if admin[0] == adminId:
            admin = Admin(admin[0], admin[1], admin[2], admin[3], admin[4])
            break

    return render_template("adminHome.html", admin=admin)


@app.route("/adminProfile")
def adminProfile():
    adminId = session['adminId']
    allAdmin = retrieveAllAdmin()
    for admin in allAdmin:
        if admin[0] == adminId:
            admin = Admin(admin[0], admin[1], admin[2], admin[3], admin[4])
            break

    success = get_flashed_messages(category_filter=['update-success'])
    if success:
        success = success[0]
    return render_template("adminProfile.html", admin=admin, success=success)


@app.route("/UpdateAdminProfile", methods=['POST'])
def UpdateAdminProfile():
    adminId = session['adminId']
    password = request.form['newPassword']
    name = request.form['name']
    email = request.form['email']

    if password == "":
        password = request.form['oldPassword']

    try:
        updateAdmin_sql = "UPDATE " + adminTable + \
            " SET Password = %s, Name = %s, Email = %s WHERE AdminId = %s"
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute(updateAdmin_sql, (password, name, email, adminId))
        connection.commit()
    except Exception as e:
        print(e)
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

    flash("Your profile has been updated!", 'update-success')

    return redirect("/adminProfile")


@app.route("/AddTask", methods=['POST'])
def AddTask():
    # Task Table
    taskTitle = request.form['taskTitle']
    taskDesc = request.form['taskDesc']
    taskDeadline = request.form['taskDeadline']
    print(taskDeadline)
    # Attachment Table (only 1 file)
    attachment = request.files['attachment']

    allStudents = retrieveAllStud()

    # Get this tasks belongs to which level of students (diploma/degree/both)
    openFor = request.form['openFor']
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

    try:
        connection = create_connection()
        cursor = connection.cursor()
        # Insert Task
        taskSeqNo = retrieveSeqNoByTblName(taskTable)
        taskId = "TK" + fillLeftZero(4, taskSeqNo)
        insertTask_sql = "INSERT INTO " + \
            taskTable + " VALUES (%s, %s, %s, %s)"
        cursor.execute(
            insertTask_sql, (taskId, taskTitle, taskDesc, taskDeadline))
        # Insert Attachment
        insertAttachment_sql = "INSERT INTO " + \
            attachmentTable + " VALUES (%s, %s, %s, %s)"
        attachSeqNo = retrieveSeqNoByTblName(attachmentTable)
        attachmentId = "A" + fillLeftZero(5, attachSeqNo)
        attachmentName = attachment.filename
        print(attachment.filename)
        attachmentURL = "Attachment/" + attachmentId + "/" + attachmentName
        uploadToS3(attachment, attachmentURL)
        cursor.execute(insertAttachment_sql, (attachmentId,
                       attachmentName, attachmentURL, taskId))
        # Update task sequence number and attachment sequence number
        updateTaskSeq_sql = "UPDATE " + sequenceTable + \
            " SET SEQ_NO = SEQ_NO + 1 WHERE TBL_NAME = '" + taskTable + "'"
        updateAttchmentSeq_sql = "UPDATE " + sequenceTable + \
            " SET SEQ_NO = SEQ_NO + 1 WHERE TBL_NAME = '" + attachmentTable + "'"
        cursor.execute(updateTaskSeq_sql)
        cursor.execute(updateAttchmentSeq_sql)

        # Create Submission for every students that involved in the task
        insertSubmission_sql = "INSERT INTO " + submissionTable + \
            " (SubmissionId, StudentEmail, TaskId) VALUES (%s, %s, %s)"
        submissionSeqNo = retrieveSeqNoByTblName(submissionTable)
        rowCreated = 0
        for stud in allStudents:
            if (diploma == "Y" and stud[1] == "Diploma") or (degree == "Y" and stud[1] == "Bachelor"):
                submissionId = "S" + fillLeftZero(6, submissionSeqNo)
                cursor.execute(insertSubmission_sql,
                               (submissionId, stud[0], taskId))
                submissionSeqNo += 1
                rowCreated += 1
        print("row created: " + str(rowCreated))
        # Update submission sequence number
        updateSubmissionSeq_sql = "UPDATE " + sequenceTable + " SET SEQ_NO = SEQ_NO + " + \
            str(rowCreated) + " WHERE TBL_NAME = '" + submissionTable + "'"
        cursor.execute(updateSubmissionSeq_sql)

        # Commit the transaction
        connection.commit()
    except Exception as e:
        print(e)
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

    flash("Task has been added successfully and assigned to students", 'task-added')
    return redirect("/adminTask")
# --------------------- Admin ---------------------------


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
    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)
