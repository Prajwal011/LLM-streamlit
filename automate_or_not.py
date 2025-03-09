import streamlit as st
import pandas as pd
import re
import os
from bs4 import BeautifulSoup as bs
import openai
import langchain
import requests
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json
from langchain_core.output_parsers import StrOutputParser
import re
from rapidfuzz import process
import pandas as pd
import os

os.environ['GROQ_API_KEY']='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'

df = pd.read_html("https://www.onetonline.org/find/all")
df= df[0]

def get_code_for_occupation(user_input):
    occupations = df["Occupation"].dropna().tolist()  # Get all occupation names
    match, score, idx = process.extractOne(user_input, occupations)  # Find best match
    if score > 70:  # Adjust threshold if needed
        matched_row = df[df["Occupation"] == match]  # Find corresponding row
        return matched_row["Code"].values[0]  # Return the code
    else:
        return "No close match found"

st.title("AI Impact on Job Roles")
# User input
role = st.text_input("Enter a job role (e.g., Actor)")
# role = input()
code = get_code_for_occupation(role)
print(code)

s = bs(requests.get("https://www.onetonline.org/link/summary/"+code).text)
tasks = []
for i in (s.find_all('div',id='Tasks')):
  for j in i.find_all("div",class_="order-2 flex-grow-1"):
    tasks.append(j.text)
print(tasks)
tech_skills = []
for i in (s.find_all('div',class_='section_TechnologySkills')):
  for j in i.find_all("div",class_="order-2 flex-grow-1"):
    tech_skills.append(j.text)
print(tech_skills)

# Initialize Groq LLM
llm = ChatGroq(
    model_name="llama-3.3-70b-versatile",
    temperature=0.7
)

# Create a simple prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", """Helpful bot which evaluates each tasks provided for role{role} as being Augmented by ai or not,
    format output ex -  ("Collaborate with other actors as part of an ensemble.", "Not Replaced by AI")
    """),
    ("user", "Tasks to classify as Replaced by AI or not{tasks}")
])

parser = StrOutputParser()

# Create the chain that guarantees JSON output
chain = prompt | llm | parser

def parse_product(role,tasks) -> dict:
    result = chain.invoke({"role": role,'tasks':tasks})
    return result



if role:

    ans = parse_product(role,tasks)
    print(ans)
    t1= []
    for i in re.findall('[\d\s\.]+\([\w\W]+\)',ans)[0].split('\n'):
      if i!='':
        t1.append([''.join(i.split(',')[:-1]).replace("(",''),i.split(',')[-1].strip(")")])

    if "No close match found" != code :
        st.write(f"### Tasks for {role} and AI Impact:")
        # df = pd.DataFrame(roles_data[role], columns=["Task", "AI Impact"])
        df = pd.DataFrame(t1,columns=['Task','AI Impact'])

        for _, row in df.iterrows():
            task, impact = row
            if   "Not" in impact :
                st.markdown(f"❌**{task}** - {impact}")
            else:
                st.markdown(f"✅ **{task}** - {impact}")
               # Question and Answer Block
        st.write("### Ask a Question")
        question = st.text_area("Enter your question about AI impact on this role:")
        if st.button("Submit"):
            if question:
                # Create a simple prompt
                prompt = ChatPromptTemplate.from_messages([
                    ("system", """Helpful bot which helps user answer questions related to tasks being automated by ai tasks{tasks}
                    """),
                    ("user", "Answer this question based on tasks:{question}")
                ])

                parser = StrOutputParser()
                # Create the chain that guarantees JSON output
                chain = prompt | llm | parser
                result = chain.invoke({"question": question,'tasks':tasks})

                st.write(f"**Model:** {result}")

                # st.write("🔍 Answer: AI can assist with many aspects of this role, but human creativity, emotional intelligence, and collaboration remain irreplaceable.")
            else:
                st.error("Please enter a question before submitting.")
    else:
        st.error("Role not found in the dataset. Try 'Actor'.")
