from aws_cdk import Duration, Stack
from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_cloudfront as cloudfront
from aws_cdk import aws_cloudfront_origins as origins
from aws_cdk import aws_codedeploy as codedeploy
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_elasticloadbalancingv2 as elbv2
from aws_cdk import aws_iam as iam
from aws_cdk import aws_route53 as route_53
from aws_cdk import aws_route53_targets as route_53_target
from aws_cdk import aws_ssm as ssm
from constructs import Construct

from cdk_stacks.stacks.code_deploy_policies import (
    EE_CODE_DEPLOY_EC2_POLICY,
    EE_CODE_DEPLOY_LAUNCH_TEMPLATE_POLICY,
    EE_CODE_DEPLOY_POLICY,
    EE_DEPLOYER_POLICY,
)

# output of
# https://eu-west-2.console.aws.amazon.com/imagebuilder/home?region=eu-west-2#/images/arn%3Aaws%3Aimagebuilder%3Aeu-west-2%3A743524368797%3Aimage%2Fdcbaseimage-ubuntu-24-04%2F0.0.5%2F1/details?region=eu-west-2
DC_BASE_IMAGE = "ami-01416396405b820af"


class EECodeDeployment(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.dc_environment = self.node.try_get_context("dc-environment")

        # self.ami = ec2.MachineImage.lookup(name=EE_IMAGE, owners=["self"])
        self.ami = ec2.MachineImage.generic_linux(
            ami_map={"eu-west-2": DC_BASE_IMAGE}
        )

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
        )

        self.code_deploy = self.create_code_deploy()

        self.cloudfront = self.create_cloudfront(self.alb)

    def create_code_deploy(self):
        codedeploy.ServerApplication(
            self, "CodeDeployApplicationID", application_name="EECodeDeploy"
        )

    def create_launch_template(
        self,
        ami: ec2.IMachineImage,
        security_group: ec2.SecurityGroup,
        role: iam.Role,
    ) -> ec2.LaunchTemplate:
        instance_types_per_env = {
            "development": "t3a.medium",
            "staging": "t3a.medium",
            "production": "t3a.medium",
            # "production": "c6a.2xlarge",
        }
        return ec2.LaunchTemplate(
            self,
            "ee-launch-template-id",
            instance_type=ec2.InstanceType(
                instance_types_per_env.get(self.dc_environment)
            ),
            machine_image=ami,
            launch_template_name="ee-launch-template",
            role=role,
            security_group=security_group,
            block_devices=[
                ec2.BlockDevice(
                    device_name="/dev/sda1",
                    volume=ec2.BlockDeviceVolume(
                        ec2.EbsDeviceProps(
                            iops=6000,
                            volume_type=ec2.EbsDeviceVolumeType.GP3,
                            volume_size=20,
                        )
                    ),
                )
            ],
        )

    def create_target_group(self):
        return elbv2.ApplicationTargetGroup(
            self,
            "ee-alb-tg-id",
            port=8001,
            protocol=elbv2.ApplicationProtocol.HTTP,
            health_check=elbv2.HealthCheck(
                enabled=True,
                healthy_threshold_count=2,
                interval=Duration.seconds(60),
                port="traffic-port",
                path="/",
                protocol=elbv2.Protocol.HTTP,
                timeout=Duration.seconds(5),
                unhealthy_threshold_count=10,
                healthy_http_codes="200",
            ),
            target_group_name="ee-alb-tg",
            target_type=elbv2.TargetType.INSTANCE,
            vpc=self.default_vpc,
            deregistration_delay=Duration.seconds(5),
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
                ec2.Peer.any_ipv4(),
                ec2.Port.tcp(443),
                "allow HTTPS from anywhere",
            )

        return alb_security_group

    def create_alb(
        self,
        security_group: ec2.SecurityGroup,
        target_group: elbv2.ApplicationTargetGroup,
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

        # Listen on HTTP
        http_listener = alb.add_listener(
            "http-listener-id", port=80, protocol=elbv2.ApplicationProtocol.HTTP
        )

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
                        "AmazonSSMManagedInstanceCore",
                    ),
                    iam.ManagedPolicy.from_aws_managed_policy_name(
                        "AmazonSSMReadOnlyAccess",
                    ),
                    iam.ManagedPolicy.from_aws_managed_policy_name(
                        "AmazonS3FullAccess",
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
        cert_arns = {
            "development": "arn:aws:acm:us-east-1:427217546102:certificate/e47eb373-80c0-47eb-8ff1-122004c132f3",
            "staging": "arn:aws:acm:us-east-1:828522531355:certificate/2fe5f310-94a2-48eb-8f16-a15f069de00a",
            "production": "arn:aws:acm:us-east-1:732292556707:certificate/3f56a526-7c50-4356-a7db-76ba48d4bf01",
        }
        cert = acm.Certificate.from_certificate_arn(
            self,
            "CertArn",
            certificate_arn=cert_arns.get(self.dc_environment),
        )

        fqdn = ssm.StringParameter.value_from_lookup(
            self,
            "FQDN",
        )

        app_origin = origins.LoadBalancerV2Origin(
            alb,
            http_port=80,
            protocol_policy=cloudfront.OriginProtocolPolicy.HTTP_ONLY,
            custom_headers={
                "X-Forwarded-Host": fqdn,
                "X-Forwarded-Proto": "https",
            },
        )

        cloudfront_dist = cloudfront.Distribution(
            self,
            "EECloudFront",
            default_behavior=cloudfront.BehaviorOptions(
                origin=app_origin,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                cache_policy=cloudfront.CachePolicy(
                    self,
                    "short_cache_not_authenticated",
                    default_ttl=Duration.minutes(10),
                    min_ttl=Duration.minutes(0),
                    max_ttl=Duration.minutes(120),
                    enable_accept_encoding_brotli=True,
                    enable_accept_encoding_gzip=True,
                    cookie_behavior=cloudfront.CacheCookieBehavior.all(),
                    query_string_behavior=cloudfront.CacheQueryStringBehavior.all(),
                    header_behavior=cloudfront.CacheHeaderBehavior.allow_list(
                        "x-csrfmiddlewaretoken",
                        "Accept",
                        "Accept-Language",
                        "Authorization",
                        "Cache-Control",
                        "Referer",
                    ),
                ),
            ),
            additional_behaviors={
                "/static/*": cloudfront.BehaviorOptions(
                    origin=origins.LoadBalancerV2Origin(
                        alb,
                        http_port=80,
                        protocol_policy=cloudfront.OriginProtocolPolicy.HTTP_ONLY,
                    ),
                    cache_policy=cloudfront.CachePolicy(
                        self,
                        "long_cache_static",
                        default_ttl=Duration.days(2000),
                        min_ttl=Duration.minutes(1),
                        max_ttl=Duration.days(2000),
                        enable_accept_encoding_brotli=True,
                        enable_accept_encoding_gzip=True,
                        header_behavior=cloudfront.CacheHeaderBehavior.allow_list(
                            "Authorization",
                        ),
                    ),
                ),
                "/api/*": cloudfront.BehaviorOptions(
                    origin=app_origin,
                    cache_policy=cloudfront.CachePolicy(
                        self,
                        "short_cache_api",
                        default_ttl=Duration.seconds(60),
                        min_ttl=Duration.seconds(0),
                        max_ttl=Duration.seconds(86400),
                        enable_accept_encoding_brotli=True,
                        enable_accept_encoding_gzip=True,
                        query_string_behavior=cloudfront.CacheQueryStringBehavior.all(),
                    ),
                ),
                "/id_creator/*": cloudfront.BehaviorOptions(
                    origin=app_origin,
                    allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                    origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER,
                    cache_policy=cloudfront.CachePolicy(
                        self,
                        "disable_cache_id_creator",
                        default_ttl=Duration.seconds(0),
                        min_ttl=Duration.seconds(0),
                        max_ttl=Duration.seconds(0),
                    ),
                ),
            },
            certificate=cert,
            domain_names=[fqdn],
            price_class=cloudfront.PriceClass.PRICE_CLASS_100,
        )

        hosted_zone = route_53.HostedZone.from_lookup(
            self, "EEDomain", domain_name=fqdn, private_zone=False
        )
        route_53.ARecord(
            self,
            "FQDN_A_RECORD_TO_CF",
            zone=hosted_zone,
            target=route_53.RecordTarget.from_alias(
                route_53_target.CloudFrontTarget(cloudfront_dist)
            ),
        )
