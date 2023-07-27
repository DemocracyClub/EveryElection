from diagrams import Cluster, Diagram
from diagrams.aws.compute import (
    EC2Ami,
    EC2AutoScaling,
    EC2ImageBuilder,
    EC2Instances,
)
from diagrams.aws.devtools import Codedeploy
from diagrams.aws.general import InternetAlt1
from diagrams.aws.management import Config, Organizations
from diagrams.aws.network import ALB, CloudFront, Route53
from diagrams.aws.security import CertificateManager
from diagrams.generic.network import Subnet

with Diagram(
    "AWS deployment resources", filename="docs/aws-resources", show=False
):
    with Cluster("Manual setup"):
        cert = CertificateManager("TLS Certificate")

    with Cluster("Application 'Golden images'"):
        base_ami = EC2Ami("DC Base AMI")
        ami = EC2Ami("EE AMI")
        image_builder = EC2ImageBuilder("EE Image builder")
        base_ami >> image_builder >> ami
        ami >> Organizations("Shared DC wide")

    with Cluster("Application hosting"):
        with Cluster("CDK Managed"):
            web = InternetAlt1("Web")
            dns = Route53("DNS")
            cf = CloudFront("CloudFront")
            alb = ALB("Application Load Balancer")

            tg = Subnet("Target Group")

            web - dns - cf >> cert >> cf
            cf >> alb >> tg

            launch_template = Config("Launch Template")

            code_deploy = Codedeploy("Code Deploy")

        with Cluster("Code Deploy Managed"):
            asg = EC2AutoScaling("Auto Scaling Group")
            code_deploy >> asg
            ami >> launch_template >> asg >> EC2Instances("Servers")

    #     for i in range(1, 4):
    #         with Cluster(
    #             f"Instance {i}",
    #         ):
    #             alb << Django("WDIV App") >> rds
    #             PostgreSQL(f"Replica/Read db {i}") << rds
    #
    # dns = Route53("DNS")
    #
    # dns >> alb
