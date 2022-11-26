from aws_cdk.core import Stack, Construct, Duration

import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_iam as iam
import aws_cdk.aws_elasticloadbalancingv2 as elbv2
from aws_cdk.aws_ssm import StringParameter
import aws_cdk.aws_codedeploy as codedeploy
import aws_cdk.aws_cloudfront as cloudfront
import aws_cdk.aws_cloudfront_origins as origins
import aws_cdk.aws_certificatemanager as acm
import aws_cdk.aws_route53 as route_53
import aws_cdk.aws_route53_targets as route_53_target

from cdk_imagebuilder.stacks.code_deploy_policies import (
    EE_DEPLOYER_POLICY,
    EE_CODE_DEPLOY_POLICY,
    EE_CODE_DEPLOY_EC2_POLICY,
    EE_CODE_DEPLOY_LAUNCH_TEMPLATE_POLICY,
)

EE_IMAGE = "ami-0be60c85eea65b701"


class EECodeDeployment(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # self.ami = ec2.MachineImage.lookup(name=EE_IMAGE, owners=["self"])
        self.ami = ec2.MachineImage.generic_linux(ami_map={"eu-west-2": EE_IMAGE})

        self.default_vpc = ec2.Vpc.from_lookup(
            scope=self, id="default-vpc-id", is_default=True
        )

        self.policies = self.create_policies()
        self.roles = self.create_roles()
        self.alb_security_group = self.create_alb_security_group()

        self.instance_security_groups = self.create_instance_security_groups(
            self.alb_security_group
        )

        self.launch_template = self.create_launch_template(
            ami=self.ami,
            security_group=self.instance_security_groups,
            role=self.roles["codedeploy-ec2-instance-profile"],
        )

        self.target_group = self.create_target_group()

        self.alb = self.create_alb(
            security_group=self.alb_security_group,
            target_group=self.target_group,
            https=False,
        )

        self.code_deploy = self.create_code_deploy()

        self.cloudfront = self.create_cloudfront(self.alb)

    def create_code_deploy(self):
        application = codedeploy.ServerApplication(
            self, "CodeDeployApplicationID", application_name="EECodeDeploy"
        )

    def create_launch_template(
        self, ami: ec2.IMachineImage, security_group: ec2.SecurityGroup, role: iam.Role
    ) -> ec2.LaunchTemplate:
        lt = ec2.LaunchTemplate(
            self,
            "ee-launch-template-id",
            instance_type=ec2.InstanceType("t3a.medium"),
            machine_image=ami,
            launch_template_name="ee-launch-template",
            role=role,
            security_group=security_group,
        )
        return lt

    def create_target_group(self):
        return elbv2.ApplicationTargetGroup(
            self,
            "ee-alb-tg-id",
            port=8001,
            protocol=elbv2.ApplicationProtocol.HTTP,
            health_check=elbv2.HealthCheck(
                enabled=True,
                healthy_threshold_count=2,
                interval=Duration.seconds(100),
                port="traffic-port",
                path="/",
                protocol=elbv2.Protocol.HTTP,
                timeout=Duration.seconds(5),
                unhealthy_threshold_count=5,
                healthy_http_codes="200",
            ),
            target_group_name="ee-alb-tg",
            target_type=elbv2.TargetType.INSTANCE,
            vpc=self.default_vpc,
        )

    def create_instance_security_groups(
        self, alb_security_group: ec2.SecurityGroup
    ) -> ec2.SecurityGroup:

        instance_security_group = ec2.SecurityGroup(
            self,
            "instance-security-group",
            vpc=self.default_vpc,
            allow_all_outbound=True,
            security_group_name="Instance Security Group",
            description="Allow HTTP access for an instance from the ALB security group",
        )

        instance_security_group.add_ingress_rule(
            ec2.Peer.security_group_id(alb_security_group.security_group_id),
            ec2.Port.tcp(8001),
            "HTTP from ALB",
        )
        return instance_security_group

    def create_alb_security_group(self, https=True):
        alb_security_group = ec2.SecurityGroup(
            self,
            "alb-security-group",
            vpc=self.default_vpc,
            allow_all_outbound=True,
            security_group_name="ALB Security Group",
            description="ALB accepts all traffic",
        )
        alb_security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "allow HTTP from anywhere"
        )
        if https:
            alb_security_group.add_ingress_rule(
                ec2.Peer.any_ipv4(), ec2.Port.tcp(443), "allow HTTPS from anywhere"
            )

        return alb_security_group

    def create_alb(
        self,
        security_group: ec2.SecurityGroup,
        target_group: elbv2.ApplicationTargetGroup,
        https=True,
    ) -> elbv2.ApplicationLoadBalancer:
        """
        Creates an Application Load Balancer (ALB).

        If https is True then the ALB will listen on post 443. This requires a
        valid cert ARN to exist in SSM at `EE_SSL_CERTIFICATE_ARN`
        """
        subnets = ec2.SubnetSelection(
            availability_zones=["eu-west-2a", "eu-west-2b", "eu-west-2c"]
        )

        alb = elbv2.ApplicationLoadBalancer(
            self,
            "application-load-balancer-id",
            vpc=self.default_vpc,
            vpc_subnets=subnets,
            internet_facing=True,
            security_group=security_group,
            ip_address_type=elbv2.IpAddressType.IPV4,
            load_balancer_name="ee-alb",
        )

        if https:
            # Listen on HTTPS
            alb.add_listener(
                "https-listener-id",
                certificates=[
                    elbv2.ListenerCertificate.from_arn(
                        StringParameter.value_from_lookup(
                            self,
                            "SSL_CERTIFICATE_ARN",
                        )
                    )
                ],
                port=443,
                protocol=elbv2.ApplicationProtocol.HTTPS,
                default_action=elbv2.ListenerAction.forward([self.ee_alb_tg]),
            )

        # Listen on HTTP
        http_listener = alb.add_listener(
            "http-listener-id", port=80, protocol=elbv2.ApplicationProtocol.HTTP
        )

        if https:
            # Redirect from HTTP to HTTPS
            http_listener.add_action(
                "redirect-http-to-https-id",
                action=elbv2.ListenerAction.redirect(
                    port="443", protocol="HTTPS", permanent=True
                ),
            )
        else:
            http_listener.add_target_groups(
                "http-target-groups-id", target_groups=[target_group]
            )

        return alb

    def create_policies(self):
        def create_policy(policy_id, name, document):
            return iam.Policy(
                self,
                policy_id,
                document=iam.PolicyDocument.from_json(document),
                policy_name=name,
            )

        return {
            "codedeploy-launch-template-permissions": create_policy(
                "codedeploy-launch-template-permissions-id",
                "CodeDeployLaunchTemplatePermissions",
                EE_CODE_DEPLOY_LAUNCH_TEMPLATE_POLICY,
            ),
            "codedeploy-ec2-permissions": create_policy(
                "codedeploy-ec2-permissions-id",
                "CodeDeploy-EC2-Permissions",
                EE_CODE_DEPLOY_EC2_POLICY,
            ),
            "codedeploy-and-related-services": create_policy(
                "codedeploy-and-related-services-id",
                "CodeDeployAndRelatedServices",
                EE_CODE_DEPLOY_POLICY,
            ),
            "ee-deployer": create_policy(
                "ee-deployer-id",
                "EEDeployer",
                EE_DEPLOYER_POLICY,
            ),
        }

    def create_roles(self) -> [str, iam.Role]:
        roles = {
            "codedeploy-ec2-instance-profile": iam.Role(
                self,
                "codedeploy-ec2-instance-profile-id",
                assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
                role_name="CodeDeployEC2InstanceProfile",
                managed_policies=[
                    iam.ManagedPolicy.from_aws_managed_policy_name(
                        "AmazonSSMReadOnlyAccess",
                    ),
                    iam.ManagedPolicy.from_aws_managed_policy_name(
                        "CloudWatchAgentServerPolicy",
                    ),
                ],
            ),
            "codedeploy-service-role": iam.Role(
                self,
                "codedeploy-service-role-id",
                assumed_by=iam.ServicePrincipal("codedeploy.amazonaws.com"),
                role_name="CodeDeployServiceRole",
            ),
        }

        roles["codedeploy-ec2-instance-profile"].attach_inline_policy(
            self.policies["codedeploy-ec2-permissions"]
        )
        roles["codedeploy-service-role"].attach_inline_policy(
            self.policies["codedeploy-launch-template-permissions"]
        )
        roles["codedeploy-service-role"].add_managed_policy(
            iam.ManagedPolicy.from_managed_policy_arn(
                self,
                "aws-code-deploy-role-id",
                "arn:aws:iam::aws:policy/service-role/AWSCodeDeployRole",
            )
        )

        return roles

    def create_cloudfront(self, alb: elbv2.ApplicationLoadBalancer):

        # Hard code the ARN due to a bug with CDK that means we can't run synth
        # with the placeholder values the SSM interface produces :(
        cert = acm.Certificate.from_certificate_arn(
            self,
            "CertArn",
            certificate_arn="arn:aws:acm:us-east-1:427217546102:certificate/e47eb373-80c0-47eb-8ff1-122004c132f3",
        )

        fqdn = StringParameter.value_from_lookup(
            self,
            "FQDN",
        )

        cloudfront_dist = cloudfront.Distribution(
            self,
            "EECloudFront",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.LoadBalancerV2Origin(alb)
            ),
            certificate=cert,
            domain_names=[fqdn],
        )

        hosted_zone = route_53.HostedZone.from_lookup(
            self, "EEDomain", domain_name=fqdn, private_zone=False
        )
        a_record = route_53.ARecord(
            self,
            "FQDN_A_RECORD_TO_CF",
            zone=hosted_zone,
            target=route_53.RecordTarget.from_alias(
                route_53_target.CloudFrontTarget(cloudfront_dist)
            ),
        )
