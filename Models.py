class Student:
    def __init__(self, studEmail, eduLvl, cohort, programme, tutGrp, latestCgpa, studId, supervisorId, name, nric, gender, ownTransport, healthRemark, personalEmail, termAddr, permAddr, contactNo, profilePic):
        self.studEmail = studEmail
        self.eduLvl = eduLvl
        self.cohort = cohort
        self.programme = programme
        self.tutGrp = tutGrp
        self.latestCgpa = latestCgpa
        self.studId = studId
        self.supervisorId = supervisorId
        self.name = name
        self.nric = nric
        self.gender = gender
        self.ownTransport = ownTransport
        self.healthRemark = healthRemark
        self.personalEmail = personalEmail
        self.termAddr = termAddr
        self.permAddr = permAddr
        self.contactNo = contactNo
        self.profilePic = profilePic
        
class Admin:
    def __init__(self, adminId, username, password, name, email):
        self.adminId = adminId
        self.username = username
        self.password = password
        self.name = name
        self.email = email
        
class UniversitySupervisor:
    def __init__(self, staffId, email, password, name, contact):
        self.staffId = staffId
        self.email = email
        self.password = password
        self.name = name
        self.contact = contact

class Company:
    def __init__(self, companyId, companyName, username, password, otClaim, address, industry, totalStf, companyStatus, website, picId):
        self.companyId = companyId
        self.companyName = companyName
        self.username = username
        self.password = password
        self.otClaim = otClaim
        self.address = address
        self.industry = industry
        self.totalStf = totalStf
        self.companyStatus = companyStatus
        self.website = website
        self.picId = picId

class CompanyPersonnel:
    def __init__(self, picId, name, designation, contactNo, email):
        self.picId = picId
        self.name = name
        self.designation = designation
        self.contactNo = contactNo
        self.email = email

class InternshipJob:
    def __init__(self, jobId, jobTitle, jobDesc, allowance, workingDay, workingHour, diploma, degree, accessoryProvide, accommodation, companyId):
        self.jobId = jobId
        self.jobTitle = jobTitle
        self.jobDesc = jobDesc
        self.allowance = allowance
        self.workingDay = workingDay
        self.workingHour = workingHour
        self.diploma = diploma
        self.degree = degree
        self.accessoryProvide = accessoryProvide
        self.accommodation = accommodation
        self.companyId = companyId
        