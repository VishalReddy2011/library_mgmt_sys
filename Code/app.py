from flask import render_template
from flask import request,redirect,url_for
from dbs import *
from datetime import datetime,timedelta,date,time
import matplotlib.pyplot as plt

@app.route("/",methods=["GET","POST"])
def login():
    if request.method=="GET":
        return render_template("index.html")
    if request.method=="POST":
        username=request.form["username"]
        password=request.form["password"]
        action=request.form["action"]
        admin_id=Admin.query.first().id
        users=User.query.all()
        if action=="Login":
            users = User.query.all()
            for user in users:
                if user.username==username:
                    if user.password==password:
                        if user.id==admin_id:
                            return redirect(url_for("admin_dash"))
                        else:
                            return redirect(url_for("user_dash",u_name=username))                
                    else:
                        return render_template("index.html",Error="Incorrect Password")
            return render_template("index.html",Error="Username not found")
        else:
            for user in users:
                if user.username==username:
                    return render_template("index.html",Error="Username already exists")
            if len(password)<6:
                return render_template("index.html",Error="Password length must be at least 6")
            new_user=User(username=username,password=password)
            db.session.add(new_user)
            db.session.commit()
            return render_template("index.html",Success="Succesfully registed. Please login")

@app.route("/admin_dash",methods=["GET","POST"])
def admin_dash():
    if request.method=="GET":
        read=Request.query.filter_by(status="read").all()
        read_months=[r.issue_date.strftime('%Y/%m') for r in read]
        unique_months=sorted(list(set(read_months)))
        no_months=[read_months.count(u) for u in unique_months]
        plt.switch_backend('agg')
        plt.bar(unique_months,no_months)
        plt.xlabel("Month")
        plt.ylabel("Number of books Read")
        plt.title("Reading Activity by Month")
        plt.savefig("static/amonth.jpg")
        plt.clf()
        
        read_sections=[r.book.section.name for r in read]
        unique_sections=sorted(list(set(read_sections)))
        no_sections=[read_sections.count(u) for u in unique_sections]
        plt.pie(no_sections,labels=unique_sections,autopct=lambda p:'{:.2f}%'.format(p))
        plt.title("Section Distribution of Issued Books")
        plt.savefig("static/asection.jpg")
        plt.clf()
        
        
        admin_id=Admin.query.first().id
        username=User.query.filter_by(id=admin_id).first().username
        return render_template("admin_dash.html",username=username)
    
    
    
    if request.method=="POST":
        action = request.form["action"]
        if action=="sections":
            return redirect(url_for('admin_sections',sections=Section.query.all()))
        else: 
            return redirect(url_for('admin_requests'))
        
@app.route("/admin_dash/sections",methods=["GET","POST"])
def admin_sections():
    if request.method=="POST":
        section_name=request.form["section_name"]
        section_desc=request.form["section_desc"]
        new_section=Section(name=section_name,date_created=datetime.now(),description=section_desc)
        db.session.add(new_section)
        db.session.commit()
    sections=Section.query.all()
    return render_template("admin_sections.html",sections=sections)

@app.route("/admin_dash/search",methods=["GET","POST"])
def search():
    all_books=Book.query.all()
    latest_books=[book for book in all_books if (datetime.now()-book.date_added).days<7]
    if request.method=="GET":
        return render_template('search.html',lbooks=latest_books)
    else:
        section=request.form.get("section")
        book_title=request.form.get("book_title")
        author_name=request.form.get("author_name")
        st=False
        bt=False
        at=False
        if section:
            st=True
            sections=Section.query.filter(Section.name.like("%{}%".format(section))).all()
            return render_template('search.html',st=st,bt=bt,at=at,sections=sections,lbooks=latest_books)
        elif book_title:
            bt=True
            books=Book.query.filter(Book.name.like("%{}%".format(book_title))).all()
            return render_template('search.html',st=st,bt=bt,at=at,books=books,lbooks=latest_books)
        else:
            at=True
            author_id=Author.query.filter(Author.name.like("%{}%".format(author_name))).first().id
            books=Book.query.filter_by(author_id=author_id).all()
            return render_template('search.html',st=st,bt=bt,at=at,books=books,lbooks=latest_books)
    

@app.context_processor
def utility_processor():
    def available_copies(book):
        return str(book.total_copies-len(Request.query.filter_by(book_id=book.id).filter_by(status="active").all()))
    return dict(available_copies=available_copies)

@app.context_processor
def utility_processor():
    def current_books(username):
        user_id=User.query.filter_by(username=username).first().id
        book_list=Request.query.filter_by(user_id=user_id).filter_by(status="active").all()
        return [[Book.query.filter_by(id=i.book_id).first(),i.issue_date+timedelta(days=7)] for i in book_list]
    return dict(current_books=current_books)

@app.context_processor
def utility_processor():
    def pending_books(username):
        user_id=User.query.filter_by(username=username).first().id
        book_list=Request.query.filter_by(user_id=user_id).filter_by(status="pending").all()
        return [Book.query.filter_by(id=i.book_id).first() for i in book_list]
    return dict(pending_books=pending_books)

@app.context_processor
def utility_processor():
    def past_books(username):
        user_id=User.query.filter_by(username=username).first().id
        book_list=Request.query.filter_by(user_id=user_id).filter((Request.status=="read")|(Request.status=="expired")).all()
        return [[Book.query.filter_by(id=i.book_id).first(),i.status] for i in book_list]
    return dict(past_books=past_books)

@app.route("/admin_dash/sections/<s_name>",methods=["GET","POST"])
def section_page(s_name,msg="",msg2=""):
    cur_section=Section.query.filter_by(name=s_name).first()
    section_books=Book.query.filter_by(section_id=cur_section.id)
    if request.method=="GET":
        return render_template("section_page.html",section=cur_section,books=section_books,msg=msg,msg2=msg2)
    else:
        action = request.form["action"]
        if action=="Edit":
            new_name=request.form["section_name"]
            new_desc=request.form["section_desc"]
            action=request.form["action"]
            cur_section.name=new_name
            cur_section.description=new_desc
            db.session.commit()
            msg="Edit Successful"
            return redirect(url_for("section_page",s_name=s_name,msg=msg,msg2=msg2))
        elif action=="Delete Section":
            for book in cur_section.books:
                db.session.delete(book)
            db.session.delete(cur_section)
            db.session.commit()
            return redirect(url_for("section_page",s_name=s_name))
        elif action=="Create Book":
            title=request.form["title"]
            author_name=request.form["author"]
            copies=request.form["tot_copies"]
            content=request.form["content"]
            
            author=Author.query.filter_by(name=author_name).first()
            
            if not(author):
                author=Author(name=author_name)
                db.session.add(author)
            new_book=Book(name=title,total_copies=copies,content=content,date_added=datetime.now(),section_id=cur_section.id,author=author)
            author.books.append(new_book)
            cur_section.books.append(new_book)
            db.session.add(new_book)                    
            db.session.commit()
            msg2="New Book Added"
            return redirect(url_for("section_page",msg2=msg2,section=cur_section,s_name=s_name))
            

@app.route("/admin_dash/sections/<s_name>/<int:b_id>",methods=["GET","POST"])
def book_page(s_name,b_id,msg=""):
    cur_book=Book.query.filter_by(id=b_id).first()
    if request.method=="POST":
        action = request.form["action"]
        if action=="Edit book":
            new_title=request.form["title"]
            new_author=request.form["author"]
            new_copies=request.form["tot_copies"]
            new_section=request.form["section"]
            new_content=request.form["content"]

            author=Author.query.filter_by(name=new_author).first()
            old_author=cur_book.author
            
            if not(author):
                author=Author(name=new_author)
                db.session.add(author)
                
            if old_author.id!=author.id:
                old_author.books.remove(cur_book)
            
            cur_book.name=new_title
            cur_book.total_copies=new_copies
            cur_book.content=new_content
            cur_book.author_id=author.id
            cur_book.section_id=Section.query.filter_by(name=new_section).first().id
            if old_author.name!=author.name:
                author.books.append(cur_book)
            db.session.commit()
            msg="Edit Successful"
        elif action=="Delete Book":        
            db.session.delete(cur_book)
            db.session.commit()
            return redirect(url_for("section_page",s_name=s_name,msg2="Book deleted successfully"))
    return render_template("book_page.html",book=cur_book,msg=msg)

@app.route("/admin_dash/requests",methods=["GET","POST"])
def admin_requests():
    requests=Request.query.all()
    if request.method=="GET":
        return render_template('admin_requests.html',requests=requests)
    else:
        name=list(request.form.keys())[0]
        action=request.form[name]
        request_id=int(list(request.form.keys())[0])
        if action=="Grant":
            cur_request=Request.query.filter_by(id=request_id).first()
            cur_request.status="active"
            cur_request.issue_date=datetime.now()
        elif action=="Revoke":
            Request.query.filter_by(id=request_id).first().status="rejected"
        db.session.commit()
        return render_template('admin_requests.html',requests=requests)
        


@app.route("/<u_name>/user_dash", methods=["GET", "POST"])
def user_dash(u_name):
    if request.method == "GET":
        user_id=User.query.filter_by(username=u_name).first().id
        requests=Request.query.filter_by(user_id=user_id).filter_by(status="active").all()
        for r in requests:
            if (datetime.now()-r.issue_date).days>6:
                r.status="expired"
                db.session.commit()
        return render_template("user_dash.html",username=u_name)
    
             
    
@app.route("/<u_name>/browse",methods=["GET","POST"])
def browse(u_name):
    if request.method=="GET":
        return render_template("user_sections.html",username=u_name,sections=Section.query.all())
    
@app.route("/<u_name>/browse/<s_name>",methods=["GET","POST"])
def user_section_page(u_name,s_name):
    section=Section.query.filter_by(name=s_name).first()
    if request.method=="GET":
        return render_template("user_section_page.html",section=section,username=u_name)

@app.route("/<u_name>/browse/<s_name>/<b_id>",methods=["GET","POST"])
def user_book_page(u_name,s_name,b_id):
    book=Book.query.filter_by(id=b_id).first()
    user_id=User.query.filter_by(username=u_name).first().id
    feedback=Feedback.query.filter_by(book_id=b_id).all()
    latest_request=Request.query.filter_by(user_id=user_id).filter_by(book_id=b_id).order_by(db.text('issue_date desc')).limit(1).first()
    issue=""
    status="You have not read this book"
    if latest_request and latest_request.issue_date!=None:
        time_since=(datetime.now()-latest_request.issue_date).days
    if not(latest_request) or (latest_request and latest_request.status in ["rejected","expired","read"]):
        issue="show_request"
    if latest_request:
        if latest_request.status=="read":
            status="You have finished reading this book"
        if latest_request.status=="pending":
            status="Your request is pending"
        if latest_request.status=="active":
            status="Your request has been accepted"
            issue="show_content"     
    if request.method=="GET":
        return render_template("user_book_page.html",username=u_name,s_name=s_name,book=book,issue=issue,status=status,feedback=feedback)
    else:
        if request.form["action"]=="Request":
            if not(latest_request) or (latest_request and latest_request.status in ["expired","read","rejected"]):
                if len(Request.query.filter_by(user_id=user_id).filter_by(status="active").all())==5:
                    return render_template("user_book_page.html",username=u_name,s_name=s_name,book=book,status=status,feedback=feedback,msg="Maximum issue limit reached")
                new_request=Request(user_id=user_id,book_id=b_id,status="pending")
                status="Your request is pending"
                db.session.add(new_request)
                db.session.commit()
            return render_template("user_book_page.html",username=u_name,s_name=s_name,book=book,status=status,feedback=feedback)
        elif request.form["action"]=="Return":
            latest_request.status="read"
            db.session.commit()
            return redirect(url_for("user_dash",u_name=u_name))
        else:
            feed=request.form["feedback"]
            rating=request.form["rating"]
            new_feed=Feedback(user_id=user_id,book_id=b_id,date=datetime.now(),text=feed,rating=rating)
            db.session.add(new_feed)
            db.session.commit()
            return render_template("user_book_page.html",username=u_name,s_name=s_name,book=book,issue=issue,status=status,feedback=feedback)
            
@app.route("/<u_name>/statistics",methods=["GET","POST"])
def user_statistics(u_name):
    if request.method=="GET":
        user_id=User.query.filter_by(username=u_name).first().id
        read=Request.query.filter_by(status="read").filter_by(user_id=user_id).all()
        read_months=[r.issue_date.strftime('%Y/%m') for r in read]
        unique_months=sorted(list(set(read_months)))
        no_months=[read_months.count(u) for u in unique_months]
        plt.switch_backend('agg')
        plt.bar(unique_months,no_months)
        plt.xlabel("Month")
        plt.ylabel("Number of books Read")
        plt.title("Reading Activity by Month")
        plt.savefig("static/umonth.jpg")
        plt.clf()
        
        read_sections=[r.book.section.name for r in read]
        unique_sections=sorted(list(set(read_sections)))
        no_sections=[read_sections.count(u) for u in unique_sections]
        plt.pie(no_sections,labels=unique_sections,autopct=lambda p:'{:.2f}%'.format(p))
        plt.title("Section Distribution of Issued Books")
        plt.savefig("static/usection.jpg")
        plt.clf()
        return render_template('user_statistics.html',username=u_name)
    
@app.route("/<u_name>/search",methods=["GET","POST"])
def user_search(u_name):
    all_books=Book.query.all()
    latest_books=[book for book in all_books if (datetime.now()-book.date_added).days<7]
    if request.method=="GET":
        return render_template('user_search.html',lbooks=latest_books,username=u_name)
    else:
        section=request.form.get("section")
        book_title=request.form.get("book_title")
        author_name=request.form.get("author_name")
        st=False
        bt=False
        at=False
        if section:
            st=True
            sections=Section.query.filter(Section.name.like("%{}%".format(section))).all()
            return render_template('user_search.html',username=u_name,st=st,bt=bt,at=at,sections=sections,lbooks=latest_books)
        elif book_title:
            bt=True
            books=Book.query.filter(Book.name.like("%{}%".format(book_title))).all()
            return render_template('user_search.html',username=u_name,st=st,bt=bt,at=at,books=books,lbooks=latest_books)
        else:
            at=True
            author_id=Author.query.filter(Author.name.like("%{}%".format(author_name))).first().id
            books=Book.query.filter_by(author_id=author_id).all()
            return render_template('user_search.html',username=u_name,st=st,bt=bt,at=at,books=books,lbooks=latest_books)
if __name__=="__main__":
    db.create_all()
    if not(Admin.query.all()):
        admin_user=User(username="VishalReddy2011",password="happy123")
        db.session.add(admin_user)
        db.session.commit()

        admin=Admin(id=1)
        db.session.add(admin)
        db.session.commit() 
    app.run(debug=True)
    