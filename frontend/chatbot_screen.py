import time
import streamlit as st
import requests
from streamlit_option_menu import option_menu


# External css styling
with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

headerSection = st.container()
loginSection = st.container()

# Retrieve all files
def get_files(params):
    return requests.get("https://api.gayle.ai/files",params=params, cookies={"cookie": st.session_state.cookie})

# Delete file
def delete_file(file_id, company_id):
    data = {
        'file_id': file_id,
        'company_id': company_id
    }
    return requests.delete("https://api.gayle.ai/delete_file",json=data,cookies={"cookie": st.session_state.cookie})

# Custom instruction update
def custom_instruction_Clicked(s_company_id):
    data = {
        "instructions": st.session_state.custom_instruction,
        "company_id": str(s_company_id)
    }
    response=requests.post("https://api.gayle.ai/update_instructions",json=data,cookies={"cookie": st.session_state.cookie})
    if response.status_code == 200:
        st.success(response.json()['message'])
    else:
        st.error("Failed to update instructions")

def get_company_details():
    response = requests.get("https://api.gayle.ai/companyDetails",cookies={"cookie": st.session_state.cookie})
    if response.status_code == 200:
        st.session_state.company_list = response.json()
    else:
        st.session_state.company_list = []
        st.error('Failed to fetch company details')


# main page schema
def show_main_page():
    loginSection.empty()
    
    with st.sidebar:
        selected = option_menu(
            menu_title=f"Hello, {st.session_state.name}!",
            menu_icon= "rocket",
            options=["Upload", "Chat Interface", "Company details"],
            icons=["cloud-upload", "robot", "building"],
        )
    st.sidebar.button("Log Out", key="logout", on_click=LoggedOut_Clicked)
    if st.session_state.company_list == []:
        get_company_details()
    if selected == "Upload":
        st.header("Upload")

        # Get the company list from the session state
        company_list = st.session_state.company_list

        # Create a list of company names for the dropdown, including 'None'
        company_names = ['None'] + [row[1] for row in company_list]

        # Add a dropdown to select a company
        selected_company_name = st.selectbox("Select a company", company_names)

        st.session_state.files = []

        # Only execute the rest of the code if a company is selected
        if selected_company_name != 'None':
            
            # Get the company ID based on the selected company name
            s_company_id = next((row[0] for row in company_list if row[1] == selected_company_name), None)
            # print(type(s_company_id))
            params = {"company_id": str(s_company_id)}
            source_option = st.radio("Select the source of your text", ["file", "website"])
            if source_option == "file":
                uploaded_file = st.file_uploader("Choose a file", type=["txt", "csv","pdf"])
                button = st.button('Submit')
                
                if button:
                    files = {"upload_file": uploaded_file}
                    with st.spinner("Uploading and generating embeddings..."):
                        response = requests.post("https://api.gayle.ai/upload_files", files=files, params=params, cookies={"cookie": st.session_state.cookie})
                    if response.status_code == 200:
                        response_data = response.json()
                        if 'message' in response_data:
                            st.session_state.files = []
                            st.success(response_data['message'])
                        elif 'error' in response_data:
                            if response.json()['error'] == "Content uploading limit has reached.":
                                st.session_state.files = []
                            st.error(response.json()['error'])
                    else:
                        st.error("Something went wrong. Please, try again")
                if st.session_state.files == []:
                    resp = get_files(params)
                    resp_data = resp.json()
                    if 'data' in resp_data:
                        st.session_state.files = [tup for tup in resp_data['data']]
                    else:
                        st.error(resp_data['error'])
            else:
                with st.form(key="myform", clear_on_submit=True):
                    url = st.text_input("Enter the website URL")
                    button = st.form_submit_button('Submit')
                if button:
                    with st.spinner("Generating embeddings..."):
                        response = requests.post("https://api.gayle.ai/upload", json={"url": url, "company_id": s_company_id},cookies={"cookie": st.session_state.cookie})
                    if response.status_code == 200:
                        response_data = response.json()
                        if 'message' in response_data:
                            st.session_state.files = []
                            st.success(response_data['message'])
                        elif 'error' in response_data:
                            if response.json()['error'] == "Content uploading limit has reached.":
                                st.session_state.files = []
                            st.error(response.json()['error'])
                    else:
                        st.error("Something went wrong. Please, try again")
                if st.session_state.files == []:
                    resp = get_files(params)
                    resp_data = resp.json()
                    if 'data' in resp_data:
                        st.session_state.files = [tup for tup in resp_data['data']]
                    else:
                        st.error(resp_data['error'])
            if st.session_state.files != []:
                files = st.session_state.files
                for file in files:
                    col1, col2 = st.columns([1,1])
                    col1.write(file[1])
                    if col2.button("Delete", key=file[0]):
                        resp = delete_file(file[0], s_company_id)
                        resp_data = resp.json()
                        if 'message' in resp_data:
                            st.session_state.files = [tup for tup in st.session_state.files if tup[0] != file[0]]
                        else :
                            st.error(resp_data['error'])
                        st.rerun()

    elif selected == "Chat Interface":
        # get_company_details()
        company_id_list = [sub_list[0] for sub_list in st.session_state.company_list]
        for company_id in company_id_list:
            if company_id not in st.session_state.thread_dict:
                response = requests.get("https://api.gayle.ai/generateThread",cookies={"cookie": st.session_state.cookie})
                if response.status_code == 200:
                    st.session_state.thread_dict[company_id] = response.json()["thread_id"]
                else: 
                    st.error('Something went wrong. Please, try again')
        print(st.session_state.thread_dict)

        st.header("Chat Interface")
        # Get the company list from the session state
        company_list = st.session_state.company_list

        # Create a list of company names for the dropdown, including 'None'
        company_names = ['None'] + [row[1] for row in company_list]

        # Add a dropdown to select a company
        selected_company_name = st.selectbox("Select a company", company_names)

        # Only execute the rest of the code if a company is selected
        if selected_company_name != 'None':
            
            # Get the company ID based on the selected company name
            s_company_id = next((row[0] for row in company_list if row[1] == selected_company_name), None)

            # Check if the selected company is different from the previous selection
            if "previous_company_id" not in st.session_state or st.session_state.previous_company_id != s_company_id:
                # Clear the messages only when a different company is selected
                st.session_state.messages = []
                st.session_state.previous_company_id = s_company_id

            if "custom_instruction" not in st.session_state:
                response = requests.get("https://api.gayle.ai/get_instructions", params={"company_id": str(s_company_id)},cookies={"cookie": st.session_state.cookie})
                if response.status_code == 200:
                    st.session_state.custom_instruction = response.json()['instructions']
                else:
                    st.error("Something went wrong. Could not fetch the current instructions.")
            st.text_area("Enter your custom instruction:", key="custom_instruction")
            if st.button("Update"):
                custom_instruction_Clicked(s_company_id)
            st.markdown(
                    """
                    <style>
                        div[data-testid="column"]:nth-of-type(3)
                        {
                            display: flex;
                            justify-content: end;
                            align-items: center;
                        }
                        div[data-testid="column"]:nth-of-type(4)
                        {
                            display: flex;
                            align-items: center;
                        }
                        div[data-testid="stHorizontalBlock"] {
                            width:46%;
                            position: fixed;
                            bottom: 72px;
                            z-index: 100;
                            }
                    </style>
                    """,unsafe_allow_html=True
                )
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            if prompt:=st.chat_input("What is up?"):
                with st.chat_message("user"):
                    st.markdown(prompt)
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("assistant"):
                    response = None
                    try:
                        if s_company_id in st.session_state.thread_dict:
                            response = requests.post("https://api.gayle.ai/query", json={"question": prompt, "company_id": str(s_company_id),"t_id":st.session_state.thread_dict[s_company_id]},cookies={"cookie": st.session_state.cookie})
                            response.raise_for_status() 
                        else:
                            st.error('Something went wrong. Please, try again')
                    except requests.exceptions.RequestException as e:
                        st.error(f"An error occurred while processing the request: {e}")
                    if response is not None:
                        if 'answer' in response.json():
                            st.markdown(response.json()["answer"])
                            st.session_state.messages.append({"role": "assistant", "content": response.json()["answer"]})
                        else:
                            st.markdown("Sorry, I don't know the answer.")
                            st.session_state.messages.append({"role": "assistant", "content": "Sorry, I don't know the answer."})
                # if response is not None:
                #     if 'answer' in response.json():
                #         resp = requests.post("https://api.gayle.ai/save", json={"answer": response.json()["answer"], "userid": st.session_state.userid},cookies={"cookie": st.session_state.cookie})
                #         st.session_state.messages.append({"role": "assistant", "content": response.json()["answer"]})
                #     else:
                #         resp = requests.post("https://api.gayle.ai/save", json={"answer": "Sorry, I don't know the answer.", "userid": st.session_state.userid},cookies={"cookie": st.session_state.cookie})
                #         st.session_state.messages.append({"role": "assistant", "content": "Sorry, I don't know the answer."})
        else:
            st.session_state.messages = []
    elif selected == "Company details":
        st.header("Company details")
        with st.form(key="logo_form", clear_on_submit=True):
            company = st.text_input("Enter company name", help="This field is required")
            domain = st.text_input("Enter domain (exclude http://)", help="This field is required")
            image_file = st.file_uploader("Upload your logo", type=["jpeg", "svg", "png"], accept_multiple_files=False)
            url = st.text_input("Or enter url of image")
            color = st.color_picker("Theme color", '#2464DA')
            
            if st.form_submit_button("Create"):
                if image_file is None and url == "":
                    st.error("Either upload your logo or enter url of image is required")
                elif company == "":
                    st.error("Enter company name is required")
                elif domain == "":
                    st.error("Enter domain is required")
                else:
                    if domain.startswith('http://') or domain.startswith('https://'):
                        domain = domain.replace('http://', '').replace('https://', '')
                    if image_file is not None:
                        payload = {"hex": color, "domain": domain,"company": company}
                        files = {"files": (image_file.name, image_file.read(), image_file.type)}
                        response = requests.post("https://api.gayle.ai/logo_file", data=payload, files=files, cookies={"cookie": st.session_state.cookie})
                        if 'message' in response.json():
                            st.success(response.json()['message'])
                        elif 'error' in response.json():
                            st.error(response.json()['error'])
                    else:
                        data = {
                            "logo": url,
                            "domain" : domain,
                            "hex" : color,
                            "company": company,
                            "userid": st.session_state.userid
                        }
                        response = requests.post("https://api.gayle.ai/logo_url", json=data, cookies={"cookie": st.session_state.cookie})
                        if 'message' in response.json():
                            st.success(response.json()['message'])
                        elif 'error' in response.json():
                            st.error(response.json()['error'])
        st.subheader('Company List')
        get_company_details()
        import pandas as pd

        data = []
        for row in st.session_state.company_list:
            snippet = f"""<script src="https://kantanna-assets.s3.amazonaws.com/plugin-js-cdn/assets/app.js" defer></script>
        <div id="root" data-domain="{row[2]}" data-apikey="{row[3]}" data-company_id="{row[0]}"></div>"""
            data.append([row[0], row[1], row[2], row[3], snippet])

        df = pd.DataFrame(data, columns=["ID", "Name", "Domain", "Auth key", "Chat UI Snippet"])

        st.write(df)
        
        # HTML table
    #     html_table = "<table><tr><th>ID</th><th>Name</th><th>Domain</th><th>Auth key</th></tr>"
    #     for row in st.session_state.company_list:
    #         html_table += f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td></tr>"
    #     html_table += "</table>"

    #     # Display the table
    #     st.write(html_table, unsafe_allow_html=True)
    #     snippet = """
    #     <script src="https://kantanna-assets.s3.amazonaws.com/plugin-js-cdn/assets/app.js" defer> </script>
    # <div id="root" data-domain="{domain}" data-apikey="{apikey}" data-company_id="{company_id}"></div>
    #     """
    #     for row in st.session_state.company_list:
    #         st.write(snippet.format(domain=row[2], apikey=row[3], company_id=row[0]))

# Logout function
def LoggedOut_Clicked():
    params = {"t_id": st.session_state.threadid}
    with st.spinner("Logging out..."):
        response = requests.post("https://api.gayle.ai/delete_session",cookies={"cookie": st.session_state.cookie}, params=params)
        for company_id in st.session_state.thread_dict:
            requests.delete("https://api.gayle.ai/deleteThread", cookies={"cookie": st.session_state.cookie}, params={"t_id": st.session_state.thread_dict[company_id]})
    st.session_state.sid = ""
    st.session_state.userid = ""
    st.session_state.cookie = ""
    st.session_state.threadid = ""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "files" in st.session_state:
        st.session_state.files = []
    if "company_list" in st.session_state:
        st.session_state.company_list = []
    if "thread_dict" in st.session_state:
        st.session_state.thread_dict = {}

# Login function
def LoggedIn_Clicked(Email, password):
    data = {
                'email': Email,
                'password': password
            }
    with st.spinner("Logging in..."):
        response = requests.post("https://api.gayle.ai/login", json=data)
    if 'message' in response.json():
        if response.json()['message'] == 'User logged in...':
            st.session_state.threadid = response.json()['t_id']
            st.session_state.name = response.json()['name']
            st.session_state.sid = response.json()['session']
            st.session_state.cookie = response.cookies.get('cookie')
            resp = requests.get("https://api.gayle.ai/whoami",cookies={"cookie": st.session_state.cookie})
            if resp.status_code == 200:
                st.session_state.userid = resp.json()['userid']
            else:
                st.error('Something is wrong. refresh page and try again.')
        elif response.json()['message'] == 'User not found':
            st.error("User not found. Please, refresh the page and try again")
        elif response.json()['message'] == 'Wrong password':
            st.error("Wrong password. Please, refresh the page and try again")
    else:
        st.error("Can't login. Please, refresh the page and try again")

# Register function
def Reg_Clicked(Name, Email, Password):
    data = {
        'name': Name,
        'email': Email,
        'password': Password
    }
    with st.spinner("Registering..."):
        response = requests.post("https://api.gayle.ai/register", json=data)
    if "message" in response.json():
        if response.json()['message'] == 'User logged in...':
            st.session_state.threadid = response.json()['t_id']
            st.session_state.name = response.json()['name']
            st.session_state.sid = response.json()['session']
            st.session_state.cookie = response.cookies.get('cookie')
            resp = requests.get("https://api.gayle.ai/whoami",cookies={"cookie": st.session_state.cookie})
            if resp.status_code == 200:
                st.session_state.userid = resp.json()['userid']
            else:
                st.error('Something is wrong. refresh page and try again.')
    else:
        st.error("Can't register this user. Please, refresh the page and try again")

# login page schema
def show_login_page():
    with loginSection:
        if st.session_state['userid'] == "":
            selected = option_menu(
                menu_title=None,
                options=["Register", "Login"],
                icons= ["person-plus", "person-check"],
                default_index=0,
                orientation="horizontal",
                )
            if selected == "Register":
                st.header("Register")
                st.text_input("Name", key="name_input")
                st.text_input("Email", key="email_input")
                st.text_input("Password", key="password_input", type="password")
                st.button("Register", on_click=Reg_Clicked, args=(st.session_state.name_input, st.session_state.email_input, st.session_state.password_input), disabled=True)
            if selected == "Login":
                st.header("Login")
                st.text_input("Email", key="email_input")
                st.text_input("Password", key="password_input", type="password")
                st.button ("Login", on_click=LoggedIn_Clicked, args= (st.session_state.email_input, st.session_state.password_input))

# initialization
with headerSection:
    if "thread_dict" not in st.session_state:
        st.session_state.thread_dict = {}
    if "files" not in st.session_state:
        st.session_state.files = []
    if "company_list" not in st.session_state:
        st.session_state.company_list = []
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "threadid" not in st.session_state:
        st.session_state.threadid = ""
    if "cookie" not in st.session_state:
        st.session_state.cookie = ""
    if "sid" not in st.session_state:
        st.session_state.sid = ""
    if "name" not in st.session_state:
        st.session_state.name = ""
    if 'userid' not in st.session_state:
        st.session_state['userid'] = ""
        show_login_page()
    else:
        if st.session_state['userid'] != "":
            show_main_page()
        else:
            show_login_page()