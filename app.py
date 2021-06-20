from flask import Flask,render_template,redirect,url_for,session,request,flash
from flaskext.mysql import MySQL
import os,json
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.secret_key = 'onlineitcourse'

mysql = MySQL()

app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'root'
app.config['MYSQL_DATABASE_DB'] = 'onlineitcourse1'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

def getData(sql,vals=0):
    con = mysql.connect()
    cur = con.cursor()
    if vals == 0: cur.execute(sql)
    else: cur.execute(sql,vals)
    res = cur.fetchall()
    cur.close()
    con.close()
    return res

def setData(sql,vals=0):
    con = mysql.connect()
    cur = con.cursor()
    if vals == 0: cur.execute(sql)
    else: cur.execute(sql,vals)
    con.commit()
    cur.close()
    con.close()
    res = cur.rowcount
    return res

@app.route('/getSubject',methods=['POST','GET'])
def getSubject():
    cid = request.form['cid']
    sql = "select * from subjects where cid=%s" % cid
    res = getData(sql)
    return json.dumps(res)


@app.route('/')
def home():
    if 'uid' in session and 'role' in session:
        return redirect('/'+session['role']+'/home')
    return render_template('public/home.html')

@app.route('/login/',methods=['POST','GET'])
def login():
    if request.method == 'POST':
        data = request.form
        sql = "select log_id,role from login where username=%s and password=%s"
        vals = (data['uname'],data['pword'])
        res = getData(sql,vals)
        if len(res):
            session['uid'] = res[0][0]
            session['role'] = res[0][1]
            return redirect('/'+res[0][1]+'/home')
        else:
            flash('Invalid login details')
    return render_template('public/login.html')

@app.route('/register',methods=['POST','GET'])
def register():
    data = ''
    if request.method == 'POST':
        data = request.form
        if data['pword'] == data['cpword']:
            sql = "select count(*) from login where username='%s'" % data['email']
            res = getData(sql)
            if res[0][0] == 0:
                sql = "select count(*) from user_details where phone='%s'" % data['phone']
                res = getData(sql)
                if res[0][0] == 0:
                    file = request.files['photo']
                    fn = os.path.basename(file.filename).split('.')
                    fn = fn[len(fn)-1]
                    sql = "select ifnull(max(log_id),0)+1 from login"
                    res = getData(sql)
                    log_id = res[0][0]
                    sql = "insert into login values(%s,%s,%s,'user')"
                    vals = (log_id,data['email'],data['pword'])
                    setData(sql,vals)
                    fn = "%s.%s" % (log_id,fn)
                    sql = "insert into user_details values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                    vals = (log_id,data['fname'],data['lname'],data['address'],data['phone'],data['dob'],data['gender'],fn,data['utype'],data['qualification'])
                    setData(sql,vals)
                    file.save('static/uploads/'+secure_filename(fn))
                    return redirect(url_for('login'))
                else:
                    flash('Phone Number Already Exists')
            else:
                flash('Email Already Exists')
        else:
            flash('Passwords Not Matching')
    sql = "select * from courses"
    res = getData(sql)
    return render_template('public/register.html',courses=res,data=data)

@app.route('/admin/home')
def adminHome():
    if 'uid' not in session or 'role' not in session:
        return redirect(url_for('home'))
    sql = "select eid,title,date,time,duration,c.name from exams e join courses c on c.cid=e.cid order by e.date desc"
    res = getData(sql)
    return render_template('admin/home.html',exams=res)

@app.route('/admin/addExam',methods=['POST','GET'])
def addExam():
    if 'uid' not in session or 'role' not in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        data = request.form
        sql = "select ifnull(max(eid),0)+1 from exams"
        res = getData(sql)
        eid = res[0][0]
        sql = "insert into exams values(%s,%s,%s,%s,%s,%s,1)"
        vals = (eid,data['title'],data['course'],data['date'],data['time'],data['duration'])
        setData(sql,vals)
        return redirect(url_for('adminHome'))
    courses = getData("select * from courses order by name")
    sql = "select * from subjects where cid=%s" % courses[0][0]
    subjects = getData(sql)
    return render_template('admin/addExam.html',courses=courses,subjects=subjects)

@app.route('/admin/editExam/<eid>/',methods=['POST','GET'])
def editExam(eid):
    if 'uid' not in session or 'role' not in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        data = request.form
        sql = "update exams set title=%s,cid=%s,date=%s,time=%s,duration=%s where eid=%s"
        vals = (data['title'],data['course'],data['date'],data['time'],data['duration'],eid)
        setData(sql,vals)
        return redirect(url_for('adminHome'))
    courses = getData("select * from courses order by name")
    sql = "select * from subjects where cid=%s" % courses[0][0]
    subjects = getData(sql)
    sql = "select title,date,time,duration from exams where eid=%s" % eid
    res = getData(sql)
    return render_template('admin/editExam.html',courses=courses,subjects=subjects,data=res[0])

@app.route('/admin/deleteQuestion/<qid>/<sid>/')
def deleteQuestion(qid,sid):
    if 'uid' not in session or 'role' not in session:
        return redirect(url_for('home'))
    sql = "delete from questions where qid=%s" % qid
    setData(sql)
    return redirect(url_for('viewQuestion',sid=sid))

@app.route('/admin/courses',methods=['POST','GET'])
def adminCourse():
    if 'uid' not in session or 'role' not in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        course = request.form['name']
        sql = "select count(*) from courses where name='%s'" % course
        res = getData(sql)
        if res[0][0] == 0:
            sql = "select ifnull(max(cid),0)+1 from courses"
            res = getData(sql)
            cid = res[0][0]
            sql = "insert into courses values(%s,%s)"
            vals = (cid,course)
            setData(sql,vals)
        else:
            flash("Course Already Exists")
    sql = "select * from courses"
    res = getData(sql)
    return render_template('admin/courses.html',courses=res)

@app.route('/admin/viewSubjects/<cid>/',methods=['GET','POST'])
def viewSubjects(cid):
    if 'uid' not in session or 'role' not in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        subject = request.form['name']
        sql = "select count(*) from subjects where name=%s and cid=%s"
        vals = (subject,cid)
        res = getData(sql,vals)
        if res[0][0] == 0:
            sql = "select ifnull(max(sid),0)+1 from subjects"
            res = getData(sql)
            sid = res[0][0]
            sql = "insert into subjects values(%s,%s,%s)"
            vals = (sid,subject,cid)
            setData(sql,vals)
        else:
            flash("Subject Already Exists")
    sql = "select * from subjects where cid=%s" % cid
    res = getData(sql)
    return render_template('admin/viewSubjects.html',subjects=res)

@app.route('/admin/deleteSubject/<sid>/<cid>/')
def deleteSubject(sid,cid):
    if 'uid' not in session or 'role' not in session:
        return redirect(url_for('home'))
    sql = "select count(*) from exams where sid=%s" % sid
    res = getData(sql)
    if res[0][0] == 0:
        sql = "delete from subjects where sid=%s" % sid
        setData(sql)
        flash("Subject Deleted!")
    else: flash("Existing Exams Found In This Subject!!")
    return redirect(url_for('viewSubjects',cid=cid))

@app.route('/admin/viewResults/<eid>/')
def adminViewResult(eid):
    if 'uid' not in session or 'role' not in session:
        return redirect(url_for('home'))
    sql = "select rid,mark,concat(fname,' ',lname) as name from results r join user_details u on u.uid=r.uid where r.eid=%s" % eid
    res = getData(sql)
    return render_template('admin/viewResult.html',results=res)

@app.route('/admin/viewUsers')
def viewUsers():
    sql = "select uid,concat(fname,' ',lname) as name,phone from user_details u join login l on l.log_id=u.uid where l.role='user'"
    res = getData(sql)
    return render_template('admin/viewUsers.html',users=res)

@app.route('/admin/userDetails/<uid>/')
def viewUserDetails(uid):
    sql = "select uid,concat(fname,' ',lname) as name,address,phone,dob,gender,photo,username as email,qualification from user_details u join login l on l.log_id=u.uid where uid=%s" % uid
    res = getData(sql)
    return render_template('admin/userDetails.html',data=res[0])

@app.route('/admin/viewFeedbacks',methods=['GET','POST'])
def viewFeedbacks():
    if request.method == 'POST':
        data = request.form
        sql = "update feedbacks set reply=%s where fid=%s"
        vals = (data['reply'],data['fid'])
        setData(sql,vals)
        flash("Reply Sended")
    sql = "select fid,message,date,reply,concat(fname,' ',lname) as name from feedbacks f join user_details u on u.uid=f.uid"
    res = getData(sql)
    return render_template('admin/viewFeedbacks.html',feedbacks=res)

@app.route('/admin/addFaculty',methods=['POST','GET'])
def addFaculty():
    data = ''
    if request.method == 'POST':
        data = request.form
        if data['pword'] == data['cpword']:
            sql = "select count(*) from login where username='%s'" % data['email']
            res = getData(sql)
            if res[0][0] == 0:
                sql = "select count(*) from user_details where phone='%s'" % data['phone']
                res = getData(sql)
                if res[0][0] == 0:
                    file = request.files['photo']
                    fn = os.path.basename(file.filename).split('.')
                    fn = fn[len(fn)-1]
                    sql = "select ifnull(max(log_id),0)+1 from login"
                    res = getData(sql)
                    log_id = res[0][0]
                    sql = "insert into login values(%s,%s,%s,'faculty')"
                    vals = (log_id,data['email'],data['pword'])
                    setData(sql,vals)
                    fn = "%s.%s" % (log_id,fn)
                    sql = "insert into user_details values(%s,%s,%s,%s,%s,%s,%s,%s,0,%s)"
                    vals = (log_id,data['fname'],data['lname'],data['address'],data['phone'],data['dob'],data['gender'],fn,data['qualification'])
                    setData(sql,vals)
                    sql = "select ifnull(max(fs_id),0)+1 from faculty_subject"
                    res = getData(sql)
                    fs_id = res[0][0]
                    sql = "insert into faculty_subject values(%s,%s,%s)"
                    vals = (fs_id,log_id,data['subject'])
                    setData(sql,vals)
                    file.save('static/uploads/'+secure_filename(fn))
                    return redirect(url_for('viewFaculty'))
                else:
                    flash('Phone Number Already Exists')
            else:
                flash('Email Already Exists')
        else:
            flash('Passwords Not Matching')
    sql = "select * from courses"
    res = getData(sql)
    sql = "select * from subjects where cid=%s" % res[0][0]
    subjects = getData(sql)
    return render_template('admin/addFaculty.html',courses=res,data=data,subjects=subjects)

@app.route('/admin/viewFaculty')
def viewFaculty():
    sql = "select u.uid,concat(fname,' ',lname) as name,phone from user_details u join login l on l.log_id=u.uid join faculty_subject f on f.uid=u.uid join subjects s on s.sid=f.sid where l.role='faculty'"
    res = getData(sql)
    return render_template('admin/viewUsers.html',users=res)

@app.route('/admin/recommend/<eid>/',methods=['POST','GET'])
def courseRecommend(eid):
    if request.method == 'POST':
        data = request.form
        sql = "select ifnull(max(rc_id),0)+1 from recommendations"
        rid = getData(sql)[0][0]
        sql = "insert into recommendations values(%s,%s,%s,%s,%s)"
        vals = (rid,eid,data['from'],data['to'],data['subject'])
        setData(sql,vals)
    # sql = "select rc_id,mark_from,mark_to,c.name from recommendations r join courses c on c.cid=r.cid where r.eid=%s" % eid
    # res = getData(sql)
    sql = "select * from subjects"
    cr = getData(sql)
    sql = "select rc_id,mark_from,mark_to,s.name from recommendations r join subjects s on s.sid=r.sid where r.eid=%s" % eid
    res = getData(sql)
    return render_template('admin/recommend.html',subjects=cr,data=res,eid=eid)

@app.route('/admin/recommendations/get/',methods=['POST'])
def getAdminRecommended():
    dtype = request.form['dtype']
    eid = request.form['eid']
    sql = ''
    if dtype == 'course':
        sql = "select rc_id,mark_from,mark_to,c.name from recommendations r join courses c on c.cid=r.cid where r.eid=%s" % eid
    elif dtype == 'job':
        sql = "select jr_id,mark_from,mark_to,title,description from job_recommendations where eid=%s" % eid
    res = getData(sql)
    return json.dumps(res)

@app.route('/admin/recommend/delete/<rc_id>/<eid>/')
def deleteRec(rc_id,eid):
    sql = "delete from recommendations where rc_id=%s" % rc_id
    setData(sql)
    return redirect(url_for('courseRecommend',eid=eid))

@app.route('/admin/recommendJob/delete/<rc_id>/<eid>/')
def deleteRecJob(rc_id,eid):
    sql = "delete from job_recommendations where jr_id=%s" % rc_id
    setData(sql)
    return redirect(url_for('courseRecommend',eid=eid))

@app.route('/faculty/home/')
def facultyHome():
    sql = "select eid,title,date,time,duration,s.name from exams e join courses c on c.cid=e.cid join subjects s on s.cid=c.cid join faculty_subject fs on s.sid where fs.uid=%s order by e.date desc" % session['uid']
    res = getData(sql)
    return render_template('faculty/home.html',exams=res)

@app.route('/faculty/subjects/')
def facultySubject():
    sql = "select s.sid,s.name from subjects s join faculty_subject fs on fs.sid=s.sid where fs.uid=%s" % session['uid']
    res = getData(sql)
    return render_template('faculty/viewSubjects.html',subjects=res)

@app.route('/faculty/viewQuestions/<sid>/',methods=['POST','GET'])
def viewQuestion(sid):
    if 'uid' not in session or 'role' not in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        data = request.form
        sql = "select ifnull(max(qid),0)+1 from questions"
        res = getData(sql)
        qid = res[0][0]
        sql = "insert into questions values(%s,%s,%s,%s,%s,%s,%s,%s)"
        vals = (qid,sid,data['question'],data['opt1'],data['opt2'],data['opt3'],data['opt4'],data['answer'])
        setData(sql,vals)
    sql = "select * from questions where sid=%s" % sid
    res = getData(sql)
    return render_template('faculty/viewQuestions.html',questions=res)

@app.route('/faculty/getIndQuestion/',methods=['POST'])
def getIndQuestion():
    sql = "select question,opt1,opt2,opt3,opt4,answer from questions where qid=%s" % request.form['qid']
    res = getData(sql)
    return json.dumps(res[0])

@app.route('/faculty/updateQuestion/',methods=['POST'])
def updateQuestion():
    data = request.form
    sql = "update questions set question=%s,opt1=%s,opt2=%s,opt3=%s,opt4=%s,answer=%s where qid=%s"
    vals = (data['question'],data['opt1'],data['opt2'],data['opt3'],data['opt4'],data['ans'],data['qid'])
    setData(sql,vals)
    return '1'

@app.route('/faculty/appliedList/')
def appliedList():
    sql = "select 1,date,concat(u.fname,' ',u.lname),c.name from apply_course ac join user_details u on u.uid=ac.uid join recommendations r on r.rc_id=ac.rc_id join subjects c on c.sid=r.sid where ac.faculty=%s" % session['uid']
    res = getData(sql)
    return render_template('faculty/appliedList.html',data=res)

@app.route('/user/home')
def userHome():
    # sql = "select eid,title,date,time,duration,s.name from exams e join subjects s on s.sid=e.sid order by e.date desc"
    sql = "select * from courses"
    res = getData(sql)
    return render_template('user/home.html',courses=res)

@app.route('/user/exam/attend/<eid>/',methods=['GET','POST'])
def attendExam(eid):
    sql = "select cid,duration,title from exams where eid=%s" % eid
    res = getData(sql)
    cid = res[0][0]
    dur = res[0][1]
    exam = res[0][2]
    sql = "select qid,question,opt1,opt2,opt3,opt4 from questions q join subjects s on s.sid=q.sid join courses c on c.cid=s.cid where c.cid=%s order by rand() limit 20" % cid
    res = getData(sql)
    return render_template('user/attendExam.html',questions=res,duration=dur,exam=exam)

@app.route('/user/exams/<cid>/')
def userGetExams(cid):
    sql = "select eid,title,date,time,duration from exams e join courses c on c.cid=e.cid where c.cid=%s order by e.date desc" % cid
    res = getData(sql)
    return render_template('user/exams.html',exams=res)

@app.route('/user/recommends/')
def userRecommends():
    sql = "select u_type from user_details where uid=%s" % session['uid']
    utype = getData(sql)[0][0]
    if utype == 1:
        sql = "select rc.sid,s.name from recommendations rc join results r on r.eid=rc.eid join subjects s on s.sid=rc.sid where r.uid=%s and r.mark between rc.mark_from and rc.mark_to" % session['uid']
    res = getData(sql)
    return render_template('user/recommends.html',data=res,utype=utype)

@app.route('/user/feedback',methods=['GET','POST'])
def userFeedback():
    if request.method == 'POST':
        data = request.form
        sql = "select ifnull(max(fid),0)+1 from feedbacks"
        fid = getData(sql)[0][0]
        sql = "insert into feedbacks values(%s,%s,%s,current_date,NULL)"
        vals = (fid,session['uid'],data['message'])
        setData(sql,vals)
    sql = "select * from feedbacks where uid=%s" % session['uid']
    res = getData(sql)
    return render_template('user/feedback.html',data=res)

@app.route('/user/applyCourse/<rc_id>/',methods=['POST','GET'])
def applyCourse(rc_id):
    if request.method == 'POST':
        data = request.form
        sql = "select ifnull(max(ac_id),0)+1 from apply_course"
        ac_id = getData(sql)[0][0]
        sql = "insert into apply_course values(%s,%s,%s,%s,current_date)"
        vals = (ac_id,rc_id,session['uid'],data['faculty'])
        setData(sql,vals)
        return redirect(url_for('userAppliedCourse'))
    sql = "select count(*) from apply_course where uid=%s and rc_id=%s"
    vals = (session['uid'],rc_id)
    status = 0
    if getData(sql,vals)[0][0] == 0:
        status = 1
    sql = "select uid,concat(fname,' ',lname) from user_details where u_type=0"
    res = getData(sql)
    return render_template('user/applyCourse.html',data=res,status=status)

@app.route('/user/courses/applied')
def userAppliedCourse():
    sql = "select ac_id,date,s.name,concat(u.fname,' ',u.lname) from apply_course ac join recommendations r on r.rc_id=ac.rc_id join user_details u on u.uid=ac.faculty join subjects s on s.sid=r.sid where ac.uid=%s" % session['uid']
    res = getData(sql)
    return render_template('user/applied.html',data=res)

@app.route('/user/applies/delete/<ac_id>/')
def deleteApplied(ac_id):
    sql = "delete from apply_course where ac_id=%s" % ac_id
    setData(sql)
    return redirect(url_for('userAppliedCourse'))

@app.route('/user/exam/validate/',methods=['POST'])
def validateExam():
    data = request.form
    score = 0
    a = ''
    for q in json.loads(data['qlist']):
        sql = "select answer from questions where qid=%s" % q
        ans = getData(sql)[0][0]
        if str(ans) == str(data['qst%s' % q]): score += 1
    sql = "select ifnull(max(rid),0)+1 from results"
    rid = getData(sql)[0][0]
    sql = "insert into results values(%s,%s,%s,%s)"
    vals= (rid,session['uid'],data['eid'],score)
    setData(sql,vals)
    return '1'

@app.route('/user/results/')
def userResult():
    sql = "select rid,e.title,e.date,e.time,e.duration,r.mark from results r join exams e on e.eid=r.eid where r.uid=%s" % session['uid']
    res = getData(sql)
    return render_template('user/results.html',results=res)

@app.route('/user/courses/<type>/')
def userCourses(type):
    sql = ''
    if type == 'all':
        sql = "select * from courses"
    elif type == 'recommended':
        sql = "select rc.cid,c.name from recommendations rc join results r on r.eid=rc.eid join courses c on c.cid=rc.cid where r.uid=%s and r.mark between rc.mark_from and rc.mark_to" % session['uid']
    res = getData(sql)
    return render_template('user/courses.html',courses=res)

@app.route('/logout')
def logout():
    del session['uid']
    del session['role']
    return redirect(url_for('home'))

app.run(debug=True)