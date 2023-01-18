import json
import re
from pathlib import Path

import yaml
from aws_cdk.core import Stack, Construct
import aws_cdk.aws_iam as iam
import aws_cdk.aws_imagebuilder as image_builder
from aws_cdk.aws_ssm import StringParameter


COMPONENTS = [
    {
        "name": "add_user",
        "file": "add_user.yml",
        "context": {"username": "every_election"},
    },
    {
        "name": "instance_connect",
        "file": "instance_connect.yml",
    },
    {
        "name": "install_app",
        "file": "install_app.yml",
        "context": {
            "username": "every_election",
            "git_branch": "ubuntu-22.04-upgrade",
        },
    },
    {
        "name": "add_manage_py_command",
        "file": "manage_py_command.yml",
        "context": {
            "command_name": "ee-manage-py-command",
            "venv_root": "/var/www/every_election/repo/.venv",
            "manage_py_location": "/var/www/every_election/repo/manage.py",
        },
    },
]


def validate_name(name):
    name = name.replace(".", "-")
    if not re.match(r"^[-_A-Za-z-0-9][-_A-Za-z0-9 ]{1,126}[-_A-Za-z-0-9]$", name):
        raise ValueError(f"{name} isn't valid")
    return name


class EEImageUpdater(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        settings = self.load_settings()

        # Make the infrastructure configuration (the type of instance
        # that will build the image)
        infra_config = self.make_infra_config()
        recipe = self.make_recipe(settings["base_ami_id"], settings["recipe_version"])
        distribution = self.make_distribution()

        pipeline = image_builder.CfnImagePipeline(
            self,
            validate_name("EE_Pipeline"),
            name=validate_name("ee_image"),
            image_recipe_arn=recipe.attr_arn,
            infrastructure_configuration_arn=infra_config.attr_arn,
            distribution_configuration_arn=distribution.attr_arn,
            schedule=image_builder.CfnImagePipeline.ScheduleProperty(
                pipeline_execution_start_condition="EXPRESSION_MATCH_AND_DEPENDENCY_UPDATES_AVAILABLE",
                schedule_expression="rate(1 day)",
            ),
        )
        pipeline.add_depends_on(infra_config)

    def make_recipe(self, base_ami_id, version):
        components_list = []
        for component in COMPONENTS:

            if component.get("context"):
                component_arn = self.make_component(component)
                params = []
                for key, value in component["context"].items():
                    params.append(
                        image_builder.CfnImageRecipe.ComponentParameterProperty(
                            name=key, value=[value]
                        )
                    )

                configuration = (
                    image_builder.CfnImageRecipe.ComponentConfigurationProperty(
                        component_arn=component_arn,
                        parameters=params,
                    )
                )
                components_list.append(configuration)
            else:
                components_list.append(
                    {
                        "componentArn": self.make_component(component),
                    }
                )
        name = validate_name("EEImage_ubuntu")
        return image_builder.CfnImageRecipe(
            self,
            name,
            name=name,
            version=version,
            components=components_list,
            parent_image=base_ami_id,
        )

    def make_component(self, component):

        if component.get("arn"):
            return component.get("arn")

        component_path = Path() / "cdk_stacks" / "components" / component.get("file")
        component_yaml = yaml.safe_load(component_path.read_text())

        name = f"{component['name']}".replace(".", "-").replace(" ", "-")

        component_cfn = image_builder.CfnComponent(
            self,
            component["name"],
            name=name,
            platform="Linux",
            version=component_yaml.pop("component_version"),
            data=yaml.dump(component_yaml),
        )

        return component_cfn.attr_arn

    def load_settings(self):
        file = Path(__file__).parent.parent.parent / "cdk_settings.json"
        return json.load(file.open())

    def make_instance_profile(self):
        role = iam.Role(
            self,
            "EEImageRole",
            role_name="EEImageRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
        )
        role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AmazonSSMManagedInstanceCore"
            )
        )
        role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "EC2InstanceProfileForImageBuilder"
            )
        )

        # create an instance profile to attach the role
        instanceprofile = iam.CfnInstanceProfile(
            self,
            "EEImageInstanceProfile",
            instance_profile_name="EEImageInstanceProfile",
            roles=["EEImageRole"],
        )
        return instanceprofile

    def make_infra_config(self) -> image_builder.CfnInfrastructureConfiguration:
        """
        https://docs.aws.amazon.com/imagebuilder/latest/userguide/manage-infra-config.html

        Infrastructure configurations specify the Amazon EC2 infrastructure
        that Image Builder uses to build and test your EC2 Image Builder image

        :param instance_profile:
        :return:
        """

        # Make the profile that will be used by the image builder for this
        # instance
        instance_profile = self.make_instance_profile()

        infraconfig = image_builder.CfnInfrastructureConfiguration(
            self,
            "EEImageInfraConfig",
            name="EEImageInfraConfig",
            instance_types=["t3.xlarge"],
            instance_profile_name="EEImageInstanceProfile",
        )

        # infrastructure need to wait for instance profile
        # to complete before beginning deployment.
        infraconfig.add_depends_on(instance_profile)
        return infraconfig

    def make_distribution(self):
        org_id = StringParameter.value_for_string_parameter(self, "OrganisationID")
        dist_name = validate_name("EE-distribution")
        return image_builder.CfnDistributionConfiguration(
            self,
            dist_name,
            name=dist_name,
            distributions=[
                image_builder.CfnDistributionConfiguration.DistributionProperty(
                    region="eu-west-2",
                    ami_distribution_configuration=image_builder.CfnDistributionConfiguration.AmiDistributionConfigurationProperty(
                        launch_permission_configuration=image_builder.CfnDistributionConfiguration.LaunchPermissionConfigurationProperty(
                            organization_arns=[org_id]
                        ),
                    ),
                )
            ],
        )
