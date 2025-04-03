from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_sqs as sqs,
    aws_sns as sns,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_lambda_event_sources as sources,

)
from constructs import Construct
from aws_cdk import RemovalPolicy

class InfraStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        student_id = self.node.try_get_context("student_id")

        # S3 Bucket
        image_bucket = s3.Bucket(
            self, "ImageBucket",
            bucket_name=f"face-comparison-bucket-{student_id}",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # SQS Queue
        image_queue = sqs.Queue(
            self, "ImageQueue",
            queue_name=f"face-comparison-queue-{student_id}"
        )

        # SNS Topic
        notification_topic = sns.Topic(
            self, "NotificationTopic",
            topic_name=f"face-comparison-topic-{student_id}"
        )

        # Lambda Function
        s3_handler = _lambda.Function(
            self, "S3HandlerFunction",
            function_name=f"S3HandlerFunction-{student_id}",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="app.lambda_handler",
            code=_lambda.Code.from_asset("cpd_coursework/lambdas/s3_trigger_lambda"),
            environment={
                "BUCKET_NAME": image_bucket.bucket_name,
                "QUEUE_URL": image_queue.queue_url,
                "TOPIC_ARN": notification_topic.topic_arn,
                "STUDENT_ID": student_id,
            }
        )

        # Face Comparison Lambda
        face_comparison_lambda = _lambda.Function(
            self, "FaceComparisonFunction",
            function_name=f"FaceComparisonFunction-{student_id}",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="app.lambda_handler",
            code=_lambda.Code.from_asset("cpd_coursework/lambdas/face_comparison_lambda"),
            environment={
                "BUCKET_NAME": image_bucket.bucket_name,
                "QUEUE_URL": image_queue.queue_url,
                "TOPIC_ARN": notification_topic.topic_arn,
                "STUDENT_ID": student_id,
            }
        )

        # Permissions for face comparison Lambda
        image_bucket.grant_read(face_comparison_lambda)
        image_queue.grant_consume_messages(face_comparison_lambda)
        notification_topic.grant_publish(face_comparison_lambda)

        # Permissions
        image_bucket.grant_read(s3_handler)
        image_queue.grant_send_messages(s3_handler)
        notification_topic.grant_publish(s3_handler)

        face_comparison_lambda.add_event_source(sources.SqsEventSource(image_queue))