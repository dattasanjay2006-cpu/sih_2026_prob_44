from groq import Groq
from flask import Flask,render_template,redirect,url_for,jsonify,request,session
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import json
import os


load_dotenv()


app=Flask(__name__)
app.secret_key=os.getenv("FLASK_SECRET_KEY","aic_portal_secret_key")


client=Groq(api_key=os.getenv("GROQ_API_KEY"))


UPLOAD_FOLDER="static/uploads"
os.makedirs(UPLOAD_FOLDER,exist_ok=True)


class TreeNode:

    def __init__(self,name,node_type="Course",payload="None"):
        self.name=name
        self.node_type=node_type
        self.children=[]
        self.payload=payload

    def add_child(self,child_node):
        self.children.append(child_node)

    def to_dict(self):

        formatted_children=[]

        for child in self.children:

            if isinstance(child,TreeNode):
                formatted_children.append(child.to_dict())

            else:
                formatted_children.append({
                    "name":str(child),
                    "node_type":"Topic",
                    "children":[]
                })

        return {
            "name":self.name,
            "node_type":self.node_type,
            "payload":self.payload,
            "children":formatted_children
        }


# Level 1: Major Academic Courses

root=TreeNode("Academic Major Course","Root")

sub1=TreeNode("Engineering & Technology")
sub2=TreeNode("Management & Bussiness")
sub3=TreeNode("Pure & Applied Sciences")
sub4=TreeNode("Humanities & Arts")
sub5=TreeNode("Medical & Healthcare")


root.add_child(sub1)
root.add_child(sub2)
root.add_child(sub3)
root.add_child(sub4)
root.add_child(sub5)


# Engineering Departments

sub1.add_child("Aerospace Engineering")
sub1.add_child("Biotechnology Engineering")
sub1.add_child("Chemical Engineering")
sub1.add_child("Civil Engineering")
sub1.add_child("Computer Science and Engineering")
sub1.add_child("Electrical Engineering")
sub1.add_child("Electronics and Communication Engineering")
sub1.add_child("Mathematics and Computing")
sub1.add_child("Mechanical Engineering")
sub1.add_child("Metallurgical and Materials Engineering")
sub1.add_child("Other Engineering Disciplines")


# Commerce/Management Courses

sub2.add_child("Accounting and Finance")
sub2.add_child("Business Analytics")
sub2.add_child("Financial Management")
sub2.add_child("Healthcare Management")
sub2.add_child("Human Resource Management")
sub2.add_child("Information Technology Management")
sub2.add_child("International Business")
sub2.add_child("Marketing Management")
sub2.add_child("Operations Management")
sub2.add_child("Supply Chain Management")
sub2.add_child("Other Management & Commerce Fields")


# Pure and Applied Science Courses

sub3.add_child("Mathematics")
sub3.add_child("Physics")
sub3.add_child("Botany")
sub3.add_child("Zoology")
sub3.add_child("Chemistry")
sub3.add_child("Geology")
sub3.add_child("Statistics")
sub3.add_child("Microbiology")
sub3.add_child("Applied Mathematics")
sub3.add_child("Applied Physics")
sub3.add_child("Applied Chemistry")
sub3.add_child("Environmental Science")
sub3.add_child("Other Natural & Applied Sciences")


# Humanities and Arts Subjects

sub4.add_child("Anthropology")
sub4.add_child("Economics")
sub4.add_child("English")
sub4.add_child("Fine Arts")
sub4.add_child("Geography")
sub4.add_child("History")
sub4.add_child("Indian Languages")
sub4.add_child("Linguistics")
sub4.add_child("Performing Arts")
sub4.add_child("Philosophy")
sub4.add_child("Political Science")
sub4.add_child("Psychology")
sub4.add_child("Sociology")
sub4.add_child("Other Humanities & Arts Disciplines")


# Medical & Healthcare Subjects

sub5.add_child("Ayurveda")
sub5.add_child("Homeopathy & Complementary medicines")
sub5.add_child("Clinical Medicine")
sub5.add_child("Dental Sciences")
sub5.add_child("Surgical Sciences")
sub5.add_child("Women & Child Health")
sub5.add_child("Nursing")
sub5.add_child("Pathology & Diagnostics")
sub5.add_child("Pharmaceutical Sciences")
sub5.add_child("Physical Therapy & Rehabilitation")
sub5.add_child("Psychiatry & Behavioral Health")
sub5.add_child("Public Health & Community Medicine")
sub5.add_child("Other Medical & Healthcare Disciplines")


def system_prompt1(subject_node,subdomain_list,year):

    return f"""
You are an expert AI analyst and skill assessment engine.
Generate ONLY ONE subdomain under {subject_node.name} which is taught
in standard academic courses under {subject_node.name} and used in
modern industry practices.

DO NOT repeat subdomain which is already present in {subdomain_list}.

Target audience: Year {year} college student.

For instance if {subject_node.name} is Computer Science & Engineering,
the subdomain may be OOPS, Web development, AI/ML, Data Structures and more.

If {subject_node.name} is Mechanical Engineering,
subdomains may include CAD/CAM, FEA, CFD, Automobile etc.

Year Guidance:
- Year 1/2: Core foundations.
- Year 3/4: Applied/Advanced topics.

STRICT REQUIREMENT:
Output must be a valid JSON object.

{{
    "subdomain": "Name of Subdomain"
}}
"""


def fetch_client1(subject_node,subdomain_list,year):

    user_prompt=f"Generate one subdomain for {subject_node.name}."

    response=client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role":"system",
                "content":system_prompt1(subject_node,subdomain_list,year)
            },
            {
                "role":"user",
                "content":user_prompt
            }
        ],
        response_format={"type":"json_object"},
        temperature=0.3,
        max_tokens=1000
    )

    return response.choices[0].message.content


def system_prompt2(current_depth,subject_node,subdomain_list,tool,year):

    topic=subdomain_list[current_depth]

    return f"""
You are an expert AI skill assessment engine for
'Portal for Academia-Industry collaboration'.

Generate a question based on {topic} to assess the skills
of the user.

Target audience: Year {year} college student.

Instructions:

1. If the user answered "No Idea" or "skip", do not ask deeper
questions on that tool.

2. There will be two types of questions:
a. SKILL_PICKER
b. CONCEPT

3. Difficulty should depend on the year:
- Year 1: Extremely basic
- Year 2: Basic to intermediate
- Year 3: Intern level
- Year 4+: Production or Industry level

JSON Schema:

{{
    "question_type": "CONCEPT",
    "question": "The question string",
    "options": [
        "Option A",
        "Option B",
        "Option C",
        "Option D",
        "No idea"
    ],
    "correct_option_index": 0,
    "difficulty": "{year} Year"
}}
"""


def fetch_client2(current_depth,subject_node,subdomain_list,tool,year):

    user_prompt="Generate one question for assessment."

    response=client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role":"system",
                "content":system_prompt2(
                    current_depth,
                    subject_node,
                    subdomain_list,
                    tool,
                    year
                )
            },
            {
                "role":"user",
                "content":user_prompt
            }
        ],
        response_format={"type":"json_object"},
        temperature=0.3,
        max_tokens=2000
    )

    return response.choices[0].message.content


# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

@app.route("/")
def home():

    return render_template("index.html")


# --------------------------------------------------
# ASSESS PAGE
# --------------------------------------------------

@app.route("/assess")
def assess():

    return render_template("assess.html")


# --------------------------------------------------
# REGISTER / START ASSESSMENT / SAVE PROFILE
# --------------------------------------------------

@app.route("/register",methods=["POST"])
def register():

    data=request.form

    # --------------------------------------------------
    # PROFILE FORM
    # --------------------------------------------------

    if "name" in data or "project1_name" in data or "career_role" in data:

        return save_profile_data(data)


    # --------------------------------------------------
    # FRIEND'S ASSESSMENT FORM
    # --------------------------------------------------

    username=data.get("username")
    year=data.get("class")
    domain=data.get("domain")
    subject=data.get("stream")
    tool=data.get("section")

    current_depth=0

    subject_node=TreeNode(
        name=subject,
        node_type="Specialization"
    )

    subdomain_list=[]

    raw_subdomain=fetch_client1(
        subject_node,
        subdomain_list,
        year
    )

    subdomain_data=json.loads(raw_subdomain)

    subdomain=subdomain_data.get(
        "subdomain",
        raw_subdomain
    )

    subdomain_list.append(subdomain)

    subject_node.add_child(
        TreeNode(
            name=subdomain,
            node_type="Subdomain"
        )
    )

    question_raw=fetch_client2(
        current_depth=current_depth,
        subject_node=subject_node,
        subdomain_list=subdomain_list,
        tool=tool,
        year=year
    )

    question_data=json.loads(question_raw)

    session["assessment"]={
        "username":username,
        "year":year,
        "domain":domain,
        "subject":subject,
        "tool":tool,
        "current_depth":current_depth,
        "subdomain_list":subdomain_list
    }

    return render_template(
        "assess.html",
        academic_tree=subject_node.to_dict(),
        target_subdomain=subdomain,
        subdomain_list=subdomain_list,
        assessment_question=question_data,
        username=username,
        year=year,
        subject=subject,
        current_depth=current_depth
    )


# --------------------------------------------------
# NEXT ASSESSMENT QUESTION
# --------------------------------------------------

@app.route("/next_question",methods=["POST"])
def next_question():

    data=request.form

    current_depth=int(
        data.get("current_depth",0)
    )+1

    max_depth=12

    raw_subdomains=data.get(
        "subdomain_list",
        "[]"
    )

    subdomain_list=json.loads(
        raw_subdomains
    )

    username=data.get("username")
    year=data.get("class")
    domain=data.get("domain")
    subject=data.get("stream")
    tool=data.get("section")

    if current_depth>=max_depth:

        message=f"""
        <h1>Assessment Complete!</h1>
        <p>Great job, {username}!</p>
        """

        return render_template(
            "assess.html",
            message=message
        )

    subject_node=TreeNode(
        name=subject,
        node_type="Specialization"
    )

    raw_subdomain=fetch_client1(
        subject_node,
        subdomain_list,
        year
    )

    subdomain_data=json.loads(
        raw_subdomain
    )

    subdomain=subdomain_data.get(
        "subdomain",
        raw_subdomain
    )

    subdomain_list.append(subdomain)

    subject_node.add_child(
        TreeNode(
            name=subdomain,
            node_type="Subdomain"
        )
    )

    question_raw=fetch_client2(
        current_depth=current_depth,
        subject_node=subject_node,
        subdomain_list=subdomain_list,
        tool=tool,
        year=year
    )

    question_data=json.loads(
        question_raw
    )

    return render_template(
        "assess.html",
        academic_tree=subject_node.to_dict(),
        target_subdomain=subdomain,
        username=username,
        year=year,
        subject=subject,
        subdomain_list=subdomain_list,
        assessment_question=question_data,
        current_depth=current_depth
    )


# --------------------------------------------------
# SAVE PROFILE DATA
# --------------------------------------------------

def save_profile_data(data):

    profile_photo=request.files.get("profile_photo")

    photo_path="images/profile.jpg"

    if profile_photo and profile_photo.filename:

        filename=secure_filename(
            profile_photo.filename
        )

        photo_path=f"uploads/{filename}"

        profile_photo.save(
            os.path.join(
                UPLOAD_FOLDER,
                filename
            )
        )

    session["profile"]={

        "name":data.get("name",""),
        "email":data.get("email",""),
        "headline":data.get("headline",""),
        "location":data.get("location",""),
        "college":data.get("college",""),
        "course":data.get("course",""),
        "about":data.get("about",""),

        "profile_photo":photo_path,

        "skill1":data.get("skill1",""),
        "skill1_level":data.get("skill1_level",""),

        "skill2":data.get("skill2",""),
        "skill2_level":data.get("skill2_level",""),

        "skill3":data.get("skill3",""),
        "skill3_level":data.get("skill3_level",""),

        "skill4":data.get("skill4",""),
        "skill4_level":data.get("skill4_level",""),

        "skill5":data.get("skill5",""),
        "skill5_level":data.get("skill5_level",""),

        "school":data.get("school",""),
        "school_start":data.get("school_start",""),
        "school_end":data.get("school_end",""),

        "college_start":data.get("college_start",""),
        "college_end":data.get("college_end",""),

        "project1_name":data.get("project1_name",""),
        "project1_description":data.get("project1_description",""),
        "project1_tech":data.get("project1_tech",""),
        "project1_link":data.get("project1_link","#"),

        "project2_name":data.get("project2_name",""),
        "project2_description":data.get("project2_description",""),
        "project2_tech":data.get("project2_tech",""),
        "project2_link":data.get("project2_link","#"),

        "cert1_name":data.get("cert1_name",""),
        "cert1_org":data.get("cert1_org",""),

        "cert2_name":data.get("cert2_name",""),
        "cert2_org":data.get("cert2_org",""),

        "career_role":data.get("career_role",""),
        "preferred_industry":data.get("preferred_industry",""),
        "work_preference":data.get("work_preference",""),
        "career_location":data.get("career_location",""),
        "career_goal":data.get("career_goal","")
    }

    return redirect(
        url_for("profile")
    )


# --------------------------------------------------
# ALSO SUPPORT /save_profile
# --------------------------------------------------

@app.route("/save_profile",methods=["POST"])
def save_profile():

    return save_profile_data(request.form)


# --------------------------------------------------
# PROFILE PAGE
# --------------------------------------------------

@app.route("/profile")
def profile():

    profile_data=session.get("profile",{})

    return render_template(
        "profile.html",
        **profile_data
    )
# --------------------------------------------------
# RUN APPLICATION
# --------------------------------------------------

if __name__=="__main__":

    app.run(
        debug=True
    )