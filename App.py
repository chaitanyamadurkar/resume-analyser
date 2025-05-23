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
from Courses import ds_course, web_course, android_course, ios_course, uiux_course, cloud_course, backend_course, cybersecurity_course, ai_engineering_course, resume_videos, interview_videos
import pafy
import plotly.express as px
import youtube_dl
import streamlit_authenticator as stauth


def fetch_yt_video(link):
    video = pafy.new(link)
    return video.title

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


def insert_data(name, email, res_score, timestamp, no_of_pages, reco_field, cand_level, skills, recommended_skills,
                courses):
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
                
                backend_keyword = ['nodejs', 'django', 'flask', 'spring', 'java', 'php', 'ruby', 'python', 'api', 
                                   'rest', 'graphql', 'microservices', 'database', 'sql', 'nosql', 'mongodb', 
                                   'postgresql', 'mysql', 'express', 'orm', 'server', 'backend']
                
                cybersecurity_keyword = ['security', 'cybersecurity', 'ethical hacking', 'penetration testing', 'network security',
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
                        reco_field = 'DevOps'
                        st.success("** Our analysis says you are looking for DevOps  Jobs **")
                        recommended_skills = [ 'Github', 'Cloud', 'Security', 'Automation', 'Docker', 'System administration',
                                              'Sql', 'Testing', 'Linux', 'Operations', 'Process', 'Aws', 'Administration', 'Scripting', 'System', 'Logging', 'Shell']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='7')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(ios_course)
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
                    
                    ## Backend Developer
                    elif i.lower() in backend_keyword:
                        print(i.lower())
                        reco_field = 'Backend Development'
                        st.success("** Our analysis says you are looking for Backend Development Jobs **")
                        recommended_skills = ['Node.js', 'Express', 'Django', 'Flask', 'Spring Boot', 'Java', 
                                              'Python', 'Ruby', 'PHP', 'REST API', 'GraphQL', 'SQL', 'NoSQL', 
                                              'MongoDB', 'PostgreSQL', 'MySQL', 'ORM', 'Microservices',
                                              'Authentication', 'Authorization', 'Docker', 'Server Architecture']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='9')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(backend_course) # Consider creating backend_course list
                        break
                    
                    ## Cyber Security
                    elif i.lower() in cybersecurity_keyword:
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

                ### Resume writing recommendation
                st.subheader("**Resume Tips & Ideas💡**")
                resume_score = 0
                if 'Objective' or 'SUMMERY' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Objective</h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add your career objective, it will give your career intension to the Recruiters.</h4>''',
                        unsafe_allow_html=True)

                if 'EXPERIENCE' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Experience✍</h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Experience✍. It will help you stand out.</h4>''',
                        unsafe_allow_html=True)

                if 'Hobbies' or 'Interests' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Hobbies⚽</h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Hobbies⚽. It will show your persnality to the Recruiters and give the assurance that you are fit for this role or not.</h4>''',
                        unsafe_allow_html=True)

                if 'Achievements' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Achievements🏅 </h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Achievements🏅. It will show that you are capable for the required position.</h4>''',
                        unsafe_allow_html=True)

                if 'Projects' or 'PEOJECTS' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects👨‍💻 </h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Projects👨‍💻. It will show that you have done work related the required position or not.</h4>''',
                        unsafe_allow_html=True)

                st.subheader("**Resume Score📝**")
                st.markdown(
                    """
                    <style>
                        .stProgress > div > div > div > div {
                            background-color: #d73b5c;
                        }
                    </style>""",
                    unsafe_allow_html=True,
                )
                my_bar = st.progress(0)
                score = 0
                for percent_complete in range(resume_score):
                    score += 1
                    time.sleep(0.1)
                    my_bar.progress(percent_complete + 1)
                st.success('** Your Resume Writing Score: ' + str(score) + '**')
                st.warning(
                    "** Note: This score is calculated based on the content that you have added in your Resume. **")
                st.balloons()

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
