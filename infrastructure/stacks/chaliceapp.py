import os

from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_sqs as sqs
from chalice.cdk import Chalice

try:
    from aws_cdk import core as cdk
except ImportError:
    import aws_cdk as cdk

RUNTIME_SOURCE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), os.pardir, 'runtime')


class ChaliceApp(cdk.Stack):

    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        self.dynamodb_table = self._create_ddb_table()
        self.sqs_queue = self._create_sqs_queue()

        self.chalice = Chalice(
            self, 'ChatGptTelegramBot',
            source_dir=RUNTIME_SOURCE_DIR,
            stage_config={
                'environment_variables': {
                    'CHAT_HISTORY_TABLE': self.dynamodb_table.table_name,
                    'UPDATE_MESSAGE_QUEUE': self.sqs_queue.queue_name,
                    'UPDATE_MESSAGE_QUEUE_ARN': self.sqs_queue.queue_arn
                }
            }
        )

        role = self.chalice.get_role('DefaultRole')
        self.dynamodb_table.grant_read_write_data(role)
        self.sqs_queue.grant_consume_messages(role)
        self.sqs_queue.grant_send_messages(role)

    def _create_ddb_table(self):
        dynamodb_table = dynamodb.Table(
            self, 'ChatHistory',
            partition_key=dynamodb.Attribute(name='ChatID', type=dynamodb.AttributeType.NUMBER),
            removal_policy=cdk.RemovalPolicy.DESTROY
        )

        cdk.CfnOutput(self, 'TableName', value=dynamodb_table.table_name)
        return dynamodb_table

    def _create_sqs_queue(self):
        sqs_dead_letter_queue = sqs.Queue(
            self, 'UpdateMessageDeadLetter',
            removal_policy=cdk.RemovalPolicy.DESTROY
        )
        sqs_queue = sqs.Queue(
            self, 'UpdateMessage',
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=10,
                queue=sqs_dead_letter_queue
            ),
            visibility_timeout=cdk.Duration.seconds(60),
            removal_policy=cdk.RemovalPolicy.DESTROY
        )

        cdk.CfnOutput(self, 'DeadLetterQueueName', value=sqs_dead_letter_queue.queue_name)
        cdk.CfnOutput(self, 'QueueName', value=sqs_queue.queue_name)
        return sqs_queue
