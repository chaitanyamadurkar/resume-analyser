import streamlit as st
import nltk
import spacy
nltk.download('stopwords')
spacy.load('en_core_web_sm')
import pickle
from pathlib import Path
import pandas as pd
import base64, random
import time, datetime
from pyresparser import ResumeParser
from pdfminer3.layout import LAParams, LTTextBox
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import TextConverter
import io, random
from streamlit_tags import st_tags
from PIL import Image
import pymysql
from Courses import ds_course, web_course, android_course, ios_course, uiux_course, devops_course, cloud_course, backend_course, cybersecurity_course, ai_engineering_course, resume_videos, interview_videos
import pafy
import plotly.express as px
import youtube_dl
import streamlit_authenticator as stauth



def get_table_download_link(df, filename, text):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    # href = f'<a href="data:file/csv;base64,{b64}">Download Report</a>'
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href


def pdf_reader(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh,
                                      caching=True,
                                      check_extractable=True):
            page_interpreter.process_page(page)
            print(page)
        text = fake_file_handle.getvalue()

    # close open handles
    converter.close()
    fake_file_handle.close()
    return text


def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    # pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf">'
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


def course_recommender(course_list):
    st.subheader("**Courses & Certificates🎓 Recommendations**")
    c = 0
    rec_course = []
    no_of_reco = st.slider('Choose Number of Course Recommendations:', 1, 10, 4)
    random.shuffle(course_list)
    for c_name, c_link in course_list:
        c += 1
        st.markdown(f"({c}) [{c_name}]({c_link})")
        rec_course.append(c_name)
        if c == no_of_reco:
            break
    return rec_course


connection = pymysql.connect(host='localhost', user='root', password='')
cursor = connection.cursor()

def insert_data(name, email, res_score, timestamp, no_of_pages, reco_field, cand_level, skills, recommended_skills, courses):
    DB_table_name = 'user_data'
     # First check if a record with the same name and email already exists
    check_duplicate_sql = f"SELECT ID FROM {DB_table_name} WHERE Name = %s AND Email_ID = %s"
    cursor.execute(check_duplicate_sql, (name, email))
    duplicate_records = cursor.fetchall()
    
    # If duplicates exist, delete the older entries
    if duplicate_records:
        for record in duplicate_records:
            delete_sql = f"DELETE FROM {DB_table_name} WHERE ID = %s"
            cursor.execute(delete_sql, (record[0],))
        
        # Log the cleanup action
        print(f"Removed {len(duplicate_records)} older entries for {name} ({email})")
    
    insert_sql = "insert into " + DB_table_name + """
    values (0,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    rec_values = (
    name, email, str(res_score), timestamp, str(no_of_pages), reco_field, cand_level, skills, recommended_skills,
    courses)
    cursor.execute(insert_sql, rec_values)
    connection.commit()


st.set_page_config(
    page_title="Next-Gen Resume Analyzer",
    
)


def run():
    st.title("Next Gen Resume Analyser")
    st.sidebar.markdown("# Choose User")
    activities = ["User", "Admin"]
    choice = st.sidebar.selectbox("Choose among the given options:", activities)
    
    

    # Create the DB
    db_sql = """CREATE DATABASE IF NOT EXISTS SRA;"""
    cursor.execute(db_sql)
    connection.select_db("sra")

    # Create table
    DB_table_name = 'user_data'
    table_sql = "CREATE TABLE IF NOT EXISTS " + DB_table_name + """
                    (ID INT NOT NULL AUTO_INCREMENT,
                     Name varchar(100) NOT NULL,
                     Email_ID VARCHAR(50) NOT NULL,
                     resume_score VARCHAR(8) NOT NULL,
                     Timestamp VARCHAR(50) NOT NULL,
                     Page_no VARCHAR(5) NOT NULL,
                     Predicted_Field VARCHAR(25) NOT NULL,
                     User_level VARCHAR(30) NOT NULL,
                     Actual_skills VARCHAR(300) NOT NULL,
                     Recommended_skills VARCHAR(300) NOT NULL,
                     Recommended_courses VARCHAR(600) NOT NULL,
                     PRIMARY KEY (ID));
                    """
    cursor.execute(table_sql)
    if choice == 'User':
       
        pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])
        if pdf_file is not None:
            # with st.spinner('Uploading your Resume....'):
            #     time.sleep(4)
            save_image_path = './Uploaded_Resumes/' + pdf_file.name
            with open(save_image_path, "wb") as f:
                f.write(pdf_file.getbuffer())
            show_pdf(save_image_path)
            resume_data = ResumeParser(save_image_path).get_extracted_data()
            if resume_data:
                ## Get the whole resume data
                resume_text = pdf_reader(save_image_path)

                st.header("**Resume Analysis**")
                st.success("Hello " + resume_data['name'])
                st.subheader("**Your Basic info**")
                try:
                    st.text('Name: ' + resume_data['name'])
                    st.text('Email: ' + resume_data['email'])
                    st.text('Contact: ' + resume_data['mobile_number'])
                    st.text('Resume pages: ' + str(resume_data['no_of_pages']))
                except:
                    pass
                cand_level = ''
                if resume_data['no_of_pages'] == 1:
                    cand_level = "Fresher"
                    st.markdown('''<h4 style='text-align: left; color: #d73b5c;'>You are looking Fresher.</h4>''',
                                unsafe_allow_html=True)
                elif resume_data['no_of_pages'] == 2:
                    cand_level = "Intermediate"
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''',
                                unsafe_allow_html=True)
                elif resume_data['no_of_pages'] >= 3:
                    cand_level = "Experienced"
                    st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at experience level!''',
                                unsafe_allow_html=True)

                st.subheader("**Skills Recommendation💡**")
                ## Skill shows
                keywords = st_tags(label='### Skills that you have',
                                   text='See our skills recommendation',
                                   value=resume_data['skills'], key='1')

                ##  recommendation
                ds_keyword = ['tensorflow', 'keras', 'pytorch', 'machine learning', 'deep Learning', 'flask',
                              'streamlit']
                web_keyword = ['react', 'django', 'node jS', 'react js', 'php', 'laravel', 'magento', 'wordpress',
                               'javascript', 'angular js', 'c#', 'flask']
                android_keyword = ['android', 'android development', 'flutter', 'kotlin', 'xml', 'kivy']
                ios_keyword = ['ios', 'ios development', 'swift', 'cocoa', 'cocoa touch', 'xcode']
                uiux_keyword = ['ux', 'adobe xd', 'figma', 'zeplin', 'balsamiq', 'ui', 'prototyping', 'wireframes',
                                'storyframes', 'adobe photoshop', 'photoshop', 'editing', 'adobe illustrator',
                                'illustrator', 'adobe after effects', 'after effects', 'adobe premier pro',
                                'premier pro', 'adobe indesign', 'indesign', 'wireframe', 'solid', 'grasp',
                                'user research', 'user experience']
                devops_keyword = ['Github', 'Cloud', 'Security', 'Automation', 'Docker', 'System administration', 
                                  'Sql', 'Linux', 'Aws', 'Scripting', 'System', 'Shell']
                cloud_keyword = ['aws', 'azure', 'gcp', 'cloud computing', 'kubernetes', 'terraform', 'cloud architecture',
                                'cloud security', 'serverless', 'microservices', 'docker', 'lambda', 'ec2', 's3', 
                                'cloudformation', 'cloud migration', 'devops', 'iaas', 'paas', 'saas']
                backend_keyword = ['node.js', 'express.js', 'django', 'flask', 'spring boot', 'fastapi', 'rest api',
                                 'graphql', 'mongodb', 'postgresql', 'mysql', 'redis', 'microservices', 'api development',
                                 'backend', 'server', 'database', 'sql', 'nosql', 'authentication', 'jwt', 'oauth',
                                 'nginx', 'apache', 'websockets', 'message queues', 'caching', 'ruby on rails',
                                'laravel', 'asp.net', 'spring', 'hibernate', 'sequelize', 'mongoose']
                cyber_keyword = ['security', 'cybersecurity', 'ethical hacking', 'penetration testing', 'network security',
                                        'encryption', 'firewall', 'siem', 'vulnerability assessment', 'threat analysis',
                                        'incident response', 'security audit', 'compliance', 'secure coding', 'identity management',
                                        'authentication', 'authorization', 'cryptography', 'security operations']
                
                ai_keyword = ['artificial intelligence', 'machine learning', 'deep learning', 'neural networks', 'nlp',
                             'computer vision', 'reinforcement learning', 'data science', 'tensorflow', 'pytorch',
                             'keras', 'scikit-learn', 'opencv', 'generative ai', 'llm', 'transformers', 'bert',
                             'gpt', 'ai ethics', 'ml ops']
                
                recommended_skills = []
                reco_field = ''
                rec_course = ''
                ## Courses recommendation
                for i in resume_data['skills']:
                    ## Data science recommendation
                    if i.lower() in ds_keyword:
                        print(i.lower())
                        reco_field = 'Data Science'
                        st.success("** Our analysis says you are looking for Data Science Jobs.**")
                        recommended_skills = ['Data Visualization', 'Predictive Analysis', 'Statistical Modeling',
                                              'Data Mining', 'Clustering & Classification', 'Data Analytics',
                                              'Quantitative Analysis', 'Web Scraping', 'ML Algorithms', 'Keras',
                                              'Pytorch', 'Probability', 'Scikit-learn', 'Tensorflow', "Flask",
                                              'Streamlit']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='2')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(ds_course)
                        break

                    ## Web development recommendation
                    elif i.lower() in web_keyword:
                        print(i.lower())
                        reco_field = 'Web Development'
                        st.success("** Our analysis says you are looking for Web Development Jobs **")
                        recommended_skills = ['React', 'Django', 'Node JS', 'React JS', 'php', 'laravel', 'Magento',
                                              'wordpress', 'Javascript', 'Angular JS', 'c#', 'Flask', 'SDK']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='3')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(web_course)
                        break

                    ## Android App Development
                    elif i.lower() in android_keyword:
                        print(i.lower())
                        reco_field = 'Android Development'
                        st.success("** Our analysis says you are looking for Android App Development Jobs **")
                        recommended_skills = ['Android', 'Android development', 'Flutter', 'Kotlin', 'XML', 'Java',
                                              'Kivy', 'GIT', 'SDK', 'SQLite']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='4')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(android_course)
                        break

                    ## IOS App Development
                    elif i.lower() in ios_keyword:
                        print(i.lower())
                        reco_field = 'IOS Development'
                        st.success("** Our analysis says you are looking for IOS App Development Jobs **")
                        recommended_skills = ['IOS', 'IOS Development', 'Swift', 'Cocoa', 'Cocoa Touch', 'Xcode',
                                              'Objective-C', 'SQLite', 'Plist', 'StoreKit', "UI-Kit", 'AV Foundation',
                                              'Auto-Layout']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='5')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(ios_course)
                        break

                    ## Ui-UX Recommendation
                    elif i.lower() in uiux_keyword:
                        print(i.lower())
                        reco_field = 'UI-UX Development'
                        st.success("** Our analysis says you are looking for UI-UX Development Jobs **")
                        recommended_skills = ['UI', 'User Experience', 'Adobe XD', 'Figma', 'Zeplin', 'Balsamiq',
                                              'Prototyping', 'Wireframes', 'Storyframes', 'Adobe Photoshop', 'Editing',
                                              'Illustrator', 'After Effects', 'Premier Pro', 'Indesign', 'Wireframe',
                                              'Solid', 'Grasp', 'User Research']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='6')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(uiux_course)
                        break
                         ## Devops Development
                    elif i.lower() in devops_keyword:
                        print(i.lower())
                        reco_field = 'DevOps Engineering'
                        st.success("** Our analysis says you are looking for DevOps  Jobs **")
                        recommended_skills = [ 'Github', 'Cloud', 'Security', 'Automation', 'Docker', 'System administration',
                                              'Sql', 'Testing', 'Linux', 'Operations', 'Process', 'Aws', 'Administration', 'Scripting', 'System', 'Logging', 'Shell']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='7')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(devops_course)
                        break
                         ## Cloud Engineering
                    elif i.lower() in cloud_keyword:
                        print(i.lower())
                        reco_field = 'Cloud Engineering'
                        st.success("** Our analysis says you are looking for Cloud Engineering Jobs **")
                        recommended_skills = ['AWS', 'Azure', 'GCP', 'Kubernetes', 'Docker', 'Terraform', 'IaC',
                                              'Serverless', 'CI/CD', 'Cloud Architecture', 'Cloud Security', 
                                              'Microservices', 'Cloud Migration', 'Lambda', 'EC2', 'S3', 
                                              'CloudFormation', 'Cloud Networking']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='8')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(cloud_course) # You should create cloud_course list
                        break
                    
                    elif i.lower() in backend_keyword:
                        print(i.lower())
                        reco_field = 'Backend Development'
                        st.success("** Our analysis says you are looking for Backend Development Jobs **")
                        recommended_skills = ['Node.js', 'Express.js', 'Django', 'Flask', 'Spring Boot', 'FastAPI',
                                              'REST API', 'GraphQL', 'MongoDB', 'PostgreSQL', 'MySQL', 'Redis',
                                              'Microservices', 'Docker', 'Kubernetes', 'AWS', 'Authentication',
                                              'JWT', 'Database Design', 'API Development', 'Server Management',
                                              'Linux', 'Git', 'Testing',]
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='9')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(backend_course)
                        break
                    ## Cyber Security
                    elif i.lower() in cyber_keyword:
                        print(i.lower())
                        reco_field = 'Cyber Security'
                        st.success("** Our analysis says you are looking for Cyber Security Jobs **")
                        recommended_skills = ['Network Security', 'Penetration Testing', 'Ethical Hacking', 
                                              'Security Operations', 'Vulnerability Assessment', 'Threat Analysis',
                                              'Incident Response', 'Firewall', 'SIEM', 'Compliance', 'Security Audit',
                                              'Encryption', 'Cryptography', 'Identity Management', 'Secure Coding', 
                                              'Risk Assessment', 'Forensics', 'Security Architecture']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='10')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(cybersecurity_course) # You should create cybersecurity_course list
                        break
                    
                    ## AI Engineer
                    elif i.lower() in ai_keyword:
                        print(i.lower())
                        reco_field = 'AI Engineering'
                        st.success("** Our analysis says you are looking for AI Engineering Jobs **")
                        recommended_skills = ['Machine Learning', 'Deep Learning', 'Neural Networks', 'NLP', 
                                              'Computer Vision', 'TensorFlow', 'PyTorch', 'Keras', 'Scikit-learn',
                                              'Reinforcement Learning', 'MLOps', 'Feature Engineering', 'OpenCV',
                                              'Generative AI', 'LLMs', 'Transformers', 'BERT', 'GPT', 
                                              'AI Ethics', 'Model Deployment']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='11')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(ai_engineering_course) # Consider creating ai_course list
                        break
                
                ## Insert into table
                ts = time.time()
                cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                timestamp = str(cur_date + '_' + cur_time)

                ### Resume writing recommendation - IMPROVED VERSION
                st.subheader("**Resume Tips & Ideas💡**")
                resume_score = 0
                max_score = 100
                criteria_met = 0
                total_criteria = 8

                # Convert resume text to uppercase for better matching
                resume_text_upper = resume_text.upper()

                # 1. Objective/Summary Check (12.5 points)
                objective_keywords = ['OBJECTIVE', 'SUMMARY', 'CAREER OBJECTIVE', 'PROFESSIONAL SUMMARY', 'PROFILE']
                if any(keyword in resume_text_upper for keyword in objective_keywords):
                    resume_score += 12.5
                    criteria_met += 1
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Excellent! You have added Career Objective/Summary</h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] Add a Career Objective or Professional Summary to clearly communicate your career goals and value proposition to recruiters.</h4>''',
                        unsafe_allow_html=True)

                # 2. Experience Check (12.5 points)
                experience_keywords = ['EXPERIENCE', 'WORK EXPERIENCE', 'EMPLOYMENT', 'PROFESSIONAL EXPERIENCE', 'WORK HISTORY']
                if any(keyword in resume_text_upper for keyword in experience_keywords):
                    resume_score += 12.5
                    criteria_met += 1
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Great! You have included your Work Experience✍</h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] Add your Work Experience section. Include internships, part-time jobs, or volunteer work if you're a fresher.</h4>''',
                        unsafe_allow_html=True)

                # 3. Hobbies/Interests Check (12.5 points) - FIXED LOGIC
                hobbies_keywords = ['HOBBIES', 'INTERESTS', 'PERSONAL INTERESTS', 'ACTIVITIES', 'EXTRACURRICULAR']
                if any(keyword in resume_text_upper for keyword in hobbies_keywords):
                    resume_score += 12.5
                    criteria_met += 1
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Nice! You have added your Hobbies/Interests⚽</h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] Add Hobbies/Interests section to showcase your personality and cultural fit for the role.</h4>''',
                        unsafe_allow_html=True)

                # 4. Achievements Check (12.5 points)
                achievement_keywords = ['ACHIEVEMENTS', 'ACCOMPLISHMENTS', 'AWARDS', 'HONORS', 'RECOGNITION']
                if any(keyword in resume_text_upper for keyword in achievement_keywords):
                    resume_score += 12.5
                    criteria_met += 1
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Excellent! You have highlighted your Achievements🏅</h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] Add Achievements/Awards section to demonstrate your capabilities and standout accomplishments.</h4>''',
                        unsafe_allow_html=True)

                # 5. Projects Check (12.5 points)
                project_keywords = ['PROJECTS', 'PROJECT', 'PORTFOLIO', 'WORK SAMPLES', 'CASE STUDIES']
                if any(keyword in resume_text_upper for keyword in project_keywords):
                    resume_score += 12.5
                    criteria_met += 1
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Fantastic! You have showcased your Projects👨‍💻</h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] Add Projects section to demonstrate practical application of your skills and hands-on experience.</h4>''',
                        unsafe_allow_html=True)

                # 6. Education Check (12.5 points)
                education_keywords = ['EDUCATION', 'ACADEMIC', 'QUALIFICATION', 'DEGREE', 'CERTIFICATION', 'UNIVERSITY', 'COLLEGE']
                if any(keyword in resume_text_upper for keyword in education_keywords):
                    resume_score += 12.5
                    criteria_met += 1
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Good! You have included your Educational Background🎓</h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] Add Education section with your academic qualifications and relevant coursework.</h4>''',
                        unsafe_allow_html=True)

                # 7. Skills Check (12.5 points)
                skills_keywords = ['SKILLS', 'TECHNICAL SKILLS', 'COMPETENCIES', 'EXPERTISE', 'TECHNOLOGIES']
                if any(keyword in resume_text_upper for keyword in skills_keywords):
                    resume_score += 12.5
                    criteria_met += 1
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Perfect! You have listed your Skills💪</h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] Add a dedicated Skills section highlighting your technical and soft skills relevant to your target role.</h4>''',
                        unsafe_allow_html=True)

                # 8. Contact Information Check (12.5 points)
                contact_keywords = ['PHONE', 'EMAIL', 'CONTACT', 'MOBILE', 'LINKEDIN', '@']
                if any(keyword in resume_text_upper for keyword in contact_keywords) or '@' in resume_text:
                    resume_score += 12.5
                    criteria_met += 1
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Great! Your contact information is included📞</h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] Ensure your contact information (phone, email, LinkedIn) is clearly visible at the top of your resume.</h4>''',
                        unsafe_allow_html=True)

                # Resume Score Display
                st.subheader("**Resume Score📝**")

                # Score color coding
                if resume_score >= 75:
                    score_color = "#1ed760"  # Green
                    score_message = "Excellent Resume!"
                elif resume_score >= 50:
                    score_color = "#fabc10"  # Yellow
                    score_message = "Good Resume - Room for improvement"
                else:
                    score_color = "#d73b5c"  # Red
                    score_message = "Needs significant improvement"

                # Display score summary
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Resume Score", f"{resume_score:.1f}/100", f"{criteria_met}/{total_criteria} criteria met")
                with col2:
                    st.metric("Completion %", f"{(resume_score/max_score)*100:.0f}%")
                with col3:
                    completion_status = "Complete" if resume_score >= 87 else "Incomplete"
                    st.metric("Status", completion_status)

                # Progress bar with custom styling
                st.markdown(
                    f"""
                    <style>
                        .stProgress > div > div > div > div {{
                            background-color: {score_color};
                        }}
                    </style>""",
                    unsafe_allow_html=True,
                )

                # Smooth progress bar animation
                progress_bar = st.progress(0)
                for i in range(int(resume_score) + 1):
                    progress_bar.progress(i)
                    time.sleep(0.02)  # Faster animation

                # Score display with color coding
                st.markdown(
                    f'''<h3 style='text-align: center; color: {score_color};'>{score_message}</h3>''',
                    unsafe_allow_html=True
                )

                st.success(f'🎯 Your Resume Score: {resume_score:.1f}/100')

                # Improvement suggestions based on score
                if resume_score < 100:
                    missing_sections = total_criteria - criteria_met
                    st.info(f"💡 **Tip**: You're missing {missing_sections} key section(s). Adding them could increase your score to 100/100!")
                    
                    if resume_score < 50:
                        st.warning("⚠️ **Priority**: Focus on adding the missing sections above to significantly improve your resume's effectiveness.")
                    elif resume_score < 75:
                        st.info("ℹ️ **Good Progress**: You're on the right track! Add the remaining sections to make your resume stand out.")

                st.warning("📋 **Note**: This score reflects the completeness of key resume sections. Quality of content is equally important!")

                if resume_score == 100:
                    st.balloons()
                    st.success("🎉 Congratulations! Your resume includes all essential sections!")

                # Convert resume_score to integer for database storage (to maintain compatibility with existing code)
                resume_score = int(resume_score)

                insert_data(resume_data['name'], resume_data['email'], str(resume_score), timestamp,
                            str(resume_data['no_of_pages']), reco_field, cand_level, str(resume_data['skills']),
                            str(recommended_skills), str(rec_course))

               
    else:
        ## Admin Side
        st.success('Welcome to Admin Side')
        # st.sidebar.subheader('**ID / Password Required!**')
        # --- USER AUTHENTICATION ---
        names = ["Group CA8 ", "Chaitanya madurkar"]
        usernames = ["ca8", "chaitanya"]

        # load hashed passwords
        file_path = Path(__file__).parent / "hashed_pw.pkl"
        with file_path.open("rb") as file:
            hashed_passwords = pickle.load(file)

        authenticator = stauth.Authenticate(names, usernames, hashed_passwords,
            "sales_dashboard", "abcdef", cookie_expiry_days=30)

        name, authentication_status, username = authenticator.login("Login", "main")

        if authentication_status == False:
            st.error("Username/password is incorrect")

        if authentication_status == None:
            st.warning("Please enter your username and password")
            
        
        if authentication_status:
             # Display Data
                cursor.execute('''SELECT*FROM user_data''')
                data = cursor.fetchall()
                st.header("**User's👨‍💻 Data**")
                df = pd.DataFrame(data, columns=['ID', 'Name', 'Email', 'Resume Score', 'Timestamp', 'Total Page',
                                                 'Predicted Field', 'User Level', 'Actual Skills', 'Recommended Skills',
                                                 'Recommended Course'])
                st.dataframe(df)


                # Add the filtering functionality here
                st.header("Filter Data")

                # Get unique values for filter options
                unique_fields = df['Predicted Field'].unique().tolist()
                unique_levels = df['User Level'].unique().tolist()

                # Create filter widgets in a side-by-side layout
                col1, col2 = st.columns(2)

                with col1:
                    selected_field = st.selectbox("Filter by Predicted Field", 
                                                ["All Fields"] + unique_fields)

                with col2:
                    selected_level = st.selectbox("Filter by User Level", 
                                                ["All Levels"] + unique_levels)

                # Apply filters
                filtered_df = df.copy()

                if selected_field != "All Fields":
                    filtered_df = filtered_df[filtered_df['Predicted Field'] == selected_field]

                if selected_level != "All Levels":
                    filtered_df = filtered_df[filtered_df['User Level'] == selected_level]

                # Display filtered data
                st.header(f"Filtered Data ({len(filtered_df)} records)")
                st.dataframe(filtered_df)

                # Provide download link for filtered data
                st.markdown(get_table_download_link(filtered_df, 'Filtered_User_Data.csv', 'Download Filtered Report'), 
                            unsafe_allow_html=True)

                ## Admin Side Data
                query = 'select * from user_data;'
                plot_data = pd.read_sql(query, connection)

                ## Pie chart for predicted field recommendations
                labels = plot_data.Predicted_Field.unique()
                print(labels)
                values = plot_data.Predicted_Field.value_counts()
                print(values)
                st.subheader("📈 **Pie-Chart for Predicted Field Recommendations**")
                fig = px.pie(df, values=values, names=labels, title='Predicted Field according to the Skills')
                st.plotly_chart(fig)

                ### Pie chart for User's👨‍💻 Experienced Level
                labels = plot_data.User_level.unique()
                values = plot_data.User_level.value_counts()
                st.subheader("📈 ** Pie-Chart for User's👨‍💻 Experienced Level**")
                fig = px.pie(df, values=values, names=labels, title="Pie-Chart📈 for User's👨‍💻 Experienced Level")
                st.plotly_chart(fig)

                authenticator.logout("Logout", "sidebar")

            
run()
