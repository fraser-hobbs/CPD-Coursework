from aws_cdk import App
from dotenv import load_dotenv
import os
from cpd_coursework.cdk.stacks.infra_stack import InfraStack

load_dotenv()

student_id = os.getenv("STUDENT_ID")

app = App(context={
    "student_id": student_id
})

InfraStack(app, "CPD-CourseworkStack")
app.synth()