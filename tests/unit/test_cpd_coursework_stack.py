import aws_cdk as core
import aws_cdk.assertions as assertions

from cpd_coursework.cpd_coursework_stack import CpdCourseworkStack

# example tests. To run these tests, uncomment this file along with the example
# resource in cpd_coursework/cpd_coursework_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = CpdCourseworkStack(app, "cpd-coursework")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
